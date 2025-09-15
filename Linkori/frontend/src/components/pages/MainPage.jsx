import React from "react";
import { useAuth } from "../hooks/useAuth";

const MainPage = () => {
    const { isAuthenticated, isRefreshing } = useAuth();

    if (isRefreshing) {
        return <div>Загрузка...</div>;
    }

    return isAuthenticated ? (
        <div>Таблица</div>
    ) : (
        <div>Войдите, пожалуйста, в аккаунт</div>
    );
};

export default MainPage;