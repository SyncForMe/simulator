import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

// Debug logging
console.log('Environment variables loaded:', {
  BACKEND_URL,
  GOOGLE_CLIENT_ID: GOOGLE_CLIENT_ID ? 'Present' : 'Missing',
  NODE_ENV: process.env.NODE_ENV
});

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  useEffect(() => {
    // Initialize token from localStorage
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      setToken(savedToken);
      checkAuthStatus(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const checkAuthStatus = async (authToken) => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setUser(response.data);
    } catch (error) {
      // Token is invalid, remove it
      console.log('Token validation failed, logging out');
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
    }
    setLoading(false);
  };

  const login = async (googleCredential) => {
    try {
      const response = await axios.post(`${API}/auth/google`, {
        credential: googleCredential
      });
      
      const { access_token, user: userData } = response.data;
      
      // Store token and user data
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    token,
    isAuthenticated: !!user,
    setUser,
    setToken
  };

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

const LoginModal = ({ isOpen, onClose }) => {
  const { login, setUser, setToken } = useAuth();
  const [loginLoading, setLoginLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGoogleLogin = () => {
    setLoginLoading(true);
    setError('');
    
    // Direct OAuth URL approach
    const googleAuthUrl = new URL('https://accounts.google.com/oauth/authorize');
    googleAuthUrl.searchParams.set('client_id', GOOGLE_CLIENT_ID);
    googleAuthUrl.searchParams.set('redirect_uri', window.location.origin);
    googleAuthUrl.searchParams.set('response_type', 'code');
    googleAuthUrl.searchParams.set('scope', 'openid profile email');
    googleAuthUrl.searchParams.set('access_type', 'offline');
    googleAuthUrl.searchParams.set('state', 'login');

    // Open Google OAuth in a popup
    const popup = window.open(
      googleAuthUrl.toString(),
      'google-oauth',
      'width=500,height=600,scrollbars=yes,resizable=yes'
    );

    // Listen for the popup to close or for a message
    const checkClosed = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkClosed);
        setLoginLoading(false);
        setError('Login was cancelled');
      }
    }, 1000);

    // Listen for messages from popup
    const messageListener = (event) => {
      if (event.origin !== window.location.origin) return;
      if (!event.data || typeof event.data !== 'object') return;
      
      if (event.data.type === 'GOOGLE_AUTH_SUCCESS') {
        clearInterval(checkClosed);
        popup.close();
        handleAuthSuccess(event.data.code);
        window.removeEventListener('message', messageListener);
      } else if (event.data.type === 'GOOGLE_AUTH_ERROR') {
        clearInterval(checkClosed);
        popup.close();
        setError(event.data.error);
        setLoginLoading(false);
        window.removeEventListener('message', messageListener);
      }
    };

    window.addEventListener('message', messageListener);
  };

  const handleAuthSuccess = async (code) => {
    try {
      // For now, let's use a test token approach
      // Since we can't easily handle the OAuth callback in this setup
      setError('OAuth implementation needs backend callback handling. Let me implement a simpler test approach...');
      setLoginLoading(false);
    } catch (err) {
      setError('Login failed. Please try again.');
      setLoginLoading(false);
    }
  };

  // Simplified test login for development
  const handleTestLogin = async () => {
    setLoginLoading(true);
    setError('');
    
    try {
      // Call the backend test login endpoint
      const response = await axios.post(`${API}/auth/test-login`);
      const { access_token, user: userData } = response.data;
      
      // Store token and user data
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      
      // Close modal and show success
      onClose();
      setTimeout(() => {
        alert('✅ Test login successful! You can now save agents and access conversation history.');
      }, 500);
      
    } catch (err) {
      console.error('Test login error:', err);
      setError(`Test login failed: ${err.response?.data?.detail || err.message}`);
    }
    setLoginLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold">Welcome to AI Agent Simulation</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        <div className="text-center mb-6">
          <p className="text-gray-600 mb-4">
            Sign in with your Google account to save your agents and conversation history.
          </p>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4 text-sm">
              {error}
            </div>
          )}
          
          {loginLoading && (
            <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2 rounded mb-4">
              Signing in...
            </div>
          )}
          
          {/* Temporary development buttons */}
          <div className="space-y-3">
            <button
              onClick={handleGoogleLogin}
              disabled={loginLoading}
              className="w-full bg-white border border-gray-300 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-50 font-medium flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              <span>Sign in with Google (Direct OAuth)</span>
            </button>
            
            <div className="text-xs text-gray-500">
              <p>Client ID: {GOOGLE_CLIENT_ID ? 'Configured' : 'Missing'}</p>
              <p>Status: Working on OAuth redirect_uri_mismatch issue</p>
            </div>
            
            <button
              onClick={handleTestLogin}
              disabled={loginLoading}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-medium disabled:opacity-50"
            >
              🧪 Test Login (Development)
            </button>
          </div>
        </div>
        
        <div className="text-xs text-gray-500 text-center">
          <p>✨ Free to use • 🔒 Secure authentication • 💾 Save your work</p>
        </div>
      </div>
    </div>
  );
};

const UserProfile = ({ user, onLogout }) => {
  const [showDropdown, setShowDropdown] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center space-x-2 bg-white rounded-lg p-2 shadow-md hover:shadow-lg transition-shadow"
      >
        {user.picture ? (
          <img 
            src={user.picture} 
            alt={user.name}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
            {user.name.charAt(0).toUpperCase()}
          </div>
        )}
        <span className="text-sm font-medium text-gray-700">{user.name}</span>
        <span className="text-gray-400">▼</span>
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-50">
          <div className="p-3 border-b">
            <p className="text-sm font-medium text-gray-900">{user.name}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
          <div className="p-1">
            <button
              onClick={() => {
                onLogout();
                setShowDropdown(false);
              }}
              className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
            >
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Agent Archetypes - matching backend
const AGENT_ARCHETYPES = {
  "scientist": {
    "name": "The Scientist",
    "description": "Logical, curious, methodical"
  },
  "artist": {
    "name": "The Artist", 
    "description": "Creative, emotional, expressive"
  },
  "leader": {
    "name": "The Leader",
    "description": "Confident, decisive, social"
  },
  "skeptic": {
    "name": "The Skeptic",
    "description": "Questioning, cautious, analytical"
  },
  "optimist": {
    "name": "The Optimist", 
    "description": "Positive, encouraging, hopeful"
  },
  "introvert": {
    "name": "The Introvert",
    "description": "Quiet, thoughtful, observant"
  },
  "adventurer": {
    "name": "The Adventurer",
    "description": "Bold, spontaneous, energetic"
  },
  "mediator": {
    "name": "The Mediator",
    "description": "Peaceful, diplomatic, empathetic"
  }
};

const ScenarioInput = ({ onSetScenario }) => {
  const [scenario, setScenario] = useState("");
  const [loading, setLoading] = useState(false);
  const [justSubmitted, setJustSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    if (!scenario.trim()) return;
    
    setLoading(true);
    setJustSubmitted(true);
    await onSetScenario(scenario);
    setLoading(false);
    
    // Keep the text visible for 3 seconds to show it was applied
    setTimeout(() => {
      setScenario("");
      setJustSubmitted(false);
    }, 3000);
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
            className={`w-full p-3 border rounded-lg resize-none ${justSubmitted ? 'bg-green-50 border-green-300' : ''}`}
            rows="3"
            disabled={loading || justSubmitted}
          />
          {justSubmitted && (
            <p className="text-xs text-green-600 mt-1">
              ✅ Scenario applied! Text will clear in a moment...
            </p>
          )}
        </div>
        <button
          type="submit"
          disabled={loading || !scenario.trim() || justSubmitted}
          className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? "Setting Scenario..." : justSubmitted ? "Scenario Applied!" : "Set New Scenario"}
        </button>
      </form>
    </div>
  );
};

const SimulationStatusBar = ({ simulationState }) => {
  const isRunning = simulationState?.auto_conversations || simulationState?.auto_time;
  
  return (
    <div className="simulation-status bg-white rounded-lg shadow-md p-4 mb-4 border-l-4 border-blue-500">
      <div className="flex items-center justify-between flex-wrap">
        <div className="flex items-center space-x-3 flex-1 min-w-0">
          <div className={`w-3 h-3 rounded-full flex-shrink-0 ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-gray-800">
              Simulation: {isRunning ? 'RUNNING' : 'PAUSED'}
            </h3>
          </div>
        </div>
        
        {isRunning && (
          <div className="text-xs text-gray-600 flex-shrink-0 ml-4 mt-2 sm:mt-0">
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                <div className="w-1 h-4 bg-blue-500 animate-pulse" style={{animationDelay: '0s'}}></div>
                <div className="w-1 h-4 bg-blue-500 animate-pulse" style={{animationDelay: '0.2s'}}></div>
                <div className="w-1 h-4 bg-blue-500 animate-pulse" style={{animationDelay: '0.4s'}}></div>
              </div>
              <span className="whitespace-nowrap">Processing...</span>
            </div>
          </div>
        )}
      </div>
      
      {isRunning && (
        <div className="mt-3 pt-2 border-t border-gray-200 text-xs text-gray-500">
          <div className="flex flex-wrap gap-4">
            {simulationState?.auto_conversations && (
              <span className="flex items-center">
                🤖 Auto conversations every {simulationState?.conversation_interval || 10}s
              </span>
            )}
            {simulationState?.auto_time && (
              <span className="flex items-center">
                ⏰ Auto time progression every {simulationState?.time_interval || 60}s
              </span>
            )}
          </div>
        </div>
      )}
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

const LanguageSelector = ({ selectedLanguage, onLanguageChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);

  const languages = [
    // Major World Languages
    { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸', voiceSupported: true },
    { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸', voiceSupported: true },
    { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷', voiceSupported: true },
    { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪', voiceSupported: true },
    { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹', voiceSupported: true },
    { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹', voiceSupported: true },
    { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺', voiceSupported: true },
    { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵', voiceSupported: true },
    { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷', voiceSupported: true },
    { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳', voiceSupported: true },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳', voiceSupported: true },
    { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', voiceSupported: true },
    
    // European Languages
    { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', flag: '🇳🇱', voiceSupported: false },
    { code: 'sv', name: 'Swedish', nativeName: 'Svenska', flag: '🇸🇪', voiceSupported: false },
    { code: 'no', name: 'Norwegian', nativeName: 'Norsk', flag: '🇳🇴', voiceSupported: false },
    { code: 'da', name: 'Danish', nativeName: 'Dansk', flag: '🇩🇰', voiceSupported: false },
    { code: 'fi', name: 'Finnish', nativeName: 'Suomi', flag: '🇫🇮', voiceSupported: false },
    { code: 'pl', name: 'Polish', nativeName: 'Polski', flag: '🇵🇱', voiceSupported: false },
    { code: 'cs', name: 'Czech', nativeName: 'Čeština', flag: '🇨🇿', voiceSupported: false },
    { code: 'sk', name: 'Slovak', nativeName: 'Slovenčina', flag: '🇸🇰', voiceSupported: false },
    { code: 'hu', name: 'Hungarian', nativeName: 'Magyar', flag: '🇭🇺', voiceSupported: false },
    { code: 'ro', name: 'Romanian', nativeName: 'Română', flag: '🇷🇴', voiceSupported: false },
    { code: 'bg', name: 'Bulgarian', nativeName: 'Български', flag: '🇧🇬', voiceSupported: false },
    { code: 'hr', name: 'Croatian', nativeName: 'Hrvatski', flag: '🇭🇷', voiceSupported: false },
    { code: 'sr', name: 'Serbian', nativeName: 'Српски', flag: '🇷🇸', voiceSupported: false },
    { code: 'sl', name: 'Slovenian', nativeName: 'Slovenščina', flag: '🇸🇮', voiceSupported: false },
    { code: 'et', name: 'Estonian', nativeName: 'Eesti', flag: '🇪🇪', voiceSupported: false },
    { code: 'lv', name: 'Latvian', nativeName: 'Latviešu', flag: '🇱🇻', voiceSupported: false },
    { code: 'lt', name: 'Lithuanian', nativeName: 'Lietuvių', flag: '🇱🇹', voiceSupported: false },
    { code: 'el', name: 'Greek', nativeName: 'Ελληνικά', flag: '🇬🇷', voiceSupported: false },
    { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷', voiceSupported: false },
    
    // Asian Languages
    { code: 'th', name: 'Thai', nativeName: 'ไทย', flag: '🇹🇭', voiceSupported: false },
    { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt', flag: '🇻🇳', voiceSupported: false },
    { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩', voiceSupported: false },
    { code: 'ms', name: 'Malay', nativeName: 'Bahasa Melayu', flag: '🇲🇾', voiceSupported: false },
    { code: 'tl', name: 'Filipino', nativeName: 'Filipino', flag: '🇵🇭', voiceSupported: false },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇧🇩', voiceSupported: false },
    { code: 'ur', name: 'Urdu', nativeName: 'اردو', flag: '🇵🇰', voiceSupported: false },
    { code: 'fa', name: 'Persian', nativeName: 'فارسی', flag: '🇮🇷', voiceSupported: false },
    { code: 'he', name: 'Hebrew', nativeName: 'עברית', flag: '🇮🇱', voiceSupported: false },
    
    // African Languages
    { code: 'sw', name: 'Swahili', nativeName: 'Kiswahili', flag: '🇹🇿', voiceSupported: false },
    { code: 'am', name: 'Amharic', nativeName: 'አማርኛ', flag: '🇪🇹', voiceSupported: false },
    { code: 'zu', name: 'Zulu', nativeName: 'isiZulu', flag: '🇿🇦', voiceSupported: false },
    { code: 'af', name: 'Afrikaans', nativeName: 'Afrikaans', flag: '🇿🇦', voiceSupported: false },
    
    // Americas Languages
    { code: 'pt-br', name: 'Portuguese (Brazil)', nativeName: 'Português (Brasil)', flag: '🇧🇷', voiceSupported: true },
    { code: 'es-mx', name: 'Spanish (Mexico)', nativeName: 'Español (México)', flag: '🇲🇽', voiceSupported: true },
    { code: 'fr-ca', name: 'French (Canada)', nativeName: 'Français (Canada)', flag: '🇨🇦', voiceSupported: false },
    
    // Additional Major Languages
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳', voiceSupported: false },
    { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳', voiceSupported: false },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳', voiceSupported: false },
    { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', flag: '🇮🇳', voiceSupported: false },
    { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳', voiceSupported: false },
    { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳', voiceSupported: false },
    { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', flag: '🇮🇳', voiceSupported: false }
  ];

  const filteredLanguages = languages.filter(lang =>
    lang.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lang.nativeName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lang.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedLang = languages.find(l => l.code === selectedLanguage) || languages[0];

  const handleLanguageSelect = async (langCode) => {
    if (langCode === selectedLanguage) return;
    
    setIsTranslating(true);
    setIsOpen(false);
    setSearchTerm('');
    
    try {
      // First set the language
      await onLanguageChange(langCode);
      
      // Then translate existing conversations
      await axios.post(`${API}/conversations/translate`, { 
        target_language: langCode 
      });
      
      // Refresh conversations to show translated versions
      window.location.reload(); // Simple way to refresh all data
    } catch (error) {
      console.error('Error changing language:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <div className="language-selector bg-white rounded-lg shadow-md p-4 mb-4">
      <h3 className="text-lg font-bold mb-3">🌍 Language / Idioma</h3>
      
      <div className="relative">
        {/* Selected Language Display - Simplified */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={isTranslating}
          className={`w-full flex items-center justify-between p-3 border rounded-lg bg-white hover:bg-gray-50 ${
            isTranslating ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          <div className="flex items-center space-x-3">
            <div className="text-left">
              <div className="font-medium">{selectedLang.name}</div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {isTranslating && <div className="text-xs text-blue-600">Translating...</div>}
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-hidden">
            {/* Search Bar */}
            <div className="p-3 border-b border-gray-100">
              <input
                type="text"
                placeholder="Search languages..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full p-2 border border-gray-200 rounded text-sm focus:border-blue-500 focus:outline-none"
                autoFocus
              />
            </div>
            
            {/* Language List */}
            <div className="max-h-60 overflow-y-auto">
              {filteredLanguages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageSelect(lang.code)}
                  className={`w-full flex items-center justify-between p-3 hover:bg-gray-50 text-left ${
                    selectedLanguage === lang.code ? 'bg-blue-50 text-blue-700' : ''
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{lang.flag}</span>
                    <div>
                      <div className="font-medium">{lang.nativeName}</div>
                      <div className="text-xs text-gray-500">{lang.name}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    {lang.voiceSupported && (
                      <span 
                        className="text-green-600 text-sm cursor-help" 
                        title="This language is supported by voice narration"
                      >
                        🔊
                      </span>
                    )}
                    {selectedLanguage === lang.code && (
                      <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
              
              {filteredLanguages.length === 0 && (
                <div className="p-3 text-center text-gray-500 text-sm">
                  No languages found matching "{searchTerm}"
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {isTranslating && (
        <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
          🔄 Translating existing conversations to {selectedLang.nativeName}...
        </div>
      )}
    </div>
  );
};

const ConversationControls = ({ 
  simulationState, 
  onPauseSimulation, 
  onResumeSimulation, 
  onGenerateConversation,
  onNextPeriod,
  onToggleAuto 
}) => {
  const isActive = simulationState?.auto_conversations || simulationState?.auto_time;
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4 mt-4">
      <h4 className="text-sm font-semibold mb-3 text-gray-700">Conversation Controls</h4>
      
      <div className="grid grid-cols-1 gap-2">
        {/* Pause/Resume Button */}
        {isActive ? (
          <button 
            onClick={onPauseSimulation}
            className="w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 text-sm font-medium"
          >
            ⏸️ Pause Simulation
          </button>
        ) : (
          <button 
            onClick={onResumeSimulation}
            className="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm font-medium"
          >
            ▶️ Resume Simulation
          </button>
        )}
        
        {/* Generate Conversation Button */}
        <button 
          onClick={onGenerateConversation}
          className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm font-medium"
        >
          💬 Generate Conversation
        </button>
        
        {/* Next Period Button */}
        <button 
          onClick={onNextPeriod}
          className="w-full bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 text-sm font-medium"
        >
          ⏭️ Next Period
        </button>
        
        {/* Auto Toggle */}
        <button 
          onClick={onToggleAuto}
          className={`w-full px-4 py-2 rounded text-sm font-medium ${
            isActive 
              ? 'bg-orange-600 text-white hover:bg-orange-700' 
              : 'bg-gray-600 text-white hover:bg-gray-700'
          }`}
        >
          🤖 Auto Mode: {isActive ? 'ON' : 'OFF'}
        </button>
      </div>
      
      <p className="text-xs text-gray-500 mt-3 text-center">
        {isActive 
          ? 'Auto mode is running - conversations and time advance automatically' 
          : 'Manual mode - use buttons to control simulation flow'
        }
      </p>
    </div>
  );
};

const StartSimulationControl = ({ onStartSimulation }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 mt-4">
      <button 
        onClick={onStartSimulation}
        className="w-full bg-blue-600 text-white px-4 py-3 rounded hover:bg-blue-700 text-sm font-medium transition-colors"
      >
        🚀 Start New Simulation
      </button>
      <p className="text-xs text-gray-500 mt-2 text-center">
        Resets all conversations and relationships, starts fresh with your configuration
      </p>
    </div>
  );
};

const ConversationTimeStatus = ({ simulationState }) => {
  const autoConversations = simulationState?.auto_conversations || false;
  const autoTime = simulationState?.auto_time || false;
  
  return (
    <div className="conversation-time-status bg-gray-50 rounded-lg p-3 mt-3 border border-gray-200">
      <div className="flex items-center space-x-6 text-xs">
        <span className={`flex items-center ${autoConversations ? 'text-green-600' : 'text-gray-500'}`}>
          <div className={`w-2 h-2 rounded-full mr-2 flex-shrink-0 ${autoConversations ? 'bg-green-500' : 'bg-gray-400'}`}></div>
          Conversations: {autoConversations ? 'AUTO' : 'MANUAL'}
        </span>
        <span className={`flex items-center ${autoTime ? 'text-blue-600' : 'text-gray-500'}`}>
          <div className={`w-2 h-2 rounded-full mr-2 flex-shrink-0 ${autoTime ? 'bg-blue-500' : 'bg-gray-400'}`}></div>
          Time: {autoTime ? 'AUTO' : 'MANUAL'}
        </span>
      </div>
    </div>
  );
};

const ObserverInput = ({ onSendMessage }) => {
  const [message, setMessage] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
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

const MarkdownRenderer = ({ text }) => {
  const renderMarkdown = (text) => {
    if (!text) return '';
    
    // Convert **bold** to <strong>
    let rendered = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert line breaks
    rendered = rendered.replace(/\n/g, '<br/>');
    
    return rendered;
  };

  return (
    <div 
      className="whitespace-pre-wrap text-gray-800"
      dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }}
    />
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
    if (!latestSummary?.summary) return;
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
            <MarkdownRenderer text={sections.key_events || "No key events identified in this period."} />
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
                    <MarkdownRenderer text={sections[section.key]} />
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
            <strong>Report Generated:</strong> Day {latestSummary.day_generated || latestSummary.day || 'Unknown'} • {latestSummary.conversations_count || 0} conversations analyzed
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
              <MarkdownRenderer text={latestSummary.summary || "No content available"} />
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
    if (e && e.preventDefault) {
      e.preventDefault();
    }
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
                {archetypes && Object.entries(archetypes).map(([key, value]) => (
                  <option key={key} value={key}>{value?.name || key}</option>
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

const AgentCard = ({ agent, relationships, onEdit, onClearMemory, onAddMemory, onDelete }) => {
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
        <button
          onClick={() => onDelete(agent.id, agent.name)}
          className="bg-red-500 hover:bg-red-600 text-white p-1 rounded text-xs"
          title="Delete Agent"
        >
          🗑️
        </button>
      </div>
      
      {/* Avatar and Agent Header */}
      <div className="agent-header flex items-start space-x-3">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {agent.avatar_url ? (
            <div className="relative">
              <img 
                src={agent.avatar_url} 
                alt={`${agent.name} avatar`}
                className="w-16 h-16 rounded-full object-cover border-2 border-gray-200 avatar-animation"
              />
              {/* Subtle animation overlay */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
            </div>
          ) : (
            <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-2xl font-bold border-2 border-gray-300">
              {agent.name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        {/* Agent Info */}
        <div className="flex-1 pr-16">
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

const CompactLanguageSelector = ({ selectedLanguage, onLanguageChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);

  const languages = [
    // Major World Languages
    { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸', voiceSupported: true },
    { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸', voiceSupported: true },
    { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷', voiceSupported: true },
    { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪', voiceSupported: true },
    { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹', voiceSupported: true },
    { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹', voiceSupported: true },
    { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺', voiceSupported: true },
    { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵', voiceSupported: true },
    { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷', voiceSupported: true },
    { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳', voiceSupported: true },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳', voiceSupported: true },
    { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', voiceSupported: true },
    
    // European Languages
    { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', flag: '🇳🇱', voiceSupported: false },
    { code: 'sv', name: 'Swedish', nativeName: 'Svenska', flag: '🇸🇪', voiceSupported: false },
    { code: 'no', name: 'Norwegian', nativeName: 'Norsk', flag: '🇳🇴', voiceSupported: false },
    { code: 'da', name: 'Danish', nativeName: 'Dansk', flag: '🇩🇰', voiceSupported: false },
    { code: 'fi', name: 'Finnish', nativeName: 'Suomi', flag: '🇫🇮', voiceSupported: false },
    { code: 'pl', name: 'Polish', nativeName: 'Polski', flag: '🇵🇱', voiceSupported: false },
    { code: 'cs', name: 'Czech', nativeName: 'Čeština', flag: '🇨🇿', voiceSupported: false },
    { code: 'sk', name: 'Slovak', nativeName: 'Slovenčina', flag: '🇸🇰', voiceSupported: false },
    { code: 'hu', name: 'Hungarian', nativeName: 'Magyar', flag: '🇭🇺', voiceSupported: false },
    { code: 'ro', name: 'Romanian', nativeName: 'Română', flag: '🇷🇴', voiceSupported: false },
    { code: 'bg', name: 'Bulgarian', nativeName: 'Български', flag: '🇧🇬', voiceSupported: false },
    { code: 'hr', name: 'Croatian', nativeName: 'Hrvatski', flag: '🇭🇷', voiceSupported: false },
    { code: 'sr', name: 'Serbian', nativeName: 'Српски', flag: '🇷🇸', voiceSupported: false },
    { code: 'sl', name: 'Slovenian', nativeName: 'Slovenščina', flag: '🇸🇮', voiceSupported: false },
    { code: 'et', name: 'Estonian', nativeName: 'Eesti', flag: '🇪🇪', voiceSupported: false },
    { code: 'lv', name: 'Latvian', nativeName: 'Latviešu', flag: '🇱🇻', voiceSupported: false },
    { code: 'lt', name: 'Lithuanian', nativeName: 'Lietuvių', flag: '🇱🇹', voiceSupported: false },
    { code: 'el', name: 'Greek', nativeName: 'Ελληνικά', flag: '🇬🇷', voiceSupported: false },
    { code: 'tr', name: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷', voiceSupported: false },
    
    // Asian Languages
    { code: 'th', name: 'Thai', nativeName: 'ไทย', flag: '🇹🇭', voiceSupported: false },
    { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt', flag: '🇻🇳', voiceSupported: false },
    { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩', voiceSupported: false },
    { code: 'ms', name: 'Malay', nativeName: 'Bahasa Melayu', flag: '🇲🇾', voiceSupported: false },
    { code: 'tl', name: 'Filipino', nativeName: 'Filipino', flag: '🇵🇭', voiceSupported: false },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা', flag: '🇧🇩', voiceSupported: false },
    { code: 'ur', name: 'Urdu', nativeName: 'اردو', flag: '🇵🇰', voiceSupported: false },
    { code: 'fa', name: 'Persian', nativeName: 'فارسی', flag: '🇮🇷', voiceSupported: false },
    { code: 'he', name: 'Hebrew', nativeName: 'עברית', flag: '🇮🇱', voiceSupported: false },
    
    // African Languages
    { code: 'sw', name: 'Swahili', nativeName: 'Kiswahili', flag: '🇹🇿', voiceSupported: false },
    { code: 'am', name: 'Amharic', nativeName: 'አማርኛ', flag: '🇪🇹', voiceSupported: false },
    { code: 'zu', name: 'Zulu', nativeName: 'isiZulu', flag: '🇿🇦', voiceSupported: false },
    { code: 'af', name: 'Afrikaans', nativeName: 'Afrikaans', flag: '🇿🇦', voiceSupported: false },
    
    // Americas Languages
    { code: 'pt-br', name: 'Portuguese (Brazil)', nativeName: 'Português (Brasil)', flag: '🇧🇷', voiceSupported: true },
    { code: 'es-mx', name: 'Spanish (Mexico)', nativeName: 'Español (México)', flag: '🇲🇽', voiceSupported: true },
    { code: 'fr-ca', name: 'French (Canada)', nativeName: 'Français (Canada)', flag: '🇨🇦', voiceSupported: false },
    
    // Additional Major Languages
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்', flag: '🇮🇳', voiceSupported: false },
    { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳', voiceSupported: false },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी', flag: '🇮🇳', voiceSupported: false },
    { code: 'gu', name: 'Gujarati', nativeName: 'ગુજરાતી', flag: '🇮🇳', voiceSupported: false },
    { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ', flag: '🇮🇳', voiceSupported: false },
    { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം', flag: '🇮🇳', voiceSupported: false },
    { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ', flag: '🇮🇳', voiceSupported: false }
  ];

  const filteredLanguages = languages.filter(lang =>
    lang.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lang.nativeName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lang.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedLang = languages.find(l => l.code === selectedLanguage) || languages[0];

  const handleLanguageSelect = async (langCode) => {
    if (langCode === selectedLanguage) return;
    
    setIsTranslating(true);
    setIsOpen(false);
    setSearchTerm('');
    
    try {
      // Set the language and trigger translation
      await onLanguageChange(langCode);
      
      // Translate existing conversations
      const response = await axios.post(`${API}/conversations/translate`, { 
        target_language: langCode 
      });
      
      if (response.data.success) {
        // Refresh to show translated content
        window.location.reload();
      } else {
        console.error('Translation failed:', response.data);
      }
    } catch (error) {
      console.error('Error changing language:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <div className="relative">
      {/* Compact Language Button - Removed globe icon, added translation status */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isTranslating}
        className={`flex items-center space-x-1 px-3 py-1 rounded text-xs border hover:bg-gray-200 ${
          isTranslating 
            ? 'bg-blue-100 text-blue-700 border-blue-300 cursor-not-allowed' 
            : 'bg-gray-100 text-gray-700 border-gray-300'
        }`}
      >
        <span>{isTranslating ? 'Translating...' : selectedLang.name}</span>
        {!isTranslating && (
          <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 w-64 max-h-80 overflow-hidden">
          {/* Search Bar */}
          <div className="p-3 border-b border-gray-100">
            <input
              type="text"
              placeholder="Search languages..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full p-2 border border-gray-200 rounded text-sm focus:border-blue-500 focus:outline-none"
              autoFocus
            />
          </div>
          
          {/* Language List */}
          <div className="max-h-60 overflow-y-auto">
            {filteredLanguages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageSelect(lang.code)}
                className={`w-full flex items-center justify-between p-3 hover:bg-gray-50 text-left ${
                  selectedLanguage === lang.code ? 'bg-blue-50 text-blue-700' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-lg">{lang.flag}</span>
                  <div>
                    <div className="font-medium">{lang.nativeName}</div>
                    <div className="text-xs text-gray-500">{lang.name}</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-1">
                  {lang.voiceSupported && (
                    <span 
                      className="text-green-600 text-sm cursor-help" 
                      title="This language is supported by voice narration"
                    >
                      🔊
                    </span>
                  )}
                  {selectedLanguage === lang.code && (
                    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
            
            {filteredLanguages.length === 0 && (
              <div className="p-3 text-center text-gray-500 text-sm">
                No languages found matching "{searchTerm}"
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const ConversationViewer = ({ conversations, selectedLanguage, onLanguageChange, audioNarrativeEnabled = true }) => {
  const [isNarrationEnabled, setIsNarrationEnabled] = useState(audioNarrativeEnabled);
  const [isNarrating, setIsNarrating] = useState(false);
  const [currentRoundIndex, setCurrentRoundIndex] = useState(-1);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(-1);
  const [audioCache, setAudioCache] = useState(new Map());

  // Update narration state when prop changes
  useEffect(() => {
    setIsNarrationEnabled(audioNarrativeEnabled);
  }, [audioNarrativeEnabled]);

  const playAudioFromBase64 = (audioBase64) => {
    return new Promise((resolve) => {
      const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
      audio.onended = resolve;
      audio.onerror = resolve;
      audio.play().catch(() => resolve()); // Resolve even on error
    });
  };

  const getOrCreateAudio = async (text, agentName) => {
    const cacheKey = `${agentName}:${text}`;
    
    if (audioCache.has(cacheKey)) {
      return audioCache.get(cacheKey);
    }
    
    try {
      const response = await axios.post(`${API}/tts/synthesize`, {
        text: text,
        agent_name: agentName,
        language: selectedLanguage
      });
      
      if (response.data.audio_data) {
        const audioData = response.data.audio_data;
        setAudioCache(prev => new Map(prev.set(cacheKey, audioData)));
        return audioData;
      } else if (response.data.fallback || !response.data.voice_supported) {
        // Fallback to browser TTS for unsupported languages
        return null;
      }
    } catch (error) {
      console.error('TTS API error:', error);
      return null;
    }
  };

  const speakMessage = async (message, agentName) => {
    if (!isNarrationEnabled) return;

    try {
      const audioData = await getOrCreateAudio(message, agentName);
      
      if (audioData) {
        // Use Google Cloud TTS
        await playAudioFromBase64(audioData);
      } else {
        // Fallback to browser TTS
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(message);
          utterance.rate = 0.9;
          utterance.pitch = 1.0;
          speechSynthesis.speak(utterance);
          
          await new Promise(resolve => {
            utterance.onend = resolve;
            utterance.onerror = resolve;
          });
        }
      }
    } catch (error) {
      console.error('Speech synthesis error:', error);
    }
  };

  const narrateAllConversations = async () => {
    if (!isNarrationEnabled || isNarrating || conversations.length === 0) return;
    
    setIsNarrating(true);
    speechSynthesis.cancel(); // Stop any browser TTS
    
    // Play through all conversation rounds
    for (let roundIndex = 0; roundIndex < conversations.length; roundIndex++) {
      const round = conversations[roundIndex];
      setCurrentRoundIndex(roundIndex);
      
      // Announce the round
      if ('speechSynthesis' in window) {
        const roundAnnouncement = new SpeechSynthesisUtterance(`Round ${round.round_number}, ${round.time_period}`);
        roundAnnouncement.rate = 1.1;
        roundAnnouncement.volume = 0.7;
        speechSynthesis.speak(roundAnnouncement);
        
        await new Promise(resolve => {
          roundAnnouncement.onend = resolve;
          roundAnnouncement.onerror = resolve;
        });
      }
      
      // Brief pause after round announcement
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Play all messages in this round
      for (let messageIndex = 0; messageIndex < round.messages.length; messageIndex++) {
        // Check if user stopped narration
        if (!isNarrating) {
          setCurrentRoundIndex(-1);
          setCurrentMessageIndex(-1);
          return;
        }
        
        const message = round.messages[messageIndex];
        setCurrentMessageIndex(messageIndex);
        
        // Brief pause before each agent speaks
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Speak the message using Google Cloud TTS
        await speakMessage(message.message, message.agent_name);
        
        // Pause between messages
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      
      // Longer pause between rounds
      await new Promise(resolve => setTimeout(resolve, 1500));
    }
    
    setIsNarrating(false);
    setCurrentRoundIndex(-1);
    setCurrentMessageIndex(-1);
  };

  const narrateConversation = async (round, roundIndex) => {
    if (!isNarrationEnabled || isNarrating) return;
    
    setIsNarrating(true);
    setCurrentRoundIndex(roundIndex);
    speechSynthesis.cancel(); // Stop any browser TTS
    
    for (let i = 0; i < round.messages.length; i++) {
      // Check if user stopped narration
      if (!isNarrating) {
        setCurrentRoundIndex(-1);
        setCurrentMessageIndex(-1);
        return;
      }
      
      const message = round.messages[i];
      setCurrentMessageIndex(i);
      
      // Brief pause before each agent speaks
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Speak the message using Google Cloud TTS
      await speakMessage(message.message, message.agent_name);
      
      // Pause between messages
      await new Promise(resolve => setTimeout(resolve, 800));
    }
    
    setIsNarrating(false);
    setCurrentRoundIndex(-1);
    setCurrentMessageIndex(-1);
  };

  const stopNarration = () => {
    speechSynthesis.cancel();
    setIsNarrating(false);
    setCurrentRoundIndex(-1);
    setCurrentMessageIndex(-1);
    // Stop any playing audio
    document.querySelectorAll('audio').forEach(audio => {
      audio.pause();
      audio.currentTime = 0;
    });
  };

  if (!conversations.length) {
    return (
      <div className="conversation-viewer bg-gray-50 rounded-lg p-4">
        <p className="text-gray-500 text-center">No conversations yet. Start the simulation!</p>
      </div>
    );
  }

  return (
    <div className="conversation-viewer bg-white rounded-lg shadow-md p-4 max-h-96 overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold">Agent Conversations</h3>
        
        {/* Voice Narration and Language Controls */}
        <div className="flex items-center space-x-2">
          <CompactLanguageSelector 
            selectedLanguage={selectedLanguage}
            onLanguageChange={onLanguageChange}
          />
          
          <button
            onClick={() => setIsNarrationEnabled(!isNarrationEnabled)}
            className={`flex items-center space-x-1 px-3 py-1 rounded text-xs ${
              isNarrationEnabled 
                ? 'bg-green-100 text-green-700 border border-green-300' 
                : 'bg-gray-100 text-gray-600 border border-gray-300'
            }`}
          >
            <span>🔊</span>
            <span>{isNarrationEnabled ? 'Voice ON' : 'Voice OFF'}</span>
          </button>
          
          {isNarrationEnabled && (
            <>
              <button
                onClick={narrateAllConversations}
                disabled={isNarrating}
                className={`px-3 py-1 rounded text-xs ${
                  isNarrating 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-purple-100 text-purple-700 hover:bg-purple-200 border border-purple-300'
                }`}
              >
                {isNarrating ? '🎵 Playing All...' : '🎵 Play All'}
              </button>
              
              {isNarrating && (
                <button
                  onClick={stopNarration}
                  className="bg-red-100 text-red-700 px-3 py-1 rounded text-xs border border-red-300 hover:bg-red-200"
                >
                  ⏹️ Stop
                </button>
              )}
            </>
          )}
        </div>
      </div>
      
      {conversations.map((round, roundIndex) => (
        <div 
          key={round.id} 
          className={`conversation-round mb-4 p-3 rounded ${
            currentRoundIndex === roundIndex ? 'bg-yellow-100 border border-yellow-400' : 'bg-gray-50'
          }`}
        >
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-semibold text-sm text-gray-700">
              Round {round.round_number} - {round.time_period}
              {currentRoundIndex === roundIndex && isNarrating && (
                <span className="ml-2 text-yellow-600 text-xs">🎵 Now Playing</span>
              )}
            </h4>
            
            {isNarrationEnabled && (
              <button
                onClick={() => narrateConversation(round, roundIndex)}
                disabled={isNarrating}
                className={`px-2 py-1 rounded text-xs ${
                  isNarrating 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200 border border-blue-300'
                }`}
              >
                {currentRoundIndex === roundIndex && isNarrating ? '🎤 Playing...' : '🎤 Play Round'}
              </button>
            )}
          </div>
          
          <div className="messages">
            {round.messages.map((message, messageIndex) => (
              <div 
                key={message.id} 
                className={`message mb-2 p-2 rounded ${
                  isNarrating && currentRoundIndex === roundIndex && currentMessageIndex === messageIndex 
                    ? 'bg-yellow-100 border-l-4 border-yellow-400' 
                    : ''
                }`}
              >
                <div className="flex items-start">
                  <div className="flex items-center mr-2">
                    <span className={`font-medium ${
                      round.time_period.includes('Observer Input') ? 'text-purple-600' : 'text-blue-600'
                    }`}>
                      {message.agent_name}:
                    </span>
                    {isNarrationEnabled && (
                      <button
                        onClick={() => speakMessage(message.message, message.agent_name)}
                        className="ml-2 text-gray-400 hover:text-blue-600 text-xs"
                        title="Play this message"
                      >
                        🔊
                      </button>
                    )}
                  </div>
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



const PreConversationConfigModal = ({ isOpen, onClose, onStartWithConfig }) => {
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [audioNarrative, setAudioNarrative] = useState(true);
  const [saving, setSaving] = useState(false);

  const languages = [
    { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸', voiceSupported: true },
    { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸', voiceSupported: true },
    { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷', voiceSupported: true },
    { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪', voiceSupported: true },
    { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹', voiceSupported: true },
    { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹', voiceSupported: true },
    { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺', voiceSupported: true },
    { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵', voiceSupported: true },
    { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷', voiceSupported: true },
    { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳', voiceSupported: true },
    { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी', flag: '🇮🇳', voiceSupported: true },
    { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', voiceSupported: true },
    { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', flag: '🇳🇱', voiceSupported: false },
    { code: 'sv', name: 'Swedish', nativeName: 'Svenska', flag: '🇸🇪', voiceSupported: false },
    { code: 'no', name: 'Norwegian', nativeName: 'Norsk', flag: '🇳🇴', voiceSupported: false }
  ];

  const selectedLang = languages.find(l => l.code === selectedLanguage) || languages[0];

  const handleStartSimulation = async () => {
    setSaving(true);
    try {
      await onStartWithConfig({
        language: selectedLanguage,
        audioNarrative: audioNarrative
      });
      onClose();
    } catch (error) {
      console.error('Error starting simulation with config:', error);
    }
    setSaving(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-xl font-bold mb-6 text-center">
          🚀 Simulation Setup
        </h3>
        
        <div className="space-y-6">
          {/* Language Selection */}
          <div>
            <label className="block text-sm font-medium mb-3">
              🌍 Choose Language / Elegir Idioma
            </label>
            <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-2">
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setSelectedLanguage(lang.code)}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                    selectedLanguage === lang.code 
                      ? 'bg-blue-50 border-blue-300 text-blue-700' 
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{lang.flag}</span>
                    <div className="text-left">
                      <div className="font-medium">{lang.nativeName}</div>
                      <div className="text-xs text-gray-500">{lang.name}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {lang.voiceSupported && (
                      <span 
                        className="text-green-600 text-sm" 
                        title="Voice narration supported"
                      >
                        🔊
                      </span>
                    )}
                    {selectedLanguage === lang.code && (
                      <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Audio Narrative Toggle */}
          <div>
            <label className="block text-sm font-medium mb-3">
              🎵 Audio Settings
            </label>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium">Voice Narration</div>
                  <div className="text-sm text-gray-600">
                    Enable AI voice narration for conversations
                    {!selectedLang.voiceSupported && (
                      <div className="text-xs text-orange-600 mt-1">
                        ⚠️ Voice not supported for {selectedLang.name} (will use browser TTS)
                      </div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setAudioNarrative(!audioNarrative)}
                  className={`ml-4 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    audioNarrative ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      audioNarrative ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Cost Information */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-sm text-blue-800">
              <strong>💰 Estimated Monthly Cost (8 agents):</strong>
              <div className="mt-1 text-xs">
                • Text only: $0.10/month
                • With voice: {audioNarrative ? '$3.34/month' : '$0.10/month'}
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            onClick={handleStartSimulation}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            disabled={saving}
          >
            {saving ? 'Starting...' : 'Start Simulation'}
          </button>
        </div>
      </div>
    </div>
  );
};

const AgentProfilesManager = ({ agents = [], onDeleteAll, onCreateAgent }) => {
  const handleDeleteAll = () => {
    if (agents.length === 0) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete ALL ${agents.length} agents?\n\nThis action cannot be undone and will remove all agents from conversations.`
    );
    
    if (confirmed) {
      onDeleteAll();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-800">
          👤 Agent Profiles
        </h2>
        <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2 py-1 rounded-full">
          {agents.length}/8
        </span>
      </div>
      
      {/* Quick Actions */}
      <div className="flex space-x-2 mb-4">
        <button
          onClick={() => onCreateAgent()}
          className="flex-1 bg-emerald-600 text-white px-3 py-2 rounded text-sm hover:bg-emerald-700 transition-colors"
        >
          ➕ Add Agent
        </button>
        {agents.length > 0 && (
          <button
            onClick={handleDeleteAll}
            className="bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600 transition-colors"
            title="Delete All Agents"
          >
            🗑️ Clear All
          </button>
        )}
      </div>
      
      {agents.length > 0 && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center">
            <span className="text-yellow-600 text-sm">💡</span>
            <p className="text-xs text-yellow-700 ml-2">
              Click the <strong>🗑️ button</strong> on any agent card to delete individual agents
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

const AvatarCreator = ({ onCreateAgent, archetypes }) => {
  const { user, token, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    archetype: 'scientist',
    goal: '',
    expertise: '',
    background: '',
    avatar_prompt: ''
  });
  const [loading, setLoading] = useState(false);
  const [generatingAvatar, setGeneratingAvatar] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const [saveToLibrary, setSaveToLibrary] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.goal.trim()) return;
    
    setLoading(true);
    try {
      // Pass the preview URL along with form data
      const agentData = {
        ...formData,
        avatar_url: previewUrl // Use the preview image as the final avatar
      };
      
      // Create agent in simulation
      await onCreateAgent(agentData);
      
      // Save to library if user is authenticated and wants to save
      if (isAuthenticated && saveToLibrary) {
        try {
          await axios.post(`${API}/saved-agents`, agentData, {
            headers: { Authorization: `Bearer ${token}` }
          });
          alert(`✅ Agent "${agentData.name}" created and saved to your library!`);
        } catch (error) {
          console.error('Error saving to library:', error);
          alert(`Agent created successfully, but couldn't save to library.`);
        }
      }
      
      // Reset form
      setFormData({
        name: '',
        archetype: 'scientist',
        goal: '',
        expertise: '',
        background: '',
        avatar_prompt: ''
      });
      setPreviewUrl('');
      setSaveToLibrary(false);
      setIsOpen(false);
    } catch (error) {
      console.error('Error creating agent:', error);
    }
    setLoading(false);
  };

  const handlePreviewAvatar = async () => {
    if (!formData.avatar_prompt.trim()) return;
    
    setGeneratingAvatar(true);
    try {
      const response = await axios.post(`${API}/avatars/generate`, {
        prompt: formData.avatar_prompt
      });
      
      if (response.data.success) {
        setPreviewUrl(response.data.image_url);
      } else {
        alert('Failed to generate avatar: ' + response.data.error);
      }
    } catch (error) {
      console.error('Error generating avatar preview:', error);
      alert('Error generating avatar preview');
    }
    setGeneratingAvatar(false);
  };

  return (
    <div className="avatar-creator">
      <button
        onClick={() => setIsOpen(true)}
        className="w-full bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700 text-sm mb-2"
      >
        👤 Create Custom Agent
      </button>
      
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold mb-4">👤 Create Custom Agent with Avatar</h3>
            
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({...prev, name: e.target.value}))}
                    className="w-full p-2 border rounded"
                    placeholder="e.g., Nikola Tesla"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Archetype</label>
                  <select
                    value={formData.archetype}
                    onChange={(e) => setFormData(prev => ({...prev, archetype: e.target.value}))}
                    className="w-full p-2 border rounded"
                  >
                    {archetypes && Object.entries(archetypes).map(([key, value]) => (
                      <option key={key} value={key}>{value?.name || key}</option>
                    ))}
                  </select>
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-1">Goal *</label>
                  <textarea
                    value={formData.goal}
                    onChange={(e) => setFormData(prev => ({...prev, goal: e.target.value}))}
                    className="w-full p-2 border rounded"
                    rows="2"
                    placeholder="What does this agent want to achieve?"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Expertise</label>
                  <input
                    type="text"
                    value={formData.expertise}
                    onChange={(e) => setFormData(prev => ({...prev, expertise: e.target.value}))}
                    className="w-full p-2 border rounded"
                    placeholder="e.g., Physics, Electrical Engineering"
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
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-1">
                    🎨 Avatar Description
                    <span className="text-xs text-gray-500 ml-2">(Describe how the agent should look)</span>
                  </label>
                  <div className="flex space-x-2">
                    <textarea
                      value={formData.avatar_prompt}
                      onChange={(e) => setFormData(prev => ({...prev, avatar_prompt: e.target.value}))}
                      className="flex-1 p-2 border rounded"
                      rows="2"
                      placeholder="Examples:
• Nikola Tesla
• an old grandma with white hair and blue eyes
• a young scientist with glasses and a lab coat
• a confident business leader in a suit"
                    />
                    <button
                      type="button"
                      onClick={handlePreviewAvatar}
                      disabled={!formData.avatar_prompt.trim() || generatingAvatar}
                      className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 self-start"
                    >
                      {generatingAvatar ? '⏳' : '👁️'} Preview
                    </button>
                  </div>
                  
                  {previewUrl && (
                    <div className="mt-3 text-center">
                      <p className="text-sm text-green-600 mb-2">✅ Avatar Preview:</p>
                      <img 
                        src={previewUrl} 
                        alt="Avatar preview" 
                        className="w-24 h-24 rounded-full object-cover mx-auto border-2 border-green-300"
                      />
                      <p className="text-xs text-green-700 mt-2 font-medium">
                        🎯 This exact image will be used for your agent!
                      </p>
                    </div>
                  )}
                  
                  <p className="text-xs text-gray-500 mt-1">
                    💡 <strong>Cost:</strong> ~$0.0008 per avatar generation (very affordable!)
                  </p>
                </div>
              </div>

              {/* Save to Library Option */}
              {isAuthenticated && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={saveToLibrary}
                      onChange={(e) => setSaveToLibrary(e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm font-medium text-blue-800">
                      💾 Save to my agent library for reuse
                    </span>
                  </label>
                  <p className="text-xs text-blue-600 mt-1">
                    Saved agents can be reused in future simulations
                  </p>
                </div>
              )}

              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setIsOpen(false);
                    setPreviewUrl('');
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700"
                  disabled={loading || !formData.name.trim() || !formData.goal.trim()}
                >
                  {loading ? 'Creating...' : 'Create Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const ControlPanel = ({ 
  simulationState, 
  apiUsage,
  onInitResearchStation,
  onTestBackgrounds,
  onCreateAgent,
  setShowFastForward
}) => {
  const isActive = simulationState?.auto_conversations || simulationState?.auto_time;
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
        <h4 className="font-semibold text-sm mb-2">📊 Daily Usage & Cost</h4>
        
        {/* Request Usage Bar */}
        <div className="mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-600">API Requests</span>
            <span className="text-xs text-gray-600">Paid Tier</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-blue-500 h-3 rounded-full"
              style={{width: `${Math.min((apiUsage?.requests_used || 0) / 50000 * 100, 100)}%`}}
            ></div>
          </div>
          <p className="text-xs mt-1">
            {apiUsage?.requests_used || 0} / 50,000 requests
            ({Math.max(50000 - (apiUsage?.requests_used || 0), 0).toLocaleString()} remaining)
          </p>
        </div>

        {/* Cost Tracking */}
        <div className="cost-tracking">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-600">Estimated Daily Cost</span>
            <span className="text-xs text-green-600">Budget: $10.00</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-green-500 h-2 rounded-full"
              style={{width: `${Math.min(((apiUsage?.requests_used || 0) * 0.0002) / 10 * 100, 100)}%`}}
            ></div>
          </div>
          <p className="text-xs mt-1 text-gray-600">
            ${((apiUsage?.requests_used || 0) * 0.0002).toFixed(4)} / $10.00
            <span className="ml-2 text-green-600">
              (~${(((apiUsage?.requests_used || 0) * 0.0002) * 30).toFixed(2)}/month)
            </span>
          </p>
        </div>
      </div>

      <div className="controls space-y-3">
        {/* Setup Controls */}
        <div className="setup-section">
          <h4 className="text-sm font-semibold mb-2 text-gray-700">Setup</h4>
          
          <AvatarCreator 
            onCreateAgent={onCreateAgent}
            archetypes={AGENT_ARCHETYPES}
          />
          
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
      </div>
    </div>
  );
};

const SavedAgentsLibrary = () => {
  const { user, token } = useAuth();
  const [savedAgents, setSavedAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);

  const fetchSavedAgents = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/saved-agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSavedAgents(response.data);
    } catch (error) {
      console.error('Error fetching saved agents:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (showLibrary && token) {
      fetchSavedAgents();
    }
  }, [showLibrary, token]);

  const handleDeleteAgent = async (agentId) => {
    if (!window.confirm('Are you sure you want to delete this saved agent?')) return;
    
    try {
      await axios.delete(`${API}/saved-agents/${agentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSavedAgents(savedAgents.filter(agent => agent.id !== agentId));
      alert('Saved agent deleted successfully!');
    } catch (error) {
      console.error('Error deleting saved agent:', error);
      alert('Failed to delete saved agent.');
    }
  };

  const handleUseAgent = (agent) => {
    // Trigger agent creation with saved agent data
    const agentData = {
      name: `${agent.name} (Copy)`,
      archetype: agent.archetype,
      personality: agent.personality,
      goal: agent.goal,
      expertise: agent.expertise,
      background: agent.background,
      avatar_url: agent.avatar_url,
      avatar_prompt: agent.avatar_prompt
    };
    
    // Here you'd call the agent creation function
    alert(`Using saved agent: ${agent.name}`);
    setShowLibrary(false);
  };

  if (!user) return null;

  return (
    <>
      <button
        onClick={() => setShowLibrary(true)}
        className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 text-sm"
      >
        📚 My Agent Library ({savedAgents.length})
      </button>

      {showLibrary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">📚 My Saved Agents</h2>
              <button
                onClick={() => setShowLibrary(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            {loading ? (
              <div className="text-center py-8">Loading saved agents...</div>
            ) : savedAgents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-4">📋</div>
                <p>No saved agents yet.</p>
                <p className="text-sm mt-2">Create agents and save them to your library for reuse!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedAgents.map(agent => (
                  <div key={agent.id} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                    <div className="flex items-start space-x-3 mb-3">
                      {agent.avatar_url ? (
                        <img 
                          src={agent.avatar_url} 
                          alt={agent.name}
                          className="w-12 h-12 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-600">
                          {agent.name.charAt(0)}
                        </div>
                      )}
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-800">{agent.name}</h3>
                        <p className="text-sm text-gray-600">{agent.archetype}</p>
                      </div>
                    </div>
                    
                    <p className="text-xs text-gray-600 mb-3 line-clamp-2">"{agent.goal}"</p>
                    
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleUseAgent(agent)}
                        className="flex-1 bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700"
                      >
                        🔄 Use Agent
                      </button>
                      <button
                        onClick={() => handleDeleteAgent(agent.id)}
                        className="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600"
                      >
                        🗑️
                      </button>
                    </div>
                    
                    <div className="text-xs text-gray-400 mt-2">
                      Created: {new Date(agent.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

const ConversationHistoryViewer = () => {
  const { user, token } = useAuth();
  const [conversationHistory, setConversationHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const fetchConversationHistory = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/conversation-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConversationHistory(response.data);
    } catch (error) {
      console.error('Error fetching conversation history:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (showHistory && token) {
      fetchConversationHistory();
    }
  }, [showHistory, token]);

  if (!user) return null;

  return (
    <>
      <button
        onClick={() => setShowHistory(true)}
        className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm"
      >
        💬 My Conversations ({conversationHistory.length})
      </button>

      {showHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-5xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">💬 My Conversation History</h2>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            {loading ? (
              <div className="text-center py-8">Loading conversation history...</div>
            ) : conversationHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-4">💭</div>
                <p>No conversation history yet.</p>
                <p className="text-sm mt-2">Your conversations will be automatically saved here!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {conversationHistory.map(conversation => (
                  <div key={conversation.id} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-gray-800">
                          {conversation.title || `Conversation from ${new Date(conversation.created_at).toLocaleDateString()}`}
                        </h3>
                        <p className="text-sm text-gray-600">
                          Participants: {conversation.participants.join(', ')}
                        </p>
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(conversation.created_at).toLocaleString()}
                      </div>
                    </div>
                    
                    <div className="bg-gray-50 rounded p-3 max-h-40 overflow-y-auto">
                      {conversation.messages.slice(0, 3).map((message, index) => (
                        <div key={index} className="text-sm mb-2">
                          <strong>{message.agent_name}:</strong> {message.message}
                        </div>
                      ))}
                      {conversation.messages.length > 3 && (
                        <div className="text-xs text-gray-500">
                          ... and {conversation.messages.length - 3} more messages
                        </div>
                      )}
                    </div>
                    
                    {conversation.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {conversation.tags.map(tag => (
                          <span key={tag} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

function App() {
  const { user, logout, isAuthenticated } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
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
  const [selectedLanguage, setSelectedLanguage] = useState(() => {
    // Load saved language from localStorage or default to 'en'
    return localStorage.getItem('selectedLanguage') || 'en';
  });
  const [showPreConfigModal, setShowPreConfigModal] = useState(false);
  const [audioNarrativeEnabled, setAudioNarrativeEnabled] = useState(() => {
    // Load saved audio preference from localStorage or default to true
    return localStorage.getItem('audioNarrativeEnabled') !== 'false';
  });

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

  const handleCreateAgent = async (agentData) => {
    try {
      const response = await axios.post(`${API}/agents`, agentData);
      await refreshAllData();
      
      // Create a more informative success message
      let avatarMessage = '';
      if (agentData.avatar_url) {
        avatarMessage = ' Preview image used as avatar.';
      } else if (agentData.avatar_prompt) {
        avatarMessage = ' Avatar generated from prompt.';
      }
      
      alert(`✅ Agent "${agentData.name}" created successfully!${avatarMessage}`);
    } catch (error) {
      console.error('Error creating agent:', error);
      alert('Failed to create agent. Please try again.');
      throw error;
    }
  };

  const handleDeleteAgent = async (agentId, agentName) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      `Are you sure you want to delete "${agentName}"?\n\nThis action cannot be undone and will remove the agent from all conversations.`
    );
    
    if (!confirmed) return;
    
    try {
      await axios.delete(`${API}/agents/${agentId}`);
      await refreshAllData();
      alert(`✅ Agent "${agentName}" has been deleted successfully.`);
    } catch (error) {
      console.error('Error deleting agent:', error);
      alert('Failed to delete agent. Please try again.');
    }
  };

  const handleDeleteAllAgents = async () => {
    if (agents.length === 0) return;
    
    try {
      // Delete all agents one by one
      for (const agent of agents) {
        await axios.delete(`${API}/agents/${agent.id}`);
      }
      await refreshAllData();
      alert(`✅ All ${agents.length} agents have been deleted successfully.`);
    } catch (error) {
      console.error('Error deleting all agents:', error);
      alert('Failed to delete all agents. Please try again.');
    }
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
      const response = await axios.get(`${API}/usage`);
      setApiUsage(response.data);
    } catch (error) {
      console.error('Error fetching API usage:', error);
      // Set default values if endpoint fails
      setApiUsage({ requests: 0, remaining: 1000 });
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
      setArchetypes(response.data || {});
    } catch (error) {
      console.error('Error fetching archetypes:', error);
      setArchetypes({}); // Set empty object on error
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
    
    // Check for auto-report generation
    await checkAutoReportGeneration();
    
    setLoading(false);
  };

  const checkAutoReportGeneration = async () => {
    try {
      const response = await axios.get(`${API}/reports/check-auto-generation`);
      const data = response.data;
      
      if (data.should_generate) {
        console.log('Auto-generating weekly report:', data.reason);
        // Auto-generate the report
        await handleGenerateSummary();
      }
    } catch (error) {
      console.error('Error checking auto-report generation:', error);
      // Don't throw error - this is just a background check
    }
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
      await fetchSimulationState(); // This will trigger the useEffect to restart timers
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
    // Show pre-conversation configuration modal
    setShowPreConfigModal(true);
  };

  const handleStartWithConfig = async (config) => {
    setLoading(true);
    try {
      // Save user preferences
      localStorage.setItem('selectedLanguage', config.language);
      localStorage.setItem('audioNarrativeEnabled', config.audioNarrative.toString());
      
      // Update state
      setSelectedLanguage(config.language);
      setAudioNarrativeEnabled(config.audioNarrative);
      
      // Clear summaries immediately in frontend before API call
      setSummaries([]);
      
      // Start new simulation (this clears everything)
      await axios.post(`${API}/simulation/start`);
      
      // Set the language for the simulation
      await axios.post(`${API}/simulation/set-language`, { 
        language: config.language 
      });
      
      // Automatically create the crypto team so users can start conversations immediately
      await axios.post(`${API}/simulation/init-research-station`);
      
      await refreshAllData();
      
      // Show success message with configuration details
      const langName = config.language === 'en' ? 'English' : config.language;
      const audioStatus = config.audioNarrative ? 'enabled' : 'disabled';
      alert(`✅ Simulation started!\nLanguage: ${langName}\nAudio Narration: ${audioStatus}`);
      
    } catch (error) {
      console.error('Error starting simulation:', error);
      alert('Failed to start simulation. Please try again.');
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

  const handleLanguageChange = async (languageCode) => {
    // Update frontend state immediately and persist to localStorage
    setSelectedLanguage(languageCode);
    localStorage.setItem('selectedLanguage', languageCode);
    
    // Update language setting in the backend
    try {
      await axios.post(`${API}/simulation/set-language`, { language: languageCode });
    } catch (error) {
      console.error('Error setting language:', error);
    }
  };

  const handleGenerateConversation = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/conversation/generate`);
      await refreshAllData();
      
      // Auto-save conversation to history if user is authenticated
      if (isAuthenticated && token) {
        try {
          const currentConversations = await axios.get(`${API}/conversations`);
          if (currentConversations.data.length > 0) {
            const latestConversation = currentConversations.data[currentConversations.data.length - 1];
            
            const conversationData = {
              simulation_id: simulationState?.id || '',
              participants: latestConversation.messages.map(m => m.agent_name),
              messages: latestConversation.messages,
              language: selectedLanguage,
              title: `Conversation - Day ${simulationState?.current_day || 1}`,
              tags: ['auto-saved', `day-${simulationState?.current_day || 1}`]
            };
            
            await axios.post(`${API}/conversation-history`, conversationData, {
              headers: { Authorization: `Bearer ${token}` }
            });
          }
        } catch (error) {
          console.error('Error auto-saving conversation:', error);
          // Don't show error to user for auto-save failures
        }
      }
    } catch (error) {
      console.error('Error generating conversation:', error);
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

  // Auto-start timers when simulation state loads with auto-mode enabled
  useEffect(() => {
    if (simulationState) {
      // Clear existing timers first
      if (autoTimers.conversation) {
        clearInterval(autoTimers.conversation);
      }
      if (autoTimers.time) {
        clearInterval(autoTimers.time);
      }
      
      // Set up new timers if enabled in simulation state
      const newTimers = { conversation: null, time: null };
      
      if (simulationState.auto_conversations) {
        console.log('Auto-starting conversations from simulation state with interval:', simulationState.conversation_interval);
        newTimers.conversation = setInterval(async () => {
          try {
            console.log('Auto generating conversation...');
            const response = await axios.post(`${API}/conversation/generate`);
            console.log('Conversation generated successfully:', response.data?.round_number);
            await refreshAllData();
          } catch (error) {
            console.error('Auto conversation error:', error);
            
            // Check if it's an API quota issue
            if (error.response?.status === 400 && error.response?.data?.detail?.includes('API requests')) {
              console.warn('API quota exceeded - auto conversations will continue trying');
            } else if (error.response?.status === 500) {
              console.warn('Server error during conversation generation - will retry');
            } else {
              console.error('Unexpected error during auto conversation:', error.response?.data || error.message);
            }
            // Don't clear interval on error, just log it
          }
        }, (simulationState.conversation_interval || 10) * 1000);
      }
      
      if (simulationState.auto_time) {
        console.log('Auto-starting time advancement from simulation state with interval:', simulationState.time_interval);
        newTimers.time = setInterval(async () => {
          try {
            console.log('Auto advancing time...');
            await axios.post(`${API}/simulation/next-period`);
            await fetchSimulationState();
          } catch (error) {
            console.error('Auto time error:', error);
            // Don't clear interval on error, just log it
          }
        }, (simulationState.time_interval || 60) * 1000);
      }
      
      setAutoTimers(newTimers);
    }
  }, [simulationState?.auto_conversations, simulationState?.auto_time, simulationState?.conversation_interval, simulationState?.time_interval]);

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
            
            <div className="flex items-center space-x-4">
              {/* User Library & History (only show when authenticated) */}
              {isAuthenticated && (
                <>
                  <SavedAgentsLibrary />
                  <ConversationHistoryViewer />
                </>
              )}
              
              {/* Refresh Button */}
              <button
                onClick={refreshAllData}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Refresh'}
              </button>
              
              {/* Authentication Section */}
              {isAuthenticated ? (
                <UserProfile user={user} onLogout={logout} />
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 font-medium"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Agent Profiles */}
          <div className="lg:col-span-1">
            <AgentProfilesManager 
              agents={agents}
              onDeleteAll={handleDeleteAllAgents}
              onCreateAgent={() => {
                // Find and trigger the Create Custom Agent button
                // This will be handled by scrolling to the control panel
                const controlPanel = document.querySelector('.control-panel');
                if (controlPanel) {
                  controlPanel.scrollIntoView({ behavior: 'smooth' });
                }
                // Flash the create button
                setTimeout(() => {
                  const createButton = document.querySelector('.control-panel button');
                  if (createButton) {
                    createButton.style.animation = 'pulse 1s ease-in-out 3 alternate';
                  }
                }, 500);
              }}
            />
            
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
                    onDelete={handleDeleteAgent}
                  />
                ))
              ) : (
                <div className="bg-white rounded-lg shadow-md p-6 text-center">
                  <div className="text-4xl mb-3">🤖</div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">No Agents Yet</h3>
                  <p className="text-gray-500 mb-4">
                    Create your first AI agent to start the simulation
                  </p>
                  <div className="space-y-2 text-sm text-gray-400">
                    <p>• Click "👤 Create Custom Agent" to design your own</p>
                    <p>• Or use "Create Crypto Team" for preset agents</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Middle Column - Conversations & Reports */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-bold mb-4">Conversations</h2>
            <ConversationViewer 
              conversations={conversations} 
              selectedLanguage={selectedLanguage}
              onLanguageChange={handleLanguageChange}
              audioNarrativeEnabled={audioNarrativeEnabled}
            />
            
            {/* Conversation Controls - Underneath conversations */}
            <ConversationControls 
              simulationState={simulationState}
              onPauseSimulation={handlePauseSimulation}
              onResumeSimulation={handleResumeSimulation}
              onGenerateConversation={handleGenerateConversation}
              onNextPeriod={handleNextPeriod}
              onToggleAuto={handleToggleAuto}
            />
            
            {/* Observer Input - Subtle placement below conversations */}
            <ObserverInput onSendMessage={handleSendObserverMessage} />
            
            {/* Start New Simulation Control - Underneath scenario creation */}
            <StartSimulationControl onStartSimulation={handleStartSimulation} />
            
            {/* Conversation and Time Status - Underneath Observer Input */}
            <ConversationTimeStatus simulationState={simulationState} />
            
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
            
            <SimulationStatusBar simulationState={simulationState} />
            
            <AutoControls 
              simulationState={simulationState}
              onToggleAuto={handleToggleAuto}
            />
            
            <ControlPanel
              simulationState={simulationState}
              apiUsage={apiUsage}
              onInitResearchStation={handleInitResearchStation}
              onTestBackgrounds={handleTestBackgrounds}
              onCreateAgent={handleCreateAgent}
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

      <PreConversationConfigModal
        isOpen={showPreConfigModal}
        onClose={() => setShowPreConfigModal(false)}
        onStartWithConfig={handleStartWithConfig}
      />

      <LoginModal 
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
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

// Wrap App with AuthProvider and Error Boundary
const AppWithAuth = () => {
  return (
    <div>
      <AuthProvider>
        <App />
      </AuthProvider>
    </div>
  );
};

export default AppWithAuth;