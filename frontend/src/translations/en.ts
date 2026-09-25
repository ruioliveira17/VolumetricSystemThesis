const en = {
    systemLoader: {
        initializing: "INITIALIZING",
        waitAMoment: "Please wait a moment..."
    },
    error_and_info_messages: {
        serverConnectionError: "Server connection error",
        error: "Error",
        loginWelcome: "Welcome!",
        loginInsertCredentials: "Please insert your login credentials.",

        loginFailed: "An error occurred while logging in.",

        registerFailed: "An error occurred while registering the user.",
        registerSuccess: "New user registered successfully.",

        errorFillAllFields: "Please fill all fields.",
        invalidUsernameOrPassword: "Invalid username or password.",
        passwordRequirements: "The password must have at least 8 characters, one uppercase letter, one number, and one special character.",
        passwordsDoNotMatch: "Passwords do not match!",
        currentPasswordInvalid: "Current password is invalid.",
        newPasswordCannotBeSame: "New password can't be the same as the current one.",
        
        resetTokenExpired: "Reset token expired. Please generate another.",
        sessionExpired: "Session expired. Please login again.",
        
        changePasswordError: "An error ocurred while trying to change the password.",
        changePasswordSuccess: "Password changed successfully.",

        systemNotCalibrated: "The system was not calibrated.",
        systemCalibratedSuccess: "The system was calibrated successfully.",
        centerPointNotAligned: "Center point isn't aligned.",
        workspaceNotEmpty: "Workspace isn't empty.",
        workspaceNotEmptyAndCenterPointNotAligned: "Center point isn't aligned and workspace isn't empty.",
        
        saveMeasurementError: "Could not save the measurement.",
        saveMeasurementSuccess: "Measurement saved (#{{id}}).",
        measurementLoadError: "Could not load measurements.",
        measurementDeleteError: "Could not delete measurement.",
        measurementsDeleteError: "Could not delete all measurements.",
        
        adminNeededError: "Admin privileges required.",
        usersLoadError: "Could not load users.",
        userDeleteError: "Could not delete user.",
        userAlreadyExists: "Username already exists.",
        userChangeRoleError: "Could not update the user role.",
        userNotFound: "User not found.",

        exposureTimeValuesType: "Only integer values are allowed for exposure time.",
        exposureTimeValuesRange: "Exposure Time values must be between 100 and 2000.",
        exposureTimeSuccess: "Exposure Time updated successfully.",

        countdownTimerValuesType: "Only integer values are allowed for the countdown timer.",
        countdownTimerValuesRange: "Countdown Timer values must be between 0 and 10.",
        countdownTimerSuccess: "Countdown Timer updated successfully.",
    },
    login: {
        title: "Login",
        username: "Username",
        password: "Password",
        noAccount: "Don't have an account?",
        register: "Register",
        loginButton: "Login"
    },
    register: {
        title: "Register",
        username: "Username",
        password: "Password",
        confirmPassword: "Confirm Password",
        haveAnAccount: "Already have an account?",
        loginButton: "Login",
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
        procedureSteps1: "1 - In the \"Color Pick\" mode, select a point in the camera image that corresponds to the platform's color.",
        procedureSteps2: "2 - If necessary, the \"Adjust\" mode grants you the option to manually adjust the points given in the previous step.",
        selectColorButton: "Color Pick",
        adjustButton: "Adjust",
        calibrateButton: "Calibrate"
    },
    confirmCalibration: {
        title: "Confirm Calibration",
        subtitle: "Do you want to confirm the changes?",
        confirmText: "Yes",
        cancelText: "No"
    },
    volumeMenu: {
        title: "Volume",
        titleInfo: "Calculates the volume of objects on the platform",
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
        outOfWSArea_Help: "To detect them, make sure they are inside.",
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
        titleInfo: "Shows the data of the measurements made on the last 90 days.",
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
    power: {
        title: "Power Options",
        subtitle: "What do you want to do?",
        shutdown: "Shutdown",
        restart: "Restart",
        confirmShutdown: "Are you sure you want to shut down?",
        confirmRestart: "Are you sure you want to restart?",
        yes: "Yes",
        no: "No",
    },
    userMenu: {
        user: "User:",
        role: "Role:",
        changePassword: "Change Password",
        manageUsers: "Manage Users",
        logout: "Logout",
        loading: "Loading...",
        headerUser: "User",
        headerRole: "Role",
        generateToken: "Generate Token",
        noUsers: "No other users."
    }
}

export default en;