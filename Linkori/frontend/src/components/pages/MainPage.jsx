import React from "react";
import { useAuth } from "../hooks/useAuth";
import LoadingSpinner from "../components/LoadingSpinner";
import styles from "../../styles/MainPage.module.css";
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
        <main className={styles.page}>
            <div className={styles.hero}>
                <div className={styles.heroImageContainer}>
                    <img src={Akira} alt="Akira" className={styles.heroImage} />
                </div>
                <div className={styles.heroContent}>
                    <h1 className={styles.description}>
                        Региональный лидерборд для osu! плееров Дальнего Востока России.
                    </h1>
                    {isAuthenticated ? (
                        <>
                            <button className={styles.button} onClick={toLeaderboard}>
                                Перейти к лидербордам
                            </button>
                        </>
                    ) : (
                        <>
                            <button className={styles.button} onClick={toLeaderboard}>
                                Перейти к лидербордам
                            </button>
                            <p className={styles.note}>
                                Чтобы получить полный доступ к функциям сервиса, пожалуйста, авторизуйтесь.
                            </p>
                            <button className={`${styles.button} ${styles.buttonLogin}`} onClick={toLogin}>
                                Авторизоваться
                            </button>
                        </>
                    )}
                </div>
            </div>
            <div className={styles.infoWrapper}>
                <section className={styles.info}>
                    <h2 className={styles.infoTitle}>О проекте</h2>
                    <p className={styles.infoText}>
                        Linkori — это региональный лидерборд osu!, ориентированный на игроков
                        из Дальнего Востока России. Здесь вы можете сравнить себя с игроками из
                        своего региона или даже города в любом режиме игры. Также есть поддержка серверных лидербордов (нужно, чтобы бот был на вашем сервере).
                        После авторизации у вас будет возможность установить свой город и регион. Идея региональных
                        лидербордов взята у qutatos (дискорд юз), можете ознакомиться с его <a href="https://docs.google.com/spreadsheets/d/1eHZBHcf9zVYLcwkx3RYF2rL5_ZspWYdfm8GtysMca6w/ ">гугл табличкой</a>. Мы не собираем какие-либо данные, кроме публично доступных,
                        а значит у нас нет возможности проверить ваше местоположение, полагаемся на вашу честность.
                        Не используйте сервис, если вы не являетесь жителем Дальнего Востока России.
                    </p>
                </section>
                <section className={styles.info}>
                    <h2 className={styles.infoTitle}>Об авторе</h2>
                    <p className={styles.infoText}>
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