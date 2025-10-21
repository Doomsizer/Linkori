import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import styles from "../../styles/Leaderboard.module.css";

const Leaderboard = () => {
    const { isAuthenticated, accessToken, isRefreshing, isLinked } = useAuth();
    const [leaderboardData, setLeaderboardData] = useState([]);
    const [regions, setRegions] = useState([]);
    const [cities, setCities] = useState([]);
    const [allCities, setAllCities] = useState([]);
    const [userServers, setUserServers] = useState([]);
    const [selectedMode, setSelectedMode] = useState('osu');
    const [selectedRegion, setSelectedRegion] = useState('');
    const [selectedCity, setSelectedCity] = useState('');
    const [selectedServer, setSelectedServer] = useState('');
    const [isServerMode, setIsServerMode] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [nextUrl, setNextUrl] = useState(null);
    const [previousUrl, setPreviousUrl] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    const fetchRegions = useCallback(async () => {
        try {
            const response = await fetch('https://127.0.0.1:8000/accounts/regions/', {
            });
            if (response.ok) {
                const data = await response.json();
                setRegions(data.regions || []);
            } else {
                setError('Ошибка загрузки регионов');
            }
        } catch (err) {
            setError('Ошибка при загрузке регионов');
        }
    }, []);

    const fetchAllCities = useCallback(async () => {
        try {
            const response = await fetch('https://127.0.0.1:8000/leaderboard/cities/', {
            });
            if (response.ok) {
                const data = await response.json();
                setAllCities(data.cities || []);
            } else {
                setError('Ошибка загрузки списка городов');
            }
        } catch (err) {
            setError('Ошибка при загрузке списка городов');
        }
    }, []);

    const fetchCities = useCallback(async (regionCode) => {
        if (!regionCode) return;
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

    const fetchUserServers = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch('https://127.0.0.1:8000/leaderboard/user-servers/', {
                headers: { Authorization: `Bearer ${accessToken}` },
                credentials: 'include',
            });
            if (response.ok) {
                const data = await response.json();
                setUserServers(data.servers || data || []);
            } else {
                setError('Ошибка загрузки серверов');
            }
        } catch (err) {
            setError('Ошибка при загрузке серверов');
        }
        setLoading(false);
    }, [accessToken]);

    const buildUrl = (page = 1) => {
        let url = `https://127.0.0.1:8000/leaderboard/leaderboard/?page=${page}&mode=${selectedMode}`;
        if (selectedRegion) {
            url += `&region=${selectedRegion}`;
        }
        if (selectedCity) {
            url += `&city=${selectedCity}`;
        }
        if (selectedServer) {
            url += `&server=${selectedServer}`;
        }
        return url;
    };

    const fetchLeaderboard = useCallback(async (url) => {
        setLoading(true);
        setError(null);

        try {
            const headers = isAuthenticated && isLinked ? { Authorization: `Bearer ${accessToken}` } : {};
            const response = await fetch(url, {
                headers,
                credentials: 'include',
            });

            if (response.ok) {
                const data = await response.json();
                setLeaderboardData(data.results || []);
                setTotalPages(Math.ceil(data.count / 25));
                setNextUrl(data.next);
                setPreviousUrl(data.previous);
            } else {
                const errData = await response.json().catch(() => ({}));
                setError(errData.detail || 'Ошибка загрузки лидерборда');
            }
        } catch (err) {
            setError('Ошибка при загрузке лидерборда');
        }
        setLoading(false);
    }, [isAuthenticated, isLinked, accessToken]);

    useEffect(() => {
        fetchAllCities();
        fetchRegions();

        const initialUrl = (isAuthenticated && isLinked) ? buildUrl() : `https://127.0.0.1:8000/leaderboard/mainboard/?page=1&page_size=25`;
        fetchLeaderboard(initialUrl);
    }, [isAuthenticated, isLinked, fetchRegions, fetchLeaderboard, fetchAllCities, selectedMode, selectedRegion, selectedCity, selectedServer]);

    const handleModeChange = (e) => {
        setSelectedMode(e.target.value);
        setCurrentPage(1);
    };

    const handleRegionChange = (e) => {
        const value = e.target.value;
        setSelectedRegion(value);
        setSelectedCity('');
        setCurrentPage(1);
        if (value) {
            fetchCities(value);
        } else {
            setCities([]);
        }
    };

    const handleCityChange = (e) => {
        setSelectedCity(e.target.value);
        setCurrentPage(1);
    };

    const handleServerSelect = (serverId) => {
        setSelectedServer(serverId);
        setCurrentPage(1);
    };

    const handleNextPage = () => {
        if (nextUrl) {
            fetchLeaderboard(nextUrl);
            setCurrentPage(prev => prev + 1);
        }
    };

    const handlePreviousPage = () => {
        if (previousUrl) {
            fetchLeaderboard(previousUrl);
            setCurrentPage(prev => prev - 1);
        }
    };

    const handleLeaderboardType = (type) => {
        if (type === 'server') {
            setIsServerMode(true);
            fetchUserServers();
        } else {
            setIsServerMode(false);
            setSelectedServer('');
            setCurrentPage(1);
            fetchLeaderboard(buildUrl(1));
        }
    };

    const getServerIconUrl = (serverIcon, serverId) => {
        if (!serverIcon) return '/default-server-icon.png';
        return `https://cdn.discordapp.com/icons/${serverId}/${serverIcon}.png`;
    };

    const getRegionName = (code) => {
        const reg = regions.find(r => r.code === code);
        return reg ? reg.name : code || '-';
    };

    const getCityName = (code) => {
        if (!code) return '-';
        const city = allCities.find(c => c.code === code);
        return city ? city.name : code;
    };

    if (isRefreshing) {
        return <LoadingSpinner />;
    }

    const startRank = (currentPage - 1) * 25 + 1;

    return (
        <main className={styles.main}>
            {error && <span className={styles.errorMessage}>{error}</span>}
            {loading ? (
                <LoadingSpinner />
            ) : (
                <>
                    {isAuthenticated && isLinked && (
                        <div className={styles.typeButtons}>
                            <button
                                onClick={() => handleLeaderboardType('usual')}
                                className={`${styles.typeButton} ${!isServerMode ? styles.active : ''}`}
                            >
                                Обычный
                            </button>
                            <button
                                onClick={() => handleLeaderboardType('server')}
                                className={`${styles.typeButton} ${isServerMode ? styles.active : ''}`}
                            >
                                Серверный
                            </button>
                        </div>
                    )}

                    {isAuthenticated && !isLinked && (
                        <div className={styles.mainError}>
                            <p style={{ color: 'var(--linkori-white)', textAlign: 'center' }}>
                                Вы вошли только при помощи одного сервиса.
                                Перейдите в свой профиль и привяжите второй сервис для открытия фильтрации лидербордов
                            </p>
                        </div>
                    )}

                    {isAuthenticated && isLinked && !isServerMode && (
                        <div className={styles.filters}>
                            <label className={styles.label}>
                                Режим:
                                <select value={selectedMode} onChange={handleModeChange} className={styles.select}>
                                    <option value="osu">osu!</option>
                                    <option value="taiko">taiko</option>
                                    <option value="fruits">fruits</option>
                                    <option value="mania">mania</option>
                                </select>
                            </label>
                            <label className={styles.label}>
                                Регион:
                                <select value={selectedRegion} onChange={handleRegionChange} className={styles.select}>
                                    <option value="">Все регионы</option>
                                    {regions.map((reg) => (
                                        <option key={reg.code} value={reg.code}>{reg.name}</option>
                                    ))}
                                </select>
                            </label>
                            <label className={styles.label}>
                                Город:
                                <select value={selectedCity} onChange={handleCityChange} className={styles.select} disabled={!selectedRegion}>
                                    <option value="">Все города</option>
                                    {cities.map((city) => (
                                        <option key={city.code} value={city.code}>{city.name}</option>
                                    ))}
                                </select>
                            </label>
                        </div>
                    )}

                    {isServerMode && isAuthenticated && isLinked && userServers.length > 0 && (
                        <div className={styles.servers}>
                            {userServers.map((server) => (
                                <button
                                    key={server.server_id}
                                    onClick={() => handleServerSelect(server.server_id)}
                                    className={`${styles.serverButton} ${selectedServer === server.server_id ? styles.active : ''}`}
                                >
                                    <img
                                        src={getServerIconUrl(server.server_icon, server.server_id)}
                                        alt={server.server_name}
                                        className={styles.icon}
                                        onError={(e) => { e.target.src = '/default-server-icon.png'; }}
                                    />
                                    <div className={styles.info}>
                                        <span className={styles.name}>{server.server_name}</span>
                                        <span className={styles.members}>{server.member_count} участников</span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}

                    {isServerMode && isAuthenticated && isLinked && userServers.length === 0 && (
                        <div className={styles.serversError}>
                            <p style={{ color: 'var(--linkori-white)', textAlign: 'center' }}>
                                Вы не были найдены ни на одном из наших серверов. Если вы недавно вступили в сервер,
                                на котором есть бот Linkori - выйдите из аккаунта
                                на сайте и авторизуйтесь при помощи дискорда. <br/>
                                Это просканирует ваш список серверов и найдет сходства в серверах бота. Спасибо за понимание.
                            </p>
                        </div>
                    )}
                    <table className={styles.table}>
                        <thead>
                        <tr>
                            <th>Ранг</th>
                            <th>Игрок</th>
                            <th>PP</th>
                            <th>Глобальный ранг</th>
                            <th>Ранг в стране</th>
                            <th>Регион</th>
                            <th>Город</th>
                        </tr>
                        </thead>
                        <tbody>
                        {leaderboardData.map((entry, index) => (
                            <tr key={entry.user.osu_id || index}>
                                <td className={styles.rank}>{startRank + index}</td>
                                <td className={styles.player}>
                                    <a className={styles.playerLink} href={`https://osu.ppy.sh/users/${entry.user.osu_id}`}>
                                        <img
                                            src={entry.user.avatar_url || 'https://osu.ppy.sh/images/layout/avatar-guest@2x.png'}
                                            alt={entry.user.nick}
                                            className={styles.avatar}
                                            onError={(e) => { e.target.src = 'https://osu.ppy.sh/images/layout/avatar-guest@2x.png'; }}
                                        />
                                        <span className={styles.nick}>{entry.user.nick}</span>
                                    </a>
                                </td>
                                <td className={styles.pp}>{Math.round(entry.pp)}</td>
                                <td className={styles.globalRank}>{entry.global_rank ? `#${entry.global_rank}` : '-'}</td>
                                <td className={styles.countryRank}>{entry.country_rank ? `#${entry.country_rank}` : '-'}</td>
                                <td className={styles.region}>{getRegionName(entry.user.region)}</td>
                                <td className={styles.city}>{getCityName(entry.user.cities)}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                    <div className={styles.pagination}>
                        <button
                            onClick={handlePreviousPage}
                            disabled={!previousUrl}
                            className={styles.paginationButton}
                        >
                            Предыдущая
                        </button>
                        <span className={styles.pageInfo}>
                            Страница {currentPage} из {totalPages}
                        </span>
                        <button
                            onClick={handleNextPage}
                            disabled={!nextUrl}
                            className={styles.paginationButton}
                        >
                            Следующая
                        </button>
                    </div>
                </>
            )}
        </main>
    );
};

export default Leaderboard;