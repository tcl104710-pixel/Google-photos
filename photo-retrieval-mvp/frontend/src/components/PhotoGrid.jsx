import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, Flame } from 'lucide-react';
import ExplanationChip from './ExplanationChip';

export default function PhotoGrid({ candidates, onFeedback }) {
  if (!candidates || candidates.length === 0) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%',
        color: 'var(--text-muted)', fontSize: '1.25rem'
      }}>
        Describe a memory on the left to see matching photos.
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1.5rem' }}>
      <AnimatePresence>
        {candidates.map((cluster, idx) => {
          const photo = cluster.representative;
          const isTop = idx === 0;

          return (
            <motion.div
              layout
              key={photo.photo_id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              style={{
                position: 'relative',
                borderRadius: '12px',
                overflow: 'hidden',
                background: 'var(--bg-surface)',
                border: isTop ? '2px solid var(--primary)' : '1px solid var(--border-color)',
                boxShadow: isTop ? 'var(--shadow-glow)' : 'var(--shadow-lg)',
                aspectRatio: '1',
              }}
              className="photo-card"
            >
              {/* Photo Image Placeholder for UI (Use real URL in prod) */}
              <img 
                src={`${photo.base_url}=w500-h500-c`} 
                alt="Candidate" 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={(e) => {
                  e.target.onerror = null; 
                  e.target.src = "https://via.placeholder.com/500?text=No+Access";
                }}
              />

              {/* Confidence Pill */}
              <div style={{
                position: 'absolute', top: '0.5rem', left: '0.5rem',
                background: photo.confidence_label === 'Strong match' ? 'var(--primary)' : 'rgba(0,0,0,0.6)',
                padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600,
                backdropFilter: 'blur(4px)'
              }}>
                {isTop ? '🏆 Best Match' : photo.confidence_label}
              </div>
              
              {/* Event grouping info */}
              {cluster.members.length > 0 && (
                <div style={{
                  position: 'absolute', top: '0.5rem', right: '0.5rem',
                  background: 'rgba(0,0,0,0.6)', padding: '2px 8px', borderRadius: '12px', 
                  fontSize: '0.75rem', backdropFilter: 'blur(4px)'
                }}>
                  +{cluster.members.length} similar
                </div>
              )}

              {/* Explanation Chip */}
              <ExplanationChip dimensions={photo.matched_dimensions} />

              {/* Feedback Controls Overlay */}
              <div className="feedback-controls" style={{
                position: 'absolute', bottom: '0.5rem', left: '0.5rem', right: '0.5rem',
                display: 'flex', justifyContent: 'center', gap: '0.5rem'
              }}>
                <button className="btn-icon" style={{ background: 'var(--accent-red)', color: 'white' }} 
                  onClick={() => onFeedback(photo.photo_id, 'no')} title="Not this">
                  <X size={16} />
                </button>
                <button className="btn-icon" style={{ background: 'var(--accent-yellow)', color: 'white' }} 
                  onClick={() => onFeedback(photo.photo_id, 'warmer')} title="Getting warmer">
                  <Flame size={16} />
                </button>
                <button className="btn" style={{ flex: 1, padding: '0.5rem', fontSize: '0.875rem' }} 
                  onClick={() => onFeedback(photo.photo_id, 'yes')}>
                  <Check size={16} /> Found It
                </button>
              </div>

              <style>{`
                .photo-card .explanation-overlay { opacity: 0; }
                .photo-card:hover .explanation-overlay { opacity: 1; }
                
                .photo-card .feedback-controls { transform: translateY(150%); transition: transform 0.2s ease; }
                .photo-card:hover .feedback-controls { transform: translateY(0); }
              `}</style>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
