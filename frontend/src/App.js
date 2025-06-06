import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ScenarioInput = ({ onSetScenario }) => {
  const [scenario, setScenario] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!scenario.trim()) return;
    
    setLoading(true);
    await onSetScenario(scenario);
    setScenario("");
    setLoading(false);
  };

  return (
    <div className="scenario-input bg-white rounded-lg shadow-md p-4 mb-4">
      <h3 className="text-lg font-bold mb-3">🎭 Custom Scenario</h3>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <textarea
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            placeholder="Describe a new scenario for your agents... (e.g., 'A mysterious signal has been detected. The team must decide how to respond.')"
            className="w-full p-3 border rounded-lg resize-none"
            rows="3"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !scenario.trim()}
          className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? "Setting Scenario..." : "Set New Scenario"}
        </button>
      </form>
    </div>
  );
};

const AutoControls = ({ simulationState, onToggleAuto }) => {
  const [autoConversations, setAutoConversations] = useState(false);
  const [autoTime, setAutoTime] = useState(false);
  const [conversationInterval, setConversationInterval] = useState(10);
  const [timeInterval, setTimeInterval] = useState(60);

  useEffect(() => {
    if (simulationState) {
      setAutoConversations(simulationState.auto_conversations || false);
      setAutoTime(simulationState.auto_time || false);
      setConversationInterval(simulationState.conversation_interval || 10);
      setTimeInterval(simulationState.time_interval || 60);
    }
  }, [simulationState]);

  const handleToggleAutoConversations = async () => {
    const newValue = !autoConversations;
    setAutoConversations(newValue);
    await onToggleAuto({
      auto_conversations: newValue,
      auto_time: autoTime,
      conversation_interval: conversationInterval,
      time_interval: timeInterval
    });
  };

  const handleToggleAutoTime = async () => {
    const newValue = !autoTime;
    setAutoTime(newValue);
    await onToggleAuto({
      auto_conversations: autoConversations,
      auto_time: newValue,
      conversation_interval: conversationInterval,
      time_interval: timeInterval
    });
  };

  const handleIntervalChange = async (type, value) => {
    const newData = {
      auto_conversations: autoConversations,
      auto_time: autoTime,
      conversation_interval: type === 'conversation' ? value : conversationInterval,
      time_interval: type === 'time' ? value : timeInterval
    };
    
    if (type === 'conversation') {
      setConversationInterval(value);
    } else {
      setTimeInterval(value);
    }
    
    await onToggleAuto(newData);
  };

  return (
    <div className="auto-controls bg-white rounded-lg shadow-md p-4 mb-4">
      <h3 className="text-lg font-bold mb-3">🤖 Automation Controls</h3>
      
      <div className="space-y-4">
        {/* Auto Conversations */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
          <div>
            <h4 className="font-semibold">Auto Conversations</h4>
            <p className="text-xs text-gray-600">Generate conversations automatically</p>
          </div>
          <button
            onClick={handleToggleAutoConversations}
            className={`px-4 py-2 rounded text-sm font-medium ${
              autoConversations 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-300 text-gray-700'
            }`}
          >
            {autoConversations ? 'ON' : 'OFF'}
          </button>
        </div>

        {autoConversations && (
          <div className="ml-4">
            <label className="block text-xs font-medium mb-1">Interval (seconds)</label>
            <input
              type="number"
              min="5"
              max="300"
              value={conversationInterval}
              onChange={(e) => handleIntervalChange('conversation', parseInt(e.target.value))}
              className="w-20 px-2 py-1 border rounded text-sm"
            />
          </div>
        )}

        {/* Auto Time */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
          <div>
            <h4 className="font-semibold">Auto Time Progression</h4>
            <p className="text-xs text-gray-600">Advance time periods automatically</p>
          </div>
          <button
            onClick={handleToggleAutoTime}
            className={`px-4 py-2 rounded text-sm font-medium ${
              autoTime 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-300 text-gray-700'
            }`}
          >
            {autoTime ? 'ON' : 'OFF'}
          </button>
        </div>

        {autoTime && (
          <div className="ml-4">
            <label className="block text-xs font-medium mb-1">Interval (seconds)</label>
            <input
              type="number"
              min="30"
              max="600"
              value={timeInterval}
              onChange={(e) => handleIntervalChange('time', parseInt(e.target.value))}
              className="w-20 px-2 py-1 border rounded text-sm"
            />
          </div>
        )}
      </div>
    </div>
  );
};

const ObserverInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (message.trim() && !sending) {
      setSending(true);
      await onSendMessage(message.trim());
      setMessage("");
      setIsExpanded(false);
      setSending(false);
    }
  };

  if (!isExpanded) {
    return (
      <div className="observer-input-collapsed mt-3">
        <button 
          onClick={() => setIsExpanded(true)}
          className="w-full text-left text-xs text-gray-500 hover:text-gray-700 py-2 px-3 bg-gray-50 hover:bg-gray-100 rounded transition-colors"
        >
          💬 Send message to team...
        </button>
      </div>
    );
  }

  return (
    <div className="observer-input-expanded mt-3 bg-gray-50 rounded-lg p-3 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <span className="text-xs text-gray-600 font-medium">Observer Message</span>
          <div className="relative ml-2 group">
            <svg 
              className="w-3 h-3 text-gray-400 cursor-help" 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
            {/* Hover Tooltip */}
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap z-10">
              You are the CEO - Agents will respond to your guidance and can offer suggestions or politely disagree based on their expertise.
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
            </div>
          </div>
        </div>
        <button 
          onClick={() => {
            setIsExpanded(false);
            setMessage("");
          }}
          className="text-xs text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Send a brief message to the team..."
          className="w-full p-2 text-sm border border-gray-300 rounded resize-none h-16 focus:outline-none focus:ring-1 focus:ring-gray-400"
          autoFocus
        />
        <div className="flex gap-2">
          <button 
            type="submit"
            disabled={!message.trim() || sending}
            className="bg-gray-600 text-white px-3 py-1 rounded text-xs hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sending ? 'Sending...' : 'Send'}
          </button>
          <button 
            type="button"
            onClick={() => {
              setIsExpanded(false);
              setMessage("");
            }}
            className="bg-gray-300 text-gray-700 px-3 py-1 rounded text-xs hover:bg-gray-400"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

const WeeklySummary = ({ onGenerateSummary, summaries, onSetupAutoReport }) => {
  const [loading, setLoading] = useState(false);
  const [latestSummary, setLatestSummary] = useState(null);
  const [autoReports, setAutoReports] = useState({ enabled: false, interval_hours: 168 });
  const [expandedSections, setExpandedSections] = useState({});
  const [copyStatus, setCopyStatus] = useState(null);

  useEffect(() => {
    if (summaries && summaries.length > 0) {
      setLatestSummary(summaries[0]);
    } else {
      // Clear the latest summary when summaries array is empty
      setLatestSummary(null);
    }
  }, [summaries]);

  const handleGenerateSummary = async () => {
    setLoading(true);
    const summary = await onGenerateSummary();
    if (summary) {
      setLatestSummary(summary);
    }
    setLoading(false);
  };

  const handleAutoReportToggle = async () => {
    const newEnabled = !autoReports.enabled;
    setAutoReports(prev => ({ ...prev, enabled: newEnabled }));
    await onSetupAutoReport({ enabled: newEnabled, interval_hours: autoReports.interval_hours });
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const copyToClipboard = async (text, label) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus(label);
      setTimeout(() => setCopyStatus(null), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopyStatus(label);
      setTimeout(() => setCopyStatus(null), 2000);
    }
  };

  const copyFullReport = () => {
    if (!latestSummary) return;
    const fullText = latestSummary.summary || "No report content available";
    copyToClipboard(fullText, "Full Report");
  };

  const copySectionContent = (sectionKey, sectionTitle) => {
    if (!latestSummary?.structured_sections?.[sectionKey]) return;
    const sectionText = `## ${sectionTitle}\n\n${latestSummary.structured_sections[sectionKey]}`;
    copyToClipboard(sectionText, sectionTitle);
  };

  const renderStructuredSummary = (summary) => {
    // Try to extract sections from the summary text
    const summaryText = summary?.summary || "";
    const sections = {};
    
    // Updated parsing patterns that match the actual backend format
    const sectionPatterns = [
      { key: 'key_events', pattern: /\*\*1\.\s*🔥\s*KEY EVENTS & DISCOVERIES\*\*(.*?)(?=\*\*2\.|$)/s },
      { key: 'relationships', pattern: /\*\*2\.\s*📈\s*RELATIONSHIP DEVELOPMENTS\*\*(.*?)(?=\*\*3\.|$)/s },
      { key: 'personalities', pattern: /\*\*3\.\s*🎭\s*EMERGING PERSONALITIES\*\*(.*?)(?=\*\*4\.|$)/s },
      { key: 'social_dynamics', pattern: /\*\*4\.\s*🤝\s*SOCIAL DYNAMICS\*\*(.*?)(?=\*\*5\.|$)/s },
      { key: 'looking_ahead', pattern: /\*\*5\.\s*🔮\s*LOOKING AHEAD\*\*(.*?)$/s }
    ];
    
    // Extract sections using the patterns
    for (const { key, pattern } of sectionPatterns) {
      const match = summaryText.match(pattern);
      if (match && match[1]) {
        sections[key] = match[1].trim();
      }
    }
    
    // If no sections were parsed, show the full summary in key_events
    if (Object.keys(sections).length === 0 && summaryText) {
      sections.key_events = summaryText;
    }
    
    return (
      <div className="structured-summary">
        {/* Copy Full Report Button */}
        <div className="flex justify-between items-center mb-4">
          <h4 className="text-lg font-semibold text-gray-800">Weekly Analysis Report</h4>
          <div className="flex items-center space-x-2">
            <button
              onClick={copyFullReport}
              className="flex items-center space-x-1 bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-2 rounded-lg transition-colors duration-200"
              title="Copy entire report"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span className="text-sm font-medium">Copy All</span>
            </button>
            {copyStatus && (
              <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded">
                ✓ {copyStatus} copied!
              </span>
            )}
          </div>
        </div>

        {/* Key Events & Discoveries - Always Visible */}
        <div className="key-events-section mb-6">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-xl font-bold text-blue-600 flex items-center">
              🔥 <span className="ml-2">KEY EVENTS & DISCOVERIES</span>
            </h3>
            <button
              onClick={() => copySectionContent('key_events', '🔥 KEY EVENTS & DISCOVERIES')}
              className="flex items-center space-x-1 bg-blue-50 hover:bg-blue-100 text-blue-600 px-2 py-1 rounded transition-colors duration-200"
              title="Copy this section"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
            <div className="whitespace-pre-wrap text-gray-800">
              {sections.key_events || "No key events identified in this period."}
            </div>
          </div>
        </div>

        {/* Collapsible Sections */}
        <div className="collapsible-sections space-y-3">
          {[
            { key: 'relationships', title: '📈 Relationship Developments', color: 'green' },
            { key: 'personalities', title: '🎭 Emerging Personalities', color: 'purple' },
            { key: 'social_dynamics', title: '🤝 Social Dynamics', color: 'yellow' },
            { key: 'looking_ahead', title: '🔮 Looking Ahead', color: 'indigo' }
          ].map(section => (
            sections[section.key] && (
              <div key={section.key} className="collapsible-section">
                <button
                  onClick={() => toggleSection(section.key)}
                  className={`w-full text-left p-3 bg-${section.color}-100 hover:bg-${section.color}-200 rounded-lg border border-${section.color}-200 transition-colors duration-200 flex justify-between items-center`}
                >
                  <span className="font-semibold text-gray-800">{section.title}</span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        copySectionContent(section.key, section.title);
                      }}
                      className={`p-1 bg-${section.color}-50 hover:bg-${section.color}-100 rounded transition-colors duration-200`}
                      title="Copy this section"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <span className="text-gray-500">
                      {expandedSections[section.key] ? '▼' : '▶'}
                    </span>
                  </div>
                </button>
                
                {expandedSections[section.key] && (
                  <div className={`mt-2 p-4 bg-${section.color}-50 border-l-4 border-${section.color}-400 rounded-r-lg`}>
                    <div className="whitespace-pre-wrap text-gray-700">
                      {sections[section.key]}
                    </div>
                  </div>
                )}
              </div>
            )
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="weekly-summary bg-white rounded-lg shadow-md p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold">📊 Weekly Report</h3>
        <div className="flex space-x-2">
          <button
            onClick={handleAutoReportToggle}
            className={`px-3 py-1 rounded text-xs font-medium ${
              autoReports.enabled 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-300 text-gray-700'
            }`}
          >
            Auto: {autoReports.enabled ? 'ON' : 'OFF'}
          </button>
          <button
            onClick={handleGenerateSummary}
            disabled={loading}
            className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Report"}
          </button>
        </div>
      </div>

      {autoReports.enabled && (
        <div className="auto-report-status mb-4 p-3 bg-green-50 border border-green-200 rounded">
          <p className="text-sm text-green-800">
            🤖 <strong>Automatic Reports Enabled</strong> - Reports generate every {autoReports.interval_hours} hours
          </p>
        </div>
      )}
      
      {latestSummary ? (
        <div className="summary-content">
          <div className="mb-3 text-xs text-gray-600 bg-gray-50 p-2 rounded">
            <strong>Report Generated:</strong> Day {latestSummary.day} • {latestSummary.conversations_count} conversations analyzed
          </div>
          
          {latestSummary.structured_sections ? (
            renderStructuredSummary(latestSummary)
          ) : (
            <div className="legacy-summary bg-gray-50 rounded p-3 text-sm">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">Report Content</span>
                <button
                  onClick={copyFullReport}
                  className="flex items-center space-x-1 bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-1 rounded text-xs"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy</span>
                </button>
              </div>
              <div className="whitespace-pre-wrap">{latestSummary.summary}</div>
            </div>
          )}
        </div>
      ) : (
        <p className="text-gray-500 text-sm italic">No reports generated yet. Click the button to create your first weekly report!</p>
      )}
    </div>
  );
};

const FastForwardModal = ({ isOpen, onClose, onFastForward }) => {
  const [targetDays, setTargetDays] = useState(3);
  const [conversationsPerPeriod, setConversationsPerPeriod] = useState(2);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onFastForward(targetDays, conversationsPerPeriod);
    setLoading(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96">
        <h3 className="text-lg font-bold mb-4">⚡ Fast Forward Simulation</h3>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Days to Fast Forward</label>
            <input
              type="number"
              min="1"
              max="30"
              value={targetDays}
              onChange={(e) => setTargetDays(parseInt(e.target.value))}
              className="w-full p-2 border rounded"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">1-30 days maximum</p>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Conversations per Time Period</label>
            <input
              type="number"
              min="1"
              max="5"
              value={conversationsPerPeriod}
              onChange={(e) => setConversationsPerPeriod(parseInt(e.target.value))}
              className="w-full p-2 border rounded"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">1-5 conversations per morning/afternoon/evening</p>
          </div>

          <div className="mb-4 p-3 bg-yellow-50 rounded">
            <p className="text-sm text-yellow-800">
              <strong>Estimated API calls:</strong> {targetDays * 3 * conversationsPerPeriod * 3} requests
            </p>
            <p className="text-xs text-yellow-600 mt-1">
              This will generate meaningful progression over time with agents developing ideas and relationships.
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              disabled={loading}
            >
              {loading ? 'Fast Forwarding...' : 'Fast Forward'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const EditAgentModal = ({ agent, isOpen, onClose, onSave, archetypes }) => {
  const [formData, setFormData] = useState({
    name: '',
    archetype: '',
    goal: '',
    expertise: '',
    background: '',
    memory_summary: '',
    personality: {
      extroversion: 5,
      optimism: 5,
      curiosity: 5,
      cooperativeness: 5,
      energy: 5
    }
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (agent) {
      setFormData({
        name: agent.name || '',
        archetype: agent.archetype || '',
        goal: agent.goal || '',
        expertise: agent.expertise || '',
        background: agent.background || '',
        memory_summary: agent.memory_summary || '',
        personality: agent.personality || {
          extroversion: 5,
          optimism: 5,
          curiosity: 5,
          cooperativeness: 5,
          energy: 5
        }
      });
    }
  }, [agent]);

  const handlePersonalityChange = (trait, value) => {
    setFormData(prev => ({
      ...prev,
      personality: {
        ...prev.personality,
        [trait]: parseInt(value)
      }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onSave(agent.id, formData);
    setLoading(false);
    onClose();
  };

  if (!isOpen || !agent) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-bold mb-4">✏️ Edit Agent: {agent.name}</h3>
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({...prev, name: e.target.value}))}
                className="w-full p-2 border rounded"
                disabled={loading}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Archetype</label>
              <select
                value={formData.archetype}
                onChange={(e) => setFormData(prev => ({...prev, archetype: e.target.value}))}
                className="w-full p-2 border rounded"
                disabled={loading}
              >
                {Object.entries(archetypes).map(([key, value]) => (
                  <option key={key} value={key}>{value.name}</option>
                ))}
              </select>
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Goal</label>
              <textarea
                value={formData.goal}
                onChange={(e) => setFormData(prev => ({...prev, goal: e.target.value}))}
                className="w-full p-2 border rounded"
                rows="2"
                disabled={loading}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Expertise</label>
              <input
                type="text"
                value={formData.expertise}
                onChange={(e) => setFormData(prev => ({...prev, expertise: e.target.value}))}
                className="w-full p-2 border rounded"
                placeholder="e.g., Machine Learning, Psychology"
                disabled={loading}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Background</label>
              <textarea
                value={formData.background}
                onChange={(e) => setFormData(prev => ({...prev, background: e.target.value}))}
                className="w-full p-2 border rounded"
                rows="3"
                placeholder="Professional background and experience"
                disabled={loading}
              />
            </div>
            
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">
                🧠 Memory & Knowledge 
                <span className="text-xs text-gray-500 ml-2">
                  (What the agent remembers + real-world URLs for additional context)
                </span>
              </label>
              <textarea
                value={formData.memory_summary}
                onChange={(e) => setFormData(prev => ({...prev, memory_summary: e.target.value}))}
                className="w-full p-2 border rounded bg-blue-50"
                rows="4"
                placeholder="Key memories, insights, relationships, and important developments...

🌐 Include URLs for real-world context:
• Social media profiles (LinkedIn, Twitter)
• News articles, research papers
• Company websites, personal blogs
• Any web content that should influence this agent's thinking

URLs will be automatically fetched and summarized!"
                disabled={loading}
              />
              <p className="text-xs text-blue-600 mt-1">
                💡 <strong>Pro tip:</strong> Add URLs to give agents real-world knowledge that will shape their responses
              </p>
              {formData.memory_summary.includes('http') && (
                <p className="text-xs text-green-600 mt-1">
                  🌐 URLs detected! They will be processed when you save.
                </p>
              )}
            </div>
          </div>

          <div className="mt-4">
            <h4 className="font-medium mb-3">Personality Traits</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(formData.personality).map(([trait, value]) => (
                <div key={trait}>
                  <label className="block text-sm font-medium mb-1 capitalize">{trait}</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={value}
                      onChange={(e) => handlePersonalityChange(trait, e.target.value)}
                      className="flex-1"
                      disabled={loading}
                    />
                    <span className="w-8 text-sm">{value}/10</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AgentCard = ({ agent, relationships, onEdit, onClearMemory, onAddMemory }) => {
  const [showMemoryInput, setShowMemoryInput] = useState(false);
  const [newMemory, setNewMemory] = useState('');

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newMemory.trim()) return;
    await onAddMemory(agent.id, newMemory);
    setNewMemory('');
    setShowMemoryInput(false);
  };
  const getPersonalityColor = (value) => {
    if (value <= 3) return "bg-red-500";
    if (value <= 6) return "bg-yellow-500"; 
    return "bg-green-500";
  };

  const agentRelationships = relationships ? relationships.filter(r => r.agent1_id === agent.id) : [];

  return (
    <div className="agent-card bg-white rounded-lg shadow-md p-4 m-2 relative">
      <div className="absolute top-2 right-2 flex space-x-1">
        <button
          onClick={() => onEdit(agent)}
          className="bg-blue-100 hover:bg-blue-200 text-blue-600 p-1 rounded text-xs"
          title="Edit Agent"
        >
          ✏️
        </button>
        {agent.memory_summary && (
          <button
            onClick={() => onClearMemory(agent.id)}
            className="bg-red-100 hover:bg-red-200 text-red-600 p-1 rounded text-xs"
            title="Clear Memory"
          >
            🧠❌
          </button>
        )}
        <button
          onClick={() => setShowMemoryInput(!showMemoryInput)}
          className="bg-green-100 hover:bg-green-200 text-green-600 p-1 rounded text-xs"
          title="Add Memory"
        >
          🧠+
        </button>
      </div>
      
      <div className="agent-header">
        <h3 className="text-lg font-bold text-gray-800 pr-16">{agent.name}</h3>
        <p className="text-sm text-gray-600">{agent.archetype}</p>
        <p className="text-xs text-gray-500 italic">"{agent.goal}"</p>
        
        {agent.expertise && (
          <p className="text-xs text-blue-600 mt-1">
            <strong>Expertise:</strong> {agent.expertise}
          </p>
        )}
        
        {agent.background && (
          <p className="text-xs text-gray-500 mt-1">
            {agent.background.substring(0, 80)}{agent.background.length > 80 ? '...' : ''}
          </p>
        )}
      </div>

      {/* Add Memory Input */}
      {showMemoryInput && (
        <div className="add-memory mt-3 p-3 bg-green-50 rounded border">
          <form onSubmit={handleAddMemory}>
            <label className="block text-sm font-medium mb-1">🧠 Add Memory</label>
            <textarea
              value={newMemory}
              onChange={(e) => setNewMemory(e.target.value)}
              placeholder="Add a specific memory, experience, or knowledge... 

💡 Pro tips:
• Include URLs to real websites/social media for additional context
• Example: 'I read this article https://example.com/ai-research that changed my perspective on AI safety'
• URLs will be automatically processed and summarized"
              className="w-full p-2 border rounded text-sm"
              rows="4"
            />
            <div className="flex space-x-2 mt-2">
              <button
                type="submit"
                className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700"
                disabled={!newMemory.trim()}
              >
                {newMemory.includes('http') ? '🌐 Add with URL Processing' : 'Add Memory'}
              </button>
              <button
                type="button"
                onClick={() => setShowMemoryInput(false)}
                className="bg-gray-300 text-gray-700 px-3 py-1 rounded text-xs hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
            {newMemory.includes('http') && (
              <p className="text-xs text-blue-600 mt-1">
                🌐 URLs detected! They will be fetched and summarized automatically.
              </p>
            )}
          </form>
        </div>
      )}
      
      <div className="personality-traits mt-3">
        <h4 className="text-sm font-semibold mb-2">Personality</h4>
        {Object.entries(agent.personality).map(([trait, value]) => (
          <div key={trait} className="trait-bar mb-1">
            <div className="flex justify-between items-center">
              <span className="text-xs capitalize">{trait}</span>
              <span className="text-xs">{value}/10</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${getPersonalityColor(value)}`}
                style={{width: `${value * 10}%`}}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {agentRelationships.length > 0 && (
        <div className="relationships mt-3">
          <h4 className="text-sm font-semibold mb-2">Relationships</h4>
          {agentRelationships.map(rel => (
            <div key={rel.id} className="text-xs">
              <span className={`px-2 py-1 rounded ${
                rel.status === 'friends' ? 'bg-green-100 text-green-800' :
                rel.status === 'tension' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {rel.status} ({rel.score})
              </span>
            </div>
          ))}
        </div>
      )}

      {agent.memory_summary && (
        <div className="memory mt-3">
          <h4 className="text-sm font-semibold mb-1">🧠 Memory</h4>
          <p className="text-xs text-gray-600 bg-blue-50 p-2 rounded border">
            {agent.memory_summary}
          </p>
        </div>
      )}
      
      <div className="agent-status mt-3">
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
          {agent.current_mood} • {agent.current_activity}
        </span>
      </div>
    </div>
  );
};

const ConversationViewer = ({ conversations }) => {
  if (!conversations.length) {
    return (
      <div className="conversation-viewer bg-gray-50 rounded-lg p-4">
        <p className="text-gray-500 text-center">No conversations yet. Start the simulation!</p>
      </div>
    );
  }

  return (
    <div className="conversation-viewer bg-white rounded-lg shadow-md p-4 max-h-96 overflow-y-auto">
      <h3 className="text-lg font-bold mb-4">Agent Conversations</h3>
      {conversations.map((round) => (
        <div key={round.id} className="conversation-round mb-4 p-3 bg-gray-50 rounded">
          <h4 className="font-semibold text-sm text-gray-700 mb-2">
            Round {round.round_number} - {round.time_period}
          </h4>
          <div className="messages">
            {round.messages.map((message) => (
              <div key={message.id} className="message mb-2">
                <div className="flex items-start">
                  <span className={`font-medium mr-2 ${
                    round.time_period.includes('Observer Input') ? 'text-purple-600' : 'text-blue-600'
                  }`}>
                    {message.agent_name}:
                  </span>
                  <span className="text-gray-800">{message.message}</span>
                </div>
                <span className="text-xs text-gray-500 ml-2">({message.mood})</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};



const ControlPanel = ({ 
  simulationState, 
  apiUsage, 
  onStartSimulation, 
  onPauseSimulation,
  onResumeSimulation,
  onNextPeriod, 
  onGenerateConversation,
  onInitResearchStation,
  onTestBackgrounds,
  onToggleAuto,
  setShowFastForward
}) => {
  const isActive = simulationState?.is_active || false;
  const autoRunning = simulationState?.auto_conversations || simulationState?.auto_time;

  return (
    <div className="control-panel bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">🎮 Simulation Control</h3>
      
      <div className="simulation-info mb-4">
        <p className="text-sm"><strong>Day:</strong> {simulationState?.current_day || 1}</p>
        <p className="text-sm"><strong>Time:</strong> {simulationState?.current_time_period || 'morning'}</p>
        <p className="text-sm"><strong>Scenario:</strong> 
          <span className="text-xs bg-gray-100 px-2 py-1 rounded ml-1">
            {simulationState?.scenario ? 
              simulationState.scenario.substring(0, 40) + (simulationState.scenario.length > 40 ? '...' : '') 
              : 'Research Station'}
          </span>
        </p>
        <p className="text-sm"><strong>Status:</strong> 
          <span className={`ml-1 px-2 py-1 rounded text-xs ${
            isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {isActive ? (autoRunning ? 'Auto Running' : 'Active') : 'Paused'}
          </span>
        </p>
        
        {/* Auto Status Indicators */}
        <div className="auto-status mt-2 space-y-1">
          <div className="flex items-center text-xs">
            <span className={`w-2 h-2 rounded-full mr-2 ${
              simulationState?.auto_conversations ? 'bg-green-500' : 'bg-gray-300'
            }`}></span>
            Auto Conversations: {simulationState?.auto_conversations ? 'ON' : 'OFF'}
          </div>
          <div className="flex items-center text-xs">
            <span className={`w-2 h-2 rounded-full mr-2 ${
              simulationState?.auto_time ? 'bg-blue-500' : 'bg-gray-300'
            }`}></span>
            Auto Time: {simulationState?.auto_time ? 'ON' : 'OFF'}
          </div>
        </div>
      </div>

      <div className="api-usage mb-4 p-3 bg-gray-50 rounded">
        <h4 className="font-semibold text-sm mb-2">API Usage Today</h4>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-blue-500 h-3 rounded-full"
            style={{width: `${(apiUsage?.requests_used || 0) / (apiUsage?.max_requests || 1400) * 100}%`}}
          ></div>
        </div>
        <p className="text-xs mt-1">
          {apiUsage?.requests_used || 0} / {apiUsage?.max_requests || 1400} requests
          ({apiUsage?.remaining || 1400} remaining)
        </p>
      </div>

      <div className="controls space-y-3">
        {/* Setup Controls */}
        <div className="setup-section">
          <h4 className="text-sm font-semibold mb-2 text-gray-700">Setup</h4>
          <button 
            onClick={onInitResearchStation}
            className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm mb-2"
          >
            Create Crypto Team
          </button>
          <p className="text-xs text-gray-500 mb-2">
            Creates 3 crypto experts: Mark (Marketing Veteran), Alex (DeFi Product Leader), Dex (Trend-Spotting Generalist)
          </p>
          
          <button 
            onClick={onTestBackgrounds}
            className="w-full bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 text-sm mb-2"
          >
            🧪 Test Background Differences
          </button>
          <p className="text-xs text-gray-500 mb-3">
            Creates 4 agents with dramatically different professional backgrounds to showcase how background influences thinking
          </p>
        </div>

        {/* Simulation Controls */}
        <div className="simulation-section">
          <h4 className="text-sm font-semibold mb-2 text-gray-700">Simulation</h4>
          
          <button 
            onClick={onStartSimulation}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm mb-2"
          >
            Start New Simulation
          </button>
          <p className="text-xs text-gray-500 mb-3">
            Resets all conversations and relationships, starts fresh
          </p>

          {/* Pause/Resume Button */}
          {isActive ? (
            <button 
              onClick={onPauseSimulation}
              className="w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 text-sm mb-2"
            >
              ⏸️ Pause Simulation
            </button>
          ) : (
            <button 
              onClick={onResumeSimulation}
              className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm mb-2"
            >
              ▶️ Resume Simulation
            </button>
          )}
        </div>
        
        {/* Fast Forward Section */}
        <div className="fast-forward-section">
          <h4 className="text-sm font-semibold mb-2 text-gray-700">Fast Forward</h4>
          <button 
            onClick={() => setShowFastForward(true)}
            className="w-full bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700 text-sm mb-2"
            disabled={!isActive}
          >
            ⚡ Fast Forward Days
          </button>
          <p className="text-xs text-gray-500 mb-3">
            Generate multiple days of progressive conversations automatically
          </p>
        </div>

        {/* Manual Controls */}
        <div className="manual-controls bg-gray-50 rounded p-3">
          <p className="text-xs font-medium mb-2 text-gray-700">Manual Controls</p>
          <button 
            onClick={onNextPeriod}
            className="w-full bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 text-xs mb-1"
            disabled={!isActive}
          >
            Next Time Period
          </button>
          
          <button 
            onClick={onGenerateConversation}
            className="w-full bg-orange-600 text-white px-3 py-2 rounded hover:bg-orange-700 text-xs"
            disabled={!isActive || (apiUsage?.remaining || 0) <= 0}
          >
            Generate Conversation
          </button>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [agents, setAgents] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [simulationState, setSimulationState] = useState(null);
  const [apiUsage, setApiUsage] = useState(null);
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoTimers, setAutoTimers] = useState({ conversation: null, time: null });
  const [showFastForward, setShowFastForward] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [archetypes, setArchetypes] = useState({});

  const handleTestBackgrounds = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/test/background-differences`);
      alert(`Created test agents with diverse backgrounds! Scenario: ${response.data.scenario}`);
      await refreshAllData();
    } catch (error) {
      console.error('Error creating test agents:', error);
    }
    setLoading(false);
  };

  // Fetch data functions
  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents`);
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API}/conversations`);
      setConversations(response.data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const fetchRelationships = async () => {
    try {
      const response = await axios.get(`${API}/relationships`);
      setRelationships(response.data);
    } catch (error) {
      console.error('Error fetching relationships:', error);
    }
  };

  const fetchSimulationState = async () => {
    try {
      const response = await axios.get(`${API}/simulation/state`);
      setSimulationState(response.data);
    } catch (error) {
      console.error('Error fetching simulation state:', error);
    }
  };

  const fetchApiUsage = async () => {
    try {
      const response = await axios.get(`${API}/api-usage`);
      setApiUsage(response.data);
    } catch (error) {
      console.error('Error fetching API usage:', error);
    }
  };

  const fetchSummaries = async () => {
    try {
      const response = await axios.get(`${API}/summaries`);
      setSummaries(response.data);
    } catch (error) {
      console.error('Error fetching summaries:', error);
    }
  };

  const fetchArchetypes = async () => {
    try {
      const response = await axios.get(`${API}/archetypes`);
      setArchetypes(response.data);
    } catch (error) {
      console.error('Error fetching archetypes:', error);
    }
  };

  const refreshAllData = async () => {
    setLoading(true);
    await Promise.all([
      fetchAgents(),
      fetchConversations(), 
      fetchRelationships(),
      fetchSimulationState(),
      fetchApiUsage(),
      fetchSummaries(),
      fetchArchetypes()
    ]);
    setLoading(false);
  };

  // Control functions
  const handleSetScenario = async (scenario) => {
    try {
      const response = await axios.post(`${API}/simulation/set-scenario`, { scenario: scenario });
      console.log('Scenario set response:', response.data);
      await fetchSimulationState();
    } catch (error) {
      console.error('Error setting scenario:', error);
      alert('Error setting scenario: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handlePauseSimulation = async () => {
    try {
      await axios.post(`${API}/simulation/pause`);
      await fetchSimulationState();
      
      // Clear timers when pausing
      if (autoTimers.conversation) {
        clearInterval(autoTimers.conversation);
      }
      if (autoTimers.time) {
        clearInterval(autoTimers.time);
      }
      setAutoTimers({ conversation: null, time: null });
    } catch (error) {
      console.error('Error pausing simulation:', error);
    }
  };

  const handleResumeSimulation = async () => {
    try {
      await axios.post(`${API}/simulation/resume`);
      await fetchSimulationState();
    } catch (error) {
      console.error('Error resuming simulation:', error);
    }
  };

  const handleToggleAuto = async (autoSettings) => {
    try {
      await axios.post(`${API}/simulation/toggle-auto-mode`, autoSettings);
      await fetchSimulationState();
      
      // Clear existing timers
      if (autoTimers.conversation) {
        clearInterval(autoTimers.conversation);
        autoTimers.conversation = null;
      }
      if (autoTimers.time) {
        clearInterval(autoTimers.time);
        autoTimers.time = null;
      }
      
      // Set up new timers if enabled
      const newTimers = { conversation: null, time: null };
      
      if (autoSettings.auto_conversations) {
        console.log('Starting auto conversations with interval:', autoSettings.conversation_interval);
        newTimers.conversation = setInterval(async () => {
          try {
            console.log('Auto generating conversation...');
            await axios.post(`${API}/conversation/generate`);
            await refreshAllData();
          } catch (error) {
            console.error('Auto conversation error:', error);
            // Don't clear interval on error, just log it
          }
        }, autoSettings.conversation_interval * 1000);
      }
      
      if (autoSettings.auto_time) {
        console.log('Starting auto time advancement with interval:', autoSettings.time_interval);
        newTimers.time = setInterval(async () => {
          try {
            console.log('Auto advancing time...');
            await axios.post(`${API}/simulation/next-period`);
            await fetchSimulationState();
          } catch (error) {
            console.error('Auto time error:', error);
            // Don't clear interval on error, just log it
          }
        }, autoSettings.time_interval * 1000);
      }
      
      setAutoTimers(newTimers);
    } catch (error) {
      console.error('Error toggling auto mode:', error);
    }
  };

  const handleGenerateSummary = async () => {
    try {
      const response = await axios.post(`${API}/simulation/generate-summary`);
      await fetchSummaries();
      return response.data;
    } catch (error) {
      console.error('Error generating summary:', error);
      return null;
    }
  };

  const handleSetupAutoReport = async (settings) => {
    try {
      const response = await axios.post(`${API}/simulation/auto-weekly-report`, settings);
      console.log('Auto report settings updated:', response.data);
    } catch (error) {
      console.error('Error setting up auto reports:', error);
    }
  };

  const handleInitResearchStation = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/simulation/init-research-station`);
      await refreshAllData();
    } catch (error) {
      console.error('Error initializing research station:', error);
    }
    setLoading(false);
  };

  const handleStartSimulation = async () => {
    setLoading(true);
    try {
      // Clear summaries immediately in frontend before API call
      setSummaries([]);
      
      await axios.post(`${API}/simulation/start`);
      await refreshAllData();
    } catch (error) {
      console.error('Error starting simulation:', error);
    }
    setLoading(false);
  };

  const handleNextPeriod = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/simulation/next-period`);
      await refreshAllData();
    } catch (error) {
      console.error('Error advancing time period:', error);
    }
    setLoading(false);
  };

  const handleGenerateConversation = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/conversation/generate`);
      await refreshAllData();
    } catch (error) {
      console.error('Error generating conversation:', error);
      alert('Error generating conversation. Check API usage limits.');
    }
    setLoading(false);
  };

  const handleFastForward = async (targetDays, conversationsPerPeriod) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/simulation/fast-forward`, {
        target_days: targetDays,
        conversations_per_period: conversationsPerPeriod
      });
      alert(`Fast forwarded ${targetDays} days! Generated ${response.data.conversations_generated} conversations.`);
      await refreshAllData();
    } catch (error) {
      console.error('Error fast forwarding:', error);
      alert('Error fast forwarding: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const handleEditAgent = (agent) => {
    setEditingAgent(agent);
  };

  const handleSaveAgent = async (agentId, agentData) => {
    try {
      await axios.put(`${API}/agents/${agentId}`, agentData);
      await fetchAgents();
    } catch (error) {
      console.error('Error updating agent:', error);
      alert('Error updating agent: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleClearMemory = async (agentId) => {
    if (!confirm('Are you sure you want to clear this agent\'s memory? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await axios.post(`${API}/agents/${agentId}/clear-memory`);
      alert(response.data.message);
      await fetchAgents();
    } catch (error) {
      console.error('Error clearing memory:', error);
      alert('Error clearing memory: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleAddMemory = async (agentId, memory) => {
    try {
      const response = await axios.post(`${API}/agents/${agentId}/add-memory`, { memory });
      
      // Show success message with URL processing info
      if (response.data.urls_processed > 0) {
        alert(`Memory added! Processed ${response.data.urls_processed} URL(s) and fetched their content.`);
      }
      
      await fetchAgents();
    } catch (error) {
      console.error('Error adding memory:', error);
      alert('Error adding memory: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSendObserverMessage = async (message) => {
    try {
      const response = await axios.post(`${API}/observer/send-message`, { observer_message: message });
      await refreshAllData();
    } catch (error) {
      console.error('Error sending observer message:', error);
      alert('Error sending message. Make sure simulation is running.');
    }
  };

  // Load initial data
  useEffect(() => {
    refreshAllData();
  }, []);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (autoTimers.conversation) clearInterval(autoTimers.conversation);
      if (autoTimers.time) clearInterval(autoTimers.time);
    };
  }, [autoTimers]);

  return (
    <div className="App min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">
              🤖 AI Agent Simulation
            </h1>
            <button 
              onClick={refreshAllData}
              disabled={loading}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 text-sm"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Agents */}
          <div className="lg:col-span-1">
            <h2 className="text-xl font-bold mb-4">AI Agents ({agents.length}/5)</h2>
            <div className="agent-grid">
              {agents.length > 0 ? (
                agents.map(agent => (
                  <AgentCard 
                    key={agent.id} 
                    agent={agent} 
                    relationships={relationships}
                    onEdit={handleEditAgent}
                    onClearMemory={handleClearMemory}
                    onAddMemory={handleAddMemory}
                  />
                ))
              ) : (
                <div className="bg-white rounded-lg shadow-md p-4 text-center">
                  <p className="text-gray-500">No agents created yet.</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Click "Initialize Research Station" to create the default 3 agents.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Middle Column - Conversations & Reports */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold mb-4">Conversations</h2>
            <ConversationViewer conversations={conversations} />
            
            {/* Observer Input - Subtle placement below conversations */}
            <ObserverInput onSendMessage={handleSendObserverMessage} />
            
            {/* Weekly Summary underneath conversations */}
            <div className="mt-6">
              <WeeklySummary 
                onGenerateSummary={handleGenerateSummary}
                summaries={summaries}
                onSetupAutoReport={handleSetupAutoReport}
              />
            </div>
          </div>

          {/* Right Column - Controls */}
          <div className="lg:col-span-1">
            <ScenarioInput onSetScenario={handleSetScenario} />
            
            <AutoControls 
              simulationState={simulationState}
              onToggleAuto={handleToggleAuto}
            />
            
            <ControlPanel
              simulationState={simulationState}
              apiUsage={apiUsage}
              onStartSimulation={handleStartSimulation}
              onPauseSimulation={handlePauseSimulation}
              onResumeSimulation={handleResumeSimulation}
              onNextPeriod={handleNextPeriod}
              onGenerateConversation={handleGenerateConversation}
              onInitResearchStation={handleInitResearchStation}
              onTestBackgrounds={handleTestBackgrounds}
              onToggleAuto={handleToggleAuto}
              setShowFastForward={setShowFastForward}
            />

            {/* Scenario Info */}
            <div className="bg-white rounded-lg shadow-md p-4 mt-4">
              <h3 className="text-lg font-bold mb-2">💰 DeFi Crisis Scenario</h3>
              <p className="text-sm text-gray-600 mb-2">
                A major DeFi protocol discovered a critical vulnerability that could drain $500M. 
                Sophisticated actors are probing the system. The team must decide on response strategy.
              </p>
              <div className="text-xs text-gray-500">
                <p><strong>Mark Castellano:</strong> Marketing veteran who survived 3 crypto cycles</p>
                <p><strong>Alex Chen:</strong> Product leader who built $2B+ TVL protocols</p>
                <p><strong>Dex Rodriguez:</strong> Crypto generalist with 30% hit rate on "crazy" ideas</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Modals */}
      <FastForwardModal
        isOpen={showFastForward}
        onClose={() => setShowFastForward(false)}
        onFastForward={handleFastForward}
      />

      <EditAgentModal
        agent={editingAgent}
        isOpen={!!editingAgent}
        onClose={() => setEditingAgent(null)}
        onSave={handleSaveAgent}
        archetypes={archetypes}
      />
    </div>
  );
}

export default App;