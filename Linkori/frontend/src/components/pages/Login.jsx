import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { loginWithDiscord, loginWithOsu, handleDiscordCallback, handleOsuCallback } from '../services/AuthService';
import discordLogo from "../../media/discord.svg"
import osuLogo from "../../media/osu.svg"
import styles from '../../styles/Login.module.css';

const Login = () => {
    const { accessToken, setTokens } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [error, setError] = useState(null);

    useEffect(() => {
        const handleCallback = async () => {
            const params = new URLSearchParams(location.search);
            const code = params.get('code');
            const access = params.get('access');
            const path = location.pathname;

            console.log('Location:', location);
            console.log('Path:', path, 'Code:', code, 'Access:', access);

            if (access) {
                console.log('Calling setTokens with access:', access);
                setTokens({ accessToken: access });
                navigate('/profile');
            } else if (code) {
                try {
                    let tokens;
                    if (path.includes('callback/discord')) {
                        console.log('Processing Discord callback with code:', code);
                        tokens = await handleDiscordCallback(code);
                    } else if (path.includes('callback/osu')) {
                        console.log('Processing osu! callback with code:', code);
                        tokens = await handleOsuCallback(code);
                    }

                    if (tokens.status === 'success') {
                        console.log('Calling setTokens with tokens.access:', tokens.access);
                        setTokens({ accessToken: tokens.access });
                        navigate('/profile');
                    } else {
                        console.error('Не удалось получить токены:', tokens.message);
                        setError(tokens.message);
                        navigate('/login');
                    }
                } catch (error) {
                    console.error('Ошибка при обработке callback:', error);
                    setError('Ошибка авторизации');
                    navigate('/login');
                }
            }
        };

        handleCallback();
    }, [location, navigate, setTokens, accessToken]);

    const handleDiscordLogin = async () => {
        try {
            const { url } = await loginWithDiscord();
            console.log('Redirecting to Discord:', url);
            window.location.href = url;
        } catch (error) {
            console.error('Ошибка при инициации входа через Discord:', error);
            setError('Ошибка при входе через Discord');
        }
    };

    const handleOsuLogin = async () => {
        try {
            const { url } = await loginWithOsu();
            console.log('Redirecting to osu!:', url);
            window.location.href = url;
        } catch (error) {
            console.error('Ошибка при инициации входа через osu!:', error);
            setError('Ошибка при входе через osu!');
        }
    };

    return (
        <main>
            <h2>Авторизация</h2>
            <p className={styles.info}>
                Для использования сервиса вам потребуется войти через ваши osu! и discord аккаунты.<br/>
                <a href="/data-privacy/">Данные</a>, получаемые с верификации являются публично доступными. <br/> Вы всегда можете отозвать привязку
                в настройках osu! или discord.
            </p>
            {error && <span className={styles.errorMessage}>{error}</span>}
            <button className={`${styles.button} ${styles.buttonDiscord}`} onClick={handleDiscordLogin}>
                Войти через<img src={discordLogo} alt="" height="40px" width="40px"/>
            </button>
            <button className={`${styles.button} ${styles.buttonOsu}`} onClick={handleOsuLogin}>
                Войти через<img src={osuLogo} alt="" width="40px" height="40px"/>
            </button>
        </main>
    );
};

export default Login;