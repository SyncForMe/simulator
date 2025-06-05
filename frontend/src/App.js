import React, { useState, useEffect } from "react";
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

const WeeklySummary = ({ onGenerateSummary, summaries }) => {
  const [loading, setLoading] = useState(false);
  const [latestSummary, setLatestSummary] = useState(null);

  useEffect(() => {
    if (summaries && summaries.length > 0) {
      setLatestSummary(summaries[0]);
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

  return (
    <div className="weekly-summary bg-white rounded-lg shadow-md p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-lg font-bold">📊 Weekly Summary</h3>
        <button
          onClick={handleGenerateSummary}
          disabled={loading}
          className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate Summary"}
        </button>
      </div>
      
      {latestSummary ? (
        <div className="summary-content bg-gray-50 rounded p-3 text-sm">
          <div className="mb-2 text-xs text-gray-600">
            Day {latestSummary.day} • {latestSummary.conversations_count} conversations analyzed
          </div>
          <div className="whitespace-pre-wrap">{latestSummary.summary}</div>
        </div>
      ) : (
        <p className="text-gray-500 text-sm italic">No summary generated yet. Click the button to create one!</p>
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
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-96 overflow-y-auto">
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
                rows="2"
                placeholder="Professional background and experience"
                disabled={loading}
              />
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

const AgentCard = ({ agent, relationships, onEdit }) => {
  const getPersonalityColor = (value) => {
    if (value <= 3) return "bg-red-500";
    if (value <= 6) return "bg-yellow-500"; 
    return "bg-green-500";
  };

  const agentRelationships = relationships.filter(r => r.agent1_id === agent.id);

  return (
    <div className="agent-card bg-white rounded-lg shadow-md p-4 m-2 relative">
      <button
        onClick={() => onEdit(agent)}
        className="absolute top-2 right-2 bg-blue-100 hover:bg-blue-200 text-blue-600 p-1 rounded text-xs"
        title="Edit Agent"
      >
        ✏️
      </button>
      
      <div className="agent-header">
        <h3 className="text-lg font-bold text-gray-800">{agent.name}</h3>
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
          <h4 className="text-sm font-semibold mb-1">Memory</h4>
          <p className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
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
                  <span className="font-medium text-blue-600 mr-2">{message.agent_name}:</span>
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
  onToggleAuto
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
            Create Research Team
          </button>
          <p className="text-xs text-gray-500 mb-3">
            Creates 3 AI agents: Dr. Sarah Chen (Scientist), Marcus Rivera (Optimist), Alex Thompson (Skeptic)
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
      fetchSummaries()
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
      }
      if (autoTimers.time) {
        clearInterval(autoTimers.time);
      }
      
      // Set up new timers if enabled
      const newTimers = { conversation: null, time: null };
      
      if (autoSettings.auto_conversations) {
        newTimers.conversation = setInterval(async () => {
          try {
            await axios.post(`${API}/conversation/generate`);
            await refreshAllData();
          } catch (error) {
            console.error('Auto conversation error:', error);
          }
        }, autoSettings.conversation_interval * 1000);
      }
      
      if (autoSettings.auto_time) {
        newTimers.time = setInterval(async () => {
          try {
            await axios.post(`${API}/simulation/next-period`);
            await fetchSimulationState();
          } catch (error) {
            console.error('Auto time error:', error);
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

          {/* Middle Column - Conversations */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold mb-4">Conversations</h2>
            <ConversationViewer conversations={conversations} />
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
              onToggleAuto={handleToggleAuto}
            />

            <div className="mt-4">
              <WeeklySummary 
                onGenerateSummary={handleGenerateSummary}
                summaries={summaries}
              />
            </div>

            {/* Scenario Info */}
            <div className="bg-white rounded-lg shadow-md p-4 mt-4">
              <h3 className="text-lg font-bold mb-2">Research Station Scenario</h3>
              <p className="text-sm text-gray-600 mb-2">
                Three researchers are stationed together for a month-long study. 
                They're getting to know each other and establishing team dynamics.
              </p>
              <div className="text-xs text-gray-500">
                <p><strong>Dr. Sarah Chen:</strong> Analytical scientist studying team behavior</p>
                <p><strong>Marcus Rivera:</strong> Optimistic team member focused on collaboration</p>
                <p><strong>Alex Thompson:</strong> Skeptical researcher concerned about mission safety</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;