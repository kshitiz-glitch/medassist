/**
 * Doctor Dashboard
 * Main dashboard for doctors with schedule overview, stats, and reports
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Calendar,
    MessageCircle,
    Users,
    Clock,
    TrendingUp,
    Bell,
    Send,
    ArrowRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { appointmentsApi, doctorsApi, authApi, Appointment, DoctorStats, Doctor } from '../api/client';
import { AppointmentList } from '../components/AppointmentCard';
import ChatInterface from '../components/ChatInterface';

export function DoctorDashboard() {
    const { user } = useAuth();
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [stats, setStats] = useState<DoctorStats | null>(null);
    const [doctorProfile, setDoctorProfile] = useState<Doctor | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // Get doctor profile
            const profile = await authApi.getProfile() as Doctor;
            setDoctorProfile(profile);

            // Get today's appointments
            const today = new Date().toISOString().split('T')[0];
            const appts = await appointmentsApi.list({ date: today });
            setAppointments(appts);

            // Get stats
            if (profile?.id) {
                const doctorStats = await doctorsApi.getStats(profile.id);
                setStats(doctorStats);
            }
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">
                    Good {getGreeting()}, Dr. {doctorProfile?.name?.split(' ').pop() || 'Doctor'}! 👋
                </h1>
                <p className="page-subtitle">
                    Here's your schedule and practice overview for today
                </p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon primary">
                        <Calendar size={24} />
                    </div>
                    <div className="stat-info">
                        <h4>{stats?.today_appointments || 0}</h4>
                        <p>Today's Appointments</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon accent">
                        <Clock size={24} />
                    </div>
                    <div className="stat-info">
                        <h4>{stats?.yesterday_visits || 0}</h4>
                        <p>Yesterday's Visits</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon warning">
                        <TrendingUp size={24} />
                    </div>
                    <div className="stat-info">
                        <h4>{stats?.tomorrow_appointments || 0}</h4>
                        <p>Tomorrow's Schedule</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon success">
                        <Users size={24} />
                    </div>
                    <div className="stat-info">
                        <h4>{stats?.total_patients || 0}</h4>
                        <p>Total Patients</p>
                    </div>
                </div>
            </div>

            {/* Main Content Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '1.5rem',
                marginTop: '1.5rem'
            }}>
                {/* Chat Section */}
                <div>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '1rem'
                    }}>
                        <h3 style={{ margin: 0 }}>
                            <MessageCircle size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                            AI Assistant
                        </h3>
                    </div>
                    <ChatInterface
                        welcomeMessage="Hello Doctor! I can help you with patient statistics, scheduling, and generating reports. Try asking me things like 'How many patients visited yesterday?' or 'How many appointments do I have tomorrow?'"
                        placeholder="e.g., How many patients with fever this week?"
                    />
                </div>

                {/* Schedule Section */}
                <div>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '1rem'
                    }}>
                        <h3 style={{ margin: 0 }}>
                            <Calendar size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                            Today's Schedule
                        </h3>
                        <Link to="/appointments" className="btn btn-ghost btn-sm">
                            View All <ArrowRight size={14} />
                        </Link>
                    </div>

                    <div className="card">
                        <div className="card-body">
                            {isLoading ? (
                                <div style={{ textAlign: 'center', padding: '2rem' }}>
                                    <div className="loading-spinner" style={{ margin: '0 auto' }} />
                                </div>
                            ) : (
                                <AppointmentList
                                    appointments={appointments}
                                    emptyMessage="No appointments scheduled for today"
                                    showActions
                                />
                            )}
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div style={{ marginTop: '1.5rem' }}>
                        <h3 style={{ marginBottom: '1rem' }}>
                            <Bell size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                            Quick Actions
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <QuickActionCard
                                icon={<Send size={20} />}
                                title="Send Report"
                                description="Send today's summary to Slack"
                                color="primary"
                            />
                            <QuickActionCard
                                icon={<Users size={20} />}
                                title="Patient Stats"
                                description="View detailed analytics"
                                color="accent"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

interface QuickActionCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    color: 'primary' | 'accent' | 'success' | 'warning';
}

function QuickActionCard({ icon, title, description, color }: QuickActionCardProps) {
    const colorMap = {
        primary: 'var(--primary-600)',
        accent: 'var(--accent-600)',
        success: 'var(--success-600)',
        warning: 'var(--warning-600)'
    };

    const bgMap = {
        primary: 'var(--primary-50)',
        accent: 'var(--accent-50)',
        success: 'rgba(34, 197, 94, 0.1)',
        warning: 'rgba(245, 158, 11, 0.1)'
    };

    return (
        <div
            className="card"
            style={{
                cursor: 'pointer',
                transition: 'all var(--transition-normal)'
            }}
        >
            <div className="card-body" style={{ padding: '1.25rem' }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem'
                }}>
                    <div style={{
                        width: '2.5rem',
                        height: '2.5rem',
                        borderRadius: 'var(--radius-lg)',
                        background: bgMap[color],
                        color: colorMap[color],
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        {icon}
                    </div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{title}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>{description}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) return 'Morning';
    if (hour < 17) return 'Afternoon';
    return 'Evening';
}

export default DoctorDashboard;
