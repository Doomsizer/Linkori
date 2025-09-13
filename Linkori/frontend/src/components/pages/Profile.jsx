import React, { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { loginWithDiscord, loginWithOsu } from '../services/AuthService';
import '../../styles/Profile.css';

const Profile = () => {
    const { accessToken, logout } = useAuth();
    const [userData, setUserData] = useState({ discord: null, osu: null });
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchUserData = async () => {
            try {
                console.log('Sending fetch with token:', accessToken);
                const response = await fetch('https://127.0.0.1:8000/accounts/user/', {
                    headers: { Authorization: `Bearer ${accessToken}` },
                    credentials: 'include',
                });
                console.log('Fetch response status:', response.status);
                if (response.ok) {
                    const data = await response.json();
                    setUserData({
                        discord: data.discord_user ? data.discord_user.nick : null,
                        osu: data.osu_user ? data.osu_user.osu.nick : null,
                    });
                } else {
                    setError('Не удалось загрузить данные пользователя');
                }
            } catch (error) {
                console.error('Fetch error:', error);
                setError('Ошибка при загрузке данных');
            }
        };

        if (accessToken) {
            fetchUserData();
        }
    }, [accessToken]);

    const handleLinkDiscord = async () => {
        try {
            const { url } = await loginWithDiscord(accessToken);
            window.location.href = url;
        } catch (error) {
            setError('Ошибка при привязке Discord');
        }
    };

    const handleLinkOsu = async () => {
        try {
            const { url } = await loginWithOsu(accessToken);
            window.location.href = url;
        } catch (error) {
            setError('Ошибка при привязке osu!');
        }
    };

    return (
        <div className="profile-container">
            <h2>Профиль</h2>
            {error && <p className="error-message">{error}</p>}
            {accessToken ? (
                <>
                    <p>Вы авторизованы!</p>
                    <p>Discord: {userData.discord || 'Не привязан'}</p>
                    <p>osu!: {userData.osu || 'Не привязан'}</p>
                    {!userData.discord && (
                        <button className="link-button" onClick={handleLinkDiscord}>
                            Привязать Discord
                        </button>
                    )}
                    {!userData.osu && (
                        <button className="link-button" onClick={handleLinkOsu}>
                            Привязать osu!
                        </button>
                    )}
                    <button className="logout-button" onClick={logout}>
                        Выйти
                    </button>
                </>
            ) : (
                <p>Пожалуйста, войдите в систему.</p>
            )}
        </div>
    );
};

export default Profile;