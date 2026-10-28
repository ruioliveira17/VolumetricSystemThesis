
import React, { useEffect, useRef, useState } from "react";
import "./QUpdating.css";
import QubicLoader from "@assets/icons/qubic-loader.svg?react";
import { apiFetch } from "../../api/client";

interface QUpdatingProps {
    onComplete: () => void;
    onLogout: () => void;
    isInitiator: boolean;
}

const POLL_INTERVAL_MS = 1000;
const RESTART_TIMEOUT_MS = 120_000;

const delay = (ms: number) =>
    new Promise<void>((resolve) => setTimeout(resolve, ms));

function QUpdating({ 
    onComplete, 
    isInitiator,
}: QUpdatingProps) {
    const [error, setError] = useState<string | null>(null);
    const installStarted = useRef(false);
    const onCompleteRef = useRef(onComplete);

    useEffect(() => {
        onCompleteRef.current = onComplete;
    }, [onComplete]);
    
    
    useEffect(() => {
        if (isInitiator && installStarted.current) return;

        if (isInitiator) {
            installStarted.current = true;
        }

        let cancelled = false;

        const runUpdate = async () => {
            try {
                if (isInitiator) {
                    // Apenas o iniciador executa a atualização.
                    const updateResponse = await apiFetch(
                        "/updates/start_update",
                        { method: "POST" }
                    );

                    if (!updateResponse.ok) {
                        const data = await updateResponse.json().catch(() => null);

                        throw new Error(
                            data?.detail || "Falha ao executar a atualização."
                        );
                    }
                } else {
                    // Os restantes clientes aguardam que a API fique indisponível.
                    const stopDeadline = Date.now() + RESTART_TIMEOUT_MS;
                    let apiStopped = false;

                    while (!cancelled && Date.now() < stopDeadline) {
                        try {
                            const response = await apiFetch("/health", {
                                method: "GET",
                            });

                            if (!response.ok) {
                                apiStopped = true;
                                break;
                            }
                        } catch {
                            apiStopped = true;
                            break;
                        }

                        await delay(POLL_INTERVAL_MS);
                    }

                    if (cancelled) return;

                    if (!apiStopped) {
                        throw new Error(
                            "A API não ficou indisponível durante a atualização."
                        );
                    }
                }

                if (cancelled) return;

                // Ambos aguardam que a API volte a responder.
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
                                window.location.reload();
                                // onCompleteRef.current();
                                return;
                            }
                        }
                    } catch {
                        // A API pode estar temporariamente indisponível.
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
    }, [isInitiator]);

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
