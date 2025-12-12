/**
 * Appointment Card Component
 * Displays individual appointment information
 */

import React from 'react';
import { Clock, User, Calendar, MoreVertical } from 'lucide-react';
import { Appointment } from '../api/client';

interface AppointmentCardProps {
    appointment: Appointment;
    showActions?: boolean;
    onCancel?: (id: string) => void;
    onReschedule?: (id: string) => void;
}

export function AppointmentCard({
    appointment,
    showActions = false,
    onCancel,
    onReschedule
}: AppointmentCardProps) {
    const date = new Date(appointment.scheduled_time);
    const time = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
    const dateStr = date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
    });

    const statusColors: Record<string, string> = {
        scheduled: 'scheduled',
        completed: 'completed',
        cancelled: 'cancelled',
        rescheduled: 'scheduled',
        no_show: 'cancelled'
    };

    return (
        <div className={`appointment-card ${statusColors[appointment.status]}`}>
            <div className="appointment-info">
                <div className="appointment-time">
                    <div className="time">{time.split(' ')[0]}</div>
                    <div className="period">{time.split(' ')[1]}</div>
                </div>

                <div className="appointment-details">
                    <h4>
                        {appointment.doctor_name || appointment.doctor?.name || `Doctor ID: ${appointment.doctor_id.slice(0, 8)}`}
                    </h4>
                    <p style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Calendar size={14} />
                        {dateStr}
                        {appointment.symptoms && (
                            <>
                                <span style={{ opacity: 0.5 }}>•</span>
                                {appointment.symptoms.slice(0, 30)}
                                {appointment.symptoms.length > 30 && '...'}
                            </>
                        )}
                    </p>
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className={`appointment-status ${statusColors[appointment.status]}`}>
                    {appointment.status}
                </span>

                {showActions && appointment.status === 'scheduled' && (
                    <div className="dropdown">
                        <button className="btn btn-ghost btn-icon">
                            <MoreVertical size={18} />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

interface AppointmentListProps {
    appointments: Appointment[];
    emptyMessage?: string;
    showActions?: boolean;
}

export function AppointmentList({
    appointments,
    emptyMessage = 'No appointments found',
    showActions = false
}: AppointmentListProps) {
    if (appointments.length === 0) {
        return (
            <div style={{
                textAlign: 'center',
                padding: '3rem',
                color: 'var(--gray-500)'
            }}>
                <Calendar size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                <p>{emptyMessage}</p>
            </div>
        );
    }

    return (
        <div className="appointment-list">
            {appointments.map((appointment) => (
                <AppointmentCard
                    key={appointment.id}
                    appointment={appointment}
                    showActions={showActions}
                />
            ))}
        </div>
    );
}

export default AppointmentCard;
