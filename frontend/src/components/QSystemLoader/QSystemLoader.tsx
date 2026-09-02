import React from "react";
import "./QSystemLoader.css";
import QubicLoader from '@assets/icons/qubic-loader.svg?react';

import QBackgroundBranding from "../QBackgroundBranding";

function QSystemLoader(){
    return (
        <div>
            <QBackgroundBranding />
            <div className="menu-wrapper">
                <div className="systemLoader">
                    <QubicLoader />
                </div>

                <div className="initText">
                    <span>INITIALIZING</span>
                    <span>Please wait a moment...</span>
                </div>
            </div>
        </div>
    );
}

export default QSystemLoader;