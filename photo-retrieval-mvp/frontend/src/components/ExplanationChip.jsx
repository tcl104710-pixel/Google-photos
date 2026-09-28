import React from 'react';

export default function ExplanationChip({ dimensions }) {
  if (!dimensions || dimensions.length === 0) return null;

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '0.5rem',
      padding: '0.5rem',
      background: 'rgba(0,0,0,0.7)',
      backdropFilter: 'blur(4px)',
      position: 'absolute',
      bottom: '3rem',
      left: '0.5rem',
      right: '0.5rem',
      borderRadius: '8px',
      fontSize: '0.75rem',
      opacity: 0,
      transition: 'opacity 0.2s ease',
      pointerEvents: 'none'
    }} className="explanation-overlay">
      {dimensions.map((dim, idx) => (
        <span key={idx} style={{
          background: 'var(--bg-surface)',
          padding: '2px 6px',
          borderRadius: '4px',
          border: '1px solid var(--border-color)'
        }}>
          <span style={{ color: 'var(--text-muted)' }}>{dim.dimension}:</span> {dim.value}
        </span>
      ))}
    </div>
  );
}
