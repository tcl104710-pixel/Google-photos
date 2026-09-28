import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { auth } from '../api/client';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('Checking sync status...');

  useEffect(() => {
    // We assume backend redirected here either directly or via /?auth=success.
    // Let's poll sync status.
    const poll = setInterval(async () => {
      try {
        const data = await auth.checkSyncStatus();
        if (data.sync_in_progress) {
          setStatus(`Syncing library... ${data.indexed_photos} / ${data.total_photos} photos indexed`);
        } else if (data.indexed_photos > 0) {
          clearInterval(poll);
          navigate('/session');
        } else {
          // Sync might not have started yet, give it a moment
          setStatus('Starting sync...');
        }
      } catch (err) {
        console.error("Sync status error", err);
        // Might be unauthorized if cookie wasn't set properly, in real app handle it.
      }
    }, 2000);

    return () => clearInterval(poll);
  }, [navigate]);

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
    }}>
      <Loader2 className="animate-spin" size={48} style={{ marginBottom: '1rem', color: 'var(--primary)' }} />
      <h2 style={{ fontSize: '1.5rem', fontWeight: 600 }}>{status}</h2>
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}
