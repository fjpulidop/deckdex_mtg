import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: number;
  email: string;
  display_name?: string;
  avatar_url?: string;
  is_admin?: boolean;
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
    const response = await fetch('/api/auth/me', {
      credentials: 'include',
    });
    if (response.ok) {
      const data = await response.json();
      // Backend returns { id, email, display_name, picture, is_admin } — map picture → avatar_url
      return {
        id: data.id,
        email: data.email,
        display_name: data.display_name,
        avatar_url: data.picture ?? data.avatar_url,
        is_admin: data.is_admin ?? false,
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
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    } catch (error) {
      console.error('Error during logout:', error);
    }
    setUser(null);
    window.location.href = '/';
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
