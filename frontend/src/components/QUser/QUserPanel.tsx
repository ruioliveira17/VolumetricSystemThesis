import { useEffect, useRef, useState } from "react";
import "./QUser.css";
import Qselect from "../Qselect"
import DeleteForeverIcon from "@assets/icons/delete_forever.svg?react";
import CopyIcon from "@assets/icons/copy.svg?react";

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
        navigator.clipboard.writeText(token).then(() => {
            setCopiedToken(token);
            setTimeout(() => setCopiedToken(null), 1500);
        });
    }

    const otherUsers = usersList.filter(
        (u) => u.username !== savedUser?.username
    );

    return (
        <>
            <div
                className="popup-overlay"
                onClick={() => setShowUsersPanel(false)}
            >
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
                                                <div className="tokens-list">
                                                    {tokens.map((token) => (
                                                        <div key={token} className="token-chip">
                                                            <span className="token-chip-text">{token}</span>
                                                            <button
                                                                className="token-copy-button"
                                                                onClick={() => handleCopy(token)}
                                                            >
                                                                <CopyIcon className="token-copy-icon" />
                                                                {copiedToken === token && (
                                                                    <span className="token-copied-badge">Copied!</span>
                                                                )}
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>

                                                <button
                                                    className="generate-token-button"
                                                    onClick={() => generateResetToken(u.id)}
                                                >
                                                    Generate Token
                                                </button>
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

                    <div className="close-button">
                        <img src="/close.svg" onClick={() => setShowUsersPanel(false)} />
                    </div>

                </div>
            </div>
        </>
    );
}

export default QUserPanel;