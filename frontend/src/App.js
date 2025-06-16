import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { motion, useAnimationControls } from 'framer-motion';
import AgentLibrary from './AgentLibrary';
import HomePage from './HomePage';
import AdminDashboard from './AdminDashboard';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "251454265437-5s1019au9fr6oh9rb47frkv8549vptk5.apps.googleusercontent.com";

// Debug logging
console.log('Environment variables loaded:', {
  BACKEND_URL,
  GOOGLE_CLIENT_ID: GOOGLE_CLIENT_ID ? 'Present' : 'Missing',
  NODE_ENV: process.env.NODE_ENV
});

// Enhanced VoiceInput Component for any text field
const VoiceInput = ({ 
  onTextUpdate, 
  fieldType = "general", 
  language = "hr", 
  disabled = false,
  className = "",
  size = "small" // "small", "medium", "large"
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [error, setError] = useState("");
  const { token } = useAuth();

  const sizeClasses = {
    small: "w-6 h-6",
    medium: "w-8 h-8", 
    large: "w-10 h-10"
  };

  // SVG Microphone Icon Component
  const MicrophoneIcon = ({ className = "" }) => (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
      <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
    </svg>
  );

  const startRecording = async () => {
    // Check authentication and provide helpful feedback
    if (!token || isDisabledDueToAuth) {
      alert('🎤 Voice input requires authentication.\n\nPlease use "Continue as Guest" button in the top navigation to enable voice input for testing.');
      return;
    }
    
    try {
      setError("");
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true 
      });
      
      const mediaRecorder = new MediaRecorder(stream);
      setMediaRecorder(mediaRecorder);
      
      const audioChunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        await processAudio(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      if (error.name === 'NotAllowedError') {
        setError("Microphone access denied. Please allow microphone access and try again.");
      } else if (error.name === 'NotFoundError') {
        setError("No microphone found");
      } else {
        setError("Recording failed");
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const processAudio = async (audioBlob) => {
    try {
      setIsProcessing(true);
      
      const formData = new FormData();
      formData.append('audio', audioBlob, `${fieldType}_audio.webm`);
      formData.append('field_type', fieldType);
      if (language) {
        formData.append('language', language);
      }

      const response = await axios.post(`${API}/speech/transcribe-and-summarize`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success && response.data.formatted_text) {
        onTextUpdate(response.data.formatted_text);
      } else {
        setError("No speech detected");
      }

    } catch (error) {
      console.error('Error processing audio:', error);
      if (error.response?.status === 401) {
        setError("Please sign in");
      } else {
        setError("Processing failed");
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // Show the microphone button always, but disable it if not authenticated
  const isDisabledDueToAuth = !token;

  return (
    <div className={`relative ${className}`}>
      {!isRecording && !isProcessing ? (
        <button
          type="button"
          onClick={startRecording}
          disabled={disabled || isDisabledDueToAuth}
          className={`${sizeClasses[size]} text-gray-600 hover:text-gray-800 disabled:opacity-50 transition-colors flex items-center justify-center`}
          title={isDisabledDueToAuth ? "Sign in to use voice input" : "Voice input"}
        >
          <MicrophoneIcon className="w-full h-full" />
        </button>
      ) : isRecording ? (
        <button
          type="button"
          onClick={stopRecording}
          className={`${sizeClasses[size]} text-red-600 hover:text-red-700 transition-colors animate-pulse flex items-center justify-center`}
          title="Stop recording"
        >
          <MicrophoneIcon className="w-full h-full" />
        </button>
      ) : (
        <button
          type="button"
          disabled={true}
          className={`${sizeClasses[size]} text-gray-400 flex items-center justify-center`}
          title="Processing..."
        >
          <MicrophoneIcon className="w-full h-full" />
        </button>
      )}
      
      {error && (
        <div className="absolute top-full left-0 mt-1 bg-red-100 text-red-700 text-xs px-2 py-1 rounded shadow-lg z-10 whitespace-nowrap">
          {error}
        </div>
      )}
    </div>
  );
};

// Animated Observer Logo Component
const ObserverLogo = () => {
  const pupilControls = useAnimationControls();

  useEffect(() => {
    // Animation sequences
    const animatePupil = async () => {
      while (true) {
        // Random chance for different movements
        const movementType = Math.random();
        
        if (movementType < 0.4) {
          // Scanning motion (40% chance) - reduced range to prevent touching outline
          await pupilControls.start({
            x: -4,
            y: Math.random() * 2 + 6, // 6-8px (reduced range)
            transition: {
              type: "spring",
              stiffness: 60,
              damping: 20
            }
          });
          
          await new Promise(resolve => setTimeout(resolve, 200));
          
          await pupilControls.start({
            x: 4,
            y: Math.random() * 2 + 6, // 6-8px (reduced range)
            transition: {
              type: "spring",
              stiffness: 60,
              damping: 20
            }
          });
          
          await new Promise(resolve => setTimeout(resolve, 200));
        } else {
          // Random movement (60% chance) - reduced range to prevent touching outline
          await pupilControls.start({
            x: (Math.random() * 8 - 4),
            y: (Math.random() * 4 + 5),
            transition: {
              type: "spring",
              stiffness: 60,
              damping: 20
            }
          });
          
          await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
        }
      }
    };
    
    // Start animation
    animatePupil();
    
    // Cleanup function
    return () => {
      pupilControls.stop();
    };
  }, [pupilControls]);

  // Blinking animation
  const [isBlinking, setIsBlinking] = useState(false);
  
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 200);
    }, Math.random() * 5000 + 5000); // Random interval between 5-10 seconds
    
    return () => clearInterval(blinkInterval);
  }, []);

  return (
    <div className="flex items-center">
      <div className="text-4xl font-bold tracking-tight relative">
        <div className="relative inline-block w-10 h-10 mr-1">
          {/* Eye */}
          <div className="absolute inset-0 bg-white rounded-full border-2 border-gray-800 overflow-hidden">
            {/* Pupil */}
            <motion.div 
              className="w-4 h-4 bg-black rounded-full absolute"
              style={{ top: '50%', left: '50%', marginLeft: -8, marginTop: -8 }}
              animate={pupilControls}
            />
            
            {/* Eyelid (only visible when blinking) */}
            <div 
              className={`absolute inset-0 bg-gray-400 border-b-2 border-gray-600 transition-transform duration-200 ${isBlinking ? 'translate-y-0' : 'translate-y-[-100%]'}`}
              style={{ borderRadius: '50% 50% 0 0' }}
            >
              {/* Eyelashes */}
              <div className="absolute bottom-0 left-1 w-1 h-1 bg-gray-600 rounded-full" />
              <div className="absolute bottom-0 left-3 w-1 h-1 bg-gray-600 rounded-full" />
              <div className="absolute bottom-0 left-5 w-1 h-1 bg-gray-600 rounded-full" />
              <div className="absolute bottom-0 left-7 w-1 h-1 bg-gray-600 rounded-full" />
            </div>
          </div>
        </div>
        bserver
      </div>
    </div>
  );
};

// Authentication Context

const CurrentScenarioCard = ({ currentScenario, autoExpand }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Auto-expand when autoExpand prop is true
  useEffect(() => {
    if (autoExpand) {
      setIsExpanded(true);
    }
  }, [autoExpand]);

  if (!currentScenario) {
    return null;
  }

  return (
    <div className="current-scenario-card bg-white rounded-lg shadow-md mb-4 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left hover:bg-gray-50 transition-colors border-none bg-white"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-blue-600">📋</span>
            <h3 className="text-md font-semibold text-gray-800">Current Scenario</h3>
          </div>
        </div>
      </button>
      
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
            <p className="text-sm text-gray-700 leading-relaxed">
              {currentScenario}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

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
    
    // Debug: Check if Client ID is loaded
    console.log('Google Client ID:', GOOGLE_CLIENT_ID);
    
    if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID.includes('undefined')) {
      alert('Google Client ID not configured properly. Please check environment variables.');
      setLoginLoading(false);
      return;
    }
    
    // Use the main domain as redirect URI (simpler for hosting platforms)
    const redirectUri = window.location.origin;
    const googleAuthUrl = new URL('https://accounts.google.com/oauth/authorize');
    
    googleAuthUrl.searchParams.set('client_id', GOOGLE_CLIENT_ID);
    googleAuthUrl.searchParams.set('redirect_uri', redirectUri);
    googleAuthUrl.searchParams.set('response_type', 'code');
    googleAuthUrl.searchParams.set('scope', 'openid profile email');
    googleAuthUrl.searchParams.set('access_type', 'offline');
    googleAuthUrl.searchParams.set('state', Math.random().toString(36).substring(2, 15));

    // Debug: Log the OAuth URL
    console.log('OAuth URL:', googleAuthUrl.toString());
    console.log('Redirect URI:', redirectUri);
    
    // Store the state for verification
    localStorage.setItem('oauth_state', googleAuthUrl.searchParams.get('state'));
    
    // Show confirmation dialog with debug info
    const confirm = window.confirm(
      `Debug Info:\n` +
      `Client ID: ${GOOGLE_CLIENT_ID}\n` +
      `Redirect URI: ${redirectUri}\n\n` +
      `Continue to Google login?`
    );
    
    if (!confirm) {
      setLoginLoading(false);
      return;
    }
    
    // Redirect to Google OAuth
    window.location.href = googleAuthUrl.toString();
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

const ScenarioInput = ({ onSetScenario, currentScenario, onScenarioCollapse }) => {
  const [scenario, setScenario] = useState("");
  const [scenarioName, setScenarioName] = useState("");
  const [loading, setLoading] = useState(false);
  const [randomLoading, setRandomLoading] = useState(false);
  const [justSubmitted, setJustSubmitted] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  // Enhanced voice recognition state for Whisper API
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState('hr'); // Default to Croatian
  const [supportedLanguages, setSupportedLanguages] = useState([]);
  const { token } = useAuth();

  // Upload functionality state
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [showUploadedFiles, setShowUploadedFiles] = useState(false);

  // Fetch supported languages and uploaded files on component mount
  useEffect(() => {
    const fetchSupportedLanguages = async () => {
      try {
        const response = await axios.get(`${API}/speech/languages`);
        setSupportedLanguages(response.data.languages);
      } catch (error) {
        console.error('Error fetching supported languages:', error);
        // Fallback to common languages
        setSupportedLanguages([
          { code: 'hr', name: 'Croatian' },
          { code: 'en', name: 'English' },
          { code: 'es', name: 'Spanish' },
          { code: 'fr', name: 'French' },
          { code: 'de', name: 'German' }
        ]);
      }
    };

    const fetchUploadedFiles = async () => {
      if (!token) return;
      try {
        const response = await axios.get(`${API}/scenario/uploads`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUploadedFiles(response.data);
      } catch (error) {
        console.error('Error fetching uploaded files:', error);
      }
    };

    fetchSupportedLanguages();
    fetchUploadedFiles();
  }, [token]);

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setUploading(true);
    setUploadError("");

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await axios.post(`${API}/scenario/upload-content`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        // Refresh uploaded files list
        const updatedResponse = await axios.get(`${API}/scenario/uploads`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUploadedFiles(updatedResponse.data);
        
        // Clear file input
        event.target.value = '';
        
        // Show success message
        alert(`Successfully uploaded ${response.data.files.length} file(s)`);
      }
    } catch (error) {
      console.error('Error uploading files:', error);
      setUploadError('Failed to upload files. Please try again.');
    }
    
    setUploading(false);
  };

  const startRecording = async () => {
    try {
      setVoiceError("");
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });

      // Create MediaRecorder
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      const chunks = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        
        // Stop all tracks to free up microphone
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setAudioChunks(chunks);
      setIsRecording(true);

    } catch (error) {
      console.error('Error starting recording:', error);
      if (error.name === 'NotAllowedError') {
        setVoiceError("Microphone access denied. Please allow microphone access in your browser settings.");
      } else if (error.name === 'NotFoundError') {
        setVoiceError("No microphone found. Please check your microphone connection.");
      } else {
        setVoiceError("Failed to start recording. Please try again.");
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setIsRecording(false);
      setIsTranscribing(true);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    try {
      setIsTranscribing(true);
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('audio', audioBlob, 'scenario_audio.webm');
      if (selectedLanguage) {
        formData.append('language', selectedLanguage);
      }

      // Send to Whisper API
      const response = await axios.post(`${API}/speech/transcribe-scenario`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success && response.data.text) {
        // Append transcribed text to existing scenario
        setScenario(prev => {
          const newText = prev ? prev + ' ' + response.data.text.trim() : response.data.text.trim();
          return newText;
        });
        
        console.log('Transcription successful:', {
          language: response.data.language_detected,
          duration: response.data.duration_seconds,
          wordCount: response.data.word_count
        });
      } else {
        setVoiceError("No speech detected. Please try speaking again.");
      }

    } catch (error) {
      console.error('Error transcribing audio:', error);
      if (error.response?.status === 401) {
        setVoiceError("Authentication failed. Please sign in again.");
      } else if (error.response?.status === 400) {
        setVoiceError("Invalid audio format. Please try again.");
      } else {
        setVoiceError("Transcription failed. Please check your internet connection and try again.");
      }
    } finally {
      setIsTranscribing(false);
    }
  };

  const clearScenario = () => {
    setScenario("");
    setVoiceError("");
  };

  // Collection of random scenarios
  const randomScenarios = [
    "A massive data breach has exposed sensitive information from a major tech company. The team must decide how to respond to the crisis and protect affected users.",
    "An alien signal has been detected from deep space. Scientists must determine if it's natural phenomenon or intelligent communication.",
    "A revolutionary AI breakthrough has been announced, but concerns about its implications are growing. The team debates the benefits and risks.",
    "A global pandemic has emerged, and the team must coordinate an international response while managing economic and social impacts.",
    "Climate change has reached a tipping point. Emergency measures are being discussed, but there's disagreement on the best approach.",
    "A major cryptocurrency exchange has collapsed, causing market panic. Financial experts debate regulatory responses and investor protection.",
    "A whistleblower has revealed unethical practices at a pharmaceutical company. The team must decide how to handle the revelations.",
    "Ancient artifacts with unknown properties have been discovered. Archaeologists and scientists debate their significance and study methods.",
    "A social media platform has been manipulating public opinion. Experts discuss the implications for democracy and free speech.",
    "A breakthrough in quantum computing threatens current encryption methods. Cybersecurity professionals debate immediate actions needed.",
    "A massive volcanic eruption is predicted to affect global climate. Scientists and policymakers debate evacuation and mitigation strategies.",
    "Gene editing technology has advanced rapidly, raising ethical questions about human enhancement. Bioethicists debate regulatory frameworks.",
    "A major oil spill threatens marine ecosystems. Environmental scientists and cleanup crews coordinate response efforts while activists demand action.",
    "Artificial general intelligence has been achieved in a lab. Researchers debate whether to announce the breakthrough or continue secret development.",
    "A mysterious disease is affecting bee populations worldwide. Agricultural experts and ecologists urgently seek solutions to prevent ecosystem collapse.",
    "Space debris is threatening critical satellites. Aerospace engineers and international agencies debate cleanup missions and future space traffic management.",
    "A deepfake video of a world leader has gone viral, causing international tensions. Digital forensics experts and diplomats work to address the crisis.",
    "Autonomous vehicles have malfunctioned in multiple cities simultaneously. Engineers and safety regulators investigate the cause and response protocols.",
    "A major social movement is gaining momentum globally. Political analysts and activists debate the movement's goals and potential outcomes.",
    "Advanced brain-computer interfaces have enabled direct neural communication. Neuroscientists and ethicists discuss the implications for human consciousness and privacy."
  ];

  const randomScenarioNames = [
    "Tech Data Breach Crisis",
    "Deep Space Signal Analysis",
    "AI Revolution Ethics Debate",
    "Global Pandemic Response",
    "Climate Emergency Summit",
    "Crypto Market Collapse",
    "Pharma Whistleblower Case",
    "Ancient Artifacts Discovery",
    "Social Media Manipulation",
    "Quantum Computing Security",
    "Volcanic Eruption Protocol",
    "Gene Editing Ethics",
    "Marine Ecosystem Crisis",
    "AGI Lab Breakthrough",
    "Global Bee Colony Crisis",
    "Space Debris Management",
    "Deepfake Diplomatic Crisis",
    "Autonomous Vehicle Failure",
    "Global Movement Analysis",
    "Neural Interface Ethics"
  ];

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    if (!scenario.trim() || !scenarioName.trim()) return;
    
    setLoading(true);
    setJustSubmitted(true);
    await onSetScenario(scenario, scenarioName);
    setLoading(false);
    
    // Keep the text visible for 3 seconds to show it was applied
    setTimeout(() => {
      setScenario("");
      setScenarioName("");
      setJustSubmitted(false);
      // Collapse the custom scenario section and expand current scenario
      setIsCollapsed(true);
      if (onScenarioCollapse) {
        onScenarioCollapse(true);
      }
    }, 3000);
  };

  const handleGenerateRandomScenario = async () => {
    setRandomLoading(true);
    
    // Select a random scenario
    const randomIndex = Math.floor(Math.random() * randomScenarios.length);
    const selectedScenario = randomScenarios[randomIndex];
    const selectedScenarioName = randomScenarioNames[randomIndex];
    
    // Set both scenario and name
    setScenario(selectedScenario);
    setScenarioName(selectedScenarioName);
    
    // Apply it automatically
    setJustSubmitted(true);
    await onSetScenario(selectedScenario, selectedScenarioName);
    setRandomLoading(false);
    
    // Keep the text visible for 3 seconds to show it was applied
    setTimeout(() => {
      setScenario("");
      setScenarioName("");
      setJustSubmitted(false);
      // Collapse the custom scenario section and expand current scenario
      setIsCollapsed(true);
      if (onScenarioCollapse) {
        onScenarioCollapse(true);
      }
    }, 3000);
  };

  return (
    <div className="scenario-input bg-white rounded-lg shadow-md mb-6">
      {/* Header with expand/collapse functionality */}
      <div 
        className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <h3 className="text-lg font-bold">🎭 Custom Scenario</h3>
        <button
          type="button"
          className="text-gray-500 hover:text-gray-700 transition-transform duration-200"
          style={{ transform: isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)' }}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Collapsible content */}
      {!isCollapsed && (
        <div className="p-4 pt-0">
          <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Scenario Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={scenarioName}
            onChange={(e) => setScenarioName(e.target.value)}
            placeholder="Enter a name for this scenario... (e.g., 'Climate Emergency Summit')"
            className={`w-full p-3 border rounded-lg ${
              justSubmitted ? 'bg-green-50 border-green-300' : ''
            }`}
            disabled={loading || justSubmitted || randomLoading}
          />
          {scenarioName.trim() === '' && scenario.trim() !== '' && (
            <p className="text-red-500 text-xs mt-1">Scenario name is required</p>
          )}
        </div>
        
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Scenario Description <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <textarea
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              placeholder="Describe a new scenario for your agents... (e.g., 'A mysterious signal has been detected. The team must decide how to respond.')"
              className={`w-full p-3 border rounded-lg resize-none pr-16 ${
                justSubmitted ? 'bg-green-50 border-green-300' : 
                isRecording ? 'bg-blue-50 border-blue-300' : ''
              }`}
              rows="4"
              disabled={loading || justSubmitted || randomLoading}
            />
            
            {/* Voice Input Controls - Fixed positioning with more spacing */}
            <div className="absolute right-6 top-3 flex flex-col space-y-1">
              {!isRecording ? (
                <button
                  type="button"
                  onClick={startRecording}
                  disabled={loading || justSubmitted || randomLoading}
                  className="w-6 h-6 text-gray-600 hover:text-gray-800 disabled:opacity-50 transition-colors flex items-center justify-center"
                  title="Voice input"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="w-full h-full"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                  </svg>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={stopRecording}
                  className="w-6 h-6 text-red-600 hover:text-red-700 transition-colors animate-pulse flex items-center justify-center"
                  title="Stop recording"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="w-full h-full"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                  </svg>
                </button>
              )}

              {/* Upload button */}
              <label className="w-6 h-6 text-gray-600 hover:text-gray-800 disabled:opacity-50 transition-colors flex items-center justify-center cursor-pointer" title="Upload files">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.png,.jpg,.jpeg,.gif"
                  onChange={handleFileUpload}
                  disabled={loading || justSubmitted || randomLoading || uploading}
                  className="hidden"
                />
                {uploading ? (
                  <div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <svg
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="w-full h-full"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                    <path d="M12,11L16,15H13V19H11V15H8L12,11Z"/>
                  </svg>
                )}
              </label>

              {/* View uploaded files button */}
              {uploadedFiles.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowUploadedFiles(!showUploadedFiles)}
                  className="w-6 h-6 text-blue-600 hover:text-blue-800 transition-colors flex items-center justify-center"
                  title={`View uploaded files (${uploadedFiles.length})`}
                >
                  <span className="text-xs font-bold">{uploadedFiles.length}</span>
                </button>
              )}
              
              {scenario.trim() && (
                <button
                  type="button"
                  onClick={clearScenario}
                  disabled={loading || justSubmitted || randomLoading || isRecording}
                  className="w-6 h-6 bg-gray-500 hover:bg-gray-600 disabled:opacity-50 text-white rounded transition-colors flex items-center justify-center"
                  title="Clear text"
                >
                  <span className="text-xs">🗑️</span>
                </button>
              )}
            </div>
          </div>
          
          {/* Enhanced Status Messages */}
          {isRecording && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2">
              <div className="flex items-center space-x-3">
                <div className="flex space-x-1">
                  <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"></div>
                  <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
                <div>
                  <div className="text-blue-700 font-semibold text-sm">🎤 Recording...</div>
                  <div className="text-blue-600 text-xs">
                    Speak your scenario clearly
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {uploadError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mt-2">
              <div className="flex items-start space-x-2">
                <span className="text-red-600 text-sm">⚠️</span>
                <div>
                  <div className="text-red-700 font-semibold text-sm">Upload Error</div>
                  <div className="text-red-600 text-xs">{uploadError}</div>
                </div>
              </div>
            </div>
          )}

          {/* Uploaded Files Display */}
          {showUploadedFiles && uploadedFiles.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-2">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-blue-700 font-semibold text-sm">📎 Uploaded Context Files ({uploadedFiles.length})</h4>
                <button
                  onClick={() => setShowUploadedFiles(false)}
                  className="text-blue-600 hover:text-blue-800 text-xs"
                >
                  Hide
                </button>
              </div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between bg-white rounded px-2 py-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs">
                        {file.file_type === 'image' ? '🖼️' : 
                         file.file_type === 'pdf' ? '📄' : 
                         file.file_type === 'excel' ? '📊' : 
                         file.file_type === 'text' ? '📝' : '📄'}
                      </span>
                      <span className="text-xs text-gray-700 truncate">{file.filename}</span>
                    </div>
                    <span className="text-xs text-gray-500">{Math.round(file.size / 1024)}KB</span>
                  </div>
                ))}
              </div>
              <div className="text-xs text-blue-600 mt-2">
                💡 Agents will use these files for context and reference during conversations.
              </div>
            </div>
          )}
          
          {voiceError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mt-2">
              <div className="flex items-start space-x-2">
                <span className="text-red-600 text-sm">⚠️</span>
                <div>
                  <div className="text-red-700 font-semibold text-sm">Voice Input Error</div>
                  <div className="text-red-600 text-xs">{voiceError}</div>
                </div>
              </div>
            </div>
          )}
          
          {justSubmitted && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-2 mt-2">
              <p className="text-green-700 text-sm flex items-center space-x-2">
                <span>✅</span>
                <span>Scenario applied successfully! Text will clear in a moment...</span>
              </p>
            </div>
          )}
          
          {isTranscribing && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 mt-2">
              <p className="text-blue-700 text-xs flex items-center space-x-2">
                <span>🔄</span>
                <span>Transcribing audio... Please wait.</span>
              </p>
            </div>
          )}
        </div>
        
        <div className="space-y-2">
          <button
            type="submit"
            disabled={loading || !scenario.trim() || !scenarioName.trim() || justSubmitted || randomLoading || isRecording || isTranscribing}
            className="w-full bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Setting Scenario..." : justSubmitted ? "Scenario Applied!" : "Set New Scenario"}
          </button>
          
          <button
            type="button"
            onClick={handleGenerateRandomScenario}
            disabled={loading || justSubmitted || randomLoading || isRecording || isTranscribing}
            className="w-full bg-gray-400 text-white px-4 py-2 rounded hover:bg-gray-500 disabled:opacity-50 transition-colors"
          >
            {randomLoading ? "Generating & Applying..." : "🎲 Random Scenario"}
          </button>
        </div>
          </form>
        </div>
      )}
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
  
  // Enhanced play/pause logic to handle start simulation
  const handlePlayPause = async () => {
    if (isActive) {
      // If simulation is running, pause it
      await onPauseSimulation();
    } else {
      // If simulation is paused/stopped, start/resume it
      // This combines the start simulation and resume functionality
      const newState = true;
      await onToggleAuto({
        auto_conversations: newState,
        auto_time: newState,
        conversation_interval: 10,
        time_interval: 60
      });
    }
  };
  
  return (
    <div className="flex items-center justify-center gap-2 mt-3">
      {/* Enhanced Play/Pause Button with Start Simulation functionality */}
      <div className="relative group">
        <button 
          onClick={handlePlayPause}
          className={`p-2 text-white rounded-full transition-colors ${
            isActive 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-green-600 hover:bg-green-700'
          }`}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            {isActive ? (
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
            ) : (
              <path d="M8 5v14l11-7z"/>
            )}
          </svg>
        </button>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap z-10">
          {isActive ? "Pause Simulation" : "Start/Resume Simulation"}
        </div>
      </div>
      
      {/* Generate Conversation Button */}
      <div className="relative group">
        <button 
          onClick={onGenerateConversation}
          className="p-2 bg-purple-600 text-white rounded-full hover:bg-purple-700 transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
          </svg>
        </button>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap z-10">
          Generate Conversation
        </div>
      </div>
      
      {/* Next Period Button */}
      <div className="relative group">
        <button 
          onClick={onNextPeriod}
          className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/>
          </svg>
        </button>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap z-10">
          Next Time Period
        </div>
      </div>
      
      {/* Auto Toggle */}
      <div className="relative group">
        <button 
          onClick={onToggleAuto}
          className={`p-2 rounded-full transition-colors ${
            isActive 
              ? 'bg-orange-600 text-white hover:bg-orange-700' 
              : 'bg-gray-600 text-white hover:bg-gray-700'
          }`}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </button>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap z-10">
          {isActive ? "Auto Mode: ON" : "Auto Mode: OFF"}
        </div>
      </div>
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
        Start New Simulation
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
      <div className="bg-white rounded-lg p-6 w-full max-w-6xl max-h-[95vh] overflow-y-auto">
        <h3 className="text-lg font-bold mb-6">✏️ Edit Agent: {agent.name}</h3>
        <form onSubmit={handleSubmit}>
          <div className="flex gap-6">
            {/* Left side - Large Avatar (30% smaller) */}
            <div className="flex-shrink-0">
              <div className="w-72 h-72">
                {agent.avatar_url ? (
                  <img 
                    src={agent.avatar_url} 
                    alt={`${agent.name} avatar`}
                    className="w-72 h-72 rounded-lg object-cover border-4 border-gray-200 shadow-lg"
                    style={{ imageRendering: 'high-quality' }}
                  />
                ) : (
                  <div className="w-72 h-72 rounded-lg bg-gray-200 flex items-center justify-center text-gray-500 border-4 border-gray-300">
                    <span className="text-8xl font-bold">{agent.name.charAt(0).toUpperCase()}</span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Right side - Form fields */}
            <div className="flex-1 min-w-0 ml-2">
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
                  <div className="relative">
                    <textarea
                      value={formData.goal}
                      onChange={(e) => setFormData(prev => ({...prev, goal: e.target.value}))}
                      className="w-full p-2 pr-10 border rounded"
                      rows="2"
                      disabled={loading}
                      placeholder="Describe the agent's main objective"
                    />
                    <div className="absolute right-2 top-2">
                      <VoiceInput
                        onTextUpdate={(text) => setFormData(prev => ({...prev, goal: text}))}
                        fieldType="goal"
                        size="small"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Expertise</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={formData.expertise}
                      onChange={(e) => setFormData(prev => ({...prev, expertise: e.target.value}))}
                      className="w-full p-2 pr-10 border rounded"
                      placeholder="e.g., Machine Learning, Psychology"
                      disabled={loading}
                    />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                      <VoiceInput
                        onTextUpdate={(text) => setFormData(prev => ({...prev, expertise: text}))}
                        fieldType="expertise"
                        size="small"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Background</label>
                  <div className="relative">
                    <textarea
                      value={formData.background}
                      onChange={(e) => setFormData(prev => ({...prev, background: e.target.value}))}
                      className="w-full p-2 pr-10 border rounded"
                      rows="3"
                      placeholder="Professional background and experience"
                      disabled={loading}
                    />
                    <div className="absolute right-2 top-2">
                      <VoiceInput
                        onTextUpdate={(text) => setFormData(prev => ({...prev, background: text}))}
                        fieldType="background"
                        size="small"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Memory section - Full width below the avatar and form */}
          <div className="mt-6">
            <label className="block text-sm font-medium mb-1">
              🧠 Memory & Knowledge 
              <span className="text-xs text-gray-500 ml-2">
                (What the agent remembers + real-world URLs for additional context)
              </span>
            </label>
            <div className="relative">
              <textarea
                value={formData.memory_summary}
                onChange={(e) => setFormData(prev => ({...prev, memory_summary: e.target.value}))}
                className="w-full p-2 pr-12 border rounded bg-blue-50"
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
              <div className="absolute right-3 top-2">
                <VoiceInput
                  onTextUpdate={(text) => setFormData(prev => ({...prev, memory_summary: text}))}
                  fieldType="memory"
                  size="small"
                  disabled={loading}
                />
              </div>
            </div>
            <p className="text-xs text-blue-600 mt-1">
              💡 <strong>Pro tip:</strong> Add URLs to give agents real-world knowledge that will shape their responses
            </p>
            {formData.memory_summary.includes('http') && (
              <p className="text-xs text-green-600 mt-1">
                🌐 URLs detected! They will be processed when you save.
              </p>
            )}
          </div>
          
          {/* Personality Traits section - Full width below memory */}
          <div className="mt-6">
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

const AgentCard = ({ agent, relationships, onEdit, onClearMemory, onAddMemory, onDelete, onSave }) => {
  const [showMemoryInput, setShowMemoryInput] = useState(false);
  const [newMemory, setNewMemory] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

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
    <div className="agent-card bg-white rounded-lg shadow-md p-4 m-2 transition-all duration-300 hover:shadow-lg">
      {/* First Line - Action Buttons (far right) */}
      <div className="flex justify-end mb-3">
        <div className="flex gap-1">
          <button
            onClick={() => onEdit(agent)}
            className="text-blue-600 hover:text-blue-800 transition-colors p-1"
            title="Edit Agent"
            style={{ fontSize: '0.75rem' }}
          >
            ✏️
          </button>
          <button
            onClick={() => onSave(agent)}
            className="text-purple-600 hover:text-purple-800 transition-colors p-1"
            title="Save Agent to Library"
            style={{ fontSize: '0.75rem' }}
          >
            💾
          </button>
          <button
            onClick={() => setShowMemoryInput(!showMemoryInput)}
            className="text-green-600 hover:text-green-800 transition-colors p-1"
            title="Add Memory"
            style={{ fontSize: '0.75rem' }}
          >
            🧠+
          </button>
          <button
            onClick={() => onDelete(agent.id, agent.name)}
            className="text-red-600 hover:text-red-800 transition-colors p-1"
            title="Delete Agent"
            style={{ fontSize: '0.75rem' }}
          >
            <svg 
              width="12" 
              height="12" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              className="inline-block"
            >
              <path d="M3 6H5H21M8 6V4C8 3.44772 8.44772 3 9 3H15C15.5523 3 16 3.44772 16 4V6M19 6V20C19 20.5523 18.5523 21 18 21H6C5.44772 21 5 20.5523 5 20V6H19ZM10 11V17M14 11V17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            </svg>
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-600 hover:text-gray-800 transition-colors p-1"
            title={isExpanded ? "Hide Details" : "Show Details"}
            style={{ fontSize: '0.75rem' }}
          >
            <svg 
              className={`w-3 h-3 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Second Line - Avatar and Name (perfectly aligned) */}
      <div className="flex items-start mb-3">
        <div className="flex-shrink-0">
          {agent.avatar_url ? (
            <div className="relative">
              <img 
                src={agent.avatar_url} 
                alt={`${agent.name} avatar`}
                className="w-12 h-12 rounded-full object-cover border-2 border-gray-200 avatar-animation"
                style={{ imageRendering: 'high-quality' }}
                loading="lazy"
              />
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer"></div>
            </div>
          ) : (
            <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-lg font-bold border-2 border-gray-300">
              {agent.name.charAt(0).toUpperCase()}
            </div>
          )}
          
          {/* Mood Bar underneath avatar */}
          <div className="mt-2 w-12">
            <div className="bg-blue-100 text-blue-800 px-1 py-0.5 rounded text-xs text-center text-[10px] leading-tight">
              {agent.current_mood}
            </div>
          </div>
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className="font-bold text-gray-800 break-words leading-tight">{agent.name}</h3>
          <p className="text-sm text-gray-600">{agent.archetype}</p>
        </div>
      </div>

      {/* Goal Section - Wider */}
      {agent.goal && (
        <div className="mb-3">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 w-full">
            <p className="text-sm text-gray-700 italic">"{agent.goal}"</p>
          </div>
        </div>
      )}

      {/* Personality Traits - Always Visible */}
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">🧠 Personality</h4>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(agent.personality).map(([trait, value]) => (
            <div key={trait} className="trait-item">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs capitalize text-gray-600">{trait}</span>
                <span className="text-xs font-medium">{value}/10</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${getPersonalityColor(value)}`}
                  style={{width: `${value * 10}%`}}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Expandable Details Section */}
      {isExpanded && (
        <div className="expanded-details mt-4 pt-4 border-t border-gray-100 animate-fade-in">
          {/* Expertise & Background */}
          {(agent.expertise || agent.background) && (
            <div className="mb-3 grid grid-cols-1 gap-2">
              {agent.expertise && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-1">🔬 Expertise</h4>
                  <p className="text-sm text-blue-600">{agent.expertise}</p>
                </div>
              )}
              {agent.background && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-1">📋 Background</h4>
                  <p className="text-sm text-gray-600">{agent.background}</p>
                </div>
              )}
            </div>
          )}

          {/* Relationships */}
          {agentRelationships.length > 0 && (
            <div className="mb-3">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">🤝 Relationships</h4>
              <div className="flex flex-wrap gap-1">
                {agentRelationships.map(rel => (
                  <span key={rel.id} className={`text-xs px-2 py-1 rounded ${
                    rel.status === 'friends' ? 'bg-green-100 text-green-800' :
                    rel.status === 'tension' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {rel.status} ({rel.score})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Memory */}
          {agent.memory_summary && (
            <div className="mb-3">
              <h4 className="text-sm font-semibold text-gray-700 mb-1">🧠 Memory</h4>
              <p className="text-xs text-gray-600 bg-blue-50 p-2 rounded border">
                {agent.memory_summary}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Memory Input */}
      {showMemoryInput && (
        <div className="memory-input mt-4 pt-4 border-t border-gray-100">
          <form onSubmit={handleAddMemory} className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Add Memory</label>
            <div className="relative">
              <textarea
                value={newMemory}
                onChange={(e) => setNewMemory(e.target.value)}
                placeholder="What should this agent remember?"
                className="w-full p-2 pr-10 border border-gray-300 rounded text-sm"
                rows="3"
              />
              <div className="absolute right-2 top-2">
                <VoiceInput
                  onTextUpdate={(text) => setNewMemory(text)}
                  fieldType="memory"
                  size="small"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
              >
                Add Memory
              </button>
              <button
                type="button"
                onClick={() => setShowMemoryInput(false)}
                className="bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
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
  
  // Time limit configuration
  const [timeLimitEnabled, setTimeLimitEnabled] = useState(false);
  const [timeLimitUnit, setTimeLimitUnit] = useState('day');
  const [timeLimitAmount, setTimeLimitAmount] = useState(1);

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
      // Calculate time limit in hours for backend
      let timeLimitHours = null;
      if (timeLimitEnabled) {
        const multipliers = {
          day: 24,
          week: 24 * 7,
          month: 24 * 30,
          year: 24 * 365
        };
        timeLimitHours = timeLimitAmount * multipliers[timeLimitUnit];
      }

      await onStartWithConfig({
        language: selectedLanguage,
        audioNarrative: audioNarrative,
        timeLimit: timeLimitEnabled ? timeLimitHours : null,
        timeLimitDisplay: timeLimitEnabled ? `${timeLimitAmount} ${timeLimitUnit}${timeLimitAmount > 1 ? 's' : ''}` : null
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

          {/* Time Limit Configuration */}
          <div>
            <label className="block text-sm font-medium mb-3">
              ⏰ Simulation Time Limit
            </label>
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              {/* Enable/Disable Toggle */}
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium">Set Time Limit</div>
                  <div className="text-sm text-gray-600">
                    Give agents a deadline to reach conclusions
                  </div>
                </div>
                <button
                  onClick={() => setTimeLimitEnabled(!timeLimitEnabled)}
                  className={`ml-4 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    timeLimitEnabled ? 'bg-orange-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      timeLimitEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* Time Limit Settings */}
              {timeLimitEnabled && (
                <div className="border-t border-gray-200 pt-4">
                  <div className="flex items-center space-x-3">
                    {/* Amount Input */}
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-700 mb-1">Amount</label>
                      <input
                        type="number"
                        min="1"
                        max="999"
                        value={timeLimitAmount}
                        onChange={(e) => setTimeLimitAmount(Math.max(1, parseInt(e.target.value) || 1))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                      />
                    </div>

                    {/* Unit Selection */}
                    <div className="flex-2">
                      <label className="block text-xs font-medium text-gray-700 mb-1">Unit</label>
                      <select
                        value={timeLimitUnit}
                        onChange={(e) => setTimeLimitUnit(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                      >
                        <option value="day">Day{timeLimitAmount > 1 ? 's' : ''}</option>
                        <option value="week">Week{timeLimitAmount > 1 ? 's' : ''}</option>
                        <option value="month">Month{timeLimitAmount > 1 ? 's' : ''}</option>
                        <option value="year">Year{timeLimitAmount > 1 ? 's' : ''}</option>
                      </select>
                    </div>

                    {/* Infinite Option */}
                    <div className="flex-shrink-0">
                      <label className="block text-xs font-medium text-gray-700 mb-1">Infinite</label>
                      <button
                        onClick={() => setTimeLimitEnabled(false)}
                        className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-500"
                        title="No time limit"
                      >
                        ∞
                      </button>
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-800">
                    <strong>⏰ Agents will work towards conclusions within {timeLimitAmount} {timeLimitUnit}{timeLimitAmount > 1 ? 's' : ''}</strong>
                    <div className="mt-1">
                      They will prioritize finding solutions and reaching consensus before the deadline.
                    </div>
                  </div>
                </div>
              )}

              {/* No Time Limit Message */}
              {!timeLimitEnabled && (
                <div className="p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
                  <strong>∞ No time restrictions</strong> - Agents can continue discussions indefinitely
                </div>
              )}
            </div>
          </div>

          {/* Cost Information */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-sm text-blue-800">
              <strong>💰 Estimated Monthly Cost (8 agents):</strong>
              <div className="mt-1 text-xs">
                • Text only: $0.10/month
                • With voice: {audioNarrative ? '$3.34/month' : '$0.10/month'}
                {timeLimitEnabled && (
                  <div className="mt-1 text-orange-700">
                    ⏰ Time limit: {timeLimitAmount} {timeLimitUnit}{timeLimitAmount > 1 ? 's' : ''}
                  </div>
                )}
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

const AgentProfilesManager = ({ 
  agents = [], 
  onDeleteAll, 
  onCreateAgent, 
  onInitResearchStation, 
  onTestBackgrounds,
  onShowAgentLibrary 
}) => {
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
      <div className="space-y-2 mb-4">
        {/* Primary Actions Row */}
        <div className="flex space-x-2">
          <div className="flex-1">
            <AvatarCreator 
              onCreateAgent={onCreateAgent}
              archetypes={AGENT_ARCHETYPES}
            />
          </div>
          {agents.length > 0 && (
            <button
              onClick={handleDeleteAll}
              className="bg-red-50 text-red-600 px-3 py-2 rounded text-sm hover:bg-red-100 transition-colors border border-red-200"
              title="Delete All Agents"
            >
              Clear All
            </button>
          )}
        </div>

        {/* Team Builder Actions */}
        <div className="space-y-2">
          <div className="border-t border-gray-200 pt-2">
            <h4 className="text-xs font-semibold text-gray-600 mb-2">Quick Team Builders</h4>
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              onClick={onInitResearchStation}
              className="flex-1 bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 text-sm"
            >
              Create Crypto Team
            </button>
            <div className="relative group">
              <svg 
                className="w-4 h-4 text-gray-400 hover:text-indigo-600 cursor-help info-icon" 
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              {/* Hover Tooltip */}
              <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none w-64 tooltip z-10">
                Creates 3 crypto experts: Mark (Marketing Veteran), Alex (DeFi Product Leader), Dex (Trend-Spotting Generalist)
                <div className="absolute top-full right-4 border-4 border-transparent border-t-gray-800"></div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 mt-2">
            <button 
              onClick={onTestBackgrounds}
              className="flex-1 bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 text-sm"
            >
              Generate Random Team
            </button>
            <div className="relative group">
              <svg 
                className="w-4 h-4 text-gray-400 hover:text-indigo-600 cursor-help info-icon" 
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              {/* Hover Tooltip */}
              <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none w-64 tooltip z-10">
                Creates 4 agents with dramatically different professional backgrounds to showcase how background influences thinking
                <div className="absolute top-full right-4 border-4 border-transparent border-t-gray-800"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Agent Library Section */}
        <div className="border-t border-gray-200 pt-2 mt-3">
          <button 
            onClick={onShowAgentLibrary}
            className="w-full bg-purple-600 text-white px-3 py-2 rounded hover:bg-purple-700 text-sm flex items-center justify-center space-x-2"
          >
            <span>📚</span>
            <span>Agent Library</span>
          </button>
        </div>
      </div>
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
        className="w-full bg-emerald-600 text-white px-3 py-2 rounded hover:bg-emerald-700 text-sm transition-colors"
      >
        ➕ Add Agent
      </button>
      
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold mb-4">➕ Create New Agent</h3>
            
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
                  <div className="relative">
                    <textarea
                      value={formData.goal}
                      onChange={(e) => setFormData(prev => ({...prev, goal: e.target.value}))}
                      className="w-full p-2 pr-10 border rounded"
                      rows="2"
                      placeholder="What does this agent want to achieve?"
                      required
                    />
                    <div className="absolute right-2 top-2">
                      <VoiceInput
                        onTextUpdate={(text) => setFormData(prev => ({...prev, goal: text}))}
                        fieldType="goal"
                        size="small"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Expertise</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={formData.expertise}
                      onChange={(e) => setFormData(prev => ({...prev, expertise: e.target.value}))}
                      className="w-full p-2 pr-10 border rounded"
                      placeholder="e.g., Machine Learning, Psychology"
                      disabled={loading}
                    />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                      <VoiceInput
                        onTextUpdate={(text) => setFormData(prev => ({...prev, expertise: text}))}
                        fieldType="expertise"
                        size="small"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Background</label>
                  <div className="relative">
                    <textarea
                      value={formData.background}
                      onChange={(e) => setFormData(prev => ({...prev, background: e.target.value}))}
                      className="w-full p-2 pr-10 border rounded"
                      rows="3"
                      placeholder="Professional background and experience"
                      disabled={loading}
                    />
                    <div className="absolute right-2 top-2">
                      <VoiceInput
                        onTextUpdate={(text) => setFormData(prev => ({...prev, background: text}))}
                        fieldType="background"
                        size="small"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-1">
                    🎨 Avatar Description
                    <span className="text-xs text-gray-500 ml-2">(Describe how the agent should look)</span>
                  </label>
                  <div className="flex space-x-2">
                    <div className="flex-1 relative">
                      <textarea
                        value={formData.avatar_prompt}
                        onChange={(e) => setFormData(prev => ({...prev, avatar_prompt: e.target.value}))}
                        className="w-full p-2 pr-10 border rounded"
                        rows="2"
                        placeholder="Examples:
• Nikola Tesla
• an old grandma with white hair and blue eyes
• a young scientist with glasses and a lab coat
• a confident business leader in a suit"
                      />
                      <div className="absolute right-2 top-2">
                        <VoiceInput
                          onTextUpdate={(text) => setFormData(prev => ({...prev, avatar_prompt: text}))}
                          fieldType="avatar_prompt"
                          size="small"
                          disabled={loading}
                        />
                      </div>
                    </div>
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
  onCreateAgent,
  setShowFastForward
}) => {
  const isActive = simulationState?.auto_conversations || simulationState?.auto_time;
  const autoRunning = simulationState?.auto_conversations || simulationState?.auto_time;

  return (
    <div className="control-panel bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold mb-4">🎮 Simulation Control</h3>
      
      {/* Simplified control panel with just auto settings */}
      <div className="simulation-info mb-4">
        <p className="text-sm">
          <strong>Auto Conversations:</strong> {simulationState?.auto_conversations ? 'ON' : 'OFF'}
        </p>
        <p className="text-sm">
          <strong>Auto Time:</strong> {simulationState?.auto_time ? 'ON' : 'OFF'}
        </p>
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

const SavedAgentsLibrary = ({ onCreateAgent }) => {
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

  const handleUseAgent = async (agent) => {
    try {
      // Trigger agent creation with saved agent data
      const agentData = {
        name: agent.name,
        archetype: agent.archetype,
        personality: agent.personality,
        goal: agent.goal,
        expertise: agent.expertise,
        background: agent.background,
        avatar_url: agent.avatar_url,
        avatar_prompt: agent.avatar_prompt
      };
      
      // Call the agent creation function
      await onCreateAgent(agentData);
      
      setShowLibrary(false);
      
      alert(`Agent "${agent.name}" has been added to your simulation!`);
    } catch (error) {
      console.error('Error using saved agent:', error);
      alert('Failed to create agent from library. Please try again.');
    }
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
                          style={{ imageRendering: 'high-quality' }}
                          loading="lazy"
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
  const [showHistory, setShowHistory] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedConversations, setSelectedConversations] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const fetchConversationHistory = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/conversation-history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConversationHistory(response.data);
      setSelectedConversations(new Set()); // Clear selections when refreshing
      setSelectAll(false);
    } catch (error) {
      console.error('Error fetching conversation history:', error);
    }
    setLoading(false);
  };

  const handleSelectConversation = (conversationId) => {
    const newSelected = new Set(selectedConversations);
    if (newSelected.has(conversationId)) {
      newSelected.delete(conversationId);
    } else {
      newSelected.add(conversationId);
    }
    setSelectedConversations(newSelected);
    setSelectAll(newSelected.size === conversationHistory.length);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedConversations(new Set());
      setSelectAll(false);
    } else {
      setSelectedConversations(new Set(conversationHistory.map(c => c.id)));
      setSelectAll(true);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedConversations.size === 0) return;
    
    const confirmMessage = `Are you sure you want to delete ${selectedConversations.size} conversation${selectedConversations.size > 1 ? 's' : ''}? This action cannot be undone.`;
    if (!window.confirm(confirmMessage)) return;
    
    setDeleting(true);
    try {
      const response = await axios.delete(`${API}/conversation-history/bulk`, {
        headers: { Authorization: `Bearer ${token}` },
        data: Array.from(selectedConversations)
      });
      
      console.log(`Successfully deleted ${response.data.deleted_count} conversations`);
      
      // Refresh the conversation history
      await fetchConversationHistory();
      
      alert(`Successfully deleted ${response.data.deleted_count} conversation${response.data.deleted_count > 1 ? 's' : ''}`);
      
    } catch (error) {
      console.error('Error deleting conversations:', error);
      alert('Failed to delete conversations. Please try again.');
    }
    setDeleting(false);
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

            {/* Bulk Selection Controls */}
            {conversationHistory.length > 0 && !loading && (
              <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectAll}
                      onChange={handleSelectAll}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Select All ({conversationHistory.length})
                    </span>
                  </label>
                  {selectedConversations.size > 0 && (
                    <span className="text-sm text-blue-600 font-medium">
                      {selectedConversations.size} selected
                    </span>
                  )}
                </div>
                
                {selectedConversations.size > 0 && (
                  <button
                    onClick={handleDeleteSelected}
                    disabled={deleting}
                    className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:opacity-50 text-sm flex items-center space-x-2"
                  >
                    {deleting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Deleting...</span>
                      </>
                    ) : (
                      <>
                        <span>🗑️</span>
                        <span>Delete Selected ({selectedConversations.size})</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            )}

            {loading ? (
              <div className="text-center py-8">Loading conversation history...</div>
            ) : conversationHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-4">💭</div>
                <p>No conversation history yet.</p>
                <p className="text-sm mt-2">Your conversations will be automatically saved here!</p>
              </div>
            ) : (
              // Group conversations by scenario name
              (() => {
                const groupedConversations = conversationHistory.reduce((groups, conversation) => {
                  const scenarioName = conversation.scenario_name || 'Unnamed Scenario';
                  if (!groups[scenarioName]) {
                    groups[scenarioName] = [];
                  }
                  groups[scenarioName].push(conversation);
                  return groups;
                }, {});

                return (
                  <div className="space-y-6">
                    {Object.entries(groupedConversations).map(([scenarioName, conversations]) => (
                      <div key={scenarioName} className="border-2 border-gray-200 rounded-lg p-4">
                        <div className="flex items-center mb-4">
                          <div className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium mr-3">
                            📋 {scenarioName}
                          </div>
                          <span className="text-gray-500 text-sm">
                            {conversations.length} conversation{conversations.length > 1 ? 's' : ''}
                          </span>
                        </div>
                        
                        <div className="space-y-3 ml-4">
                          {conversations.map(conversation => (
                            <div key={conversation.id} className="border rounded-lg p-4 hover:shadow-lg transition-shadow bg-white">
                              <div className="flex items-start space-x-3">
                                <label className="flex items-center mt-1 cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={selectedConversations.has(conversation.id)}
                                    onChange={() => handleSelectConversation(conversation.id)}
                                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                                  />
                                </label>
                                
                                <div className="flex-1">
                                  <div className="flex justify-between items-start mb-3">
                                    <div>
                                      <h4 className="font-bold text-gray-800">
                                        Round {conversation.round_number} - {conversation.time_period}
                                      </h4>
                                      <p className="text-sm text-gray-600">
                                                        Participants: {conversation.messages?.map(m => m.agent_name).filter((name, index, arr) => arr.indexOf(name) === index).join(', ') || 'N/A'}
                                      </p>
                                    </div>
                                    <div className="text-xs text-gray-400">
                                      {new Date(conversation.created_at).toLocaleString()}
                                    </div>
                                  </div>
                                  
                                  <div className="bg-gray-50 rounded p-3 max-h-40 overflow-y-auto">
                                    {conversation.messages?.slice(0, 3).map((message, index) => (
                                      <div key={index} className="text-sm mb-2">
                                        <strong>{message.agent_name}:</strong> {message.message}
                                      </div>
                                    )) || (
                                      <div className="text-sm text-gray-500">No messages available</div>
                                    )}
                                    {conversation.messages?.length > 3 && (
                                      <div className="text-xs text-gray-500 italic">
                                        ...and {conversation.messages.length - 3} more messages
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                );
              })()
            )}
          </div>
        </div>
      )}
    </>
  );
};

// Enhanced File Center Component with Beautiful UI and Scenario Organization
const FileCenter = ({ onRefresh }) => {
  const { user, token } = useAuth();
  const [showFileCenter, setShowFileCenter] = useState(false);
  const [scenarioDocuments, setScenarioDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [documentSuggestions, setDocumentSuggestions] = useState([]);
  const [showSuggestionModal, setShowSuggestionModal] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [deleting, setDeleting] = useState(false);
  
  const categories = ["Protocol", "Training", "Research", "Equipment", "Budget", "Reference"];

  const fetchScenarioDocuments = async (forceRefresh = false) => {
    if (!token) return;
    
    setLoading(true);
    try {
      // Add cache-busting parameter if force refresh is requested
      const cacheParam = forceRefresh ? `?_t=${Date.now()}` : '';
      
      // Use the faster direct documents endpoint instead of by-scenario
      const response = await axios.get(`${API}/documents${cacheParam}`, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      console.log('Fetched documents from server:', response.data?.length || 0);
      
      // Group documents by scenario for display
      const documentsByScenario = response.data.reduce((acc, doc) => {
        const scenarioName = doc.scenario_name || 'Default Scenario';
        if (!acc[scenarioName]) {
          acc[scenarioName] = {
            scenario_name: scenarioName,
            documents: [],
            document_count: 0
          };
        }
        acc[scenarioName].documents.push(doc);
        acc[scenarioName].document_count++;
        return acc;
      }, {});
      
      // Convert to array format expected by the component
      const scenarioArray = Object.values(documentsByScenario);
      console.log('Grouped into scenarios:', scenarioArray.length);
      setScenarioDocuments(scenarioArray);
      setSelectedDocuments(new Set()); // Clear selections when refreshing
      setSelectAll(false);
    } catch (error) {
      console.error('Error fetching documents:', error);
      
      // Fallback to the by-scenario endpoint if direct approach fails
      try {
        const response = await axios.get(`${API}/documents/by-scenario`, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
        console.log('Fallback fetch successful:', response.data?.length || 0);
        setScenarioDocuments(response.data);
      } catch (fallbackError) {
        console.error('Error with fallback endpoint:', fallbackError);
      }
    }
    setLoading(false);
  };

  const handleSelectDocument = (documentId) => {
    const newSelected = new Set(selectedDocuments);
    if (newSelected.has(documentId)) {
      newSelected.delete(documentId);
    } else {
      newSelected.add(documentId);
    }
    setSelectedDocuments(newSelected);
    
    // Calculate total documents across all scenarios
    const totalDocuments = scenarioDocuments.reduce((total, scenario) => total + scenario.documents.length, 0);
    setSelectAll(newSelected.size === totalDocuments);
  };

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedDocuments(new Set());
      setSelectAll(false);
    } else {
      // Select all documents across all scenarios
      const allDocumentIds = scenarioDocuments.flatMap(scenario => 
        scenario.documents.map(doc => doc.id)
      );
      setSelectedDocuments(new Set(allDocumentIds));
      setSelectAll(true);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedDocuments.size === 0) return;
    
    const confirmMessage = `Are you sure you want to delete ${selectedDocuments.size} document${selectedDocuments.size > 1 ? 's' : ''}? This action cannot be undone.`;
    if (!window.confirm(confirmMessage)) return;
    
    setDeleting(true);
    try {
      // Convert Set to Array for the API call
      const documentIds = Array.from(selectedDocuments);
      console.log('Attempting to delete documents:', documentIds);
      console.log('API URL:', `${API}/documents/bulk-delete`);
      
      // Use the POST endpoint with proper request format
      const response = await axios.post(`${API}/documents/bulk-delete`, 
        documentIds, // Send array directly in body
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('Delete response:', response.data);
      console.log(`Successfully deleted ${response.data.deleted_count} documents`);
      
      // Add a small delay to ensure database operation is complete
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force refresh the document list with cache busting
      await fetchScenarioDocuments(true);
      
      alert(`Successfully deleted ${response.data.deleted_count} document${response.data.deleted_count > 1 ? 's' : ''}`);
      
    } catch (error) {
      console.error('Error deleting documents:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      // Try alternative DELETE endpoint if POST fails
      try {
        const documentIds = Array.from(selectedDocuments);
        console.log('Trying DELETE endpoint with documents:', documentIds);
        
        const deleteResponse = await axios.delete(`${API}/documents/bulk`, {
          data: documentIds, // Send data in the delete request body
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        console.log('DELETE response:', deleteResponse.data);
        console.log(`Successfully deleted ${deleteResponse.data.deleted_count} documents`);
        
        // Add a small delay to ensure database operation is complete
        await new Promise(resolve => setTimeout(resolve, 500));
        
        await fetchScenarioDocuments(true);
        alert(`Successfully deleted ${deleteResponse.data.deleted_count} document${deleteResponse.data.deleted_count > 1 ? 's' : ''}`);
        
      } catch (deleteError) {
        console.error('Error with DELETE endpoint:', deleteError);
        console.error('DELETE error response:', deleteError.response?.data);
        console.error('DELETE error status:', deleteError.response?.status);
        alert('Failed to delete documents. Please try again or contact support.');
      }
    }
    setDeleting(false);
  };

  const fetchDocumentSuggestions = async (documentId) => {
    try {
      const response = await axios.get(`${API}/documents/${documentId}/suggestions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDocumentSuggestions(response.data);
    } catch (error) {
      console.error('Error fetching document suggestions:', error);
    }
  };

  useEffect(() => {
    if (showFileCenter && token) {
      fetchScenarioDocuments();
    }
  }, [showFileCenter, token]);

  const handleDocumentView = async (document) => {
    try {
      const response = await axios.get(`${API}/documents/${document.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedDocument(response.data);
      await fetchDocumentSuggestions(document.id);
      setShowDocumentModal(true);
    } catch (error) {
      console.error('Error fetching document:', error);
      alert('Failed to load document');
    }
  };

  const handleDownloadDocument = (document) => {
    try {
      const blob = new Blob([document.content], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = document.metadata.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading document:', error);
      alert('Failed to download document');
    }
  };

  const handleSuggestionDecision = async (suggestionId, decision) => {
    try {
      const agents = await axios.get(`${API}/agents`);
      if (agents.data.length === 0) {
        alert('No agents available');
        return;
      }

      const response = await axios.post(`${API}/documents/${selectedDocument.id}/review-suggestion`, {
        suggestion_id: suggestionId,
        decision: decision,
        creator_agent_id: agents.data[0].id // Use first agent as creator for demo
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        alert(`Suggestion ${decision}ed successfully!`);
        await fetchScenarioDocuments();
        await fetchDocumentSuggestions(selectedDocument.id);
        if (decision === 'accept') {
          // Refresh the document content
          handleDocumentView(selectedDocument);
        }
      }
    } catch (error) {
      console.error('Error handling suggestion:', error);
      alert('Failed to handle suggestion');
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Protocol': 'bg-red-100 text-red-800 border-red-200',
      'Training': 'bg-blue-100 text-blue-800 border-blue-200',
      'Research': 'bg-green-100 text-green-800 border-green-200',
      'Equipment': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'Budget': 'bg-purple-100 text-purple-800 border-purple-200',
      'Reference': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[category] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filter documents based on search and category
  const filteredScenarios = (scenarioDocuments || []).map(scenario => ({
    ...scenario,
    documents: (scenario?.documents || []).filter(doc => {
      const matchesSearch = searchTerm === "" || 
        (doc?.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (doc?.description || '').toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === "" || doc?.category === selectedCategory;
      return matchesSearch && matchesCategory;
    })
  })).filter(scenario => (scenario?.documents || []).length > 0);

  if (!user) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-bold">📁 File Center</h3>
          <div className="text-xs text-gray-500">Sign in required</div>
        </div>
        <p className="text-center text-gray-500 py-4">Sign in to access your team's documents</p>
      </div>
    );
  }

  return (
    <>
      {/* File Center Card */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-bold">📁 File Center</h3>
          <div className="flex items-center space-x-2">
            <div className="text-xs text-gray-500">
              {(() => {
                try {
                  return scenarioDocuments?.reduce((total, scenario) => {
                    const count = scenario?.document_count || scenario?.documents?.length || 0;
                    return total + count;
                  }, 0) || 0;
                } catch (error) {
                  console.error('Error calculating document count:', error);
                  return 0;
                }
              })()} documents
            </div>
            <button
              onClick={() => setShowFileCenter(true)}
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
            >
              📖 Open File Center
            </button>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="bg-blue-50 p-2 rounded text-center">
            <div className="font-semibold text-blue-700">
              {scenarioDocuments?.length || 0}
            </div>
            <div className="text-blue-600">Scenarios</div>
          </div>
          <div className="bg-green-50 p-2 rounded text-center">
            <div className="font-semibold text-green-700">
              {scenarioDocuments?.reduce((total, scenario) => {
                // Handle both document_count field and documents array length
                const count = scenario?.document_count || scenario?.documents?.length || 0;
                return total + count;
              }, 0) || 0}
            </div>
            <div className="text-green-600">Documents</div>
          </div>
          <div className="bg-purple-50 p-2 rounded text-center">
            <div className="font-semibold text-purple-700">
              {(() => {
                try {
                  const allDocs = scenarioDocuments?.flatMap(s => s?.documents || []) || [];
                  const categories = allDocs.map(d => d?.category).filter(Boolean);
                  return new Set(categories).size;
                } catch (error) {
                  console.error('Error calculating categories:', error);
                  return 0;
                }
              })()}
            </div>
            <div className="text-purple-600">Categories</div>
          </div>
        </div>
      </div>

      {/* File Center Modal */}
      {showFileCenter && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-7xl max-h-[95vh] overflow-hidden">
            {/* Header */}
            <div className="border-b border-gray-200 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">📁 File Center</h2>
                  <p className="text-gray-600 mt-1">Documents organized by simulation scenario</p>
                </div>
                <button
                  onClick={() => setShowFileCenter(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ✕
                </button>
              </div>

              {/* Search and Filter Bar */}
              <div className="mt-6 flex gap-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Categories</option>
                  {categories?.map(category => (
                    <option key={category} value={category}>{category}</option>
                  )) || []}
                </select>
                <button
                  onClick={() => fetchScenarioDocuments(true)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  🔄 Refresh
                </button>
              </div>

              {/* Bulk Selection Controls */}
              {(() => {
                try {
                  const totalDocuments = filteredScenarios?.reduce((total, scenario) => {
                    return total + (scenario?.documents?.length || 0);
                  }, 0) || 0;
                  return totalDocuments > 0 && !loading ? (
                  <div className="mt-4 flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectAll}
                          onChange={handleSelectAll}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          Select All ({totalDocuments})
                        </span>
                      </label>
                      {selectedDocuments.size > 0 && (
                        <span className="text-sm text-blue-600 font-medium">
                          {selectedDocuments.size} selected
                        </span>
                      )}
                    </div>
                    
                    {selectedDocuments.size > 0 && (
                      <button
                        onClick={handleDeleteSelected}
                        disabled={deleting}
                        className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:opacity-50 text-sm flex items-center space-x-2"
                      >
                        {deleting ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span>Deleting...</span>
                          </>
                        ) : (
                          <>
                            <span>🗑️</span>
                            <span>Delete Selected ({selectedDocuments.size})</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                ) : null;
                } catch (error) {
                  console.error('Error rendering bulk selection controls:', error);
                  return null;
                }
              })()}
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(95vh-200px)]">
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading documents...</p>
                </div>
              ) : (filteredScenarios || []).length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📄</div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">No Documents Found</h3>
                  <p className="text-gray-600">
                    {searchTerm || selectedCategory 
                      ? "Try adjusting your search criteria" 
                      : "Documents will appear here when your agents create them during conversations"
                    }
                  </p>
                </div>
              ) : (
                <div className="space-y-8">
                  {(filteredScenarios || []).map((scenario, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900">{scenario?.scenario_name || scenario?.scenario || 'Unknown Scenario'}</h3>
                          <p className="text-gray-600">{(scenario?.documents || []).length} documents</p>
                        </div>
                        <div className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                          Active Scenario
                        </div>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                        {(scenario?.documents || []).map((doc) => (
                          <div key={doc.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow relative">
                            {/* Selection Checkbox */}
                            <label className="absolute top-3 left-3 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={selectedDocuments.has(doc?.id)}
                                onChange={() => handleSelectDocument(doc?.id)}
                                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                              />
                            </label>

                            <div className="flex justify-between items-start mb-3 ml-8">
                              <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-gray-900 mb-2 truncate" title={doc?.title || 'Untitled'}>
                                  {doc?.title || 'Untitled Document'}
                                </h4>
                                <div className={`inline-block text-xs px-2 py-1 rounded border ${getCategoryColor(doc?.category || 'Reference')}`}>
                                  {doc?.category || 'Reference'}
                                </div>
                              </div>
                            </div>

                            <p className="text-sm text-gray-600 mb-3 line-clamp-2 ml-8">
                              {doc?.description || 'No description available'}
                            </p>

                            <div className="text-xs text-gray-500 mb-3 ml-8">
                              <div>By: {doc?.authors?.join(', ') || 'Unknown'}</div>
                              <div>{formatDate(doc?.created_at || new Date().toISOString())}</div>
                            </div>

                            <div className="bg-gray-50 p-2 rounded text-xs text-gray-600 mb-3 h-16 overflow-hidden ml-8">
                              {doc?.preview || 'No preview available'}
                            </div>

                            <div className="flex space-x-2 ml-8">
                              <button
                                onClick={() => handleDocumentView(doc)}
                                className="flex-1 bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700 transition-colors"
                              >
                                👁 View
                              </button>
                              <button
                                onClick={() => handleDownloadDocument(doc)}
                                className="bg-green-600 text-white px-3 py-1 rounded text-xs hover:bg-green-700 transition-colors"
                              >
                                ⬇
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Document Viewer Modal */}
      {showDocumentModal && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-5xl max-h-[95vh] overflow-hidden">
            {/* Header */}
            <div className="border-b border-gray-200 p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold">{selectedDocument.metadata.title}</h2>
                  <div className="flex items-center space-x-2 mt-2">
                    <span className={`text-xs px-2 py-1 rounded border ${getCategoryColor(selectedDocument.metadata.category)}`}>
                      {selectedDocument.metadata.category}
                    </span>
                    <span className="text-xs text-gray-500">
                                      by {selectedDocument.metadata.authors?.join(', ') || 'Unknown Author'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatDate(selectedDocument.metadata.created_at)}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  {documentSuggestions.length > 0 && (
                    <button
                      onClick={() => setShowSuggestionModal(true)}
                      className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 transition-colors"
                    >
                      📝 Suggestions ({documentSuggestions.length})
                    </button>
                  )}
                  <button
                    onClick={() => handleDownloadDocument(selectedDocument)}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors"
                  >
                    ⬇ Download
                  </button>
                  <button
                    onClick={() => setShowDocumentModal(false)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(95vh-150px)]">
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded">
                  {selectedDocument.content}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Suggestions Modal */}
      {showSuggestionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="border-b border-gray-200 p-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold">💡 Improvement Suggestions</h3>
                <button
                  onClick={() => setShowSuggestionModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-4 overflow-y-auto max-h-96">
              {documentSuggestions.map((suggestion, index) => (
                <div key={suggestion.id} className="border border-gray-200 rounded p-4 mb-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-semibold text-gray-900">
                      From: {suggestion.suggesting_agent_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(suggestion.created_at)}
                    </div>
                  </div>
                  <p className="text-gray-700 mb-3">{suggestion.suggestion}</p>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleSuggestionDecision(suggestion.id, 'accept')}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      ✅ Accept
                    </button>
                    <button
                      onClick={() => handleSuggestionDecision(suggestion.id, 'reject')}
                      className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                    >
                      ❌ Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

function App() {
  // Handle OAuth callback
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');
      
      // Check if this is an OAuth callback (code parameter present)
      if (code || error) {
        if (error) {
          alert('Google authentication failed: ' + error);
          // Clean up URL
          window.history.replaceState({}, document.title, window.location.pathname);
          return;
        }
        
        if (code && state) {
          // Verify state to prevent CSRF attacks
          const storedState = localStorage.getItem('oauth_state');
          if (state !== storedState) {
            alert('Invalid authentication state. Please try again.');
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
          }
          
          try {
            // Exchange code for tokens
            const response = await axios.post(`${API}/auth/google/callback`, {
              code: code,
              redirect_uri: window.location.origin
            });
            
            const { access_token, user: userData } = response.data;
            
            // Store token and user data
            localStorage.setItem('auth_token', access_token);
            setToken(access_token);
            setUser(userData);
            
            // Clean up
            localStorage.removeItem('oauth_state');
            
            // Clean up URL and show success
            window.history.replaceState({}, document.title, window.location.pathname);
            alert('✅ Successfully signed in with Google!');
            
          } catch (error) {
            console.error('OAuth callback error:', error);
            alert('Authentication failed. Please try again.');
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        }
      }
    };
    
    handleOAuthCallback();
  }, []);

  const { user, logout, isAuthenticated, token, setToken, setUser } = useAuth();
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
  const [showAgentLibrary, setShowAgentLibrary] = useState(false);
  const [autoExpandCurrentScenario, setAutoExpandCurrentScenario] = useState(false);
  const [showAdminDashboard, setShowAdminDashboard] = useState(false);

  // Check if current user is admin
  const isAdmin = user && user.email && user.email.toLowerCase() === 'dino@cytonic.com';

  const handleTestBackgrounds = async () => {
    setLoading(true);
    try {
      // Create agents with diverse backgrounds
      const response = await axios.post(`${API}/test/background-differences`);
      alert(`Created test agents with diverse backgrounds! Scenario: ${response.data.scenario}`);
      
      // Refresh data to get the new agents
      await refreshAllData();
      
      // Wait a moment for the agents to be properly created
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Generate avatars for the newly created agents
      const agentsResponse = await axios.get(`${API}/agents`);
      const newAgents = agentsResponse.data;
      
      // Generate avatars for agents that don't have them
      const agentsNeedingAvatars = newAgents.filter(agent => !agent.avatar_url || agent.avatar_url === '');
      
      if (agentsNeedingAvatars.length > 0) {
        console.log(`Generating avatars for ${agentsNeedingAvatars.length} agents...`);
        
        // Generate all avatars in parallel for better performance
        const avatarPromises = agentsNeedingAvatars.map(async (agent) => {
          try {
            // Create a prompt based on the agent's characteristics
            const avatarPrompt = `Professional headshot of a ${agent.archetype.replace('_', ' ')} named ${agent.name}, ${agent.background ? agent.background.substring(0, 100) : 'professional appearance'}, high quality, realistic, business professional style`;
            
            console.log(`Generating avatar for ${agent.name}...`);
            const avatarResponse = await axios.post(`${API}/avatars/generate`, {
              prompt: avatarPrompt
            });
            
            if (avatarResponse.data.success) {
              console.log(`Avatar generated for ${agent.name}, updating agent...`);
              // Update the agent with the generated avatar - send only the avatar_url field
              await axios.put(`${API}/agents/${agent.id}`, {
                avatar_url: avatarResponse.data.image_url
              });
              console.log(`Agent ${agent.name} updated with avatar`);
              return true;
            } else {
              console.error(`Failed to generate avatar for ${agent.name}:`, avatarResponse.data.error);
              return false;
            }
          } catch (avatarError) {
            console.error(`Failed to generate avatar for ${agent.name}:`, avatarError);
            return false;
          }
        });
        
        // Wait for all avatar generations to complete
        const results = await Promise.all(avatarPromises);
        const successCount = results.filter(r => r).length;
        console.log(`Successfully generated ${successCount}/${agentsNeedingAvatars.length} avatars`);
        
        // Refresh data again to show the new avatars
        await refreshAllData();
      }
      
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

  const handleSaveAgent = async (agent) => {
    if (!token) {
      alert('Please sign in to save agents to your library.');
      return;
    }

    try {
      const agentData = {
        name: agent.name,
        archetype: agent.archetype,
        personality: agent.personality,
        goal: agent.goal,
        expertise: agent.expertise || "",
        background: agent.background || "",
        avatar_url: agent.avatar_url || "",
        avatar_prompt: agent.avatar_prompt || "",
        is_template: true // Mark as template for reuse
      };

      await axios.post(`${API}/saved-agents`, agentData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(`✅ Agent "${agent.name}" has been saved to your library!`);
    } catch (error) {
      console.error('Error saving agent:', error);
      if (error.response?.status === 401) {
        alert('Please sign in to save agents.');
      } else {
        alert('Failed to save agent. Please try again.');
      }
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
      const response = await axios.get(`${API}/agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAgents(response.data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API}/conversations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConversations(response.data);
      
      // Auto-save new conversations to user's history if authenticated
      if (token && response.data.length > 0) {
        await saveConversationsToHistory(response.data);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const saveConversationsToHistory = async (conversations) => {
    if (!token || !conversations.length) return;
    
    try {
      // Save the latest conversation to user's history
      const latestConversation = conversations[conversations.length - 1];
      
      if (latestConversation && latestConversation.messages && latestConversation.messages.length > 0) {
        const conversationData = {
          simulation_id: `sim_${Date.now()}`,
          participants: latestConversation.messages.map(m => m.agent_name),
          messages: latestConversation.messages.map(m => ({
            agent_name: m.agent_name,
            message: m.message,
            timestamp: m.timestamp || new Date().toISOString()
          })),
          language: latestConversation.language || 'en',
          title: `${latestConversation.time_period} - ${latestConversation.scenario}`,
          tags: ['simulation', 'auto-generated']
        };
        
        await axios.post(`${API}/conversation-history`, conversationData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (error) {
      console.error('Error saving conversation to history:', error);
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
  const handleSetScenario = async (scenario, scenarioName) => {
    try {
      const response = await axios.post(`${API}/simulation/set-scenario`, { 
        scenario: scenario,
        scenario_name: scenarioName 
      });
      console.log('Scenario set response:', response.data);
      await fetchSimulationState();
    } catch (error) {
      console.error('Error setting scenario:', error);
      alert('Error setting scenario: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleScenarioCollapse = (shouldExpand) => {
    setAutoExpandCurrentScenario(shouldExpand);
    // Reset the auto-expand after a short delay so it can be triggered again
    if (shouldExpand) {
      setTimeout(() => {
        setAutoExpandCurrentScenario(false);
      }, 1000);
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
      // Create the crypto team
      await axios.post(`${API}/simulation/init-research-station`);
      
      // Refresh data to get the new agents
      await refreshAllData();
      
      // Wait a moment for the agents to be properly created
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Generate avatars for the newly created agents
      const agentsResponse = await axios.get(`${API}/agents`);
      const newAgents = agentsResponse.data;
      
      // Generate avatars for agents that don't have them
      const agentsNeedingAvatars = newAgents.filter(agent => !agent.avatar_url || agent.avatar_url === '');
      
      if (agentsNeedingAvatars.length > 0) {
        console.log(`Generating avatars for ${agentsNeedingAvatars.length} crypto team agents...`);
        
        // Generate all avatars in parallel for better performance
        const avatarPromises = agentsNeedingAvatars.map(async (agent) => {
          try {
            // Create specific prompts for the crypto team members
            let avatarPrompt;
            if (agent.name.includes('Mark') || agent.name.includes('Castellano')) {
              avatarPrompt = 'Professional headshot of an experienced marketing executive, mature confident businessman, crypto industry veteran, high quality realistic photo';
            } else if (agent.name.includes('Alex') || agent.name.includes('Chen')) {
              avatarPrompt = 'Professional headshot of a female tech product leader, confident and charismatic, DeFi industry executive, high quality realistic photo';
            } else if (agent.name.includes('Diego') || agent.name.includes('Dex')) {
              avatarPrompt = 'Professional headshot of a young crypto analyst, tech-savvy researcher, trend spotter, high quality realistic photo';
            } else {
              avatarPrompt = `Professional headshot of a ${agent.archetype.replace('_', ' ')} in the crypto industry, ${agent.background ? agent.background.substring(0, 100) : 'professional appearance'}, high quality realistic photo`;
            }
            
            console.log(`Generating avatar for ${agent.name}...`);
            const avatarResponse = await axios.post(`${API}/avatars/generate`, {
              prompt: avatarPrompt
            });
            
            if (avatarResponse.data.success) {
              console.log(`Avatar generated for ${agent.name}, updating agent...`);
              // Update the agent with the generated avatar - send only the avatar_url field
              await axios.put(`${API}/agents/${agent.id}`, {
                avatar_url: avatarResponse.data.image_url
              });
              console.log(`Agent ${agent.name} updated with avatar`);
              return true;
            } else {
              console.error(`Failed to generate avatar for ${agent.name}:`, avatarResponse.data.error);
              return false;
            }
          } catch (avatarError) {
            console.error(`Failed to generate avatar for ${agent.name}:`, avatarError);
            return false;
          }
        });
        
        // Wait for all avatar generations to complete
        const results = await Promise.all(avatarPromises);
        const successCount = results.filter(r => r).length;
        console.log(`Successfully generated ${successCount}/${agentsNeedingAvatars.length} avatars`);
        
        // Refresh data again to show the new avatars
        await refreshAllData();
      }
      
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
      await axios.post(`${API}/simulation/start`, {
        time_limit_hours: config.timeLimit,
        time_limit_display: config.timeLimitDisplay
      });
      
      // Set the language for the simulation
      await axios.post(`${API}/simulation/set-language`, { 
        language: config.language 
      });
      
      // Automatically create the crypto team so users can start conversations immediately
      await axios.post(`${API}/simulation/init-research-station`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      await refreshAllData();
      
      // Show success message with configuration details
      const langName = config.language === 'en' ? 'English' : config.language;
      const audioStatus = config.audioNarrative ? 'enabled' : 'disabled';
      const timeLimitInfo = config.timeLimit ? `\nTime Limit: ${config.timeLimitDisplay}` : '\nTime Limit: Unlimited';
      alert(`✅ Simulation started!\nLanguage: ${langName}\nAudio Narration: ${audioStatus}${timeLimitInfo}`);
      
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

  const handleUpdateAgent = async (agentId, agentData) => {
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
      {/* Show HomePage if user is not authenticated */}
      {!isAuthenticated && (
        <HomePage onAuthenticated={(token, user) => {
          setToken(token);
          setUser(user);
        }} />
      )}
      
      {/* Show main app if user is authenticated */}
      {isAuthenticated && (
        <>
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-4">
                <ObserverLogo />
                
                <div className="flex items-center space-x-4">
                  {/* User Library & History (only show when authenticated) */}
                  {isAuthenticated && (
                    <>
                      <SavedAgentsLibrary onCreateAgent={handleCreateAgent} />
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
                <div className="flex items-center space-x-3">
                  {/* Admin Dashboard Button */}
                  {isAdmin && (
                    <button
                      onClick={() => setShowAdminDashboard(true)}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 font-medium transition-colors flex items-center space-x-2"
                      title="Admin Dashboard"
                    >
                      <span>👑</span>
                      <span>Admin Dashboard</span>
                    </button>
                  )}
                  <UserProfile user={user} onLogout={logout} />
                </div>
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
              onInitResearchStation={handleInitResearchStation}
              onTestBackgrounds={handleTestBackgrounds}
              onCreateAgent={handleCreateAgent}
              onShowAgentLibrary={() => setShowAgentLibrary(true)}
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
                    onSave={handleSaveAgent}
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
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Conversations</h2>
              <div className="text-sm text-gray-600 font-medium">
                Day {simulationState?.current_day || 1}, {simulationState?.current_time_period || 'morning'}
              </div>
            </div>
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
            {/* Start New Simulation Control - Above scenario creation */}
            <StartSimulationControl onStartSimulation={handleStartSimulation} />
            
            <ScenarioInput 
              onSetScenario={handleSetScenario} 
              currentScenario={simulationState?.scenario}
              onScenarioCollapse={handleScenarioCollapse}
            />
            
            <CurrentScenarioCard 
              currentScenario={simulationState?.scenario}
              autoExpand={autoExpandCurrentScenario}
            />
            
            
            <ControlPanel
              simulationState={simulationState}
              apiUsage={apiUsage}
              onCreateAgent={handleCreateAgent}
              setShowFastForward={setShowFastForward}
            />
            
            {/* File Center for Action-Oriented Agent Behavior */}
            <div className="mt-4">
              <FileCenter 
                onRefresh={refreshAllData}
              />
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
        onSave={handleUpdateAgent}
        archetypes={archetypes}
      />

      <AgentLibrary
        isOpen={showAgentLibrary}
        onClose={() => setShowAgentLibrary(false)}
        onAddAgent={async (agent) => {
          try {
            // Generate avatar if not already generated
            if (!agent.avatar_url) {
              const avatarResponse = await axios.post(`${API}/avatars/generate`, {
                prompt: agent.avatar_prompt
              }, {
                headers: { Authorization: `Bearer ${token}` }
              });
              if (avatarResponse.data.success) {
                agent.avatar_url = avatarResponse.data.image_url;
              }
            }

            // Create the agent in the simulation
            const agentData = {
              name: agent.name,
              archetype: agent.archetype,
              goal: agent.goal,
              expertise: agent.expertise,
              background: agent.background,
              memory_summary: agent.memory_summary,
              avatar_url: agent.avatar_url,
              avatar_prompt: agent.avatar_prompt
            };

            await axios.post(`${API}/agents`, agentData, {
              headers: { Authorization: `Bearer ${token}` }
            });

            await refreshAllData();
            // Don't close the library and don't show alert
            return { success: true, message: `${agent.name} has been added to your simulation!` };
          } catch (error) {
            console.error('Error adding agent:', error);
            return { success: false, message: 'Failed to add agent. Please try again.' };
          }
        }}
      />

      {/* Admin Dashboard */}
      {showAdminDashboard && isAdmin && (
        <AdminDashboard
          token={token}
          onClose={() => setShowAdminDashboard(false)}
        />
      )}
        </>
      )}
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