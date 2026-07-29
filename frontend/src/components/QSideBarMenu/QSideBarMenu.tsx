import "./QSideBarMenu.css";
import SettingsIcon from '@assets/icons/settings.svg?react';
import UserIcon from '@assets/icons/user.svg?react';

interface QSideBarMenuProps {
    isAuthScreen: boolean;
    menuSideNavOpen: boolean;
    lockMenu: boolean;

    currentMenu: string;

    setCurrentMenu: (menu: string) => void;

    setShowSettingsPopup: (value: boolean) => void;
    showSettingsPopup : boolean;
    setShowUserPopup: (value: boolean) => void;
    showUserPopup: boolean;
}


function QSideBarMenu({
    isAuthScreen,
    menuSideNavOpen,
    lockMenu,
    currentMenu,
    setCurrentMenu,
    setShowSettingsPopup,
    showSettingsPopup,
    setShowUserPopup,
    showUserPopup,
}: QSideBarMenuProps) {

    return (
        <div
            className={`menuSideNav ${
                (!isAuthScreen && menuSideNavOpen) ? "open" : ""
            }`}
        >

            {!lockMenu && (
                <div
                    className={`nav-item ${
                        currentMenu === "volume-menu" ? "active" : ""
                    }`}
                    onClick={() => setCurrentMenu("volume-menu")}
                >
                    VOLUME
                </div>
            )}


            <div
                className={`nav-item ${
                    currentMenu === "calibration-menu" ? "active" : ""
                }`}
                onClick={() => setCurrentMenu("calibration-menu")}
            >
                CALIBRATION
            </div>


            <div
                className={`nav-item ${
                    currentMenu === "measurementHistory-menu"
                        ? "active"
                        : ""
                }`}
                onClick={() =>
                    setCurrentMenu("measurementHistory-menu")
                }
            >
                MEASUREMENT HISTORY
            </div>

            <div className={`nav-icon-container ${
                        (isAuthScreen || !menuSideNavOpen) ? "hidden" : ""
                    } ${showSettingsPopup ? "active" : ""}`}>
                <SettingsIcon className={`nav-icon ${
                        (isAuthScreen || !menuSideNavOpen) ? "hidden" : ""
                    } ${showSettingsPopup ? "active" : ""}`}
                    onClick={() => setShowSettingsPopup(true)}
                />
            </div>

            <div className={`nav-icon-container ${
                isAuthScreen ? "hidden" : ""
            } ${showUserPopup ? "active" : ""}`}>
                <UserIcon className={`nav-icon ${
                        isAuthScreen ? "hidden" : ""
                    } ${showUserPopup ? "active" : ""}`}
                    onClick={() => setShowUserPopup(true)}
                />
            </div>

        </div>
    );
}

export default QSideBarMenu;