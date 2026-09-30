const fr = {
    systemLoader: {
        initializing: "INITIALISATION",
        waitAMoment: "Veuillez patienter un instant..."
    },
    error_and_info_messages: {
        serverConnectionError: "Erreur de connexion au serveur.",
        error: "Erreur",
        loginWelcome: "Bienvenue !",
        loginInsertCredentials: "Veuillez saisir vos identifiants de connexion.",

        loginFailed: "Une erreur s'est produite lors de la connexion.",

        registerFailed: "Une erreur s'est produite lors de l'inscription de l'utilisateur.",
        registerSuccess: "Nouvel utilisateur inscrit avec succès.",

        errorFillAllFields: "Veuillez remplir tous les champs.",
        invalidUsernameOrPassword: "Nom d'utilisateur ou mot de passe invalide.",
        passwordRequirements: "Le mot de passe doit contenir au moins 8 caractères, une lettre majuscule, un chiffre et un caractère spécial.",
        passwordsDoNotMatch: "Les mots de passe ne correspondent pas !",
        currentPasswordInvalid: "Le mot de passe actuel est invalide.",
        newPasswordCannotBeSame: "Le nouveau mot de passe ne peut pas être identique au mot de passe actuel.",

        resetTokenExpired: "Le code de réinitialisation du mot de passe a expiré. Veuillez en générer un nouveau.",
        sessionExpired: "Session expirée. Veuillez vous reconnecter.",

        changePasswordError: "Une erreur s'est produite lors de la modification du mot de passe.",
        changePasswordSuccess: "Mot de passe modifié avec succès.",

        systemNotCalibrated: "Le système n'a pas été calibré.",
        systemCalibratedSuccess: "Le système a été calibré avec succès.",
        centerPointNotAligned: "Le point central n'est pas aligné.",
        workspaceNotEmpty: "La zone de travail n'est pas vide.",
        workspaceNotEmptyAndCenterPointNotAligned: "Le point central n'est pas aligné et la zone de travail n'est pas vide.",

        saveMeasurementError: "Impossible d'enregistrer la mesure.",
        saveMeasurementSuccess: "Mesure enregistrée ",
        measurementLoadError: "Impossible de charger les mesures.",
        measurementDeleteError: "Impossible de supprimer la mesure.",
        measurementsDeleteError: "Impossible de supprimer toutes les mesures.",

        adminNeededError: "Privilèges d'administrateur requis.",
        usersLoadError: "Impossible de charger les utilisateurs.",
        userDeleteError: "Impossible de supprimer l'utilisateur.",
        userAlreadyExists: "Ce nom d'utilisateur existe déjà.",
        userChangeRoleError: "Impossible de mettre à jour le rôle de l'utilisateur.",
        userNotFound: "Utilisateur introuvable.",

        exposureTimeValuesType: "Seules les valeurs entières sont autorisées pour le temps d'exposition.",
        exposureTimeValuesRange: "Les valeurs du Temps d'exposition doivent être comprises entre 100 et 2000.",
        exposureTimeSuccess: "Temps d'exposition mis à jour avec succès.",

        countdownTimerValuesType: "Seules les valeurs entières sont autorisées pour le compte à rebours.",
        countdownTimerValuesRange: "Les valeurs du Compte à rebours doivent être comprises entre 0 et 10.",
        countdownTimerSuccess: "Compte à rebours mis à jour avec succès.",
    },
    login: {
        title: "Connexion",
        username: "Nom d'utilisateur",
        password: "Mot de passe",
        noAccount: "Vous n'avez pas de compte ?",
        register: "S'inscrire",
        loginButton: "Se connecter"
    },
    register: {
        title: "Inscription",
        username: "Nom d'utilisateur",
        password: "Mot de passe",
        confirmPassword: "Confirmer le mot de passe",
        haveAnAccount: "Vous avez déjà un compte ?",
        loginButton: "Se connecter",
        registerButton: "S'inscrire"
    },
    changePassword: {
        title: "Modifier le mot de passe",
        username: "Nom d'utilisateur",
        currentPassword: "Mot de passe actuel",
        newPassword: "Nouveau mot de passe",
        confirmNewPassword: "Confirmer le nouveau mot de passe",
        confirmButton: "Confirmer"
    },
    topBar:{
        volume: "Volume",
        calibration: "Calibrage",
        measurementHistory: "Historique des mesures"
    },
    calibration: {
        title: "Calibrage",
        titleInfo: "Calibre la zone de travail en fonction de la zone détectée.",
        procedureSteps: "Étapes pour effectuer le calibrage :",
        procedureSteps1: "1 - En mode \"Sélection de couleur\", sélectionnez un point de l'image de la caméra correspondant à la couleur de la plateforme.",
        procedureSteps2: "2 - Si nécessaire, utilisez le mode \"Ajuster\" pour ajuster manuellement les points détectés.",
        selectColorButton: "Sélection de couleur",
        adjustButton: "Ajuster",
        calibrateButton: "Calibrer"
    },
    confirmCalibration: {
        title: "Confirmer le calibrage",
        subtitle: "Voulez-vous confirmer les modifications ?",
        confirmText: "Oui",
        cancelText: "Non"
    },
    volumeMenu: {
        title: "Volume",
        titleInfo: "Calcule le volume des objets présents sur la plateforme.",
        weightBar: "POIDS :",
        volumeButton: "Obtenir le volume",
        objects: "Objets :",
        width: "Largeur (cm)",
        length: "Longueur (cm)",
        height: "Hauteur (cm)",
        volume_m: "Volume (m³)",
        volume_cm :"Volume (cm³)",
        weight: "Poids (kg)",
        totalWeight: "POIDS TOTAL :",
        totalVolume: "VOLUME TOTAL :",
        outOfWSArea: "Des objets se trouvent en dehors de la zone de travail.",
        outOfWSArea_Help: "Pour les détecter, assurez-vous qu'ils se trouvent dans la zone de travail.",
        failedToIdentify: "Aucun objet n'a pu être identifié."
    },
    measurementInfo: {
        title: "Informations de mesure",
        objects: "Objets :",
        width: "Largeur (cm)",
        length: "Longueur (cm)",
        height: "Hauteur (cm)",
        volume_m: "Volume (m³)",
        volume_cm :"Volume (cm³)",
        weight: "Poids (kg)",
        totalWeight: "POIDS TOTAL :",
        totalVolume: "VOLUME TOTAL :"
    },
    measurementHistory: {
        title: "Historique des mesures",
        titleInfo: "Affiche les données des mesures effectuées au cours des 90 derniers jours.",
        labelTimePeriod: "Période",
        labelSortBy: "Trier par",
        labelSearchBy: "Rechercher par",
        labelSearchBar: "Rechercher...",
        headerUser: "Utilisateur",
        headerMeasurementMode: "Mode de mesure",
        headerObjects: "Nombre d'objets",
        headerTotalVolume: "Volume total",
        headerWeight: "Poids",
        headerMeasurementDate: "Date de mesure",
        deleteAllButton: "Tout supprimer",
        deleteButton: "Supprimer"
    },
    measurementSearchOptions: {
        all: "Tout",
        today: "Aujourd'hui",
        yesterday: "Hier",
        thisWeek: "Cette semaine",
        thisMonth: "Ce mois-ci",
        lastMonths: "3 derniers mois",
        date: "Date",
        measurementMode: "Mode de mesure",
        objectNumber: "Nombre d'objets",
        user: "Utilisateur"
    },
    settings: {
        title: "Paramètres",
        language: "Langue",
        exposureType: "Type d'exposition",
        exposureTime: "Temps d'exposition",
        volumeMode: "Mode de mesure",
        countdownTimer: "Compte à rebours",
        set: "Définir",
        preferences: "Préférences",
        videoSize: "Taille de la vidéo"
    },
    windowResizer: {
        title: "Redimensionner la fenêtre",
        cancelButton: "Annuler",
        revertButton: "Rétablir",
        confirmButton: "Confirmer"
    },
    power: {
        title: "Options d'alimentation",
        subtitle: "Que voulez-vous faire ?",
        shutdown: "Éteindre",
        restart: "Redémarrer",
        confirmShutdown: "Voulez-vous vraiment éteindre ?",
        confirmRestart: "Voulez-vous vraiment redémarrer ?",
        yes: "Oui",
        no: "Non",
    },
    userMenu: {
        user: "Utilisateur :",
        role: "Rôle :",
        changePassword: "Modifier le mot de passe",
        manageUsers: "Gérer les utilisateurs",
        logout: "Se déconnecter",
        loading: "Chargement...",
        headerUser: "Utilisateur",
        headerRole: "Rôle",
        generateToken: "Générer un code",
        noUsers: "Aucun autre utilisateur."
    }
}

export default fr;
