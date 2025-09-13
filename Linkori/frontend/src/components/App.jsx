import * as React from "react";
import { Fragment, Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

const Profile = lazy(() => import("./pages/Profile"));
const Login = lazy(() => import("./pages/Login"));

function App() {
    return (
        <Fragment>
            <BrowserRouter>
                <Suspense fallback={<div>Загрузка...</div>}>
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/callback/discord/*" element={<Login />} />
                        <Route path="/callback/osu/*" element={<Login />} />
                        <Route path="/profile" element={<Profile />} />
                    </Routes>
                </Suspense>
            </BrowserRouter>
        </Fragment>
    );
}

export default App;