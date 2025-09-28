import React from "react";
import { useAuth } from "../hooks/useAuth";
import LoadingSpinner from "../components/LoadingSpinner";
import "../../styles/MainPage.css";
import { useNavigate } from "react-router-dom";
import Akira from "../../media/Akira-no-bg.png";

const MainPage = () => {
    const navigate = useNavigate();
    const { isAuthenticated, isRefreshing } = useAuth();

    const toLeaderboard = () => {
        navigate("/leaderboard");
    };

    const toLogin = () => {
        navigate("/login");
    };

    if (isRefreshing) {
        return <LoadingSpinner />;
    }

    return (
        <main className="main-page">
            <div className="main-hero">
                <div className="main-hero-image-container">
                    <img src={Akira} alt="Akira" className="main-hero-image" />
                </div>
                <div className="main-hero-content">
                    <h1 className="main-hero-description">
                        Региональный лидерборд для osu! плееров Дальнего Востока России.
                    </h1>
                    {isAuthenticated ? (
                        <>
                            <button className="main-hero-button" onClick={toLeaderboard}>
                                Перейти к лидербордам
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="main-hero-button" onClick={toLeaderboard}>
                                Перейти к лидербордам
                            </button>
                            <p className="main-hero-note">
                                Чтобы получить полный доступ к функциям сервиса, пожалуйста, авторизуйтесь.
                            </p>
                            <button className="main-hero-button main-hero-button-login" onClick={toLogin}>
                                Авторизоваться
                            </button>
                        </>
                    )}
                </div>
            </div>
            <div className="main-info-wrapper">
                <section className="main-info">
                    <h2 className="main-info-title">О проекте</h2>
                    <p className="main-info-text">
                        Linkori — это региональный лидерборд osu!, ориентированный на игроков
                        из Дальнего Востока России. Здесь вы можете сравнить себя с игроками из
                        своего региона или даже города в любом режиме игры. Также есть поддержка серверных лидербордов (нужно, чтобы бот был на вашем сервере).
                        После авторизации у вас будет возможность установить свой город и регион. Идея региональных
                        лидербордов взята у qutatos (дискорд юз), можете ознакомиться с его <a href="https://docs.google.com/spreadsheets/d/1eHZBHcf9zVYLcwkx3RYF2rL5_ZspWYdfm8GtysMca6w/ ">гугл табличкой</a>. Мы не собираем какие-либо данные, кроме публично доступных,
                        а значит у нас нет возможности проверить ваше местоположение, полагаемся на вашу честность.
                        Не используйте сервис, если вы не являетесь жителем Дальнего Востока России.
                    </p>
                </section>
                <section className="main-info">
                    <h2 className="main-info-title">Об авторе</h2>
                    <p className="main-info-text">
                         <a href="https://github.com/Doomsizer">Автор</a> проекта. <a href="https://github.com/Doomsizer/Linkori">Github</a> репозиторий проекта.
                        Обнаруженные баги или ваши
                        предложения по развитию проекта можете написать в телеграм @D0omik. Хостинг и домен не бесплатные,
                        а на сайте нет рекламы. Если вы хотите поддержать проект - напишите в телеграм:)
                    </p>
                </section>
            </div>
        </main>
    );
};

export default MainPage;