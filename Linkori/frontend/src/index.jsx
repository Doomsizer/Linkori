import React from "react";
import { createRoot } from 'react-dom/client';
import App from "./components/App";

import { AuthProvider } from "./components/hooks/useAuth";

const container = document.getElementById("root");
if (container) {
    const root = createRoot(container);
    root.render(
        <React.StrictMode>
            <AuthProvider>
                    <App />
            </AuthProvider>
        </React.StrictMode>
    );
}