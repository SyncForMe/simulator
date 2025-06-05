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

const AgentCard = ({ agent, relationships }) => {
  const getPersonalityColor = (value) => {
    if (value <= 3) return "bg-red-500";
    if (value <= 6) return "bg-yellow-500"; 
    return "bg-green-500";
  };

  const agentRelationships = relationships.filter(r => r.agent1_id === agent.id);

  return (
    <div className="agent-card bg-white rounded-lg shadow-md p-4 m-2">
      <div className="agent-header">
        <h3 className="text-lg font-bold text-gray-800">{agent.name}</h3>
        <p className="text-sm text-gray-600">{agent.archetype}</p>
        <p className="text-xs text-gray-500 italic">"{agent.goal}"</p>
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
  onNextPeriod, 
  onGenerateConversation,
  onInitResearchStation,
  onToggleAuto
}) => {
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
            simulationState?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {simulationState?.is_active ? 'Active' : 'Inactive'}
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

      <div className="controls space-y-2">
        <button 
          onClick={onInitResearchStation}
          className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm"
        >
          Initialize Research Station
        </button>
        
        <button 
          onClick={onStartSimulation}
          className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm"
        >
          Start New Simulation
        </button>
        
        <div className="manual-controls bg-gray-50 rounded p-2">
          <p className="text-xs font-medium mb-2">Manual Controls</p>
          <button 
            onClick={onNextPeriod}
            className="w-full bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 text-xs mb-1"
            disabled={!simulationState?.is_active}
          >
            Next Time Period
          </button>
          
          <button 
            onClick={onGenerateConversation}
            className="w-full bg-orange-600 text-white px-3 py-2 rounded hover:bg-orange-700 text-xs"
            disabled={!simulationState?.is_active || (apiUsage?.remaining || 0) <= 0}
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
      await axios.post(`${API}/simulation/set-scenario`, { scenario });
      await fetchSimulationState();
    } catch (error) {
      console.error('Error setting scenario:', error);
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