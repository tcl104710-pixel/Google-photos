import React, { useState, useRef, useEffect } from 'react';
import { Send, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ChatPanel({ messages, onSendMessage, isTyping, contextSnapshot, onStartOver }) {
  const [input, setInput] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isTyping) {
      onSendMessage(input);
      setInput("");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{ 
        padding: '1rem', 
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Memory Context</h2>
        <button className="btn-icon" onClick={onStartOver} title="Start over">
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Progress Indicators */}
      {contextSnapshot && (
        <div style={{ padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.2)', fontSize: '0.875rem' }}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {contextSnapshot.people?.length > 0 && 
              <span style={{ color: 'var(--accent-green)' }}>✓ People</span>}
            {contextSnapshot.places?.length > 0 && 
              <span style={{ color: 'var(--accent-green)' }}>✓ Place</span>}
            {contextSnapshot.time_window && 
              <span style={{ color: 'var(--accent-green)' }}>✓ Time</span>}
            {contextSnapshot.activities?.length > 0 && 
              <span style={{ color: 'var(--accent-yellow)' }}>• Activity</span>}
          </div>
        </div>
      )}

      {/* Message List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                background: msg.role === 'user' ? 'var(--primary)' : 'var(--bg-surface-hover)',
                padding: '0.75rem 1rem',
                borderRadius: '12px',
                borderBottomRightRadius: msg.role === 'user' ? '2px' : '12px',
                borderBottomLeftRadius: msg.role === 'ai' ? '2px' : '12px',
                maxWidth: '85%',
                lineHeight: 1.5,
              }}
            >
              {msg.text}
            </motion.div>
          ))}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                alignSelf: 'flex-start',
                background: 'var(--bg-surface-hover)',
                padding: '0.75rem 1rem',
                borderRadius: '12px',
                borderBottomLeftRadius: '2px',
                color: 'var(--text-muted)'
              }}
            >
              Building context...
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '0.5rem' }}>
        <input 
          className="input-field"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Describe the photo..."
          disabled={isTyping}
        />
        <button type="submit" className="btn" disabled={isTyping || !input.trim()} style={{ padding: '1rem' }}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
