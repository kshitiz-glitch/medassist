/**
 * Patient Dashboard
 * Main dashboard for patients with appointment overview and chat
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Calendar,
    MessageCircle,
    Clock,
    CheckCircle,
    ArrowRight,
    User,
    Stethoscope
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { patientsApi, doctorsApi, Appointment, Doctor } from '../api/client';
import { AppointmentList } from '../components/AppointmentCard';
import ChatInterface from '../components/ChatInterface';

export function PatientDashboard() {
    const { user } = useAuth();
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [doctors, setDoctors] = useState<Doctor[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [appts, docs] = await Promise.all([
                patientsApi.getAppointments({ upcoming_only: true }),
                doctorsApi.list()
            ]);
            setAppointments(appts);
            setDoctors(docs);
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const upcomingCount = appointments.filter(a => a.status === 'scheduled').length;
    const completedCount = appointments.filter(a => a.status === 'completed').length;

    return (
        <div>
            <div className="page-header">
                <h1 className="page-title">Welcome back! 👋</h1>
                <p className="page-subtitle">
                    Manage your appointments and connect with doctors
                </p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon primary">
                        <Calendar size={24} />
                    </div>
                    <div className="stat-info">
                        <h4>{upcomingCount}</h4>
                        <p>Upcoming Appointments</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon success">
                        <CheckCircle size={24} />
                    </div>
                    <div className="stat-info">
                        <h4>{completedCount}</h4>
                        <p>Completed Visits</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon accent">
                        <Stethoscope size={24} />
                    </div>
                    <div className="stat-info">
                        <h4>{doctors.length}</h4>
                        <p>Available Doctors</p>
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
                            Book Appointment
                        </h3>
                    </div>
                    <ChatInterface
                        welcomeMessage="Hello! I can help you book an appointment with a doctor. Just tell me which doctor you'd like to see and when!"
                        placeholder="e.g., I want to book with Dr. Ahuja tomorrow morning..."
                    />
                </div>

                {/* Appointments Section */}
                <div>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '1rem'
                    }}>
                        <h3 style={{ margin: 0 }}>
                            <Calendar size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                            Upcoming Appointments
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
                                    appointments={appointments.slice(0, 5)}
                                    emptyMessage="No upcoming appointments. Use the chat to book one!"
                                />
                            )}
                        </div>
                    </div>

                    {/* Available Doctors */}
                    <div style={{ marginTop: '1.5rem' }}>
                        <h3 style={{ marginBottom: '1rem' }}>
                            <User size={20} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                            Available Doctors
                        </h3>
                        <div className="card">
                            <div className="card-body" style={{ padding: '0' }}>
                                {doctors.slice(0, 3).map((doctor) => (
                                    <div
                                        key={doctor.id}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '1rem',
                                            padding: '1rem 1.5rem',
                                            borderBottom: '1px solid var(--gray-100)'
                                        }}
                                    >
                                        <div style={{
                                            width: '3rem',
                                            height: '3rem',
                                            borderRadius: '50%',
                                            background: 'var(--gradient-primary)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            color: 'white',
                                            fontWeight: 600
                                        }}>
                                            {doctor.name.split(' ').map(n => n[0]).join('')}
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontWeight: 600 }}>{doctor.name}</div>
                                            <div style={{ fontSize: '0.875rem', color: 'var(--gray-500)' }}>
                                                {doctor.specialty}
                                            </div>
                                        </div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>
                                            {doctor.consultation_duration} min
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default PatientDashboard;
