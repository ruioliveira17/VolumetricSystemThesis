import "./QUser.css";

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
    deleteUserById
}: QUserPanelProps) {

    const otherUsers = usersList.filter(
        (u) => u.username !== savedUser?.username
    );

    return (
        <>
            <div
                className="popup-overlay"
                onClick={() => setShowUsersPanel(false)}
            />


            <div className="user-panel">

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


                {!usersLoading &&
                    otherUsers.map((u) => (
                        <div
                            key={u.id}
                            className="user-item"
                        >

                            <span
                                className="user-name"
                                title={u.username}
                            >
                                {u.username}
                            </span>


                            <select
                                value={u.role}
                                onChange={(e) =>
                                    changeUserRole(
                                        u.id,
                                        e.target.value
                                    )
                                }
                            >
                                <option value="user">
                                    user
                                </option>

                                <option value="admin">
                                    admin
                                </option>
                            </select>


                            <button
                                onClick={() =>
                                    deleteUserById(u.id)
                                }
                            >
                                Delete
                            </button>

                        </div>
                    ))
                }


                {!usersLoading &&
                    otherUsers.length === 0 &&
                    !usersMsg && (
                        <div className="no-users">
                            No other users.
                        </div>
                    )
                }


                <div
                    className="close-users-panel"
                    onClick={() => setShowUsersPanel(false)}
                >
                    Close
                </div>

            </div>
        </>
    );
}

export default QUserPanel;