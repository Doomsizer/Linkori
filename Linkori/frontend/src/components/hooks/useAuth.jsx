import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://127.0.0.1:8000';

export const instance = axios.create({
    baseURL: API_URL,
    withCredentials: true,
});

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [accessToken, setAccessToken] = useState(localStorage.getItem('accessToken') || null);
    const [isLinked, setIsLinked] = useState(false)
    const [isAuthenticated, setIsAuthenticated] = useState(null);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const setTokens = useCallback(({ accessToken }) => {
        if (accessToken) {
            localStorage.setItem('accessToken', accessToken);
            setAccessToken(accessToken);
            setIsAuthenticated(true);
        } else {
            localStorage.removeItem('accessToken');
            setAccessToken(null);
            setIsAuthenticated(false);
        }
        setIsRefreshing(false);
    }, []);

    const logout = useCallback(() => {
        setTokens({ accessToken: null });
    }, [setTokens]);

    const verifyToken = useCallback(async (token) => {
        if (!token || token.split('.').length !== 3) {
            return { isValid: false };
        }
        try {
            const response = await instance.post('/api/token/verify/', {}, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            return {
                isValid: true,
                isLinked: response.data.is_linked
            };
        } catch (error) {
            return { isValid: false };
        }
    }, []);

    useEffect(() => {
        const checkAuth = async () => {
            if (accessToken) {
                const result = await verifyToken(accessToken);
                if (result.isValid) {
                    setIsAuthenticated(true);
                    setIsLinked(result.isLinked);
                } else {
                    setIsLinked(false);
                    setIsRefreshing(true);
                    const newToken = await refreshAccessToken(setTokens, logout);
                    setIsAuthenticated(!!newToken);
                }
            } else {
                setIsLinked(false);
                setIsAuthenticated(false);
            }
        };

        checkAuth();
    }, []);

    return (
        <AuthContext.Provider value={{
            accessToken,
            isLinked,
            isAuthenticated,
            isRefreshing,
            setTokens,
            logout,
            refreshAccessToken: () => refreshAccessToken(setTokens, logout)
        }}>
            {children}
        </AuthContext.Provider>
    );
};

const refreshAccessToken = async (setTokens, logout, retryCount = 0) => {
    if (retryCount > 3) {
        logout();
        return null;
    }
    try {
        const response = await instance.post('/api/token/refresh/');
        if (response.data.access) {
            setTokens({ accessToken: response.data.access });
            return response.data.access;
        }
    } catch (error) {
        if (retryCount < 3) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            return refreshAccessToken(setTokens, logout, retryCount + 1);
        } else {
            logout();
            return null;
        }
    }
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};