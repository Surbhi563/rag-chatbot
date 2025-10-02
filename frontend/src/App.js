import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Loader, Globe, Plus, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://rag-chatbot-backend.railway.app';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState({ total_documents: 0, total_chunks: 0 });
  const [websiteSources, setWebsiteSources] = useState([]);
  const [isIngestingWebsites, setIsIngestingWebsites] = useState(false);
  const [websiteUrls, setWebsiteUrls] = useState(['']);
  const [websiteError, setWebsiteError] = useState('');
  const [websiteSuccess, setWebsiteSuccess] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchStats();
    fetchWebsiteSources();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/v1/chat/documents/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchWebsiteSources = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/v1/websites/sources`);
      setWebsiteSources(response.data.sources);
    } catch (error) {
      console.error('Failed to fetch website sources:', error);
    }
  };

  const handleWebsiteIngestion = async () => {
    const validUrls = websiteUrls.filter(url => url.trim() && isValidUrl(url.trim()));
    
    if (validUrls.length === 0) {
      setWebsiteError('Please enter at least one valid URL');
      return;
    }

    setIsIngestingWebsites(true);
    setWebsiteError('');
    setWebsiteSuccess('');

    try {
      const response = await axios.post(`${API_BASE_URL}/v1/websites/ingest-multiple`, {
        urls: validUrls,
        max_pages_per_site: 10
      });

      if (response.data.success) {
        setWebsiteSuccess(`Successfully ingested ${response.data.successful_sites}/${response.data.total_sites} websites. Added ${response.data.total_chunks} chunks.`);
        setWebsiteUrls(['']);
        await fetchStats();
        await fetchWebsiteSources();
      } else {
        setWebsiteError('Failed to ingest websites');
      }
    } catch (error) {
      console.error('Website ingestion error:', error);
      setWebsiteError(error.response?.data?.detail || 'Failed to ingest websites');
    } finally {
      setIsIngestingWebsites(false);
    }
  };

  const isValidUrl = (string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const addWebsiteUrl = () => {
    setWebsiteUrls([...websiteUrls, '']);
  };

  const removeWebsiteUrl = (index) => {
    const newUrls = websiteUrls.filter((_, i) => i !== index);
    setWebsiteUrls(newUrls);
  };

  const updateWebsiteUrl = (index, value) => {
    const newUrls = [...websiteUrls];
    newUrls[index] = value;
    setWebsiteUrls(newUrls);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await axios.post(`${API_BASE_URL}/v1/chat/message`, {
        message: userMessage,
        context_limit: 5,
        temperature: 0.1
      });

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
        confidence: response.data.confidence,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your message. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Website Knowledge Assistant</h1>
        <p>Ask questions about the websites I've learned from</p>
      </header>

      <div className="main-content">
        <div className="sidebar">
          <div className="upload-section">
            <h3>Add Website Sources</h3>
            <div className="website-ingestion">
              {websiteUrls.map((url, index) => (
                <div key={index} className="url-input-group">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => updateWebsiteUrl(index, e.target.value)}
                    placeholder="Enter website URL (e.g., https://example.com)"
                    className="url-input"
                  />
                  {websiteUrls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeWebsiteUrl(index)}
                      className="remove-url-button"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
              
              <div className="url-actions">
                <button
                  type="button"
                  onClick={addWebsiteUrl}
                  className="add-url-button"
                >
                  <Plus size={16} />
                  Add Another URL
                </button>
                
                <button
                  type="button"
                  onClick={handleWebsiteIngestion}
                  disabled={isIngestingWebsites}
                  className="ingest-button"
                >
                  {isIngestingWebsites ? (
                    <>
                      <Loader className="loading-spinner" />
                      Ingesting...
                    </>
                  ) : (
                    <>
                      <Globe size={16} />
                      Ingest Websites
                    </>
                  )}
                </button>
              </div>

              {websiteError && <div className="error">{websiteError}</div>}
              {websiteSuccess && <div className="success">{websiteSuccess}</div>}
            </div>

            {websiteSources.length > 0 && (
              <div className="website-sources">
                <h4>Website Sources</h4>
                {websiteSources.map((source, index) => (
                  <div key={index} className="website-source">
                    <div className="source-info">
                      <Globe size={16} />
                      <div>
                        <div className="source-title">{source.title}</div>
                        <div className="source-url">{source.url}</div>
                      </div>
                    </div>
                    <div className="source-chunks">{source.chunks} chunks</div>
                  </div>
                ))}
              </div>
            )}
          </div>


          <div className="stats-section">
            <h3>Document Statistics</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{stats.total_documents}</div>
                <div className="stat-label">Documents</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.total_chunks}</div>
                <div className="stat-label">Chunks</div>
              </div>
            </div>
          </div>

        </div>

        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '2rem' }}>
                <h3>Welcome to Website Knowledge Assistant</h3>
                <p>I can help you with questions based on the content I've learned from the websites you've added.</p>
                {websiteSources.length > 0 ? (
                  <div style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                    <p><strong>I've learned from these websites:</strong></p>
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                      {websiteSources.slice(0, 3).map((source, index) => (
                        <li key={index}>• {new URL(source.url).hostname}</li>
                      ))}
                    </ul>
                    <p style={{ marginTop: '1rem' }}><strong>Try asking questions about their content!</strong></p>
                  </div>
                ) : (
                  <div style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
                    <p><strong>Add some websites to get started!</strong></p>
                    <p>Use the sidebar to add website URLs for me to learn from.</p>
                  </div>
                )}
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className={`message ${message.role}`}>
                  <div className="message-avatar">
                    {message.role === 'user' ? 'U' : 'A'}
                  </div>
                  <div className="message-content">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                    {message.sources && message.sources.length > 0 && (
                      <div className="message-sources">
                        <strong>Sources:</strong> {message.sources.length} document(s) used
                        {message.confidence && (
                          <span> • Confidence: {(message.confidence * 100).toFixed(1)}%</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="message assistant">
                <div className="message-avatar">A</div>
                <div className="message-content">
                  <div className="loading">
                    <Loader className="loading-spinner" />
                    Thinking...
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <form onSubmit={sendMessage} className="chat-input-form">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask about the websites I've learned from..."
                className="chat-input"
                rows="1"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(e);
                  }
                }}
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || isLoading}
                className="send-button"
              >
                <Send size={20} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
