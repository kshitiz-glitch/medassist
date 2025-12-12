/**
 * Chat Interface Component
 * Main chat UI for interacting with the AI agent
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, RefreshCw, Loader2 } from 'lucide-react';
import { useChat } from '../hooks/useChat';
import { ChatMessage } from '../api/client';

interface ChatInterfaceProps {
    welcomeMessage?: string;
    placeholder?: string;
}

export function ChatInterface({
    welcomeMessage = "Hello! I'm your healthcare assistant. How can I help you today?",
    placeholder = "Type your message..."
}: ChatInterfaceProps) {
    const { messages, isLoading, sendMessage, clearChat, toolsUsed } = useChat();
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input on mount
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const message = input.trim();
        setInput('');
        await sendMessage(message);
        inputRef.current?.focus();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const displayMessages: ChatMessage[] = messages.length > 0
        ? messages
        : [{ role: 'assistant', content: welcomeMessage }];

    return (
        <div className="chat-container card" style={{ height: '600px' }}>
            {/* Header */}
            <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div className="chat-avatar assistant">
                        <Bot size={20} />
                    </div>
                    <div>
                        <h4 style={{ margin: 0, fontSize: '1rem' }}>Healthcare Assistant</h4>
                        <span className="text-muted" style={{ fontSize: '0.8rem' }}>
                            {isLoading ? 'Thinking...' : 'Online'}
                        </span>
                    </div>
                </div>
                <button
                    className="btn btn-ghost btn-icon"
                    onClick={clearChat}
                    title="New conversation"
                >
                    <RefreshCw size={18} />
                </button>
            </div>

            {/* Messages */}
            <div className="chat-messages">
                {displayMessages.map((msg, index) => (
                    <MessageBubble key={index} message={msg} />
                ))}

                {/* Loading indicator */}
                {isLoading && (
                    <div className="chat-message assistant">
                        <div className="chat-avatar assistant">
                            <Bot size={18} />
                        </div>
                        <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Loader2 size={16} className="animate-spin" />
                            <span>Thinking...</span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Tools Used Badge */}
            {toolsUsed.length > 0 && (
                <div style={{
                    padding: '0.5rem 1rem',
                    background: 'var(--primary-50)',
                    fontSize: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    flexWrap: 'wrap'
                }}>
                    <span style={{ color: 'var(--primary-700)', fontWeight: 600 }}>Tools used:</span>
                    {toolsUsed.slice(-3).map((tool, i) => (
                        <span
                            key={i}
                            style={{
                                background: 'var(--primary-100)',
                                color: 'var(--primary-700)',
                                padding: '0.125rem 0.5rem',
                                borderRadius: '9999px',
                                fontSize: '0.7rem'
                            }}
                        >
                            {tool.replace(/_/g, ' ')}
                        </span>
                    ))}
                </div>
            )}

            {/* Input */}
            <form className="chat-input-container" onSubmit={handleSubmit}>
                <input
                    ref={inputRef}
                    type="text"
                    className="chat-input"
                    placeholder={placeholder}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    className="chat-send-btn"
                    disabled={!input.trim() || isLoading}
                >
                    <Send size={18} />
                </button>
            </form>
        </div>
    );
}

interface MessageBubbleProps {
    message: ChatMessage;
}

function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === 'user';

    return (
        <div className={`chat-message ${message.role}`}>
            <div className={`chat-avatar ${message.role}`}>
                {isUser ? <User size={18} /> : <Bot size={18} />}
            </div>
            <div className={`chat-bubble ${message.role}`}>
                <MessageContent content={message.content} />
            </div>
        </div>
    );
}

interface MessageContentProps {
    content: string;
}

function MessageContent({ content }: MessageContentProps) {
    // Simple markdown-like formatting
    const lines = content.split('\n');

    return (
        <div>
            {lines.map((line, i) => {
                // Check for bullet points
                if (line.startsWith('• ') || line.startsWith('- ')) {
                    return <div key={i} style={{ paddingLeft: '1rem', marginBottom: '0.25rem' }}>• {line.slice(2)}</div>;
                }
                // Check for headers
                if (line.startsWith('**') && line.endsWith('**')) {
                    return <div key={i} style={{ fontWeight: 600, marginTop: '0.5rem' }}>{line.slice(2, -2)}</div>;
                }
                // Check for success/checkmark
                if (line.includes('✅')) {
                    return <div key={i} style={{ color: 'var(--success-600)', fontWeight: 500 }}>{line}</div>;
                }
                // Empty line
                if (!line.trim()) {
                    return <div key={i} style={{ height: '0.5rem' }} />;
                }
                return <div key={i}>{line}</div>;
            })}
        </div>
    );
}

export default ChatInterface;
