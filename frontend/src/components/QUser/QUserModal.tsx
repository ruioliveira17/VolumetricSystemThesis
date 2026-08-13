import { type CSSProperties } from 'react';
import "./QUser.css";
import UserIcon from '@assets/icons/user.svg?react';
import CloseIcon from '@assets/icons/close.svg?react';
import PopupConnection from '@assets/icons/popup_connection.svg?react';

interface QUserModalProps {
    savedUser: {
        username: string;
        role: string;
    } | null;

    userAnchorRect: DOMRect | null;
    setShowUserPopup: (value: boolean) => void;
    openChangePasswordModal: () => void;
    openUsersPanel: () => void;
    logout: () => void;
}

function QUserModal({
    savedUser,
    setShowUserPopup,
    userAnchorRect,
    openChangePasswordModal,
    openUsersPanel,
    logout
}: QUserModalProps) {
    const popupStyle: CSSProperties = userAnchorRect
        ? {
            position: 'absolute',
            top: userAnchorRect.bottom + 35,
            left: userAnchorRect.left + userAnchorRect.width / 2,
            transform: 'translate(-85%, 0)',
          }
        : {};

    const connectionStyle: CSSProperties = userAnchorRect
        ? {
            position: 'absolute',
            top: userAnchorRect.bottom + 10,
            left: userAnchorRect.left + userAnchorRect.width / 2,
            transform: 'translate(-50%, 0)',
          }
        : {};

    return (
        <>
            <div className="popup-overlay"/>

            <div className="user-popup-connection" style={connectionStyle}>
                <PopupConnection />
            </div>
            <div className="user-popup" style={popupStyle}>

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

                <div className="user-panel-close-button">
                    <CloseIcon onClick={() => setShowUserPopup(false)}/>
                </div>

                <div
                    className="user-options"
                >

                    <div
                        className="logout-option"
                        onClick={openChangePasswordModal}
                    >
                        Redefine Password
                    </div>

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