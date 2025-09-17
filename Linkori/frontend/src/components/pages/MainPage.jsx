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
        <div>Войдите, пожалуйста, в аккаунт</div>
    );
};

export default MainPage;