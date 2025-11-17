import React, { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL;

export const instance = axios.create({
    baseURL: API_URL,
    withCredentials: true,
    timeout: 10000,
});

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [accessToken, setAccessToken] = useState(null);
    const [isLinked, setIsLinked] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(null);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const setTokens = useCallback(async ({ accessToken }) => {
        if (accessToken) {
            localStorage.setItem('accessToken', accessToken);
            setAccessToken(accessToken);
            setIsAuthenticated(true);

            const result = await verifyToken(accessToken);
            if (result.isValid) {
                setIsLinked(result.isLinked || false);
            } else {
                logout();
            }
        } else {
            localStorage.removeItem('accessToken');
            setAccessToken(null);
            setIsAuthenticated(false);
            setIsLinked(false);
        }
        setIsRefreshing(false);
    }, [verifyToken, logout]);

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
            const storedToken = localStorage.getItem('accessToken');
            if (storedToken) {
                const result = await verifyToken(storedToken);
                if (result.isValid) {
                    setAccessToken(storedToken);
                    setIsAuthenticated(true);
                    setIsLinked(result.isLinked || false);
                } else {
                    setIsRefreshing(true);
                    const newToken = await refreshAccessToken(setTokens, logout);
                    if (newToken) {
                        const refreshResult = await verifyToken(newToken);
                        if (refreshResult.isValid) {
                            await setTokens({ accessToken: newToken });
                            setIsLinked(refreshResult.isLinked || false);
                        } else {
                            logout();
                        }
                    } else {
                        setIsAuthenticated(false);
                        setIsLinked(false);
                    }
                }
            } else {
                setIsAuthenticated(false);
                setIsLinked(false);
            }
        };

        checkAuth();
    }, [setTokens, logout, verifyToken]);

    const refresh = useCallback(async () => {
        setIsRefreshing(true);
        try {
            return await refreshAccessToken(setTokens, logout);
        } finally {
            setIsRefreshing(false);
        }
    }, [setTokens, logout]);

    const value = useMemo(() => ({
        accessToken,
        isLinked,
        isAuthenticated,
        isRefreshing,
        setTokens,
        logout,
        refreshAccessToken: refresh
    }), [accessToken, isLinked, isAuthenticated, isRefreshing, setTokens, logout, refresh]);

    return (
        <AuthContext.Provider value={value}>
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
            await setTokens({ accessToken: response.data.access });
            return response.data.access;
        }
    } catch (error) {
        if (error.response?.status === 401) {
            logout();
            return null;
        }
        if (retryCount < 3) {
            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount)));
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