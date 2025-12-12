/**
 * Chat Page
 * Dedicated page for AI chat interactions
 */

import React from 'react';
import { MessageCircle, History, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ChatInterface from '../components/ChatInterface';

export function ChatPage() {
    const { user } = useAuth();
    const isDoctor = user?.role === 'doctor';

    const patientExamples = [
        "I want to book an appointment with Dr. Ahuja tomorrow morning",
        "What doctors are available for pediatrics?",
        "Check Dr. Sharma's availability for Friday",
        "I need to reschedule my appointment",
        "Cancel my appointment for tomorrow"
    ];

    const doctorExamples = [
        "How many patients visited yesterday?",
        "How many appointments do I have today?",
        "How many patients with fever this week?",
        "Send me a summary report on Slack",
        "What's my schedule for tomorrow?"
    ];

    const examples = isDoctor ? doctorExamples : patientExamples;

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">
                    <MessageCircle size={28} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                    {isDoctor ? 'AI Assistant' : 'Book Appointment'}
                </h1>
                <p className="page-subtitle">
                    {isDoctor
                        ? 'Ask questions about your patients, schedule, and generate reports'
                        : 'Use natural language to book, reschedule, or cancel appointments'
                    }
                </p>
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: '2fr 1fr',
                gap: '1.5rem'
            }}>
                {/* Main Chat */}
                <ChatInterface
                    welcomeMessage={isDoctor
                        ? "Hello Doctor! I'm your AI assistant. I can help you with patient statistics, scheduling, and reports. What would you like to know?"
                        : "Hello! I'm your healthcare assistant. I can help you book appointments with our doctors. Just tell me which doctor you'd like to see and when!"
                    }
                    placeholder={isDoctor
                        ? "Ask about patients, schedule, or reports..."
                        : "e.g., I want to book with Dr. Ahuja tomorrow at 10 AM"
                    }
                />

                {/* Sidebar */}
                <div>
                    {/* Example Prompts */}
                    <div className="card" style={{ marginBottom: '1.5rem' }}>
                        <div className="card-header">
                            <h4 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <Sparkles size={18} />
                                Try These Prompts
                            </h4>
                        </div>
                        <div className="card-body" style={{ padding: '0.5rem' }}>
                            {examples.map((example, index) => (
                                <div
                                    key={index}
                                    style={{
                                        padding: '0.75rem 1rem',
                                        fontSize: '0.875rem',
                                        color: 'var(--gray-600)',
                                        borderBottom: index < examples.length - 1 ? '1px solid var(--gray-100)' : 'none',
                                        cursor: 'pointer',
                                        transition: 'background var(--transition-fast)'
                                    }}
                                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--gray-50)'}
                                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                                >
                                    "{example}"
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Features */}
                    <div className="card">
                        <div className="card-header">
                            <h4 style={{ margin: 0 }}>
                                ✨ Features
                            </h4>
                        </div>
                        <div className="card-body">
                            <ul style={{
                                listStyle: 'none',
                                padding: 0,
                                margin: 0,
                                fontSize: '0.875rem',
                                color: 'var(--gray-600)'
                            }}>
                                <li style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--success-500)' }}>✓</span>
                                    Multi-turn conversations with context
                                </li>
                                <li style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--success-500)' }}>✓</span>
                                    Natural language understanding
                                </li>
                                <li style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--success-500)' }}>✓</span>
                                    Automatic calendar integration
                                </li>
                                <li style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--success-500)' }}>✓</span>
                                    Email confirmations
                                </li>
                                <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                                    <span style={{ color: 'var(--success-500)' }}>✓</span>
                                    {isDoctor ? 'Slack/WhatsApp reports' : 'Smart rescheduling'}
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ChatPage;
