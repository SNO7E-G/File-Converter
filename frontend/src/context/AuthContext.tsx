import React, { createContext, useState, useEffect, useCallback } from 'react';
import { jwtDecode } from 'jwt-decode';
import apiService, { rawApi, User } from '../utils/api';

// Define JwtPayload type
interface JwtPayload {
  exp?: number;
  sub?: string;
  user_id?: number;
  [key: string]: any;
}

// Define context type
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
  updateUser: (userData: Partial<User>) => Promise<void>;
  checkAuth: () => Promise<boolean>;
}

// Create context with default values
export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  refreshToken: async () => null,
  updateUser: async () => {},
  checkAuth: async () => false,
});

interface AuthProviderProps {
  children: React.ReactNode;
}

// Interface for auth response
interface AuthResponse {
  token: string;
  refreshToken: string;
  user: User;
  message: string;
}

// Local storage keys
const TOKEN_KEY = 'token';
const REFRESH_TOKEN_KEY = 'refreshToken';
const USER_KEY = 'user_data';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshInProgress, setRefreshInProgress] = useState(false);
  const [refreshPromise, setRefreshPromise] = useState<Promise<string | null> | null>(null);

  // Check if token is valid
  const isTokenValid = (token: string): boolean => {
    try {
      const decoded = jwtDecode<JwtPayload>(token);
      const currentTime = Date.now() / 1000;
      
      // Add a 30-second buffer to consider token as expired
      // This prevents edge cases where token expires during API call
      return (decoded.exp ?? 0) > (currentTime + 30);
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  };

  // Save auth data to local storage
  const saveAuthData = (data: { token: string; refreshToken: string; user: User }) => {
    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refreshToken);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  };

  // Clear auth data from local storage
  const clearAuthData = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  // Function to refresh the token
  const refreshTokenFn = useCallback(async (): Promise<string | null> => {
    // If refresh is already in progress, return the existing promise
    if (refreshInProgress && refreshPromise) {
      return refreshPromise;
    }
    
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    
    if (!refreshToken) {
      return null;
    }

    try {
      setRefreshInProgress(true);
      
      // Create a refresh promise
      const promise = (async () => {
        try {
          // Create a one-time instance with the refresh token for this particular call
          const refreshResponse = await rawApi.post('/api/auth/refresh', {}, {
            headers: {
              Authorization: `Bearer ${refreshToken}`
            }
          });
          
          const { token: newToken, refreshToken: newRefreshToken } = refreshResponse.data;
          
          // Store both the new token and refresh token
          localStorage.setItem(TOKEN_KEY, newToken);
          
          // Only update refresh token if a new one was provided
          if (newRefreshToken) {
            localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
          }
          
          // Return the new token
          return newToken;
        } catch (error) {
          // Clear tokens on failure
          clearAuthData();
          setUser(null);
          console.error('Token refresh failed:', error);
          return null;
        } finally {
          setRefreshInProgress(false);
          setRefreshPromise(null);
        }
      })();
      
      setRefreshPromise(promise);
      return promise;
    } catch (error) {
      // Clear tokens on failure
      clearAuthData();
      setUser(null);
      console.error('Token refresh failed:', error);
      setRefreshInProgress(false);
      setRefreshPromise(null);
      return null;
    }
  }, [refreshInProgress, refreshPromise]);

  // Check authentication status
  const checkAuth = useCallback(async (): Promise<boolean> => {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      
      // If no token, user is not authenticated
      if (!token) {
        return false;
      }
      
      // If token is invalid, try to refresh it
      if (!isTokenValid(token)) {
        const newToken = await refreshTokenFn();
        if (!newToken) {
          return false;
        }
      }
      
      // Fetch user data
      try {
        const userData = await apiService.get<{user: User}>('/api/auth/me');
        if (userData && userData.user) {
          setUser(userData.user);
          
          // Update local storage with latest user data
          localStorage.setItem(USER_KEY, JSON.stringify(userData.user));
          
          return true;
        }
        return false;
      } catch (error) {
        // If API call fails, check if it's due to auth issues
        if (error.response && error.response.status === 401) {
          clearAuthData();
          setUser(null);
        }
        console.error('Error fetching user data:', error);
        return false;
      }
    } catch (error) {
      console.error('Authentication check failed:', error);
      clearAuthData();
      setUser(null);
      return false;
    }
  }, [refreshTokenFn, isTokenValid]);

  // Initialize auth state from local storage
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      
      try {
        // Try to load cached user data while checking auth
        const cachedUserData = localStorage.getItem(USER_KEY);
        if (cachedUserData) {
          try {
            setUser(JSON.parse(cachedUserData));
          } catch (e) {
            console.error('Error parsing cached user data:', e);
          }
        }
        
        // Check full authentication
        await checkAuth();
      } catch (error) {
        console.error('Auth initialization error:', error);
        clearAuthData();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
    
    // Set up a timer to check token validity periodically
    const tokenCheckInterval = setInterval(() => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token && !isTokenValid(token)) {
        refreshTokenFn().catch(console.error);
      }
    }, 5 * 60 * 1000); // Check every 5 minutes
    
    return () => {
      clearInterval(tokenCheckInterval);
    };
  }, [checkAuth, refreshTokenFn, isTokenValid]);

  // Login function
  const login = async (email: string, password: string, rememberMe = false) => {
    try {
      const authData = await apiService.post<AuthResponse>('/api/auth/login', { 
        email, 
        password,
        remember_me: rememberMe
      });
      
      const { token, refreshToken, user } = authData;
      
      // Save auth data
      saveAuthData({ token, refreshToken, user });
      
      // Set user state
      setUser(user);
    } catch (error) {
      throw error;
    }
  };

  // Register function
  const register = async (username: string, email: string, password: string) => {
    try {
      const authData = await apiService.post<AuthResponse>('/api/auth/register', {
        username,
        email,
        password
      });
      
      const { token, refreshToken, user } = authData;
      
      // Save auth data
      saveAuthData({ token, refreshToken, user });
      
      // Set user state
      setUser(user);
    } catch (error) {
      throw error;
    }
  };

  // Update user function
  const updateUser = async (userData: Partial<User>) => {
    try {
      const updatedUser = await apiService.put<{user: User}>('/api/user/profile', userData);
      
      if (updatedUser && updatedUser.user) {
        // Update local state and storage
        setUser(prevUser => prevUser ? { ...prevUser, ...updatedUser.user } : updatedUser.user);
        
        // Update cached user data
        const cachedUserData = localStorage.getItem(USER_KEY);
        if (cachedUserData) {
          try {
            const parsedUser = JSON.parse(cachedUserData);
            localStorage.setItem(USER_KEY, JSON.stringify({ ...parsedUser, ...updatedUser.user }));
          } catch (e) {
            console.error('Error updating cached user data:', e);
          }
        }
      }
    } catch (error) {
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      
      // Attempt to invalidate token on server (best effort)
      if (refreshToken) {
        try {
          await apiService.post('/api/auth/logout', { refresh_token: refreshToken });
        } catch (error) {
          console.warn('Error during logout:', error);
          // Continue with local logout even if server request fails
        }
      }
    } finally {
      // Always clear local auth data
      clearAuthData();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshToken: refreshTokenFn,
        updateUser,
        checkAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}; 