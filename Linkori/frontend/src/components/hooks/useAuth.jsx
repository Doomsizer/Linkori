import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { refreshToken } from '../services/AuthService';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [accessToken, setAccessToken] = useState(localStorage.getItem('accessToken') || null);
    const [rebindModal, setRebindModal] = useState({ open: false, provider: null, providerId: null });

    const setTokens = useCallback(({ accessToken }) => {
        console.log('Setting accessToken:', accessToken);
        setAccessToken(accessToken);
        localStorage.setItem('accessToken', accessToken);
    }, []);

    const logout = useCallback(() => {
        console.log('Logging out');
        setAccessToken(null);
        localStorage.removeItem('accessToken');
        document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    }, []);

    const refreshAccessToken = useCallback(async () => {
        try {
            console.log('Attempting to refresh access token');
            const response = await refreshToken();
            if (response.access) {
                console.log('Refreshed accessToken:', response.access);
                setTokens({ accessToken: response.access });
                return response.access;
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
        }
    }, [setTokens]);

    useEffect(() => {
        if (!accessToken) {
            refreshAccessToken();
        }
    }, [accessToken, refreshAccessToken]);

    const openRebindModal = useCallback((provider, providerId) => {
        setRebindModal({ open: true, provider, providerId });
    }, []);

    const closeRebindModal = useCallback(() => {
        setRebindModal({ open: false, provider: null, providerId: null });
    }, []);

    return (
        <AuthContext.Provider value={{ accessToken, setTokens, logout, refreshAccessToken, rebindModal, openRebindModal, closeRebindModal }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        console.error('useAuth must be used within an AuthProvider');
        return { accessToken: null, setTokens: () => {}, logout: () => {}, refreshAccessToken: () => {}, rebindModal: { open: false }, openRebindModal: () => {}, closeRebindModal: () => {} };
    }
    return context;
};