import React from "react";
import { useEffect, useState } from "react";
import "./QUpdating.css";
import QubicLoader from '@assets/icons/qubic-loader.svg?react';

interface QUpdatingProps {
    onComplete: () => void;
}

function QUpdating({ onComplete }: QUpdatingProps) {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setProgress((current) => {
                if (current >= 100) {
                    clearInterval(interval);

                    setTimeout(() => {
                        onComplete();
                    }, 500);

                    return 100;
                }

                return current + 5;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    const getUpdateMessage = () => {
        if (progress < 30) {
            return "Downloading update...";
        }

        if (progress < 70) {
            return "Extracting files...";
        }

        if (progress < 80) {
            return "Backing up current version...";
        }

        if (progress < 95) {
            return "Installing update...";
        }

        return "The system is about to restart...";
    };

    return (
        <div className="updating-overlay">
            <div className="updating-loader">
                <QubicLoader />
            </div>

            <div className="updating-progress">
                <div
                    className="updating-progress-bar"
                    style={{ width: `${progress}%` }}
                />
            </div>

            <span className="updating-message">
                {getUpdateMessage()}
            </span>

            <span className="updating-progress-text">
                {progress}%
            </span>
        </div>
    );
}

export default QUpdating;