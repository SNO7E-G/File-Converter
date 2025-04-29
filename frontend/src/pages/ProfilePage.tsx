import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useError } from '../context/ErrorContext';

const ProfilePage: React.FC = () => {
  const { user, updateUser, logout } = useAuth();
  const { addError } = useError();
  
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Load user data
  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setEmail(user.email);
    }
  }, [user]);
  
  // Handle saving profile changes
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!user) return;
    
    // Basic validation
    if (!username || !email) {
      addError('Username and email are required', 'error');
      return;
    }
    
    setIsLoading(true);
    
    try {
      await updateUser({
        username,
        email
      });
      setIsEditing(false);
      addError('Profile updated successfully', 'success');
    } catch (error: any) {
      addError(
        error.message || 'Failed to update profile',
        'error',
        error.details ? JSON.stringify(error.details) : undefined
      );
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle password change - redirect to dedicated password change page
  const handlePasswordChange = () => {
    // This would typically navigate to a password change page
    addError('Password change feature will be implemented soon', 'info');
  };
  
  // Handle account logout
  const handleLogout = async () => {
    try {
      await logout();
      // No need to navigate, AuthContext will handle redirect
    } catch (error: any) {
      addError('Error logging out', 'error');
    }
  };
  
  if (!user) {
    return <div>Loading user profile...</div>;
  }
  
  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">My Profile</h1>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Account Information</h2>
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Edit Profile
            </button>
          ) : (
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          )}
        </div>
        
        {isEditing ? (
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="username" className="block text-gray-700 font-medium mb-2">
                Username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <div className="mb-4">
              <label htmlFor="email" className="block text-gray-700 font-medium mb-2">
                Email
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className={`px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 ${
                isLoading ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        ) : (
          <div>
            <div className="mb-4">
              <p className="text-gray-600">Username</p>
              <p className="font-medium">{user.username}</p>
            </div>
            
            <div className="mb-4">
              <p className="text-gray-600">Email</p>
              <p className="font-medium">{user.email}</p>
            </div>
            
            <div className="mb-4">
              <p className="text-gray-600">Account Type</p>
              <p className="font-medium capitalize">{user.plan || 'Basic'}</p>
            </div>
            
            <div className="mb-4">
              <p className="text-gray-600">Member Since</p>
              <p className="font-medium">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        )}
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Security</h2>
        <button
          onClick={handlePasswordChange}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 mr-3"
        >
          Change Password
        </button>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 text-red-600">Danger Zone</h2>
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Log Out
        </button>
      </div>
    </div>
  );
};

export default ProfilePage; 