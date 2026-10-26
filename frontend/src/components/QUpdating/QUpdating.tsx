
import React, { useEffect, useRef, useState } from "react";
import "./QUpdating.css";
import QubicLoader from "@assets/icons/qubic-loader.svg?react";
import { apiFetch } from "../../api/client";

interface QUpdatingProps {
    onComplete: () => void;
}

const POLL_INTERVAL_MS = 1000;
const RESTART_TIMEOUT_MS = 120_000;

const delay = (ms: number) =>
    new Promise<void>((resolve) => setTimeout(resolve, ms));

function QUpdating({ onComplete }: QUpdatingProps) {
    const [error, setError] = useState<string | null>(null);
    const installStarted = useRef(false);
    const onCompleteRef = useRef(onComplete);

    useEffect(() => {
        onCompleteRef.current = onComplete;
    }, [onComplete]);

    useEffect(() => {
        if (installStarted.current) return;
        installStarted.current = true;

        let cancelled = false;

        const runUpdate = async () => {
            try {
                const installResponse = await apiFetch("/updates/install", {
                    method: "POST",
                });

                if (!installResponse.ok) {
                    const data = await installResponse.json().catch(() => null);
                    throw new Error(
                        data?.detail || "Falha ao instalar a atualização."
                    );
                }

                const deadline = Date.now() + RESTART_TIMEOUT_MS;

                while (!cancelled && Date.now() < deadline) {
                    try {
                        const response = await apiFetch("/health", {
                            method: "GET",
                        });

                        if (response.status === 200) {
                            await delay(1000);

                            if (cancelled) return;

                            const confirmation = await apiFetch("/health", {
                                method: "GET",
                            });

                            if (confirmation.status === 200) {
                                onCompleteRef.current();
                                return;
                            }
                        }
                    } catch {
                        // A API pode estar temporariamente indisponível
                        // enquanto reinicia.
                    }

                    await delay(POLL_INTERVAL_MS);
                }

                if (!cancelled) {
                    throw new Error(
                        "Não foi possível confirmar o reinício da API."
                    );
                }
            } catch (err) {
                if (!cancelled) {
                    setError(
                        err instanceof Error
                            ? err.message
                            : "Ocorreu um erro inesperado."
                    );
                }
            }
        };

        void runUpdate();

        return () => {
            cancelled = true;
        };
    }, []);

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
