/**
 * Login Page
 * Role-based authentication for patients and doctors
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Stethoscope, User, UserCog, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

type UserRole = 'patient' | 'doctor';
type FormMode = 'login' | 'register';

export function LoginPage() {
    const navigate = useNavigate();
    const { login, register } = useAuth();

    const [mode, setMode] = useState<FormMode>('login');
    const [role, setRole] = useState<UserRole>('patient');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            if (mode === 'login') {
                await login(email, password);
            } else {
                await register(email, password, name, role);
            }
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <div className="login-header">
                    <div className="login-logo">
                        <Stethoscope size={32} color="white" />
                    </div>
                    <h1>MedAssist</h1>
                    <p>Smart Doctor Appointment Assistant</p>
                </div>

                {/* Role Selector */}
                <div className="role-selector">
                    <button
                        type="button"
                        className={`role-btn ${role === 'patient' ? 'active' : ''}`}
                        onClick={() => setRole('patient')}
                    >
                        <div className="role-btn-icon"><User size={24} /></div>
                        <div className="role-btn-label">Patient</div>
                    </button>
                    <button
                        type="button"
                        className={`role-btn ${role === 'doctor' ? 'active' : ''}`}
                        onClick={() => setRole('doctor')}
                    >
                        <div className="role-btn-icon"><UserCog size={24} /></div>
                        <div className="role-btn-label">Doctor</div>
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit}>
                    {mode === 'register' && (
                        <div className="form-group">
                            <label className="form-label">Full Name</label>
                            <input
                                type="text"
                                className="form-input"
                                placeholder="Enter your full name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <input
                            type="email"
                            className="form-input"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            className="form-input"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            minLength={6}
                        />
                    </div>

                    {error && (
                        <div className="form-error" style={{ marginBottom: '1rem', textAlign: 'center' }}>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        className="btn btn-primary w-full"
                        disabled={isLoading}
                        style={{ marginTop: '0.5rem' }}
                    >
                        {isLoading ? (
                            <>
                                <Loader2 size={18} className="animate-spin" />
                                {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                            </>
                        ) : (
                            mode === 'login' ? 'Sign In' : 'Create Account'
                        )}
                    </button>
                </form>

                <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
                    {mode === 'login' ? (
                        <p className="text-muted">
                            Don't have an account?{' '}
                            <button
                                type="button"
                                onClick={() => setMode('register')}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--primary-600)',
                                    cursor: 'pointer',
                                    fontWeight: 600
                                }}
                            >
                                Sign up
                            </button>
                        </p>
                    ) : (
                        <p className="text-muted">
                            Already have an account?{' '}
                            <button
                                type="button"
                                onClick={() => setMode('login')}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--primary-600)',
                                    cursor: 'pointer',
                                    fontWeight: 600
                                }}
                            >
                                Sign in
                            </button>
                        </p>
                    )}
                </div>

                {/* Demo Credentials */}
                <div style={{
                    marginTop: '2rem',
                    padding: '1rem',
                    background: 'var(--gray-50)',
                    borderRadius: 'var(--radius-lg)',
                    fontSize: '0.8rem'
                }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: 'var(--gray-700)' }}>
                        Demo Credentials
                    </div>
                    <div style={{ color: 'var(--gray-600)' }}>
                        <div><strong>Patient:</strong> patient@example.com / patient123</div>
                        <div><strong>Doctor:</strong> dr.ahuja@clinic.com / doctor123</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default LoginPage;
