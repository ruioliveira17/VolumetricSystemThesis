import "./QUser.css";
import UserIcon from '@assets/icons/user.svg?react';
import CloseIcon from '@assets/icons/close.svg?react';
import PopupConnection from '@assets/icons/popup_connection.svg?react';

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
            <div className="popup-overlay"/>

            <div className="user-popup-connection">
                <PopupConnection />
            </div>
            <div className="user-popup">

                <div className="user-info-container">
                    <div className="user-row">

                        <UserIcon
                            className="user-icon"
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

                <div className="close-button">
                    <CloseIcon onClick={() => setShowUserPopup(false)}/>
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