import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [oauthError, setOauthError] = useState(null);

  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    // Check for OAuth callback parameters in URL
    const urlParams = new URLSearchParams(window.location.search);
    const oauthToken = urlParams.get('token');
    const oauthErrorParam = urlParams.get('error');

    if (oauthToken) {
      // OAuth callback with token - store it and validate
      localStorage.setItem('token', oauthToken);
      setToken(oauthToken);
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      validateTokenWithValue(oauthToken);
    } else if (oauthErrorParam) {
      // OAuth callback with error
      setOauthError(oauthErrorParam === 'oauth_failed' ? 'OAuth login failed. Please try again.' : oauthErrorParam);
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      setLoading(false);
    } else if (token) {
      // Normal token validation
      validateToken();
    } else {
      setLoading(false);
    }
  }, []);

  const validateToken = async () => {
    try {
      const response = await fetch(`${backendBaseUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token invalid, clear it
        logout();
      }
    } catch (error) {
      console.error('Token validation error:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const validateTokenWithValue = async (tokenValue) => {
    try {
      const response = await fetch(`${backendBaseUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${tokenValue}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token invalid, clear it
        logout();
      }
    } catch (error) {
      console.error('Token validation error:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${backendBaseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);

    // Fetch user info
    const userResponse = await fetch(`${backendBaseUrl}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${data.access_token}`
      }
    });
    const userData = await userResponse.json();
    setUser(userData);

    return data;
  };

  const register = async (username, password, email = null) => {
    const response = await fetch(`${backendBaseUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password, email }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    // Auto-login after registration
    await login(username, password);
    return data;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  const oauthLogin = (provider) => {
    // Redirect to backend OAuth endpoint
    window.location.href = `${backendBaseUrl}/auth/${provider}`;
  };

  const clearOauthError = () => {
    setOauthError(null);
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    oauthLogin,
    oauthError,
    clearOauthError,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
