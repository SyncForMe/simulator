import React, { useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Profile Settings Modal Component
export const ProfileSettingsModal = ({ isOpen, onClose, user, analyticsData, token }) => {
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bio: user?.bio || ''
  });
  const [profilePicture, setProfilePicture] = useState(user?.picture || '');
  const [showPictureOptions, setShowPictureOptions] = useState(false);
  const [avatarPrompt, setAvatarPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  if (!isOpen) return null;

  const handleInputChange = (e) => {
    if (!e || !e.target) return;
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleFileUpload = async (e) => {
    if (!e || !e.target || !e.target.files) return;
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      alert('File size must be less than 5MB');
      return;
    }

    setIsUploading(true);
    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onload = () => {
        setProfilePicture(reader.result);
        setShowPictureOptions(false);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  const generateAvatar = async () => {
    console.log('🔍 generateAvatar function called!');
    console.log('🔍 avatarPrompt:', avatarPrompt);
    console.log('🔍 token:', token ? 'present' : 'missing');
    
    if (!avatarPrompt.trim()) {
      alert('Please enter a description for your avatar');
      return;
    }

    console.log('🔍 Starting avatar generation...');
    setIsGenerating(true);
    try {
      console.log('🔍 Making API call to:', `${API}/auth/generate-profile-avatar`);
      
      const response = await axios.post(`${API}/auth/generate-profile-avatar`, {
        prompt: avatarPrompt,
        name: formData.name || 'User'
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('🔍 API response:', response.data);
      if (response.data.avatar_url) {
        setProfilePicture(response.data.avatar_url);
        setAvatarPrompt('');
        setShowPictureOptions(false);
        console.log('🔍 Avatar updated successfully!');
      }
    } catch (error) {
      console.error('🔍 Error generating avatar:', error);
      alert('Failed to generate avatar. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    console.log('🔍 handleSave function called');
    console.log('🔍 formData:', formData);
    console.log('🔍 profilePicture:', profilePicture);
    console.log('🔍 token:', token ? 'present' : 'missing');
    
    setIsSaving(true);
    try {
      const updateData = {
        name: formData.name || '',
        email: formData.email || '',
        bio: formData.bio || '',
        picture: profilePicture || ''
      };

      console.log('🔍 updateData to send:', updateData);
      console.log('🔍 Making API call to:', `${API}/auth/profile`);

      const response = await axios.put(`${API}/auth/profile`, updateData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('🔍 Save response:', response.data);
      if (response.data && response.data.success) {
        alert('✅ Profile updated successfully!');
        onClose();
        // Don't reload the page to avoid potential null reference errors
        // window.location.reload();
      } else {
        console.error('🔍 Save failed - no success in response:', response.data);
        alert('❌ Failed to save profile. Please try again.');
      }
    } catch (error) {
      console.error('🔍 Error updating profile:', error);
      console.error('🔍 Error details:', error.response?.data);
      alert('❌ Failed to update profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleEnable2FA = async () => {
    try {
      const response = await axios.post(`${API}/auth/enable-2fa`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.qr_code) {
        alert('Two-Factor Authentication setup initiated. Please scan the QR code with your authenticator app.');
        // In a real app, you'd show a modal with the QR code
        window.open(response.data.qr_code, '_blank');
      }
    } catch (error) {
      console.error('Error enabling 2FA:', error);
      alert('Failed to enable 2FA. This feature will be available soon.');
    }
  };

  const handleChangeEmail = async () => {
    const currentPassword = prompt('Enter your current password to change email:');
    if (!currentPassword) return;

    const newEmail = prompt('Enter your new email address:');
    if (!newEmail) return;

    if (!/\S+@\S+\.\S+/.test(newEmail)) {
      alert('Please enter a valid email address');
      return;
    }

    try {
      const response = await axios.put(`${API}/auth/change-email`, {
        current_password: currentPassword,
        new_email: newEmail
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        alert('✅ Email changed successfully! Please check your new email for verification.');
        setFormData({ ...formData, email: newEmail });
      }
    } catch (error) {
      console.error('Error changing email:', error);
      alert('❌ Failed to change email. Please check your password and try again.');
    }
  };

  const handleChangePassword = async () => {
    const currentPassword = prompt('Enter your current password:');
    if (!currentPassword) return;

    const newPassword = prompt('Enter your new password:');
    if (!newPassword) return;

    if (newPassword.length < 8) {
      alert('Password must be at least 8 characters long');
      return;
    }

    const confirmPassword = prompt('Confirm your new password:');
    if (newPassword !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    try {
      const response = await axios.put(`${API}/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        alert('✅ Password changed successfully!');
      }
    } catch (error) {
      console.error('Error changing password:', error);
      alert('❌ Failed to change password. Please check your current password and try again.');
    }
  };

  const handleDataExport = async () => {
    try {
      const response = await axios.get(`${API}/auth/export-data`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      // Create a downloadable file
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `profile-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      alert('✅ Data exported successfully!');
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('❌ Failed to export data. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">👤 Profile Settings</h2>
              <p className="text-white/80 mt-1">Manage your account information and preferences</p>
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white text-2xl p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="space-y-6">
            {/* Profile Photo Section */}
            <div className="flex items-center space-x-6">
              <div className="relative">
                {profilePicture ? (
                  <img 
                    src={profilePicture} 
                    alt={formData.name || 'User'}
                    className="w-20 h-20 rounded-full border-4 border-blue-100 object-cover"
                  />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-2xl font-bold border-4 border-blue-100">
                    {(formData.name && formData.name.charAt(0).toUpperCase()) || 'U'}
                  </div>
                )}
                <button 
                  onClick={() => setShowPictureOptions(!showPictureOptions)}
                  className="absolute -bottom-1 -right-1 bg-blue-600 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs hover:bg-blue-700 transition-colors"
                >
                  ✏️
                </button>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">{formData.name || 'User'}</h3>
                <p className="text-gray-600">{formData.email || 'No email'}</p>
                <button 
                  onClick={() => setShowPictureOptions(!showPictureOptions)}
                  className="text-blue-600 text-sm hover:text-blue-700 mt-1"
                >
                  Change profile photo
                </button>
              </div>
            </div>

            {/* Picture Options */}
            {showPictureOptions && (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-medium text-gray-800 mb-3">Choose Profile Picture</h4>
                <div className="space-y-3">
                  {/* File Upload */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Upload Photo</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      disabled={isUploading}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    {isUploading && <p className="text-sm text-blue-600 mt-1">Uploading...</p>}
                  </div>

                  {/* AI Avatar Generation */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Generate AI Avatar</label>
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={avatarPrompt}
                        onChange={(e) => e?.target && setAvatarPrompt(e.target.value)}
                        placeholder="Describe your ideal avatar (e.g., professional businessman, creative artist)"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        disabled={isGenerating}
                      />
                      <button
                        onClick={generateAvatar}
                        disabled={isGenerating || !avatarPrompt.trim()}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isGenerating ? 'Generating...' : 'Generate'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Basic Information */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">Basic Information</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter your full name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter your email"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Bio</label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleInputChange}
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Tell us about yourself..."
                ></textarea>
              </div>
            </div>

            {/* Account Statistics */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">Account Statistics</h4>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">{analyticsData?.summary?.total_conversations || 0}</div>
                  <div className="text-sm text-blue-600">Conversations</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">{analyticsData?.summary?.total_agents || 0}</div>
                  <div className="text-sm text-green-600">Saved Agents</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-purple-600">{analyticsData?.summary?.total_documents || 0}</div>
                  <div className="text-sm text-purple-600">Documents</div>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-orange-600">{Math.ceil((user?.created_at ? (Date.now() - new Date(user.created_at)) / (1000 * 60 * 60 * 24) : 0))}</div>
                  <div className="text-sm text-orange-600">Days Active</div>
                </div>
              </div>
            </div>

            {/* Security Settings */}
            <div className="space-y-4">
              <h4 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">Security & Privacy</h4>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-800">Change Email</div>
                    <div className="text-sm text-gray-600">Update your email address with password verification</div>
                  </div>
                  <button 
                    onClick={handleChangeEmail}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-indigo-700 transition-colors"
                  >
                    Change
                  </button>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-800">Two-Factor Authentication</div>
                    <div className="text-sm text-gray-600">Add an extra layer of security to your account</div>
                  </div>
                  <button 
                    onClick={handleEnable2FA}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors"
                  >
                    Enable
                  </button>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-800">Change Password</div>
                    <div className="text-sm text-gray-600">Update your account password with current password verification</div>
                  </div>
                  <button 
                    onClick={handleChangePassword}
                    className="bg-gray-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 transition-colors"
                  >
                    Change
                  </button>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-800">Data Export</div>
                    <div className="text-sm text-gray-600">Download all your data and conversations</div>
                  </div>
                  <button 
                    onClick={handleDataExport}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700 transition-colors"
                  >
                    Export
                  </button>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={isSaving}
              >
                Cancel
              </button>
              <button 
                onClick={handleSave}
                disabled={isSaving}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Preferences Modal Component
export const PreferencesModal = ({ isOpen, onClose, audioNarrativeEnabled }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">⚙️ Preferences</h2>
              <p className="text-white/80 mt-1">Customize your AI simulation experience</p>
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white text-2xl p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Appearance Settings */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">🎨 Appearance</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">Theme</label>
                  <div className="grid grid-cols-3 gap-3">
                    {['Light', 'Dark', 'Auto'].map((theme) => (
                      <button
                        key={theme}
                        className={`p-3 border-2 rounded-lg text-sm font-medium transition-all ${
                          theme === 'Light' 
                            ? 'border-purple-500 bg-purple-50 text-purple-700' 
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        {theme === 'Light' && '☀️'} {theme === 'Dark' && '🌙'} {theme === 'Auto' && '🔄'} {theme}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">Color Scheme</label>
                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { name: 'Purple', color: 'bg-purple-500', selected: true },
                      { name: 'Blue', color: 'bg-blue-500' },
                      { name: 'Green', color: 'bg-green-500' },
                      { name: 'Red', color: 'bg-red-500' }
                    ].map((scheme) => (
                      <button
                        key={scheme.name}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          scheme.selected 
                            ? 'border-purple-500 ring-2 ring-purple-200' 
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        <div className={`w-full h-8 rounded ${scheme.color} mb-2`}></div>
                        <div className="text-xs text-gray-600">{scheme.name}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Language & Region */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">🌍 Language & Region</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Interface Language</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                    <option value="en">🇺🇸 English</option>
                    <option value="es">🇪🇸 Spanish</option>
                    <option value="fr">🇫🇷 French</option>
                    <option value="de">🇩🇪 German</option>
                    <option value="hr">🇭🇷 Croatian</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Time Zone</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                    <option>🌍 UTC (Coordinated Universal Time)</option>
                    <option>🇺🇸 EST (Eastern Standard Time)</option>
                    <option>🇺🇸 PST (Pacific Standard Time)</option>
                    <option>🇪🇺 CET (Central European Time)</option>
                    <option>🇭🇷 Croatia (Central European Time)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Date Format</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                    <option>MM/DD/YYYY (US Format)</option>
                    <option>DD/MM/YYYY (European Format)</option>
                    <option>YYYY-MM-DD (ISO Format)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Notifications */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">🔔 Notifications</h3>
              
              <div className="space-y-4">
                {[
                  { label: 'Email Notifications', desc: 'Receive updates via email', enabled: true },
                  { label: 'Browser Notifications', desc: 'Show desktop notifications', enabled: false },
                  { label: 'Conversation Updates', desc: 'Notify when agents finish conversations', enabled: true },
                  { label: 'Document Generation', desc: 'Alert when documents are created', enabled: true },
                  { label: 'Weekly Reports', desc: 'Send weekly analytics summaries', enabled: false }
                ].map((setting, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-800">{setting.label}</div>
                      <div className="text-sm text-gray-600">{setting.desc}</div>
                    </div>
                    <div className="flex items-center">
                      <input 
                        type="checkbox" 
                        defaultChecked={setting.enabled}
                        className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Settings */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-800 border-b border-gray-200 pb-2">🤖 AI Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Default Conversation Length</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                    <option>Short (3-5 exchanges)</option>
                    <option defaultValue>Medium (8-12 exchanges)</option>
                    <option>Long (15+ exchanges)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Agent Response Speed</label>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">Fast</span>
                    <input type="range" min="1" max="5" defaultValue="3" className="flex-1" />
                    <span className="text-sm text-gray-600">Thoughtful</span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-800">Audio Narration</div>
                      <div className="text-sm text-gray-600">Enable voice narration for conversations</div>
                    </div>
                    <div className="flex items-center">
                      <input 
                        type="checkbox" 
                        defaultChecked={audioNarrativeEnabled}
                        className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-800">Auto-save Conversations</div>
                      <div className="text-sm text-gray-600">Automatically save conversations to history</div>
                    </div>
                    <div className="flex items-center">
                      <input 
                        type="checkbox" 
                        defaultChecked={true}
                        className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-6 mt-8 border-t border-gray-200">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
              Save Preferences
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Help & Support Modal Component
export const HelpSupportModal = ({ isOpen, onClose, onOpenFeedback }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">🆘 Help & Support</h2>
              <p className="text-white/80 mt-1">Find answers and get help with AI Agent Simulation</p>
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white text-2xl p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Quick Help */}
            <div className="lg:col-span-2 space-y-8">
              {/* FAQ Section */}
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
                  <span className="mr-2">❓</span> Frequently Asked Questions
                </h3>
                
                <div className="space-y-4">
                  {[
                    {
                      question: "How do I create my first AI agent?",
                      answer: "Click the purple 'Agent Library' button in the navigation to browse professionally crafted agents, or use the 'Create Custom Agent' form to build your own. Simply fill in the agent's goal, expertise, and background to get started."
                    },
                    {
                      question: "What scenarios can I simulate?",
                      answer: "You can simulate any scenario! Use the Custom Scenario section to describe your situation, or click the 🎲 Random Scenario button for inspiration. The system supports universal topics beyond medical contexts."
                    },
                    {
                      question: "How do I save my conversations?",
                      answer: "Conversations are automatically saved when you're signed in. Access them via the 'Chat History' tab in the navigation. You can search, filter, and organize conversations by scenario."
                    },
                    {
                      question: "What is the Agent Library?",
                      answer: "The Agent Library contains professionally crafted agent profiles across various sectors like Healthcare, Business, Technology, and more. Each agent has specialized expertise and can be added to your simulations instantly."
                    },
                    {
                      question: "How does document generation work?",
                      answer: "When agents in your conversations agree to create documentation (using phrases like 'let's create a protocol'), the system automatically generates professional documents. Access them in the File Center."
                    },
                    {
                      question: "Can I use voice input?",
                      answer: "Yes! Look for microphone icons 🎤 next to text areas. Voice input works for scenarios, agent creation, and memory addition. Make sure to allow microphone access in your browser."
                    }
                  ].map((faq, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-800 mb-2">{faq.question}</h4>
                      <p className="text-gray-600 text-sm leading-relaxed">{faq.answer}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Getting Started Guide */}
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
                  <span className="mr-2">🚀</span> Getting Started Guide
                </h3>
                
                <div className="space-y-4">
                  {[
                    {
                      step: "1",
                      title: "Create Your First Scenario",
                      description: "Use the Custom Scenario section to describe a situation you want to simulate, or try a random scenario for inspiration."
                    },
                    {
                      step: "2", 
                      title: "Add AI Agents",
                      description: "Browse the Agent Library for professional profiles or create custom agents with specific expertise for your scenario."
                    },
                    {
                      step: "3",
                      title: "Start the Simulation",
                      description: "Click 'Start New Simulation' to begin. Agents will have conversations based on your scenario and their personalities."
                    },
                    {
                      step: "4",
                      title: "Review & Save Results",
                      description: "View generated conversations and documents. Everything is automatically saved to your Chat History and File Center."
                    }
                  ].map((step, index) => (
                    <div key={index} className="flex items-start space-x-4 p-4 bg-blue-50 rounded-lg">
                      <div className="bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm">
                        {step.step}
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-800 mb-1">{step.title}</h4>
                        <p className="text-gray-600 text-sm">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Support Sidebar */}
            <div className="space-y-6">
              {/* Contact Support */}
              <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                <h4 className="font-semibold text-green-800 mb-4 flex items-center">
                  <span className="mr-2">📞</span> Contact Support
                </h4>
                
                <div className="space-y-3 text-sm">
                  <div className="flex items-center space-x-2">
                    <span className="text-green-600">📧</span>
                    <span className="text-gray-700">support@emergent.ai</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-600">⏰</span>
                    <span className="text-gray-700">24/7 Support Available</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-600">🌍</span>
                    <span className="text-gray-700">Global Support Team</span>
                  </div>
                </div>
                
                <button
                  onClick={() => {
                    onClose();
                    onOpenFeedback();
                  }}
                  className="w-full mt-4 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Submit Support Ticket
                </button>
              </div>

              {/* Documentation Links */}
              <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
                <h4 className="font-semibold text-blue-800 mb-4 flex items-center">
                  <span className="mr-2">📚</span> Documentation
                </h4>
                
                <div className="space-y-2">
                  {[
                    { title: "User Guide", icon: "📖" },
                    { title: "API Documentation", icon: "🔌" },
                    { title: "Video Tutorials", icon: "🎥" },
                    { title: "Best Practices", icon: "⭐" }
                  ].map((doc, index) => (
                    <button
                      key={index}
                      className="w-full text-left p-2 hover:bg-blue-100 rounded transition-colors flex items-center space-x-2"
                    >
                      <span>{doc.icon}</span>
                      <span className="text-blue-700 text-sm">{doc.title}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Community */}
              <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
                <h4 className="font-semibold text-purple-800 mb-4 flex items-center">
                  <span className="mr-2">👥</span> Community
                </h4>
                
                <div className="space-y-2">
                  {[
                    { title: "Discord Community", icon: "💬" },
                    { title: "GitHub Repository", icon: "🐙" },
                    { title: "Feature Requests", icon: "💡" },
                    { title: "User Forum", icon: "🗣️" }
                  ].map((link, index) => (
                    <button
                      key={index}
                      className="w-full text-left p-2 hover:bg-purple-100 rounded transition-colors flex items-center space-x-2"
                    >
                      <span>{link.icon}</span>
                      <span className="text-purple-700 text-sm">{link.title}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Send Feedback Modal Component
export const FeedbackModal = ({ isOpen, onClose, token }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    if (!e || !e.target) return;
    e.preventDefault();
    setIsSubmitting(true);

    const formData = new FormData(e.target);
    const feedbackData = {
      type: formData.get('type'),
      subject: formData.get('subject'),
      message: formData.get('message')
    };

    try {
      const response = await axios.post(`${API}/feedback/send`, feedbackData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.data.success) {
        alert('✅ Thank you for your feedback! We\'ll review it and get back to you soon.');
        onClose();
        e.target && e.target.reset();
      }
    } catch (error) {
      alert('❌ Failed to send feedback. Please try again or contact support directly.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-600 to-red-600 text-white p-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">💬 Send Feedback</h2>
              <p className="text-white/80 mt-1">Help us improve AI Agent Simulation</p>
            </div>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white text-2xl p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              {/* Feedback Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Feedback Type</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'bug', label: 'Bug Report', icon: '🐛', color: 'red' },
                    { value: 'feature', label: 'Feature Request', icon: '💡', color: 'blue' },
                    { value: 'general', label: 'General Feedback', icon: '💬', color: 'green' }
                  ].map((type) => (
                    <label key={type.value} className="cursor-pointer">
                      <input
                        type="radio"
                        name="type"
                        value={type.value}
                        defaultChecked={type.value === 'general'}
                        className="sr-only peer"
                      />
                      <div className="p-4 border-2 rounded-lg text-center transition-all border-gray-300 hover:border-orange-300 peer-checked:border-orange-500 peer-checked:bg-orange-50">
                        <div className="text-2xl mb-2">{type.icon}</div>
                        <div className="text-sm font-medium text-gray-700">{type.label}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Subject */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Subject</label>
                <input
                  type="text"
                  name="subject"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="Brief description of your feedback..."
                  required
                />
              </div>

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Message</label>
                <textarea
                  name="message"
                  rows="6"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                  placeholder="Please provide detailed feedback. For bug reports, include steps to reproduce the issue..."
                  required
                ></textarea>
              </div>

              {/* Additional Info */}
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-800 mb-2">📋 For Bug Reports, Please Include:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Steps to reproduce the issue</li>
                  <li>• What you expected to happen</li>
                  <li>• What actually happened</li>
                  <li>• Browser and operating system</li>
                  <li>• Screenshots (if applicable)</li>
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Sending...' : 'Send Feedback'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};