import "./QUser.css";

interface QUserModalProps {
    savedUser: {
        username: string;
        role: string;
    } | null;

    setShowUserPopup: (value: boolean) => void;
    openUsersPanel: () => void;
    logout: () => void;
}

function QUserModal({
    savedUser,
    setShowUserPopup,
    openUsersPanel,
    logout
}: QUserModalProps) {

    return (
        <>
            <div
                className="popup-overlay"
                onClick={() => setShowUserPopup(false)}
            />

            <div className="user-popup">

                <div className="user-info-container">
                    <div className="user-row">

                        <img
                            src="/user.svg"
                            className="user-icon"
                            alt="User"
                        />

                        <div className="user-texts">
                            <span className="text-user">
                                User: {savedUser?.username}
                            </span>

                            <span className="text-role">
                                Role: {savedUser?.role}
                            </span>
                        </div>

                    </div>
                </div>


                <div
                    className="user-options"
                >

                    {savedUser?.role === "admin" && (
                        <div
                            className="logout-option"
                            onClick={openUsersPanel}
                        >
                            Manage Users
                        </div>
                    )}


                    <div
                        className="logout-option"
                        onClick={logout}
                    >
                        Logout
                    </div>

                </div>

            </div>
        </>
    );
}

export default QUserModal;