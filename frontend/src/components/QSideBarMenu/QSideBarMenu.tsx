import "./QSideBarMenu.css";

interface QSideBarMenuProps {
    isAuthScreen: boolean;
    menuSideNavOpen: boolean;
    lockMenu: boolean;

    currentMenu: string;

    setCurrentMenu: (menu: string) => void;

    setShowSettingsPopup: (value: boolean) => void;
    setShowUserPopup: (value: boolean) => void;
}


function QSideBarMenu({
    isAuthScreen,
    menuSideNavOpen,
    lockMenu,
    currentMenu,
    setCurrentMenu,
    setShowSettingsPopup,
    setShowUserPopup
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


            <img
                src="/settings.svg"
                className={`nav-icon ${
                    (isAuthScreen || !menuSideNavOpen)
                        ? "hidden"
                        : ""
                }`}
                alt="Settings"
                onClick={() => setShowSettingsPopup(true)}
            />


            <img
                src="/user.svg"
                className={`nav-icon ${
                    isAuthScreen ? "hidden" : ""
                }`}
                alt="User"
                onClick={() => setShowUserPopup(true)}
            />

        </div>
    );
}

export default QSideBarMenu;