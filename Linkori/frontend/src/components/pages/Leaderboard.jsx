import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import "../../styles/Leaderboard.css";

const Leaderboard = () => {
    const { isAuthenticated, accessToken, isRefreshing } = useAuth();
    const [leaderboardData, setLeaderboardData] = useState([]);
    const [regions, setRegions] = useState([]);
    const [cities, setCities] = useState([]);
    const [allCities, setAllCities] = useState([]); // Новое состояние для всех городов
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

    // Функция для загрузки всех городов
    const fetchAllCities = useCallback(async () => {
        try {
            const response = await fetch('https://127.0.0.1:8000/leaderboard/cities/', {
                credentials: 'include',
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

    const fetchRegions = useCallback(async () => {
        try {
            const response = await fetch('https://127.0.0.1:8000/accounts/regions/', {
                credentials: 'include',
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
            const headers = isAuthenticated ? { Authorization: `Bearer ${accessToken}` } : {};
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
    }, [isAuthenticated, accessToken]);

    useEffect(() => {
        // Загружаем все города при монтировании компонента
        fetchAllCities();

        if (isAuthenticated) {
            fetchRegions();
        }
        const initialUrl = isAuthenticated ? buildUrl() : `https://127.0.0.1:8000/leaderboard/mainboard/?page=1&page_size=25`;
        fetchLeaderboard(initialUrl);
    }, [isAuthenticated, fetchRegions, fetchLeaderboard, fetchAllCities, selectedMode, selectedRegion, selectedCity, selectedServer]);

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

    const toLogin = () => {
        navigate('/login');
    };

    const getServerIconUrl = (serverIcon, serverId) => {
        if (!serverIcon) return '/default-server-icon.png';
        return `https://cdn.discordapp.com/icons/${serverId}/${serverIcon}.png`;
    };

    // Функция для получения названия региона по коду
    const getRegionName = (code) => {
        const reg = regions.find(r => r.code === code);
        return reg ? reg.name : code || '-';
    };

    // Функция для получения названия города по коду
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
        <main className="leaderboard-main">
            {error && <span className="leaderboard-error-message">{error}</span>}
            {loading ? (
                <LoadingSpinner />
            ) : (
                <>
                    {isAuthenticated && (
                        <div className="leaderboard-type-buttons">
                            <button
                                onClick={() => handleLeaderboardType('usual')}
                                className={`leaderboard-type-button ${!isServerMode ? 'active' : ''}`}
                            >
                                Обычный
                            </button>
                            <button
                                onClick={() => handleLeaderboardType('server')}
                                className={`leaderboard-type-button ${isServerMode ? 'active' : ''}`}
                            >
                                Серверный
                            </button>
                        </div>
                    )}
                    {isAuthenticated && (
                        <div className="leaderboard-filters">
                            <label className="leaderboard-label">
                                Режим:
                                <select value={selectedMode} onChange={handleModeChange} className="leaderboard-select">
                                    <option value="osu">osu!</option>
                                    <option value="taiko">taiko</option>
                                    <option value="fruits">fruits</option>
                                    <option value="mania">mania</option>
                                </select>
                            </label>
                            <label className="leaderboard-label">
                                Регион:
                                <select value={selectedRegion} onChange={handleRegionChange} className="leaderboard-select">
                                    <option value="">Все регионы</option>
                                    {regions.map((reg) => (
                                        <option key={reg.code} value={reg.code}>{reg.name}</option>
                                    ))}
                                </select>
                            </label>
                            <label className="leaderboard-label">
                                Город:
                                <select value={selectedCity} onChange={handleCityChange} className="leaderboard-select" disabled={!selectedRegion}>
                                    <option value="">Все города</option>
                                    {cities.map((city) => (
                                        <option key={city.code} value={city.code}>{city.name}</option>
                                    ))}
                                </select>
                            </label>
                        </div>
                    )}
                    {isServerMode && userServers.length > 0 && (
                        <div className="leaderboard-servers">
                            {userServers.map((server) => (
                                <button
                                    key={server.server_id}
                                    onClick={() => handleServerSelect(server.server_id)}
                                    className={`leaderboard-server-button ${selectedServer === server.server_id ? 'active' : ''}`}
                                >
                                    <img
                                        src={getServerIconUrl(server.server_icon, server.server_id)}
                                        alt={server.server_name}
                                        className="server-icon"
                                        onError={(e) => { e.target.src = '/default-server-icon.png'; }}
                                    />
                                    <div className="server-info">
                                        <span className="server-name">{server.server_name}</span>
                                        <span className="server-members">{server.member_count} участников</span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                    {isServerMode && userServers.length === 0 && (
                        <div className="leaderboard-servers">
                            <p style={{ color: 'var(--linkori-white)', textAlign: 'center' }}>
                                Вы не состоите ни в одном сервере или серверы не найдены
                            </p>
                        </div>
                    )}
                    <table className="leaderboard-table">
                        <thead>
                        <tr>
                            <th>Ранг</th>
                            <th>Игрок</th>
                            <th>PP</th>
                            <th>Глобальный ранг</th>
                            <th>Страна ранг</th>
                            <th>Регион</th>
                            <th>Город</th>
                        </tr>
                        </thead>
                        <tbody>
                        {leaderboardData.map((entry, index) => (
                            <tr key={entry.user.osu_id || index}>
                                <td className="leaderboard-rank">{startRank + index}</td>
                                <td className="leaderboard-player">
                                    <img
                                        src={entry.user.avatar_url}
                                        alt={entry.user.nick}
                                        className="leaderboard-avatar"
                                        onError={(e) => { e.target.src = '/default-avatar.png'; }}
                                    />
                                    <span className="leaderboard-nick">{entry.user.nick}</span>
                                </td>
                                <td className="leaderboard-pp">{Math.round(entry.pp)}</td>
                                <td className="leaderboard-global-rank">{entry.global_rank ? `#${entry.global_rank}` : '-'}</td>
                                <td className="leaderboard-country-rank">{entry.country_rank ? `#${entry.country_rank}` : '-'}</td>
                                <td className="leaderboard-region">{getRegionName(entry.user.region)}</td>
                                <td className="leaderboard-city">{getCityName(entry.user.cities)}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                    <div className="leaderboard-pagination">
                        <button
                            onClick={handlePreviousPage}
                            disabled={!previousUrl}
                            className="leaderboard-pagination-button"
                        >
                            Предыдущая
                        </button>
                        <span className="leaderboard-page-info">
                            Страница {currentPage} из {totalPages}
                        </span>
                        <button
                            onClick={handleNextPage}
                            disabled={!nextUrl}
                            className="leaderboard-pagination-button"
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