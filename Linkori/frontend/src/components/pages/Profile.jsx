import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { loginWithDiscord, loginWithOsu } from '../services/AuthService';
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import styles from "../../styles/Profile.module.css";
import discordLogo from "../../media/discord.svg";
import osuLogo from "../../media/osu.svg";

const Profile = () => {
    const { accessToken, logout } = useAuth();
    const [userData, setUserData] = useState({
        discord_user: null,
        osu_user: null,
        avatar_source: '',
        nick_source: '',
        region: '',
        city: '',
        region_display: '',
        city_display: '',
        displayed_avatar_url: null,
        displayed_nick: null
    });
    const [regions, setRegions] = useState([]);
    const [cities, setCities] = useState([]);
    const [selectedAvatarSource, setSelectedAvatarSource] = useState('');
    const [selectedNickSource, setSelectedNickSource] = useState('');
    const [selectedRegion, setSelectedRegion] = useState('');
    const [selectedCity, setSelectedCity] = useState('');
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [loading, setLoading] = useState(false);
    const [initialLoadComplete, setInitialLoadComplete] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    useEffect(() => {
        if (success) {
            const timer = setTimeout(() => setSuccess(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [success]);

    const getDisplayedAvatarUrl = (avatarSource, userData) => {
        if (avatarSource === 'osu' && userData.osu_user) {
            return userData.osu_user.osu.avatar_url;
        } else if (avatarSource === 'discord' && userData.discord_user) {
            const avatar = userData.discord_user.avatar;
            if (!avatar) return null;
            const ext = avatar.startsWith('a_') ? '.gif' : '.png';
            return `https://cdn.discordapp.com/avatars/${userData.discord_user.discord_id}/${avatar}${ext}?size=128`;
        }
        return null;
    };

    const getDisplayedNick = (nickSource, userData) => {
        if (nickSource === 'osu' && userData.osu_user) {
            return userData.osu_user.osu.nick;
        } else if (nickSource === 'discord_username' && userData.discord_user) {
            return userData.discord_user.nick;
        } else if (nickSource === 'discord_display_name' && userData.discord_user) {
            return userData.discord_user.display_name;
        }
        return null;
    };

    const fetchCities = useCallback(async (regionCode) => {
        if (!accessToken || !regionCode) return;
        setLoading(true);
        try {
            const res = await fetch(`https://127.0.0.1:8000/accounts/cities/?region=${regionCode}`, {
                headers: { Authorization: `Bearer ${accessToken}` },
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                setCities(data.cities || []);
            } else {
                setCities([]);
                setError('Ошибка загрузки городов');
            }
        } catch (err) {
            setCities([]);
            setError('Ошибка при загрузке городов');
        }
        setLoading(false);
    }, [accessToken]);

    const fetchUserData = useCallback(async () => {
        if (!accessToken) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetch('https://127.0.0.1:8000/accounts/user/', {
                headers: { Authorization: `Bearer ${accessToken}` },
                credentials: 'include',
            });
            if (response.ok) {
                const data = await response.json();
                setUserData(data);

                let avatarSource = data.avatar_source;
                if (!avatarSource) {
                    avatarSource = data.osu_user && data.osu_user.osu.avatar_url ? 'osu' :
                        data.discord_user && data.discord_user.avatar ? 'discord' : '';
                }

                let nickSource = data.nick_source;
                if (!nickSource) {
                    nickSource = data.osu_user && data.osu_user.osu.nick ? 'osu' :
                        data.discord_user && data.discord_user.nick ? 'discord_username' : '';
                }

                setSelectedAvatarSource(avatarSource);
                setSelectedNickSource(nickSource);
                setSelectedRegion(data.region || '');
                setSelectedCity(data.city || '');

                if (data.region) {
                    await fetchCities(data.region);
                }
            } else {
                setError('Не удалось загрузить данные пользователя');
            }
        } catch (error) {
            setError('Ошибка при загрузке данных');
        }
        setLoading(false);
    }, [accessToken, fetchCities]);

    useEffect(() => {
        const fetchInitialData = async () => {
            if (!accessToken) return;

            try {
                const regionsRes = await fetch('https://127.0.0.1:8000/accounts/regions/', {
                });
                if (regionsRes.ok) {
                    const regionsData = await regionsRes.json();
                    setRegions(regionsData.regions || []);
                } else {
                    setError('Не удалось загрузить регионы');
                }
            } catch (err) {
                setError('Ошибка при загрузке регионов');
            }

            await fetchUserData();
            setInitialLoadComplete(true);
        };

        fetchInitialData();
    }, [accessToken, fetchUserData]);

    const handleRegionChange = (e) => {
        const value = e.target.value;
        setSelectedRegion(value);

        const selectedRegionObj = regions.find(region => region.code === value);
        const regionDisplay = selectedRegionObj ? selectedRegionObj.name : '';

        if (!value) {
            setSelectedCity('');
            setCities([]);
            setUserData(prev => ({
                ...prev,
                region_display: '',
                city_display: ''
            }));
        } else {
            setUserData(prev => ({
                ...prev,
                region_display: regionDisplay,
                city_display: ''
            }));
            fetchCities(value);
        }
    };

    const handleAvatarSourceChange = (e) => {
        const value = e.target.value;
        setSelectedAvatarSource(value);

        const newAvatarUrl = getDisplayedAvatarUrl(value, userData);
        setUserData(prev => ({
            ...prev,
            displayed_avatar_url: newAvatarUrl
        }));
    };

    const handleNickSourceChange = (e) => {
        const value = e.target.value;
        setSelectedNickSource(value);

        const newNick = getDisplayedNick(value, userData);
        setUserData(prev => ({
            ...prev,
            displayed_nick: newNick
        }));
    };

    const handleCityChange = (e) => {
        const value = e.target.value;
        setSelectedCity(value);

        const selectedCityObj = cities.find(city => city.code === value);
        const cityDisplay = selectedCityObj ? selectedCityObj.name : '';

        setUserData(prev => ({
            ...prev,
            city_display: cityDisplay
        }));
    };

    const handleSave = async () => {
        if (!accessToken || loading) return;

        const hasChanges =
            selectedAvatarSource !== userData.avatar_source ||
            selectedNickSource !== userData.nick_source ||
            selectedRegion !== userData.region ||
            selectedCity !== userData.city;

        if (!hasChanges) {
            setError('Нет изменений для сохранения');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const updateData = {
                avatar_source: selectedAvatarSource,
                nick_source: selectedNickSource,
                region: selectedRegion,
                city: selectedCity
            };

            const response = await fetch('https://127.0.0.1:8000/accounts/user/', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${accessToken}`,
                },
                body: JSON.stringify(updateData),
                credentials: 'include',
            });

            if (response.ok) {
                await fetchUserData();
                setSuccess('Профиль обновлён!');
            } else {
                const errData = await response.json();
                setError(errData.detail || Object.values(errData).join(', ') || 'Ошибка при сохранении');
            }
        } catch (err) {
            setError('Ошибка при сохранении');
        }
        setLoading(false);
    };

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

    const toLogin = () => {
        navigate('/login');
    };

    if (!accessToken) {
        return (
            <>
                <h2>Профиль</h2>
                <span>Пожалуйста, войдите в систему.</span>
                <button className={styles.toLoginButton} onClick={toLogin}>Войти</button>
            </>
        );
    }

    const hasDiscord = !!userData.discord_user;
    const hasOsu = !!userData.osu_user;

    return (
        <main>
            {!initialLoadComplete ? (
                <LoadingSpinner/>
            ) : (
                <>
                    <h2>Профиль</h2>
                    {error && <span className={styles.errorMessage}>{error}</span>}
                    {success && <span className={styles.successMessage}>{success}</span>}
                    <div className={styles.displayCard}>
                        <div className={styles.avatarContainer}>
                            <img
                                src={userData.displayed_avatar_url}
                                alt="Avatar"
                                className={styles.avatar}
                            />
                        </div>
                        <div className={styles.info}>
                            <h3 className={styles.nick}>{userData.displayed_nick || 'Не выбран'}</h3>
                            <div className={styles.location}>
                                <span className={styles.region}>{userData.region_display}</span>
                                {userData.city_display && (
                                    <span className={styles.citySeparator}>, </span>
                                )}
                                <span className={styles.city}>{userData.city_display}</span>
                            </div>
                        </div>
                    </div>

                    <div className={styles.editSection}>
                        <h3 className={styles.editSectionTitle}>Настройки отображения</h3>

                        <label className={styles.label}>
                            Источник аватара:
                            <select value={selectedAvatarSource} onChange={handleAvatarSourceChange} className={styles.select} disabled={loading}>
                                {hasOsu && <option value="osu">Osu!</option>}
                                {hasDiscord && <option value="discord">Discord</option>}
                            </select>
                        </label>

                        <label className={styles.label}>
                            Источник ника:
                            <select value={selectedNickSource} onChange={handleNickSourceChange} className={styles.select} disabled={loading}>
                                {hasOsu && <option value="osu">Osu! Username</option>}
                                {hasDiscord && (
                                    <>
                                        <option value="discord_username">Discord Username</option>
                                        <option value="discord_display_name">Discord Display Name</option>
                                    </>
                                )}
                            </select>
                        </label>

                        <label className={styles.label}>
                            Регион:
                            <select value={selectedRegion} onChange={handleRegionChange} className={styles.select} disabled={loading}>
                                <option value="">Без региона</option>
                                {regions.map((reg) => (
                                    <option key={reg.code} value={reg.code}>{reg.name}</option>
                                ))}
                            </select>
                        </label>

                        <label className={styles.label}>
                            Город:
                            <select value={selectedCity} onChange={handleCityChange} className={styles.select} disabled={!selectedRegion || loading}>
                                <option value="">Без города</option>
                                {cities.map((city) => (
                                    <option key={city.code} value={city.code}>{city.name}</option>
                                ))}
                            </select>
                        </label>

                        <button className={styles.saveButton} onClick={handleSave} disabled={loading}>
                            {loading ? 'Сохранение...' : 'Сохранить'}
                        </button>
                    </div>

                    {!hasDiscord && (
                        <button className={`${styles.linkButton} ${styles.linkButtonDiscord}`} onClick={handleLinkDiscord} disabled={loading}>
                            Привязать<img src={discordLogo} alt="" height="30px" width="30px"/>
                        </button>
                    )}
                    {!hasOsu && (
                        <button className={`${styles.linkButton} ${styles.linkButtonOsu}`} onClick={handleLinkOsu} disabled={loading}>
                            Привязать<img src={osuLogo} alt="" width="30px" height="30px"/>
                        </button>
                    )}
                    <button className={styles.logoutButton} onClick={logout} disabled={loading}>
                        Выйти
                    </button>
                </>
            )}
        </main>
    );
};

export default Profile;