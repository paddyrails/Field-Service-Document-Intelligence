import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./Onboarding.css";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const AGENT_URL = "http://localhost/query";

const Onboarding: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post(AGENT_URL, {
        query: text,
        session_id: sessionId,
        user_id: "admin",
        bu_hint: "BU1",
      });

      const aiMsg: Message = {
        role: "assistant",
        content: response.data.response || "No response received.",
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        role: "assistant",
        content: `Error: ${err.response?.data?.detail || err.message || "Failed to reach agent."}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="onboarding-page">
      <h1>Onboarding Assistant</h1>
      <p className="page-subtitle">
        Ask questions about customer onboarding, KYC status, and registration
      </p>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              Start a conversation — ask about customers, KYC status, or
              onboarding procedures.
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              <div className="chat-bubble-header">
                <span className="chat-role">
                  {msg.role === "user" ? "You" : "RiteCare AI"}
                </span>
                <span className="chat-time">{msg.timestamp}</span>
              </div>
              <div className="chat-text">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble assistant">
              <div className="chat-bubble-header">
                <span className="chat-role">RiteCare AI</span>
              </div>
              <div className="chat-typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your question..."
            rows={1}
            disabled={loading}
          />
          <button
            className="chat-send"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
