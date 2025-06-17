import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { motion, useAnimationControls, AnimatePresence } from 'framer-motion';
import AgentLibrary from './AgentLibrary';
import HomePage from './HomePage';
import AdminDashboard from './AdminDashboard';
import './ModernApp.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "251454265437-5s1019au9fr6oh9rb47frkv8549vptk5.apps.googleusercontent.com";

// Debug logging
console.log('Environment variables loaded:', {
  BACKEND_URL,
  GOOGLE_CLIENT_ID: GOOGLE_CLIENT_ID ? 'Present' : 'Missing',
  NODE_ENV: process.env.NODE_ENV
});

// Enhanced VoiceInput Component with Modern Design
const VoiceInput = ({ 
  onTextUpdate, 
  fieldType = "general", 
  language = "hr", 
  disabled = false,
  className = "",
  size = "small"
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [error, setError] = useState("");
  const { token } = useAuth();

  const sizeClasses = {
    small: "w-8 h-8",
    medium: "w-10 h-10", 
    large: "w-12 h-12"
  };

  // Enhanced SVG Microphone Icon
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
    if (!token || isDisabledDueToAuth) {
      alert('🎤 Voice input requires authentication.\n\nPlease use "Continue as Guest" button to enable voice input.');
      return;
    }
    
    try {
      setError("");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      setMediaRecorder(mediaRecorder);
      
      const audioChunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        await processAudio(audioBlob);
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

  const isDisabledDueToAuth = !token;

  return (
    <div className={`relative ${className}`}>
      <motion.button
        type="button"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled || isDisabledDueToAuth}
        className={`${sizeClasses[size]} ${
          isRecording ? 'text-red-500 bg-red-50' : 'text-gray-600 hover:text-purple-600'
        } disabled:opacity-50 transition-all duration-300 flex items-center justify-center rounded-lg p-2 hover:bg-purple-50`}
        title={isDisabledDueToAuth ? "Sign in to use voice input" : isRecording ? "Stop recording" : "Voice input"}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        animate={isRecording ? { scale: [1, 1.1, 1] } : {}}
        transition={{ repeat: isRecording ? Infinity : 0, duration: 1 }}
      >
        <MicrophoneIcon className="w-full h-full" />
        {isProcessing && (
          <motion.div
            className="absolute inset-0 border-2 border-purple-500 rounded-lg"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1 }}
          />
        )}
      </motion.button>
      
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 mt-2 bg-red-100 text-red-700 text-xs px-3 py-2 rounded-lg shadow-lg z-10 whitespace-nowrap border border-red-200"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Keep the original animated Observer Logo (unchanged as requested)
const ObserverLogo = () => {
  const pupilControls = useAnimationControls();

  useEffect(() => {
    const animatePupil = async () => {
      while (true) {
        const movementType = Math.random();
        
        if (movementType < 0.4) {
          await pupilControls.start({
            x: -4,
            y: Math.random() * 2 + 6,
            transition: {
              type: "spring",
              stiffness: 60,
              damping: 20
            }
          });
          
          await new Promise(resolve => setTimeout(resolve, 200));
          
          await pupilControls.start({
            x: 4,
            y: Math.random() * 2 + 6,
            transition: {
              type: "spring",
              stiffness: 60,
              damping: 20
            }
          });
          
          await new Promise(resolve => setTimeout(resolve, 200));
        } else {
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
    
    animatePupil();
    
    return () => {
      pupilControls.stop();
    };
  }, [pupilControls]);

  const [isBlinking, setIsBlinking] = useState(false);
  
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 200);
    }, Math.random() * 5000 + 5000);
    
    return () => clearInterval(blinkInterval);
  }, []);

  return (
    <motion.div 
      className="flex items-center"
      whileHover={{ scale: 1.05 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <div className="text-4xl font-bold tracking-tight relative">
        <div className="relative inline-block w-10 h-10 mr-1">
          <div className="absolute inset-0 bg-white rounded-full border-2 border-gray-800 overflow-hidden shadow-lg">
            <motion.div 
              className="w-4 h-4 bg-black rounded-full absolute"
              style={{ top: '50%', left: '50%', marginLeft: -8, marginTop: -8 }}
              animate={pupilControls}
            />
            
            <div 
              className={`absolute inset-0 bg-gray-400 border-b-2 border-gray-600 transition-transform duration-200 ${isBlinking ? 'translate-y-0' : 'translate-y-[-100%]'}`}
              style={{ borderRadius: '50% 50% 0 0' }}
            >
              <div className="absolute bottom-0 left-1 w-1 h-1 bg-gray-600 rounded-full" />
              <div className="absolute bottom-0 left-3 w-1 h-1 bg-gray-600 rounded-full" />
              <div className="absolute bottom-0 left-5 w-1 h-1 bg-gray-600 rounded-full" />
              <div className="absolute bottom-0 left-7 w-1 h-1 bg-gray-600 rounded-full" />
            </div>
          </div>
        </div>
        <span className="text-white">bserver</span>
      </div>
    </motion.div>
  );
};

// Modern Current Scenario Card
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
      className="modern-card p-6 mb-6"
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

// Authentication Context (unchanged logic, modern UI)
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

  if (loading) {
    return (
      <div className="modern-app flex items-center justify-center">
        <div className="glass-container p-8 text-center">
          <motion.div
            className="w-16 h-16 border-4 border-white border-t-transparent rounded-full mx-auto mb-4"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1 }}
          />
          <p className="text-white text-lg">Loading...</p>
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

// Modern Login Modal
const LoginModal = ({ isOpen, onClose }) => {
  const { login, setUser, setToken } = useAuth();
  const [loginLoading, setLoginLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGoogleLogin = () => {
    setLoginLoading(true);
    setError('');
    
    console.log('Google Client ID:', GOOGLE_CLIENT_ID);
    
    if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID.includes('undefined')) {
      alert('Google Client ID not configured properly. Please check environment variables.');
      setLoginLoading(false);
      return;
    }
    
    const redirectUri = window.location.origin;
    const googleAuthUrl = new URL('https://accounts.google.com/oauth/authorize');
    
    googleAuthUrl.searchParams.set('client_id', GOOGLE_CLIENT_ID);
    googleAuthUrl.searchParams.set('redirect_uri', redirectUri);
    googleAuthUrl.searchParams.set('response_type', 'code');
    googleAuthUrl.searchParams.set('scope', 'openid profile email');
    googleAuthUrl.searchParams.set('access_type', 'offline');
    googleAuthUrl.searchParams.set('state', Math.random().toString(36).substring(2, 15));

    console.log('OAuth URL:', googleAuthUrl.toString());
    console.log('Redirect URI:', redirectUri);
    
    localStorage.setItem('oauth_state', googleAuthUrl.searchParams.get('state'));
    
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
    
    window.location.href = googleAuthUrl.toString();
  };

  const handleTestLogin = async () => {
    setLoginLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/auth/test-login`);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);
      setUser(userData);
      
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
    <AnimatePresence>
      <motion.div
        className="modal-modern"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="modal-content-modern max-w-md w-full mx-4"
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-800">Welcome to</h2>
              <h3 className="text-xl text-gradient font-semibold">AI Agent Simulation</h3>
            </div>
            <motion.button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              ✕
            </motion.button>
          </div>
          
          <div className="text-center mb-8">
            <p className="text-gray-600 mb-6">
              Sign in with your Google account to save your agents and conversation history.
            </p>
            
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
            
            <AnimatePresence>
              {loginLoading && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg mb-4"
                >
                  Signing in...
                </motion.div>
              )}
            </AnimatePresence>
            
            <div className="space-y-4">
              <motion.button
                onClick={handleGoogleLogin}
                disabled={loginLoading}
                className="btn-premium btn-outline w-full"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span>Sign in with Google</span>
              </motion.button>
              
              <motion.button
                onClick={handleTestLogin}
                disabled={loginLoading}
                className="btn-premium btn-primary w-full"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                🧪 Continue as Guest
              </motion.button>
            </div>
          </div>
          
          <div className="text-xs text-gray-500 text-center space-y-2">
            <p>✨ Free to use • 🔒 Secure authentication • 💾 Save your work</p>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// Modern User Profile
const UserProfile = ({ user, onLogout }) => {
  const [showDropdown, setShowDropdown] = useState(false);

  return (
    <div className="relative">
      <motion.button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center space-x-3 glass-container p-3 rounded-xl"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {user.picture ? (
          <motion.img 
            src={user.picture} 
            alt={user.name}
            className="w-10 h-10 rounded-full border-2 border-white/20"
            whileHover={{ scale: 1.1 }}
          />
        ) : (
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg border-2 border-white/20">
            {user.name.charAt(0).toUpperCase()}
          </div>
        )}
        <div className="text-left">
          <span className="text-sm font-medium text-white block">{user.name}</span>
          <span className="text-xs text-white/70">{user.email}</span>
        </div>
        <motion.span 
          className="text-white/70 text-sm"
          animate={{ rotate: showDropdown ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          ▼
        </motion.span>
      </motion.button>

      <AnimatePresence>
        {showDropdown && (
          <motion.div
            className="dropdown-content-modern right-0 mt-2 w-56"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <div className="p-4 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
            <div className="p-2">
              <motion.button
                onClick={() => {
                  onLogout();
                  setShowDropdown(false);
                }}
                className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                🚪 Sign Out
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Modern Navigation
const ModernNavigation = ({ user, onLogin, onLogout, activeTab, setActiveTab }) => {
  const [showLoginModal, setShowLoginModal] = useState(false);

  const navItems = [
    { id: 'home', label: '🏠 Simulation', icon: '🤖' },
    { id: 'agents', label: '👥 Agent Library', icon: '📚' },
    { id: 'admin', label: '⚙️ Admin', icon: '🛠️', adminOnly: true }
  ];

  return (
    <nav className="nav-modern">
      <div className="flex items-center space-x-8">
        <ObserverLogo />
        
        <div className="flex items-center space-x-2">
          {navItems.map((item) => {
            if (item.adminOnly && (!user || !user.is_admin)) return null;
            
            return (
              <motion.button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  activeTab === item.id
                    ? 'bg-white/20 text-white shadow-lg'
                    : 'text-white/70 hover:text-white hover:bg-white/10'
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </motion.button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {user ? (
          <UserProfile user={user} onLogout={onLogout} />
        ) : (
          <motion.button
            onClick={() => setShowLoginModal(true)}
            className="btn-premium btn-outline"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <span>🔐</span>
            Sign In
          </motion.button>
        )}
      </div>

      <LoginModal 
        isOpen={showLoginModal} 
        onClose={() => setShowLoginModal(false)} 
      />
    </nav>
  );
};

// Get the remaining content for the next part...
// (This is getting long, should I continue with the rest of the components?)