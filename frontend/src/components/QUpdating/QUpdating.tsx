import React from "react";
import { useEffect, useState } from "react";
import "./QUpdating.css";
import QubicLoader from '@assets/icons/qubic-loader.svg?react';
import {apiFetch} from "../../api/client"

interface QUpdatingProps {
    onComplete: () => void;
}

function QUpdating({ onComplete }: QUpdatingProps) {
    // const [progress, setProgress] = useState(0);

    // useEffect(() => {
    //     const interval = setInterval(() => {
    //         setProgress((current) => {
    //             if (current >= 100) {
    //                 clearInterval(interval);

    //                 setTimeout(() => {
    //                     onComplete();
    //                 }, 500);

    //                 return 100;
    //             }

    //             return current + 5;
    //         });
    //     }, 1000);

    //     return () => clearInterval(interval);
    // }, []);

    // const getUpdateMessage = () => {
    //     if (progress < 30) {
    //         return "Downloading update...";
    //     }

    //     if (progress < 70) {
    //         return "Extracting files...";
    //     }

    //     if (progress < 80) {
    //         return "Backing up current version...";
    //     }

    //     if (progress < 95) {
    //         return "Installing update...";
    //     }

    //     return "The system is about to restart...";
    // };

    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        const installUpdate = async () => {
            try {
                const response = await apiFetch("/updates/install-test", {
                    method: "POST",
                });

                if (!response.ok) {
                    const data = await response.json().catch(() => null);

                    throw new Error(
                        data?.detail || "Failed to install the update."
                    );
                }

                if (!cancelled) {
                    onComplete();
                }
            } catch (err) {
                if (cancelled) return;

                setError(
                    err instanceof Error
                        ? err.message
                        : "An unexpected error occurred."
                );
            }
        };

        void installUpdate();

        return () => {
            cancelled = true;
        };
    }, [onComplete]);

    return (
        <div className="updating-overlay">
            <div className="updating-loader">
                <QubicLoader />
            </div>

            {error && (
                <span className="updating-message">
                    {error}
                </span>
            )}
        </div>
    );
}

export default QUpdating;