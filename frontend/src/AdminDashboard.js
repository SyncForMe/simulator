import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminDashboard = ({ token, onClose }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [recentActivity, setRecentActivity] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchDashboardStats();
    } else if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'activity') {
      fetchRecentActivity();
    }
  }, [activeTab]);

  const fetchDashboardStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/dashboard/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      setError('Failed to fetch dashboard stats');
      console.error('Dashboard stats error:', error);
    }
    setLoading(false);
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/users?limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data.users);
    } catch (error) {
      setError('Failed to fetch users');
      console.error('Users fetch error:', error);
    }
    setLoading(false);
  };

  const fetchRecentActivity = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/activity/recent?hours=24`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecentActivity(response.data);
    } catch (error) {
      setError('Failed to fetch recent activity');
      console.error('Activity fetch error:', error);
    }
    setLoading(false);
  };

  const fetchUserDetails = async (userId) => {
    try {
      const response = await axios.get(`${API}/admin/user/${userId}/details`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedUser(response.data);
    } catch (error) {
      setError('Failed to fetch user details');
      console.error('User details error:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const StatCard = ({ title, value, subtitle, icon, color = 'blue' }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-3xl font-bold text-${color}-600`}>{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`w-12 h-12 bg-${color}-100 rounded-lg flex items-center justify-center`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold">Admin Dashboard</h2>
              <p className="text-purple-100 mt-1">Observer AI Platform Analytics</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors text-2xl"
            >
              ×
            </button>
          </div>

          {/* Tab Navigation */}
          <div className="mt-6 flex space-x-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'bg-white text-purple-600'
                  : 'text-purple-100 hover:text-white hover:bg-purple-500'
              }`}
            >
              📊 Overview
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'users'
                  ? 'bg-white text-purple-600'
                  : 'text-purple-100 hover:text-white hover:bg-purple-500'
              }`}
            >
              👥 Users
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'activity'
                  ? 'bg-white text-purple-600'
                  : 'text-purple-100 hover:text-white hover:bg-purple-500'
              }`}
            >
              ⚡ Activity
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
              <span className="ml-3 text-gray-600">Loading...</span>
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && dashboardData && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard
                      title="Total Users"
                      value={dashboardData.overview.total_users}
                      subtitle={`${dashboardData.overview.recent_users} new this month`}
                      icon="👥"
                      color="blue"
                    />
                    <StatCard
                      title="Active Users"
                      value={dashboardData.overview.active_users}
                      subtitle="Last 7 days"
                      icon="⚡"
                      color="green"
                    />
                    <StatCard
                      title="Total Conversations"
                      value={dashboardData.overview.total_conversations}
                      subtitle="AI interactions"
                      icon="💬"
                      color="purple"
                    />
                    <StatCard
                      title="Documents Created"
                      value={dashboardData.overview.total_documents}
                      subtitle="Generated by agents"
                      icon="📄"
                      color="orange"
                    />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <StatCard
                      title="Total Agents"
                      value={dashboardData.overview.total_agents}
                      subtitle="Active in simulations"
                      icon="🤖"
                      color="indigo"
                    />
                    <StatCard
                      title="Saved Agents"
                      value={dashboardData.overview.total_saved_agents}
                      subtitle="User-created agents"
                      icon="⭐"
                      color="pink"
                    />
                  </div>

                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Platform Health</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {Math.round((dashboardData.overview.active_users / dashboardData.overview.total_users) * 100)}%
                        </div>
                        <div className="text-sm text-gray-600">User Engagement</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {Math.round(dashboardData.overview.total_documents / dashboardData.overview.total_users)}
                        </div>
                        <div className="text-sm text-gray-600">Docs per User</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {Math.round(dashboardData.overview.total_conversations / dashboardData.overview.total_users)}
                        </div>
                        <div className="text-sm text-gray-600">Conversations per User</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Users Tab */}
              {activeTab === 'users' && (
                <div className="space-y-6">
                  <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-4 border-b border-gray-200">
                      <h3 className="text-xl font-bold text-gray-900">User Management</h3>
                      <p className="text-gray-600">Manage and monitor user accounts</p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Auth Type</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Activity</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {users.map((user) => (
                            <tr key={user.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div>
                                  <div className="text-sm font-medium text-gray-900">{user.name}</div>
                                  <div className="text-sm text-gray-500">{user.email}</div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                  user.auth_type === 'email' 
                                    ? 'bg-blue-100 text-blue-800' 
                                    : 'bg-green-100 text-green-800'
                                }`}>
                                  {user.auth_type === 'email' ? 'Email' : 'Google'}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                <div className="flex space-x-4">
                                  <span>📄 {user.stats.documents}</span>
                                  <span>🤖 {user.stats.saved_agents}</span>
                                  <span>💬 {user.stats.conversations}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatDate(user.last_login)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <button
                                  onClick={() => fetchUserDetails(user.id)}
                                  className="text-purple-600 hover:text-purple-900"
                                >
                                  View Details
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* User Details Modal */}
                  {selectedUser && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-y-auto">
                        <div className="p-6 border-b border-gray-200">
                          <div className="flex items-center justify-between">
                            <h3 className="text-xl font-bold text-gray-900">User Details</h3>
                            <button
                              onClick={() => setSelectedUser(null)}
                              className="text-gray-400 hover:text-gray-600"
                            >
                              ×
                            </button>
                          </div>
                        </div>
                        <div className="p-6 space-y-6">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                              <h4 className="font-semibold text-gray-900 mb-2">User Information</h4>
                              <div className="space-y-2 text-sm">
                                <p><strong>Name:</strong> {selectedUser.user.name}</p>
                                <p><strong>Email:</strong> {selectedUser.user.email}</p>
                                <p><strong>Joined:</strong> {formatDate(selectedUser.user.created_at)}</p>
                                <p><strong>Last Login:</strong> {formatDate(selectedUser.user.last_login)}</p>
                                <p><strong>Auth Type:</strong> {selectedUser.user.auth_type}</p>
                              </div>
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-900 mb-2">Activity Summary</h4>
                              <div className="space-y-2 text-sm">
                                <p><strong>Total Documents:</strong> {selectedUser.activity.total_documents}</p>
                                <p><strong>Total Saved Agents:</strong> {selectedUser.activity.total_saved_agents}</p>
                                <p><strong>Recent Documents:</strong> {selectedUser.activity.recent_documents}</p>
                                <p><strong>Recent Agents:</strong> {selectedUser.activity.recent_agents}</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                              <h4 className="font-semibold text-gray-900 mb-2">Recent Documents</h4>
                              <div className="space-y-2">
                                {selectedUser.recent_documents.map((doc) => (
                                  <div key={doc.id} className="text-sm bg-gray-50 p-2 rounded">
                                    <div className="font-medium">{doc.title}</div>
                                    <div className="text-gray-600">{doc.category} • {formatDate(doc.created_at)}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-900 mb-2">Recent Agents</h4>
                              <div className="space-y-2">
                                {selectedUser.recent_agents.map((agent) => (
                                  <div key={agent.id} className="text-sm bg-gray-50 p-2 rounded">
                                    <div className="font-medium">{agent.name}</div>
                                    <div className="text-gray-600">{agent.archetype} • {formatDate(agent.created_at)}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Activity Tab */}
              {activeTab === 'activity' && recentActivity && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Users</h3>
                      <div className="space-y-3">
                        {recentActivity.recent_users.slice(0, 5).map((user) => (
                          <div key={user.id} className="flex items-center justify-between">
                            <div>
                              <div className="font-medium text-sm">{user.name}</div>
                              <div className="text-xs text-gray-500">{user.email}</div>
                            </div>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              user.auth_type === 'email' 
                                ? 'bg-blue-100 text-blue-600' 
                                : 'bg-green-100 text-green-600'
                            }`}>
                              {user.auth_type}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Documents</h3>
                      <div className="space-y-3">
                        {recentActivity.recent_documents.slice(0, 5).map((doc) => (
                          <div key={doc.id} className="text-sm">
                            <div className="font-medium">{doc.title}</div>
                            <div className="text-gray-500">{doc.category}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                      <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Agents</h3>
                      <div className="space-y-3">
                        {recentActivity.recent_agents.slice(0, 5).map((agent) => (
                          <div key={agent.id} className="text-sm">
                            <div className="font-medium">{agent.name}</div>
                            <div className="text-gray-500">{agent.archetype}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;