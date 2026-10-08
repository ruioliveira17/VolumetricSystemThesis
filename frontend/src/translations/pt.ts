const pt = {
    yes: "Sim",
    no: "Não",
    systemLoader: {
        initializing: "A INICIALIZAR",
        waitAMoment: "Por favor, aguarde um momento..."
    },
    error_and_info_messages: {
        serverConnectionError: "Erro de ligação ao servidor",
        error: "Erro",
        loginWelcome: "Bem-vindo!",
        loginInsertCredentials: "Por favor, introduza as suas credenciais de acesso.",

        loginFailed: "Ocorreu um erro ao iniciar sessão.",

        registerFailed: "Ocorreu um erro ao registar o utilizador.",
        registerSuccess: "Novo utilizador registado com sucesso.",

        errorFillAllFields: "Por favor, preencha todos os campos.",
        invalidUsernameOrPassword: "Nome de utilizador ou palavra-passe inválidos.",
        passwordRequirements: "A palavra-passe deve ter, pelo menos, 8 caracteres, uma letra maiúscula, um número e um caráter especial.",
        passwordsDoNotMatch: "As palavras-passe não coincidem!",
        currentPasswordInvalid: "A palavra-passe atual é inválida.",
        newPasswordCannotBeSame: "A nova palavra-passe não pode ser igual à atual.",

        resetTokenExpired: "O código de reposição da palavra-passe expirou. Por favor, gere outro.",
        sessionExpired: "A sessão expirou. Por favor, inicie sessão novamente.",

        changePasswordError: "Ocorreu um erro ao tentar alterar a palavra-passe.",
        changePasswordSuccess: "Palavra-passe alterada com sucesso.",

        systemNotCalibrated: "O sistema não foi calibrado.",
        systemCalibratedSuccess: "O sistema foi calibrado com sucesso.",
        centerPointNotAligned: "O ponto central não está alinhado.",
        workspaceNotEmpty: "A área de trabalho não está vazia.",
        workspaceNotEmptyAndCenterPointNotAligned: "O ponto central não está alinhado e a área de trabalho não está vazia.",

        saveMeasurementError: "Não foi possível guardar a medição.",
        saveMeasurementSuccess: "Medição guardada ",
        measurementLoadError: "Não foi possível carregar as medições.",
        measurementDeleteError: "Não foi possível eliminar a medição.",
        measurementsDeleteError: "Não foi possível eliminar todas as medições.",

        adminNeededError: "São necessários privilégios de administrador.",
        usersLoadError: "Não foi possível carregar os utilizadores.",
        userDeleteError: "Não foi possível eliminar o utilizador.",
        userAlreadyExists: "O nome de utilizador já existe.",
        userChangeRoleError: "Não foi possível atualizar a função do utilizador.",
        userNotFound: "Utilizador não encontrado.",

        exposureTimeValuesType: "Apenas são permitidos valores inteiros para o tempo de exposição.",
        exposureTimeValuesRange: "Os valores do tempo de exposição devem estar entre {{min}} e {{max}}.",
        exposureTimeSuccess: "Tempo de Exposição atualizado com sucesso.",

        countdownTimerValuesType: "Apenas são permitidos valores inteiros para a contagem decrescente.",
        countdownTimerValuesRange: "Os valores da contagem decrescente devem estar entre 0 e 10.",
        countdownTimerSuccess: "Contagem Decrescente atualizada com sucesso.",
    },
    login: {
        title: "Iniciar Sessão",
        username: "Nome de utilizador",
        password: "Palavra-passe",
        noAccount: "Não tem conta?",
        register: "Registar",
        loginButton: "Entrar"
    },
    register: {
        title: "Registar",
        username: "Nome de utilizador",
        password: "Palavra-passe",
        confirmPassword: "Confirmar Palavra-passe",
        haveAnAccount: "Já tem conta?",
        loginButton: "Entrar",
        registerButton: "Registar"
    },
    changePassword: {
        title: "Alterar Palavra-passe",
        username: "Nome de utilizador",
        currentPassword: "Palavra-passe Atual",
        newPassword: "Nova Palavra-passe",
        confirmNewPassword: "Confirmar Nova Palavra-passe",
        confirmButton: "Confirmar"
    },
    topBar:{
        volume: "Volume",
        calibration: "Calibração",
        measurementHistory: "Histórico de Medições"
    },
    calibration: {
        title: "Calibração",
        titleInfo: "Calibra a área de trabalho com base na área detetada.",
        procedureSteps: "Passos para realizar a calibração:",
        procedureSteps1: "1 - No modo \"Selecionar Cor\", selecione um ponto na imagem da câmara que corresponda à cor da plataforma.",
        procedureSteps2: "2 - Se necessário, o modo \"Ajustar\" permite ajustar manualmente os pontos obtidos no passo anterior.",
        selectColorButton: "Selecionar Cor",
        adjustButton: "Ajustar",
        calibrateButton: "Calibrar"
    },
    confirmCalibration: {
        title: "Confirmar Calibração",
        subtitle: "Pretende confirmar as alterações?",
    },
    volumeMenu: {
        title: "Volume",
        titleInfo: "Calcula o volume dos objetos na plataforma",
        weightBar: "PESO:",
        volumeButton: "Obter Volume",
        objects: "Objetos:",
        width: "Largura (cm)",
        length: "Comprimento (cm)",
        height: "Altura (cm)",
        volume_m: "Volume (m³)",
        volume_cm :"Volume (cm³)",
        weight: "Peso (kg)",
        totalWeight: "PESO TOTAL:",
        totalVolume: "VOLUME TOTAL:",
        outOfWSArea: "Existem objetos fora da área de trabalho.",
        outOfWSArea_Help: "Para os detetar, certifique-se de que estão dentro da área.",
        failedToIdentify: "Não foi possível identificar nenhum objeto."
    },
    measurementInfo: {
        title: "Informação da Medição",
        objects: "Objetos:",
        width: "Largura (cm)",
        length: "Comprimento (cm)",
        height: "Altura (cm)",
        volume_m: "Volume (m³)",
        volume_cm :"Volume (cm³)",
        weight: "Peso (kg)",
        totalWeight: "PESO TOTAL:",
        totalVolume: "VOLUME TOTAL:"
    },
    measurementHistory: {
        title: "Histórico de Medições",
        titleInfo: "Mostra os dados das medições efetuadas nos últimos 90 dias.",
        labelTimePeriod: "Período",
        labelSortBy: "Ordenar Por",
        labelSearchBy: "Pesquisar Por",
        labelSearchBar: "Pesquisar...",
        headerUser: "Utilizador",
        headerMeasurementMode: "Modo de Medição",
        headerObjects: "N.º de Objetos",
        headerTotalVolume: "Volume Total",
        headerWeight: "Peso",
        headerMeasurementDate: "Data da Medição",
        deleteAllButton: "Eliminar Tudo",
        deleteButton: "Eliminar"
    },
    measurementSearchOptions: {
        all: "Todos",
        today: "Hoje",
        yesterday: "Ontem",
        thisWeek: "Esta Semana",
        thisMonth: "Este Mês",
        lastMonths: "Últimos 3 Meses",
        date: "Data",
        measurementMode: "Modo de Medição",
        objectNumber: "N.º de Objetos",
        user: "Utilizador"
    },
    settings: {
        title: "Definições",
        language: "Idioma",
        exposureType: "Tipo de Exposição",
        exposureTime: "Tempo de Exposição",
        volumeMode: "Modo de Medição",
        countdownTimer: "Contagem Decrescente",
        set: "Definir",
        preferences: "Preferências",
        videoSize: "Tamanho do Vídeo"
    },
    windowResizer: {
        title: "Redimensionar Janela",
        cancelButton: "Cancelar",
        revertButton: "Reverter",
        confirmButton: "Confirmar"
    },
    update: {
        title: "Atualizar Sistema",
        subtitle: "Tem a certeza de que pretende atualizar o sistema?",
        version: "Versão",
        newUpdateAvailable: "Nova Atualização Disponível",
        about: "Sobre",
        update: "Atualizar",
    },
    power: {
        title: "Opções de Energia",
        subtitle: "O que pretende fazer?",
        shutdown: "Encerrar",
        restart: "Reiniciar",
        confirmShutdown: "Tem a certeza de que pretende encerrar?",
        confirmRestart: "Tem a certeza de que pretende reiniciar?",
    },
    userMenu: {
        user: "Utilizador:",
        role: "Função:",
        changePassword: "Alterar Palavra-passe",
        manageUsers: "Gerir Utilizadores",
        logout: "Terminar Sessão",
        loading: "A carregar...",
        headerUser: "Utilizador",
        headerRole: "Função",
        generateToken: "Gerar Token",
        noUsers: "Não existem outros utilizadores."
    }
}

export default pt;
