import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Modern Homepage for the main simulation interface
const ModernHomePage = () => {
  const [agents, setAgents] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [currentScenario, setCurrentScenario] = useState('');
  const [loading, setLoading] = useState(true);
  const [simulationState, setSimulationState] = useState(null);

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [agentsRes, conversationsRes, documentsRes, simStateRes] = await Promise.all([
          axios.get(`${API}/agents`),
          axios.get(`${API}/conversations`),
          axios.get(`${API}/documents`),
          axios.get(`${API}/simulation/state`)
        ]);

        setAgents(agentsRes.data);
        setConversations(conversationsRes.data);
        setDocuments(documentsRes.data);
        setSimulationState(simStateRes.data);
        setCurrentScenario(simStateRes.data.scenario || '');
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Simulation Controls
  const startSimulation = async () => {
    try {
      await axios.post(`${API}/simulation/start`);
      // Refresh simulation state
      const response = await axios.get(`${API}/simulation/state`);
      setSimulationState(response.data);
    } catch (error) {
      console.error('Error starting simulation:', error);
    }
  };

  const generateConversation = async () => {
    try {
      const response = await axios.post(`${API}/conversation/generate`);
      if (response.data.conversation) {
        setConversations(prev => [response.data.conversation, ...prev]);
      }
    } catch (error) {
      console.error('Error generating conversation:', error);
    }
  };

  const handleSetScenario = async (scenario, scenarioName) => {
    try {
      await axios.post(`${API}/simulation/set-scenario`, {
        scenario,
        scenario_name: scenarioName
      });
      setCurrentScenario(scenario);
    } catch (error) {
      console.error('Error setting scenario:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          className="glass-container p-8 text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1 }}
          />
          <p className="text-white text-lg">Loading your simulation workspace...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Hero Section */}
      <motion.div
        className="glass-container p-8 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <motion.h1
          className="heading-xl mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          AI Agent Simulation
        </motion.h1>
        <motion.p
          className="text-xl text-white/80 mb-8 max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          Create intelligent teams of AI agents that collaborate, discuss, and generate professional documents. 
          Watch them solve complex problems through natural conversation and expert analysis.
        </motion.p>

        <motion.div
          className="flex flex-wrap justify-center gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
        >
          <motion.button
            onClick={startSimulation}
            className="btn-premium btn-primary"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            🚀 Start New Simulation
          </motion.button>
          
          <motion.button
            onClick={generateConversation}
            className="btn-premium btn-secondary"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            💬 Generate Conversation
          </motion.button>
        </motion.div>
      </motion.div>

      {/* Current Scenario Display */}
      {currentScenario && (
        <CurrentScenarioCard currentScenario={currentScenario} autoExpand={false} />
      )}

      {/* Scenario Input */}
      <ScenarioInput onSetScenario={handleSetScenario} currentScenario={currentScenario} />

      {/* Dashboard Grid */}
      <div className="grid grid-3 gap-6">
        {/* Agents Overview */}
        <motion.div
          className="modern-card p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <span className="text-2xl">👥</span>
              Active Agents
            </h3>
            <span className="status-indicator status-info">
              {agents.length} agents
            </span>
          </div>
          
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {agents.slice(0, 5).map((agent) => (
              <motion.div
                key={agent.id}
                className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
                whileHover={{ scale: 1.02 }}
              >
                <img
                  src={agent.avatar_url}
                  alt={agent.name}
                  className="w-10 h-10 rounded-full border-2 border-white shadow-sm"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{agent.name}</p>
                  <p className="text-xs text-gray-500 truncate">{agent.expertise}</p>
                </div>
              </motion.div>
            ))}
          </div>
          
          {agents.length > 5 && (
            <div className="mt-3 text-center">
              <span className="text-sm text-gray-500">+{agents.length - 5} more agents</span>
            </div>
          )}
        </motion.div>

        {/* Recent Conversations */}
        <motion.div
          className="modern-card p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <span className="text-2xl">💬</span>
              Recent Conversations
            </h3>
            <span className="status-indicator status-success">
              {conversations.length} total
            </span>
          </div>
          
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {conversations.slice(0, 3).map((conversation, index) => (
              <motion.div
                key={conversation.id || index}
                className="p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-l-4 border-blue-400"
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-800">
                    Conversation #{conversation.id || index + 1}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(conversation.created_at || Date.now()).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {conversation.messages?.[0]?.message || conversation.content || 'No content available'}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Generated Documents */}
        <motion.div
          className="modern-card p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <span className="text-2xl">📄</span>
              Generated Documents
            </h3>
            <span className="status-indicator status-warning">
              {documents.length} docs
            </span>
          </div>
          
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {documents.slice(0, 4).map((document) => (
              <motion.div
                key={document.id}
                className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border-l-4 border-green-400"
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-800 truncate">
                    {document.metadata?.title || `Document ${document.id}`}
                  </span>
                  <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                    {document.metadata?.category || 'General'}
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  {new Date(document.metadata?.created_at || Date.now()).toLocaleDateString()}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Simulation Status */}
      {simulationState && (
        <SimulationStatusCard simulationState={simulationState} />
      )}

      {/* Quick Actions */}
      <motion.div
        className="modern-card p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.5 }}
      >
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <span className="text-2xl">⚡</span>
          Quick Actions
        </h3>
        
        <div className="grid grid-2 gap-4">
          <motion.div
            className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200 cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🎭</span>
              <div>
                <h4 className="font-medium text-gray-800">Create Agents</h4>
                <p className="text-sm text-gray-600">Add new AI agents to your team</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200 cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center space-x-3">
              <span className="text-2xl">📊</span>
              <div>
                <h4 className="font-medium text-gray-800">View Analytics</h4>
                <p className="text-sm text-gray-600">Track simulation performance</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200 cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🔄</span>
              <div>
                <h4 className="font-medium text-gray-800">Auto Mode</h4>
                <p className="text-sm text-gray-600">Enable continuous simulation</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-lg border border-orange-200 cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center space-x-3">
              <span className="text-2xl">📋</span>
              <div>
                <h4 className="font-medium text-gray-800">Export Results</h4>
                <p className="text-sm text-gray-600">Download simulation data</p>
              </div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

// Modern Current Scenario Card Component
const CurrentScenarioCard = ({ currentScenario, autoExpand }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (autoExpand) {
      setIsExpanded(true);
    }
  }, [autoExpand]);

  if (!currentScenario) {
    return null;
  }

  return (
    <motion.div
      className="modern-card p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full text-left flex items-center justify-between group"
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        <div className="flex items-center space-x-3">
          <motion.span 
            className="text-2xl"
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            📋
          </motion.span>
          <h3 className="text-lg font-semibold text-gray-800 group-hover:text-purple-600 transition-colors">
            Current Scenario
          </h3>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.3 }}
          className="text-gray-400 group-hover:text-purple-600"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </motion.div>
      </motion.button>
      
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border-l-4 border-blue-400">
              <p className="text-sm text-gray-700 leading-relaxed">
                {currentScenario}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Scenario Input Component (placeholder - will import from ModernApp)
const ScenarioInput = ({ onSetScenario, currentScenario }) => {
  return (
    <motion.div
      className="modern-card p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <span className="text-2xl">🎭</span>
        Scenario Management
      </h3>
      <p className="text-gray-600">
        Scenario management interface will be integrated here.
      </p>
    </motion.div>
  );
};

// Simulation Status Card
const SimulationStatusCard = ({ simulationState }) => {
  const isRunning = simulationState?.auto_conversations || simulationState?.auto_time;
  
  return (
    <motion.div
      className="modern-card p-6 border-l-4 border-blue-500"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <motion.div
            className={`w-4 h-4 rounded-full ${isRunning ? 'bg-green-500' : 'bg-gray-400'}`}
            animate={isRunning ? { scale: [1, 1.2, 1] } : {}}
            transition={{ repeat: isRunning ? Infinity : 0, duration: 2 }}
          />
          <div>
            <h3 className="text-lg font-semibold text-gray-800">
              Simulation Status: {isRunning ? 'RUNNING' : 'PAUSED'}
            </h3>
            <p className="text-sm text-gray-600">
              {isRunning ? 'Agents are actively collaborating' : 'Simulation is currently paused'}
            </p>
          </div>
        </div>
        
        {isRunning && (
          <div className="flex items-center space-x-2">
            <motion.div
              className="flex space-x-1"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ repeat: Infinity, duration: 2 }}
            >
              <div className="w-2 h-6 bg-blue-500 rounded"></div>
              <div className="w-2 h-6 bg-blue-500 rounded"></div>
              <div className="w-2 h-6 bg-blue-500 rounded"></div>
            </motion.div>
            <span className="text-sm text-gray-600">Processing...</span>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ModernHomePage;