import React from "react";
import "./QSystemLoader.css";
import QubicLoader from '@assets/icons/qubic-loader.svg?react';

import QBackgroundBranding from "../QBackgroundBranding";

interface QSystemLoaderProps {
    t: (key: string) => string;

    fadingOut?: boolean;
}

function QSystemLoader({ t, fadingOut = false }: QSystemLoaderProps){
    return (
        <div className={`system-loader ${fadingOut ? "fade-out" : ""}`}>
            <QBackgroundBranding />
            <div className="menu-wrapper">
                <div className="systemLoader">
                    <QubicLoader />
                </div>

                <div className="initText">
                    <span>{t("systemLoader.initializing")}</span>
                    <span>{t("systemLoader.waitAMoment")}</span>
                </div>
            </div>
        </div>
    );
}

export default QSystemLoader;