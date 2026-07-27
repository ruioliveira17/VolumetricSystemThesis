import React from "react";
import "./QSystemLoader.css";

function QSystemLoader(){
    return (
        <div>
            {/* Logo */}
            <div className="logo">
                <img src="/Qubic.svg" alt="BM Logo" />
            </div>

            <div className="menu-wrapper">
                <div className="systemLoader">
                    <img src="/qubic-loader.svg" alt="loadingSystem" />
                </div>

                <div className="initText">
                    <span>INITIALIZING</span>
                    <span>Please wait a moment...</span>
                </div>
            </div>

            {/* Powered By */}
            <div className="powered-by-panel">
                <div className="powered-by-text" translate="no">
                    Powered by
                </div>
                <img
                    src="/MarquesLogo.svg"
                    className="powered-by-logo"
                    alt="Marques Logo"
                />
            </div>
        </div>
    );
}

export default QSystemLoader;