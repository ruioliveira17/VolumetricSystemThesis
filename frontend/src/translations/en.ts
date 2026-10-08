const en = {
    yes: "Yes",
    no: "No",
    systemLoader: {
        initializing: "INITIALIZING",
        waitAMoment: "Please wait a moment..."
    },
    error_and_info_messages: {
        serverConnectionError: "Server connection error.",
        error: "Error",
        loginWelcome: "Welcome!",
        loginInsertCredentials: "Please enter your login credentials.",

        loginFailed: "An error occurred while logging in.",

        registerFailed: "An error occurred while registering the user.",
        registerSuccess: "New user registered successfully.",

        errorFillAllFields: "Please fill in all fields.",
        invalidUsernameOrPassword: "Invalid username or password.",
        passwordRequirements: "The password must have at least 8 characters, one uppercase letter, one number, and one special character.",
        passwordsDoNotMatch: "Passwords do not match!",
        currentPasswordInvalid: "The current password is invalid.",
        newPasswordCannotBeSame: "The new password cannot be the same as the current one.",

        resetTokenExpired: "The password reset code has expired. Please generate a new one.",
        sessionExpired: "Session expired. Please log in again.",

        changePasswordError: "An error occurred while trying to change the password.",
        changePasswordSuccess: "Password changed successfully.",

        systemNotCalibrated: "The system was not calibrated.",
        systemCalibratedSuccess: "The system was calibrated successfully.",
        centerPointNotAligned: "The center point is not aligned.",
        workspaceNotEmpty: "The workspace is not empty.",
        workspaceNotEmptyAndCenterPointNotAligned: "The center point is not aligned and the workspace is not empty.",

        saveMeasurementError: "Could not save the measurement.",
        saveMeasurementSuccess: "Measurement saved ",
        measurementLoadError: "Could not load measurements.",
        measurementDeleteError: "Could not delete the measurement.",
        measurementsDeleteError: "Could not delete all measurements.",

        adminNeededError: "Admin privileges required.",
        usersLoadError: "Could not load users.",
        userDeleteError: "Could not delete the user.",
        userAlreadyExists: "Username already exists.",
        userChangeRoleError: "Could not update the user role.",
        userNotFound: "User not found.",

        exposureTimeValuesType: "Only integer values are allowed for the exposure time.",
        exposureTimeValuesRange: "Exposure Time values must be between {{min}} and {{max}}.",
        exposureTimeSuccess: "Exposure Time updated successfully.",

        countdownTimerValuesType: "Only integer values are allowed for the countdown timer.",
        countdownTimerValuesRange: "Countdown Timer values must be between 0 and 10.",
        countdownTimerSuccess: "Countdown Timer updated successfully.",
    },
    login: {
        title: "Log In",
        username: "Username",
        password: "Password",
        noAccount: "No account yet?",
        register: "Register",
        loginButton: "Log In"
    },
    register: {
        title: "Register",
        username: "Username",
        password: "Password",
        confirmPassword: "Confirm Password",
        haveAnAccount: "Already have an account?",
        loginButton: "Log In",
        registerButton: "Register"
    },
    changePassword: {
        title: "Change Password",
        username: "Username",
        currentPassword: "Current Password",
        newPassword: "New Password",
        confirmNewPassword: "Confirm New Password",
        confirmButton: "Confirm"
    },
    topBar:{
        volume: "Volume",
        calibration: "Calibration",
        measurementHistory: "Measurement History"
    },
    calibration: {
        title: "Calibration",
        titleInfo: "Calibrates the workspace based on the detected area.",
        procedureSteps: "Steps to perform the calibration:",
        procedureSteps1: "1 - In \"Color Pick\" mode, select a point in the camera image that matches the platform's color.",
        procedureSteps2: "2 - If necessary, use \"Adjust\" mode to manually adjust the detected points.",
        selectColorButton: "Color Pick",
        adjustButton: "Adjust",
        calibrateButton: "Calibrate"
    },
    confirmCalibration: {
        title: "Confirm Calibration",
        subtitle: "Do you want to confirm the changes?",
    },
    volumeMenu: {
        title: "Volume",
        titleInfo: "Calculates the volume of the objects on the platform.",
        weightBar: "WEIGHT:",
        volumeButton: "Get Volume",
        objects: "Objects:",
        width: "Width (cm)",
        length: "Length (cm)",
        height: "Height (cm)",
        volume_m: "Volume (m³)",
        volume_cm :"Volume (cm³)",
        weight: "Weight (kg)",
        totalWeight: "TOTAL WEIGHT:",
        totalVolume: "TOTAL VOLUME:",
        outOfWSArea: "There are objects outside the workspace area.",
        outOfWSArea_Help: "To detect them, make sure they are inside the workspace area.",
        failedToIdentify: "Failed to identify any objects."
    },
    measurementInfo: {
        title: "Measurement Info",
        objects: "Objects:",
        width: "Width (cm)",
        length: "Length (cm)",
        height: "Height (cm)",
        volume_m: "Volume (m³)",
        volume_cm :"Volume (cm³)",
        weight: "Weight (kg)",
        totalWeight: "TOTAL WEIGHT:",
        totalVolume: "TOTAL VOLUME:"
    },
    measurementHistory: {
        title: "Measurement History",
        titleInfo: "Shows the data of the measurements made in the last 90 days.",
        labelTimePeriod: "Period",
        labelSortBy: "Sort By",
        labelSearchBy: "Search By",
        labelSearchBar: "Search...",
        headerUser: "User",
        headerMeasurementMode: "Measurement Mode",
        headerObjects: "No. of Objects",
        headerTotalVolume: "Total Volume",
        headerWeight: "Weight",
        headerMeasurementDate: "Measurement Date",
        deleteAllButton: "Delete All",
        deleteButton: "Delete"
    },
    measurementSearchOptions: {
        all: "All",
        today: "Today",
        yesterday: "Yesterday",
        thisWeek: "This Week",
        thisMonth: "This Month",
        lastMonths: "Last 3 Months",
        date: "Date",
        measurementMode: "Measurement Mode",
        objectNumber: "No. of Objects",
        user: "User"
    },
    settings: {
        title: "Settings",
        language: "Language",
        exposureType: "Exposure Type",
        exposureTime: "Exposure Time",
        volumeMode: "Measurement Mode",
        countdownTimer: "Countdown Timer",
        set: "Set",
        preferences: "Preferences",
        videoSize: "Video Size"
    },
    windowResizer: {
        title: "Window Resizer",
        cancelButton: "Cancel",
        revertButton: "Revert",
        confirmButton: "Confirm"
    },
    update: {
        title: "Update System",
        subtitle: "Are you sure you want to update the system?",
        version: "Version",
        newUpdateAvailable: "New Update Available",
        about: "About",
        update: "Update",
    },
    power: {
        title: "Power Options",
        subtitle: "What do you want to do?",
        shutdown: "Shut Down",
        restart: "Restart",
        confirmShutdown: "Are you sure you want to shut down?",
        confirmRestart: "Are you sure you want to restart?",
    },
    userMenu: {
        user: "User:",
        role: "Role:",
        changePassword: "Change Password",
        manageUsers: "Manage Users",
        logout: "Log Out",
        loading: "Loading...",
        headerUser: "User",
        headerRole: "Role",
        generateToken: "Generate Code",
        noUsers: "No other users."
    }
}

export default en;
