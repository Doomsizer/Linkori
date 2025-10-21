import React, { useState, useEffect } from "react";
import styles from "../../styles/Header.module.css"
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";

const Header = () => {
    const { accessToken, logout } = useAuth();
    const navigate = useNavigate();
    const [userData, setUserData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUserData = async () => {
            if (!accessToken) {
                setLoading(false);
                return;
            }

            try {
                const response = await fetch('https://127.0.0.1:8000/accounts/user/', {
                    headers: { Authorization: `Bearer ${accessToken}` },
                    credentials: 'include',
                });

                if (response.ok) {
                    const data = await response.json();
                    setUserData(data);
                } else {
                    console.error('Не удалось загрузить данные пользователя');
                }
            } catch (error) {
                console.error('Ошибка при загрузке данных пользователя:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchUserData();
    }, [accessToken]);

    const toMainpage = () => {
        navigate("/");
    };

    const toProfile = () => {
        navigate("/profile");
    };

    return (
        <header>
            <button className={styles.logo} onClick={toMainpage}>Linkori</button>
            {loading ? (
                <LoadingSpinner/>
            ) : accessToken && userData ? (
                <div className={styles.userContainer}>
                    <div className={styles.userInfo} onClick={toProfile}>
                        <img
                            src={userData.displayed_avatar_url}
                            alt="Avatar"
                            className={styles.userAvatar}
                        />
                        <span>{userData.displayed_nick}</span>
                    </div>
                    <button className={styles.logoutBtn} onClick={logout}>
                        Выйти
                    </button>
                </div>
            ) : (
                <button
                    className={styles.loginBtn}
                    onClick={() => navigate('/login')}
                >
                    Войти
                </button>
            )}
        </header>
    );
};

export default Header;