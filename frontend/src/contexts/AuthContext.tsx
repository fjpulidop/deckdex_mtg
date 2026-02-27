import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: number;
  email: string;
  display_name?: string;
  avatar_url?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  logout: async () => {},
  refreshUser: async () => {},
});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

async function fetchMe(): Promise<User | null> {
  try {
    const response = await fetch('http://localhost:8000/api/auth/me', {
      credentials: 'include',
    });
    if (response.ok) {
      const data = await response.json();
      // Backend returns { id, email, display_name, picture } — map picture → avatar_url
      return {
        id: data.id,
        email: data.email,
        display_name: data.display_name,
        avatar_url: data.picture ?? data.avatar_url,
      };
    }
    return null;
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchMe().then((u) => {
      setUser(u);
      setIsLoading(false);
    });
  }, []);

  const refreshUser = async () => {
    const u = await fetchMe();
    setUser(u);
  };

  const logout = async () => {
    try {
      await fetch('http://localhost:8000/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
      setUser(null);
      window.location.href = '/';
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
