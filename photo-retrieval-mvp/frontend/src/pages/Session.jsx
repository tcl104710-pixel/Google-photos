import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatPanel from '../components/ChatPanel';
import PhotoGrid from '../components/PhotoGrid';
import { session as sessionApi } from '../api/client';

export default function Session() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [contextSnapshot, setContextSnapshot] = useState(null);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    // Start session on mount
    sessionApi.start().then((data) => {
      setSessionId(data.session_id);
      setMessages([{
        id: 'initial',
        role: 'ai',
        text: "Hi! Describe a photo you're looking for, even if your memory is hazy."
      }]);
    }).catch(err => {
      console.error("Failed to start session:", err);
      navigate('/');
    });
  }, [navigate]);

  const handleSendMessage = async (text) => {
    if (!text.trim() || !sessionId) return;
    
    // Optimistic UI
    const userMsg = { id: Date.now().toString(), role: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const data = await sessionApi.sendMessage(sessionId, text);
      
      setCandidates(data.candidates);
      setContextSnapshot(data.context_snapshot);
      
      if (data.response_text) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'ai',
          text: data.response_text
        }]);
      }
    } catch (err) {
      console.error("Send message error:", err);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'ai',
        text: "Sorry, I ran into an error processing that."
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleFeedback = async (photoId, feedbackType) => {
    if (!sessionId) return;
    
    setIsTyping(true); // Re-ranking is quick but good to show loading
    try {
      const data = await sessionApi.sendFeedback(sessionId, photoId, feedbackType);
      
      if (feedbackType === 'yes' || !data.context_snapshot) {
        // Session ended
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'ai',
          text: "Glad you found it! The session has been concluded."
        }]);
        setCandidates([]);
      } else {
        setCandidates(data.candidates);
        setContextSnapshot(data.context_snapshot);
      }
    } catch (err) {
      console.error("Feedback error:", err);
    } finally {
      setIsTyping(false);
    }
  };

  const handleStartOver = async () => {
    if (sessionId) {
      await sessionApi.end(sessionId);
    }
    window.location.reload();
  };

  if (!sessionId) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Initializing session...</div>;
  }

  return (
    <div className="app-container">
      <div className="chat-panel">
        <ChatPanel 
          messages={messages} 
          onSendMessage={handleSendMessage} 
          isTyping={isTyping}
          contextSnapshot={contextSnapshot}
          onStartOver={handleStartOver}
        />
      </div>
      <div className="photo-grid-panel">
        <PhotoGrid 
          candidates={candidates} 
          onFeedback={handleFeedback}
        />
      </div>
    </div>
  );
}
