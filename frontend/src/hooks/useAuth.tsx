import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import axios from 'axios';

// Add axios type declarations
declare module 'axios';

// Use relative path for API calls
const API_URL = '';

interface User {
  id: number;
  login: string;
  email: string;
  first_name: string;
  last_name: string;
  company?: string;
  language_code: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (userData: {
    login: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    company?: string;
  }) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  const login = useCallback(async (username: string, password: string) => {
    console.log('Attempting to login with:', { username, password: '***' });
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      console.log('Sending login request to:', `${API_URL}/api/auth/token`);
      const response = await axios.post(`${API_URL}/api/auth/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      console.log('Login response:', response.data);
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);

      // Add a small delay before making the /me request
      await new Promise(resolve => setTimeout(resolve, 1000));

      try {
        console.log('Fetching user data from:', `${API_URL}/api/auth/me`);
        // Get user data
        const userResponse = await axios.get(`${API_URL}/api/auth/me`);
        console.log('User data response:', userResponse.data);
        setUser(userResponse.data);
      } catch (error: any) {
        console.error('Error fetching user data:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          headers: error.response?.headers,
          config: error.config
        });
        // If we can't get user data, we should still consider the user logged in
        // as they have a valid token
        setUser({
          id: 0,
          login: username,
          email: '',
          first_name: '',
          last_name: '',
          language_code: 'en'
        });
      }
    } catch (error: any) {
      console.error('Login error:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers,
        config: error.config
      });
      throw error;
    }
  }, []);

  const register = useCallback(async (userData: {
    login: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    company?: string;
  }) => {
    console.log('Attempting to register with data:', {
      ...userData,
      password: '***' // Не логируем пароль
    });
  
    try {
      const response = await axios.post(`${API_URL}/api/auth/register`, {
        login: userData.login,
        email: userData.email,
        password: userData.password,
        first_name: userData.first_name,
        last_name: userData.last_name,
        company: userData.company,
        language_code: 'en' // Добавляем язык по умолчанию
      });
      console.log('Registration successful:', response.data);
      // After successful registration, log the user in
      await login(userData.login, userData.password);
    } catch (error: any) {
      console.error('Registration error:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
      throw error;
    }
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  }, []);

  const value = {
    user,
    token,
    login,
    register,
    logout,
    isAuthenticated: !!token,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider and only there');
  }
  return context;
} 