import React from "react";
import { useAuth } from "../hooks/useAuth";
import LoadingSpinner from "../components/LoadingSpinner";
import "../../styles/MainPage.css";

const MainPage = () => {
    const { isAuthenticated, isRefreshing } = useAuth();

    if (isRefreshing) {
        return <LoadingSpinner/>;
    }

    return isAuthenticated ? (
        <div>Таблица</div>
    ) : (
        <main>
            <span>Войдите, пожалуйста, в аккаунт</span>
        </main>
    );
};

export default MainPage;