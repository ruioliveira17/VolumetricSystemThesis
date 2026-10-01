const es = {
    yes: "Sí",
    no: "No",
    systemLoader: {
        initializing: "INICIALIZANDO",
        waitAMoment: "Espere un momento, por favor..."
    },
    error_and_info_messages: {
        serverConnectionError: "Error de conexión con el servidor.",
        error: "Error",
        loginWelcome: "¡Bienvenido!",
        loginInsertCredentials: "Introduzca sus credenciales de acceso.",

        loginFailed: "Se ha producido un error al iniciar sesión.",

        registerFailed: "Se ha producido un error al registrar el usuario.",
        registerSuccess: "Nuevo usuario registrado correctamente.",

        errorFillAllFields: "Rellene todos los campos.",
        invalidUsernameOrPassword: "Nombre de usuario o contraseña no válidos.",
        passwordRequirements: "La contraseña debe tener al menos 8 caracteres, una letra mayúscula, un número y un carácter especial.",
        passwordsDoNotMatch: "¡Las contraseñas no coinciden!",
        currentPasswordInvalid: "La contraseña actual no es válida.",
        newPasswordCannotBeSame: "La nueva contraseña no puede ser igual a la actual.",

        resetTokenExpired: "El código de restablecimiento de la contraseña ha caducado. Genere uno nuevo.",
        sessionExpired: "La sesión ha caducado. Vuelva a iniciar sesión.",

        changePasswordError: "Se ha producido un error al intentar cambiar la contraseña.",
        changePasswordSuccess: "Contraseña cambiada correctamente.",

        systemNotCalibrated: "El sistema no se ha calibrado.",
        systemCalibratedSuccess: "El sistema se ha calibrado correctamente.",
        centerPointNotAligned: "El punto central no está alineado.",
        workspaceNotEmpty: "El área de trabajo no está vacía.",
        workspaceNotEmptyAndCenterPointNotAligned: "El punto central no está alineado y el área de trabajo no está vacía.",

        saveMeasurementError: "No se ha podido guardar la medición.",
        saveMeasurementSuccess: "Medición guardada ",
        measurementLoadError: "No se han podido cargar las mediciones.",
        measurementDeleteError: "No se ha podido eliminar la medición.",
        measurementsDeleteError: "No se han podido eliminar todas las mediciones.",

        adminNeededError: "Se requieren privilegios de administrador.",
        usersLoadError: "No se han podido cargar los usuarios.",
        userDeleteError: "No se ha podido eliminar el usuario.",
        userAlreadyExists: "El nombre de usuario ya existe.",
        userChangeRoleError: "No se ha podido actualizar el rol del usuario.",
        userNotFound: "Usuario no encontrado.",

        exposureTimeValuesType: "Solo se permiten valores enteros para el tiempo de exposición.",
        exposureTimeValuesRange: "Los valores del Tiempo de Exposición deben estar entre 100 y 2000.",
        exposureTimeSuccess: "Tiempo de Exposición actualizado correctamente.",

        countdownTimerValuesType: "Solo se permiten valores enteros para la cuenta atrás.",
        countdownTimerValuesRange: "Los valores de la Cuenta Atrás deben estar entre 0 y 10.",
        countdownTimerSuccess: "Cuenta Atrás actualizada correctamente.",
    },
    login: {
        title: "Iniciar Sesión",
        username: "Nombre de usuario",
        password: "Contraseña",
        noAccount: "¿No tiene una cuenta?",
        register: "Registrarse",
        loginButton: "Iniciar Sesión"
    },
    register: {
        title: "Registro",
        username: "Nombre de usuario",
        password: "Contraseña",
        confirmPassword: "Confirmar Contraseña",
        haveAnAccount: "¿Ya tiene una cuenta?",
        loginButton: "Iniciar Sesión",
        registerButton: "Registrarse"
    },
    changePassword: {
        title: "Cambiar Contraseña",
        username: "Nombre de usuario",
        currentPassword: "Contraseña Actual",
        newPassword: "Nueva Contraseña",
        confirmNewPassword: "Confirmar Nueva Contraseña",
        confirmButton: "Confirmar"
    },
    topBar:{
        volume: "Volumen",
        calibration: "Calibración",
        measurementHistory: "Historial de Mediciones"
    },
    calibration: {
        title: "Calibración",
        titleInfo: "Calibra el área de trabajo en función del área detectada.",
        procedureSteps: "Pasos para realizar la calibración:",
        procedureSteps1: "1 - En el modo \"Seleccionar Color\", seleccione un punto de la imagen de la cámara que corresponda al color de la plataforma.",
        procedureSteps2: "2 - Si es necesario, utilice el modo \"Ajustar\" para ajustar manualmente los puntos detectados.",
        selectColorButton: "Seleccionar Color",
        adjustButton: "Ajustar",
        calibrateButton: "Calibrar"
    },
    confirmCalibration: {
        title: "Confirmar Calibración",
        subtitle: "¿Desea confirmar los cambios?",
    },
    volumeMenu: {
        title: "Volumen",
        titleInfo: "Calcula el volumen de los objetos que hay en la plataforma.",
        weightBar: "PESO:",
        volumeButton: "Obtener Volumen",
        objects: "Objetos:",
        width: "Ancho (cm)",
        length: "Largo (cm)",
        height: "Alto (cm)",
        volume_m: "Volumen (m³)",
        volume_cm :"Volumen (cm³)",
        weight: "Peso (kg)",
        totalWeight: "PESO TOTAL:",
        totalVolume: "VOLUMEN TOTAL:",
        outOfWSArea: "Hay objetos fuera del área de trabajo.",
        outOfWSArea_Help: "Para detectarlos, asegúrese de que estén dentro del área de trabajo.",
        failedToIdentify: "No se ha podido identificar ningún objeto."
    },
    measurementInfo: {
        title: "Información de la Medición",
        objects: "Objetos:",
        width: "Ancho (cm)",
        length: "Largo (cm)",
        height: "Alto (cm)",
        volume_m: "Volumen (m³)",
        volume_cm :"Volumen (cm³)",
        weight: "Peso (kg)",
        totalWeight: "PESO TOTAL:",
        totalVolume: "VOLUMEN TOTAL:"
    },
    measurementHistory: {
        title: "Historial de Mediciones",
        titleInfo: "Muestra los datos de las mediciones realizadas en los últimos 90 días.",
        labelTimePeriod: "Período",
        labelSortBy: "Ordenar Por",
        labelSearchBy: "Buscar Por",
        labelSearchBar: "Buscar...",
        headerUser: "Usuario",
        headerMeasurementMode: "Modo de Medición",
        headerObjects: "N.º de Objetos",
        headerTotalVolume: "Volumen Total",
        headerWeight: "Peso",
        headerMeasurementDate: "Fecha de Medición",
        deleteAllButton: "Eliminar Todo",
        deleteButton: "Eliminar"
    },
    measurementSearchOptions: {
        all: "Todos",
        today: "Hoy",
        yesterday: "Ayer",
        thisWeek: "Esta Semana",
        thisMonth: "Este Mes",
        lastMonths: "Últimos 3 Meses",
        date: "Fecha",
        measurementMode: "Modo de Medición",
        objectNumber: "N.º de Objetos",
        user: "Usuario"
    },
    settings: {
        title: "Configuración",
        language: "Idioma",
        exposureType: "Tipo de Exposición",
        exposureTime: "Tiempo de Exposición",
        volumeMode: "Modo de Medición",
        countdownTimer: "Cuenta Atrás",
        set: "Establecer",
        preferences: "Preferencias",
        videoSize: "Tamaño del Vídeo"
    },
    windowResizer: {
        title: "Redimensionar Ventana",
        cancelButton: "Cancelar",
        revertButton: "Revertir",
        confirmButton: "Confirmar"
    },
    update: {
        title: "Actualizar sistema",
        subtitle: "¿Está seguro de que desea actualizar el sistema?",
        version: "Versión",
        newUpdateAvailable: "Nueva actualización disponible",
        about: "Acerca de",
        update: "Actualizar",
    },
    power: {
        title: "Opciones de Energía",
        subtitle: "¿Qué desea hacer?",
        shutdown: "Apagar",
        restart: "Reiniciar",
        confirmShutdown: "¿Seguro que desea apagar?",
        confirmRestart: "¿Seguro que desea reiniciar?",
    },
    userMenu: {
        user: "Usuario:",
        role: "Rol:",
        changePassword: "Cambiar Contraseña",
        manageUsers: "Gestionar Usuarios",
        logout: "Cerrar Sesión",
        loading: "Cargando...",
        headerUser: "Usuario",
        headerRole: "Rol",
        generateToken: "Generar Código",
        noUsers: "No hay otros usuarios."
    }
}

export default es;
