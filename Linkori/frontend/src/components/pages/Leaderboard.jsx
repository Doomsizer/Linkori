import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import "../../styles/Leaderboard.css";

const Leaderboard = () => {
    const { isAuthenticated, accessToken, isRefreshing } = useAuth();
    const [leaderboardData, setLeaderboardData] = useState([]);
    const [regions, setRegions] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [nextUrl, setNextUrl] = useState(null);
    const [previousUrl, setPreviousUrl] = useState(null);
    const navigate = useNavigate();

    const fetchRegions = useCallback(async () => {
        try {
            const response = await fetch('https://127.0.0.1:8000/accounts/regions/', {
                credentials: 'include',
            });
            if (response.ok) {
                const data = await response.json();
                const regionsMap = {};
                data.regions.forEach(region => {
                    regionsMap[region.code] = region.name;
                });
                setRegions(regionsMap);
            } else {
                setError('Ошибка загрузки регионов');
            }
        } catch (err) {
            setError('Ошибка при загрузке регионов');
        }
    }, []);

    const fetchLeaderboard = useCallback(async (url = `https://127.0.0.1:8000/leaderboard/main/?page=1&page_size=25`) => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(url, {
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
    }, []);

    useEffect(() => {
        fetchRegions();
        fetchLeaderboard();
    }, [fetchRegions, fetchLeaderboard]);

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

    const toLogin = () => {
        navigate('/login');
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
                                <td className="leaderboard-pp">{entry.pp.toFixed(0)}</td>
                                <td className="leaderboard-global-rank">{entry.global_rank ? `#${entry.global_rank}` : '-'}</td>
                                <td className="leaderboard-country-rank">{entry.country_rank ? `#${entry.country_rank}` : '-'}</td>
                                <td className="leaderboard-region">{regions[entry.user.region] || entry.user.region || '-'}</td>
                                <td className="leaderboard-city">{entry.user.cities || '-'}</td>
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