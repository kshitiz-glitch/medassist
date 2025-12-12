"""
AI Agent Controller
Orchestrates LLM (Mistral AI) and MCP tools for agentic behavior with context management.
"""

import json
import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from mistralai import Mistral
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.config import settings
from app.database import async_session_maker
from app.models import (
    User, Doctor, Patient, ConversationHistory, 
    PromptHistory, UserRole
)
from app.mcp_server import mcp_tools, MCPTools


class DoctorAssistantAgent:
    """
    Agentic AI controller that orchestrates Mistral LLM and MCP tools.
    Supports multi-turn conversations with context management.
    """
    
    def __init__(self):
        self.client = Mistral(api_key=settings.mistral_api_key)
        self.model = settings.mistral_model
        self.tools = self._convert_tools_to_mistral_format()
    
    def _convert_tools_to_mistral_format(self) -> List[dict]:
        """Convert OpenAI-style tools to Mistral format."""
        openai_tools = MCPTools.get_tool_definitions()
        # Mistral uses the same format as OpenAI for tools
        return openai_tools
    
    def _get_system_prompt(self, user_role: str, user_context: dict = None) -> str:
        """Build role-specific system prompt."""
        
        base_prompt = """You are a helpful medical appointment assistant for a healthcare clinic. 
You help patients book appointments with doctors and help doctors manage their schedules and view reports.

IMPORTANT GUIDELINES:
1. Be professional, friendly, and empathetic
2. Always confirm important details before taking actions
3. Use the provided tools to check availability, book appointments, and retrieve information
4. Maintain context from previous messages in the conversation
5. If you're unsure about something, ask for clarification
6. Format responses in a clear, easy-to-read manner
7. Include relevant details like appointment times, doctor names, and confirmation numbers

CURRENT DATE AND TIME: """ + datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        if user_role == "patient":
            role_prompt = """

PATIENT CONTEXT:
You are helping a patient. They can:
- Ask about doctor availability
- Book, reschedule, or cancel appointments
- Check their upcoming appointments
- Ask questions about their scheduled visits

When booking appointments:
1. First check doctor availability using check_doctor_availability
2. Present available slots clearly
3. Confirm the chosen slot before booking
4. Use schedule_appointment to complete the booking
5. Confirm success and provide appointment details

For multi-turn conversations, remember:
- If patient has already asked about a specific doctor, don't ask again
- If they say "book the 3 PM slot", use context to know which doctor
- Maintain context about dates and doctors discussed"""

        elif user_role == "doctor":
            role_prompt = """

DOCTOR CONTEXT:
You are helping a doctor manage their practice. They can:
- View patient statistics (yesterday's visits, today's appointments, etc.)
- Get summary reports about specific symptoms or conditions
- Send reports via Slack or other channels
- View their schedule

When generating reports:
1. Use get_patient_statistics to gather data
2. Format the report in a professional, scannable format
3. Offer to send the report via their preferred channel
4. Use send_doctor_report when they want to receive it

For queries like "How many patients with fever?", use the by_symptom query type."""

        else:
            role_prompt = ""
        
        context_prompt = ""
        if user_context:
            context_prompt = f"""

CONVERSATION CONTEXT:
{json.dumps(user_context, indent=2)}

Use this context to understand references to previous messages."""
        
        return base_prompt + role_prompt + context_prompt
    
    async def process_message(
        self,
        user_message: str,
        user_id: str,
        session_id: Optional[str] = None,
        user_role: str = "patient"
    ) -> Dict[str, Any]:
        """
        Process a user message and return an AI response.
        Handles tool calling, context management, and multi-turn conversations.
        """
        start_time = time.time()
        tools_used = []
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        async with async_session_maker() as session:
            # Get or create conversation history
            conversation = await self._get_or_create_conversation(
                session, user_id, session_id, user_role
            )
            
            # Build messages with context
            messages = self._build_messages(
                conversation, 
                user_message, 
                user_role,
                await self._get_user_context(session, user_id, user_role)
            )
            
            # Add user message to history
            new_messages = conversation.messages.copy() if conversation.messages else []
            new_messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            conversation.messages = new_messages
            flag_modified(conversation, 'messages')
            
            # Get context for agent (e.g., doctor being discussed)
            context = conversation.context or {}
            
            # If user is a doctor, add their doctor_id to context
            if user_role == "doctor":
                doctor = await self._get_doctor_profile(session, user_id)
                if doctor:
                    context["doctor_id"] = str(doctor.id)
                    context["doctor_name"] = doctor.name
            
            # Call Mistral LLM with tools
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
            
            # Handle tool calls
            while assistant_message.tool_calls:
                # Execute each tool call
                tool_results = []
                
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tools_used.append(tool_name)
                    
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Inject doctor_id for doctor tools if needed
                    if user_role == "doctor" and "doctor_id" not in arguments:
                        if tool_name in ["get_patient_statistics", "send_doctor_report", "get_appointment_details"]:
                            if "doctor_id" in context:
                                arguments["doctor_id"] = context["doctor_id"]
                    
                    # Inject patient email for patient tools
                    if user_role == "patient" and "patient_email" not in arguments:
                        if tool_name == "schedule_appointment":
                            user = await session.get(User, uuid.UUID(user_id))
                            if user:
                                arguments["patient_email"] = user.email
                    
                    # Update context with doctor info if checking availability
                    if tool_name == "check_doctor_availability":
                        result = await mcp_tools.execute_tool(tool_name, arguments)
                        if result.get("success") and result.get("doctor_id"):
                            context["last_doctor_id"] = result["doctor_id"]
                            context["last_doctor_name"] = result.get("doctor_name")
                            context["last_date"] = result.get("date")
                            context["available_slots"] = result.get("available_slots", [])
                    else:
                        # Use context for partial references
                        if tool_name == "schedule_appointment":
                            if "doctor_name" not in arguments and "last_doctor_name" in context:
                                arguments["doctor_name"] = context["last_doctor_name"]
                        
                        result = await mcp_tools.execute_tool(tool_name, arguments)
                    
                    tool_results.append({
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id
                    })
                
                # Update conversation context
                conversation.context = context.copy()
                flag_modified(conversation, 'context')
                
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })
                
                # Add tool results
                messages.extend(tool_results)
                
                # Get next response
                response = self.client.chat.complete(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                assistant_message = response.choices[0].message
            
            # Final response
            final_response = assistant_message.content or "I apologize, but I couldn't generate a response. Please try again."
            
            # Update conversation history
            final_messages = conversation.messages.copy() if conversation.messages else []
            final_messages.append({
                "role": "assistant",
                "content": final_response,
                "timestamp": datetime.now().isoformat(),
                "tools_used": tools_used
            })
            conversation.messages = final_messages
            flag_modified(conversation, 'messages')
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Save prompt history (Bonus feature)
            prompt_history = PromptHistory(
                user_id=uuid.UUID(user_id),
                session_id=session_id,
                prompt=user_message,
                response=final_response,
                tools_used=tools_used,
                processing_time_ms=processing_time_ms,
                tokens_used=response.usage.total_tokens if response.usage else None,
                success=True
            )
            session.add(prompt_history)
            
            # Commit all changes
            await session.commit()
            
            return {
                "message": final_response,
                "session_id": session_id,
                "tools_used": tools_used,
                "context": context,
                "processing_time_ms": processing_time_ms
            }
    
    async def _get_or_create_conversation(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        user_role: str
    ) -> ConversationHistory:
        """Get existing conversation or create new one."""
        result = await session.execute(
            select(ConversationHistory).where(
                and_(
                    ConversationHistory.user_id == uuid.UUID(user_id),
                    ConversationHistory.session_id == session_id,
                    ConversationHistory.is_active == True
                )
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            conversation = ConversationHistory(
                user_id=uuid.UUID(user_id),
                session_id=session_id,
                messages=[],
                context={}
            )
            session.add(conversation)
            await session.flush()
        
        return conversation
    
    def _build_messages(
        self,
        conversation: ConversationHistory,
        user_message: str,
        user_role: str,
        user_context: dict = None
    ) -> List[dict]:
        """Build message list for LLM including history."""
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(user_role, user_context)
            }
        ]
        
        # Add conversation history (last 10 messages for context window management)
        history = conversation.messages[-10:] if conversation.messages else []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    async def _get_user_context(
        self,
        session: AsyncSession,
        user_id: str,
        user_role: str
    ) -> dict:
        """Get additional context about the user."""
        context = {}
        
        try:
            user = await session.get(User, uuid.UUID(user_id))
            if not user:
                return context
            
            context["user_email"] = user.email
            
            if user_role == "patient":
                patient_result = await session.execute(
                    select(Patient).where(Patient.user_id == user.id)
                )
                patient = patient_result.scalar_one_or_none()
                if patient:
                    context["patient_name"] = patient.name
                    context["patient_id"] = str(patient.id)
            
            elif user_role == "doctor":
                doctor_result = await session.execute(
                    select(Doctor).where(Doctor.user_id == user.id)
                )
                doctor = doctor_result.scalar_one_or_none()
                if doctor:
                    context["doctor_name"] = doctor.name
                    context["doctor_id"] = str(doctor.id)
                    context["specialty"] = doctor.specialty
        
        except Exception as e:
            print(f"Error getting user context: {e}")
        
        return context
    
    async def _get_doctor_profile(
        self,
        session: AsyncSession,
        user_id: str
    ) -> Optional[Doctor]:
        """Get doctor profile for a user."""
        result = await session.execute(
            select(Doctor).where(Doctor.user_id == uuid.UUID(user_id))
        )
        return result.scalar_one_or_none()
    
    async def get_prompt_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Get prompt history for a user (Bonus feature)."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(PromptHistory)
                .where(PromptHistory.user_id == uuid.UUID(user_id))
                .order_by(PromptHistory.created_at.desc())
                .limit(limit)
            )
            history = result.scalars().all()
            
            return [
                {
                    "id": str(h.id),
                    "session_id": h.session_id,
                    "prompt": h.prompt,
                    "response": h.response,
                    "tools_used": h.tools_used,
                    "processing_time_ms": h.processing_time_ms,
                    "created_at": h.created_at.isoformat()
                }
                for h in history
            ]
    
    async def clear_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> bool:
        """Clear a conversation session."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(ConversationHistory).where(
                    and_(
                        ConversationHistory.user_id == uuid.UUID(user_id),
                        ConversationHistory.session_id == session_id
                    )
                )
            )
            conversation = result.scalar_one_or_none()
            
            if conversation:
                conversation.is_active = False
                await session.commit()
                return True
            
            return False


# Global agent instance
agent = DoctorAssistantAgent()
