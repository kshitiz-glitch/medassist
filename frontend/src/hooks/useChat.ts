/**
 * useChat Hook
 * Manages chat state and interactions with the AI agent
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { chatApi, ChatMessage, ChatResponse } from '../api/client';

interface UseChatReturn {
    messages: ChatMessage[];
    isLoading: boolean;
    error: string | null;
    sessionId: string | null;
    toolsUsed: string[];
    sendMessage: (message: string) => Promise<void>;
    clearChat: () => void;
    startNewSession: () => Promise<void>;
}

export function useChat(): UseChatReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [toolsUsed, setToolsUsed] = useState<string[]>([]);

    const messagesRef = useRef(messages);
    messagesRef.current = messages;

    // Load existing session on mount
    useEffect(() => {
        const savedSessionId = localStorage.getItem('chatSessionId');
        if (savedSessionId) {
            setSessionId(savedSessionId);
            // Optionally load history
            chatApi.getSession(savedSessionId)
                .then((session) => {
                    const formattedMessages = session.messages.map(msg => ({
                        role: msg.role as 'user' | 'assistant',
                        content: msg.content,
                        timestamp: msg.timestamp,
                    }));
                    setMessages(formattedMessages);
                })
                .catch(() => {
                    // Session doesn't exist, start fresh
                    localStorage.removeItem('chatSessionId');
                });
        }
    }, []);

    const sendMessage = useCallback(async (message: string) => {
        if (!message.trim()) return;

        setIsLoading(true);
        setError(null);

        // Add user message immediately
        const userMessage: ChatMessage = {
            role: 'user',
            content: message,
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMessage]);

        try {
            const response = await chatApi.sendMessage(message, sessionId || undefined);

            // Save session ID
            if (response.session_id && response.session_id !== sessionId) {
                setSessionId(response.session_id);
                localStorage.setItem('chatSessionId', response.session_id);
            }

            // Track tools used
            if (response.tools_used && response.tools_used.length > 0) {
                setToolsUsed(prev => [...new Set([...prev, ...response.tools_used])]);
            }

            // Add assistant response
            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: response.message,
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, assistantMessage]);

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
            setError(errorMessage);

            // Add error message
            const errorMessageObj: ChatMessage = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, errorMessageObj]);
        } finally {
            setIsLoading(false);
        }
    }, [sessionId]);

    const clearChat = useCallback(() => {
        if (sessionId) {
            chatApi.clearSession(sessionId).catch(console.error);
        }
        setMessages([]);
        setSessionId(null);
        setToolsUsed([]);
        setError(null);
        localStorage.removeItem('chatSessionId');
    }, [sessionId]);

    const startNewSession = useCallback(async () => {
        clearChat();
        try {
            const { session_id } = await chatApi.createNewSession();
            setSessionId(session_id);
            localStorage.setItem('chatSessionId', session_id);
        } catch (err) {
            console.error('Failed to create new session:', err);
        }
    }, [clearChat]);

    return {
        messages,
        isLoading,
        error,
        sessionId,
        toolsUsed,
        sendMessage,
        clearChat,
        startNewSession,
    };
}
