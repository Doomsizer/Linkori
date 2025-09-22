import { instance } from '../hooks/useAuth';

export const loginWithDiscord = async (accessToken) => {
    try {
        const response = await instance.get(`/accounts/discord/login/?state=${accessToken || ''}`);
        console.log('Response from Discord login:', response.data);
        if (response.data.status === 'success') {
            return { url: response.data.url };
        }
        throw new Error('Не удалось получить URL для входа через Discord');
    } catch (error) {
        console.error('Ошибка при получении URL для Discord:', error);
        throw error;
    }
};

export const loginWithOsu = async (accessToken) => {
    try {
        const response = await instance.get(`/accounts/osu/login/?state=${accessToken || ''}`);
        console.log('Response from osu! login:', response.data);
        if (response.data.status === 'success') {
            return { url: response.data.url };
        }
        throw new Error('Не удалось получить URL для входа через osu!');
    } catch (error) {
        console.error('Ошибка при получении URL для osu!:', error);
        throw error;
    }
};

export const handleDiscordCallback = async (code) => {
    try {
        const url = `/accounts/discord/callback/?code=${code || ''}`;
        const response = await instance.get(url);
        console.log('Callback response from Discord:', response.data);
        return response.data;
    } catch (error) {
        console.error('Ошибка при обработке callback Discord:', error);
        throw error;
    }
};

export const handleOsuCallback = async (code) => {
    try {
        const url = `/accounts/osu/callback/?code=${code || ''}`;
        const response = await instance.get(url);
        console.log('Callback response from osu!:', response.data);
        return response.data;
    } catch (error) {
        console.error('Ошибка при обработке callback osu!:', error);
        throw error;
    }
};