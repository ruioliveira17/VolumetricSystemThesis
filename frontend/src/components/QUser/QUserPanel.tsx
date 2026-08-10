import { useEffect, useRef, useState } from "react";
import "./QUser.css";
import Qselect from "../Qselect"
import CheckIcon from "@assets/icons/check_icon.svg?react";
import CopyIcon from "@assets/icons/copy.svg?react";
import DeleteForeverIcon from "@assets/icons/delete_forever.svg?react";

interface User {
    id: number;
    username: string;
    role: string;
}

interface QUserPanelProps {
    usersList: User[];
    usersLoading: boolean;
    usersMsg: string;

    savedUser: {
        username: string;
        role: string;
    } | null;

    setShowUsersPanel: (value: boolean) => void;

    changeUserRole: (
        id: number,
        role: string
    ) => void;

    resetTokensByUser: Record<number, string[]>;
    generateResetToken: (
        id: number
    ) => void;

    deleteUserById: (
        id: number
    ) => void;
}


function QUserPanel({
    usersList,
    usersLoading,
    usersMsg,
    savedUser,
    setShowUsersPanel,
    changeUserRole,
    resetTokensByUser = {},
    generateResetToken,
    deleteUserById
}: QUserPanelProps) {

    const [copiedToken, setCopiedToken] = useState<string | null>(null);

    function handleCopy(token: string) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(token).then(() => {
                setCopiedToken(token);
                setTimeout(() => setCopiedToken(null), 1500);
            });
        } else {
            const textarea = document.createElement("textarea");
            textarea.value = token;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            try {
                document.execCommand("copy");
                setCopiedToken(token);
                setTimeout(() => setCopiedToken(null), 3000);
            } catch (err) {
                console.error("Copy failed", err);
            }
            document.body.removeChild(textarea);
        }
    }

    const otherUsers = usersList.filter(
        (u) => u.username !== savedUser?.username
    );

    return (
        <>
            <div className="darker-popup">
                <div className="user-panel" onClick={(e) => e.stopPropagation()}>

                    <div className="user-panel-title">
                        Manage Users
                    </div>

                    {usersLoading && (
                        <div className="user-panel-loading">
                            Loading...
                        </div>
                    )}

                    {usersMsg && (
                        <div className="user-panel-error">
                            {usersMsg}
                        </div>
                    )}

                    {!usersLoading && (
                        <div className="user-table-container">

                            <div className="user-header">
                                <div>User</div>
                                <div>Role</div>
                                <div></div>
                                <div></div>
                            </div>

                            <div className="user-table">
                                {otherUsers.map((u, index) => {
                                    const tokens = resetTokensByUser[u.id] ?? [];
                                    return (
                                        <div
                                            key={u.id}
                                            className={`user-item ${index % 2 === 0 ? "even" : "odd"}`}
                                        >
                                            <span
                                                className="user-name"
                                                title={u.username}
                                            >
                                                {u.username}
                                            </span>

                                            <div className="select">
                                                <Qselect
                                                    value={u.role}
                                                    options={[
                                                        { value: 'user', label: 'user' },
                                                        { value: 'admin', label: 'admin' },
                                                    ]}
                                                    onChange={(value) => changeUserRole(u.id, value)}
                                                />
                                            </div>

                                            <div className="tokens-cell">
                                                {tokens.length > 0 ? (
                                                    <div
                                                        className="token-field"
                                                        onClick={() => handleCopy(tokens[tokens.length - 1])}
                                                    >
                                                        <span className="token-field-text">
                                                            {tokens[tokens.length - 1]}
                                                        </span>
                                                        <button
                                                            className="token-copy-button"
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleCopy(tokens[tokens.length - 1]);
                                                            }}
                                                        >
                                                            {copiedToken === tokens[tokens.length - 1] ? (
                                                                <CheckIcon className="token-copied-icon" />
                                                            ) : (
                                                                <CopyIcon className="token-copy-icon" />
                                                            )}
                                                            {copiedToken === tokens[tokens.length - 1] && (
                                                                <span className="token-copied-badge">Copied!</span>
                                                            )}
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <button
                                                        className="generate-token-button"
                                                        onClick={() => generateResetToken(u.id)}
                                                    >
                                                        <span>Generate Token</span>
                                                    </button>
                                                )}
                                            </div>

                                            <button
                                                className="delete-button"
                                                onClick={() => deleteUserById(u.id)}
                                            >
                                                <DeleteForeverIcon className="deleteUser-icon" />
                                                <div className="deleteUser-text">Delete</div>
                                            </button>
                                        </div>
                                    );
                                })}
                                {otherUsers.length === 0 && !usersMsg && (
                                    <div className="no-users">
                                        No other users.
                                    </div>
                                )}
                            </div>

                        </div>
                    )}

                    <div className="manage-users-close-button ">
                        <img src="/close.svg" onClick={() => setShowUsersPanel(false)} />
                    </div>

                </div>
            </div>
        </>
    );
}

export default QUserPanel;