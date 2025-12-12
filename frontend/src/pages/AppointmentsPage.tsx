/**
 * Appointments Page
 * Lists all appointments for current user
 */

import React, { useEffect, useState } from 'react';
import { Calendar, Filter, Plus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { appointmentsApi, patientsApi, Appointment } from '../api/client';
import { AppointmentList } from '../components/AppointmentCard';

type FilterType = 'all' | 'scheduled' | 'completed' | 'cancelled';

export function AppointmentsPage() {
    const { user } = useAuth();
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [filter, setFilter] = useState<FilterType>('all');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadAppointments();
    }, [filter]);

    const loadAppointments = async () => {
        setIsLoading(true);
        try {
            let appts: Appointment[];

            if (user?.role === 'patient') {
                appts = await patientsApi.getAppointments(
                    filter !== 'all' ? { status: filter } : undefined
                );
            } else {
                appts = await appointmentsApi.list(
                    filter !== 'all' ? { status: filter } : undefined
                );
            }

            setAppointments(appts);
        } catch (error) {
            console.error('Failed to load appointments:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const filters: { value: FilterType; label: string }[] = [
        { value: 'all', label: 'All' },
        { value: 'scheduled', label: 'Scheduled' },
        { value: 'completed', label: 'Completed' },
        { value: 'cancelled', label: 'Cancelled' }
    ];

    return (
        <div>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title">
                        <Calendar size={28} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                        {user?.role === 'doctor' ? 'Schedule' : 'My Appointments'}
                    </h1>
                    <p className="page-subtitle">
                        {user?.role === 'doctor'
                            ? 'View and manage your patient appointments'
                            : 'View your upcoming and past appointments'
                        }
                    </p>
                </div>

                {user?.role === 'patient' && (
                    <a href="/chat" className="btn btn-primary">
                        <Plus size={18} />
                        Book New
                    </a>
                )}
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: '1.5rem' }}>
                <div className="card-body" style={{ padding: '0.75rem 1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Filter size={18} style={{ color: 'var(--gray-500)' }} />
                        <span style={{ color: 'var(--gray-500)', marginRight: '0.5rem' }}>Filter:</span>
                        {filters.map((f) => (
                            <button
                                key={f.value}
                                onClick={() => setFilter(f.value)}
                                className={`btn btn-sm ${filter === f.value ? 'btn-primary' : 'btn-ghost'}`}
                            >
                                {f.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Appointments List */}
            <div className="card">
                <div className="card-body">
                    {isLoading ? (
                        <div style={{ textAlign: 'center', padding: '3rem' }}>
                            <div className="loading-spinner" style={{ margin: '0 auto' }} />
                        </div>
                    ) : (
                        <AppointmentList
                            appointments={appointments}
                            emptyMessage={
                                filter === 'all'
                                    ? 'No appointments found'
                                    : `No ${filter} appointments`
                            }
                            showActions={user?.role === 'doctor'}
                        />
                    )}
                </div>
            </div>

            {/* Stats Footer */}
            {!isLoading && appointments.length > 0 && (
                <div style={{
                    marginTop: '1rem',
                    textAlign: 'center',
                    color: 'var(--gray-500)',
                    fontSize: '0.875rem'
                }}>
                    Showing {appointments.length} appointment{appointments.length !== 1 ? 's' : ''}
                </div>
            )}
        </div>
    );
}

export default AppointmentsPage;
