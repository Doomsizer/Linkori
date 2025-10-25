import { instance } from '../hooks/useAuth';

export const loginWithDiscord = async (accessToken) => {
    try {
        const response = await instance.get(`/accounts/discord/login/?state=${accessToken || ''}`);
        if (response.data.status === 'success') {
            return { url: response.data.url };
        }
        throw new Error('Не удалось получить URL для входа через Discord');
    } catch (error) {
        throw error;
    }
};

export const loginWithOsu = async (accessToken) => {
    try {
        const response = await instance.get(`/accounts/osu/login/?state=${accessToken || ''}`);
        if (response.data.status === 'success') {
            return { url: response.data.url };
        }
        throw new Error('Не удалось получить URL для входа через osu!');
    } catch (error) {
        throw error;
    }
};

export const handleDiscordCallback = async (code) => {
    try {
        const url = `/accounts/discord/callback/?code=${code || ''}`;
        const response = await instance.get(url);
        return response.data;
    } catch (error) {
        throw error;
    }
};

export const handleOsuCallback = async (code) => {
    try {
        const url = `/accounts/osu/callback/?code=${code || ''}`;
        const response = await instance.get(url);
        return response.data;
    } catch (error) {
        throw error;
    }
};