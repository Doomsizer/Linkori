import React from "react";
import { Fragment, Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import LoadingSpinner from "./components/LoadingSpinner";
import Header from "./components/Header"
import Footer from "./components/Footer"
import "../styles/index.css";

const Profile = lazy(() => import("./pages/Profile"));
const Login = lazy(() => import("./pages/Login"));
const MainPage = lazy(() => import('./pages/MainPage'));
const DataPrivacy = lazy(() => import('./pages/DataPrivacy'))

function App() {
    return (
        <Fragment>
            <BrowserRouter>
                <Suspense fallback={<LoadingSpinner/>}>
                    <Header/>
                    <Routes>
                        <Route path="*" element={<MainPage />}/>
                        <Route path="/login" element={<Login />} />
                        <Route path="/data-privacy/" element={<DataPrivacy />} />
                        <Route path="/callback/discord/*" element={<Login />} />
                        <Route path="/callback/osu/*" element={<Login />} />
                        <Route path="/profile" element={<Profile />} />
                    </Routes>
                    <Footer/>
                </Suspense>
            </BrowserRouter>
        </Fragment>
    );
}

export default App;