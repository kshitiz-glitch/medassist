/**
 * Navigation Component
 * Sidebar navigation for the dashboard
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    Home,
    MessageCircle,
    Calendar,
    Users,
    BarChart3,
    Settings,
    LogOut,
    Stethoscope,
    User
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Navigation() {
    const location = useLocation();
    const { user, logout } = useAuth();

    const isDoctor = user?.role === 'doctor';

    const patientLinks = [
        { path: '/dashboard', icon: Home, label: 'Dashboard' },
        { path: '/chat', icon: MessageCircle, label: 'Book Appointment' },
        { path: '/appointments', icon: Calendar, label: 'My Appointments' },
        { path: '/profile', icon: User, label: 'Profile' },
    ];

    const doctorLinks = [
        { path: '/dashboard', icon: Home, label: 'Dashboard' },
        { path: '/chat', icon: MessageCircle, label: 'AI Assistant' },
        { path: '/appointments', icon: Calendar, label: 'Schedule' },
        { path: '/patients', icon: Users, label: 'Patients' },
        { path: '/reports', icon: BarChart3, label: 'Reports' },
        { path: '/settings', icon: Settings, label: 'Settings' },
    ];

    const links = isDoctor ? doctorLinks : patientLinks;

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <Link to="/dashboard" className="sidebar-logo">
                    <Stethoscope size={28} />
                    <span>MedAssist</span>
                </Link>
            </div>

            <nav className="sidebar-nav">
                {links.map((link) => {
                    const Icon = link.icon;
                    const isActive = location.pathname === link.path;

                    return (
                        <Link
                            key={link.path}
                            to={link.path}
                            className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                        >
                            <Icon size={20} />
                            <span>{link.label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="sidebar-footer">
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    marginBottom: '1rem',
                    padding: '0.5rem',
                    borderRadius: 'var(--radius-lg)',
                    background: 'rgba(255,255,255,0.1)'
                }}>
                    <div style={{
                        width: '2.5rem',
                        height: '2.5rem',
                        borderRadius: '50%',
                        background: 'var(--gradient-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 600
                    }}>
                        {user?.email?.charAt(0).toUpperCase()}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{
                            fontSize: '0.875rem',
                            fontWeight: 500,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                        }}>
                            {user?.email}
                        </div>
                        <div style={{
                            fontSize: '0.75rem',
                            opacity: 0.7,
                            textTransform: 'capitalize'
                        }}>
                            {user?.role}
                        </div>
                    </div>
                </div>

                <button
                    className="sidebar-nav-item"
                    onClick={logout}
                    style={{ width: '100%', border: 'none', background: 'transparent' }}
                >
                    <LogOut size={20} />
                    <span>Logout</span>
                </button>
            </div>
        </aside>
    );
}

export default Navigation;
