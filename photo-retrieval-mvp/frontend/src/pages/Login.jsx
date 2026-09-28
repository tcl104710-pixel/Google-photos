import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { auth } from '../api/client';
import { LogIn } from 'lucide-react';

export default function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    if (searchParams.get('auth') === 'success') {
      navigate('/auth/callback');
    }
  }, [searchParams, navigate]);

  const handleLogin = () => {
    // Redirect to backend OAuth route
    window.location.href = auth.getLoginUrl();
  };

  return (
    <div style={{
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center',
      width: '100%',
      height: '100vh',
      background: 'var(--bg-color)',
      color: 'var(--text-main)',
      textAlign: 'center',
      padding: '2rem'
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '1rem', fontWeight: 700 }}>
        Antigravity Photos
      </h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '1.25rem', maxWidth: '600px', marginBottom: '3rem' }}>
        AI-native photo retrieval. Find that one photo using vague, incomplete, or hazy memories.
      </p>
      
      <button className="btn" onClick={handleLogin} style={{ fontSize: '1.25rem', padding: '1rem 2rem' }}>
        <LogIn size={24} />
        Sign in with Google
      </button>
    </div>
  );
}
