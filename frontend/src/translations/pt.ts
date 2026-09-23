const pt = {
    systemLoader: {
        initializing: "INICIANDO",
        waitAMoment: "Por favor, aguarde..."
    },
    error_and_info_messages: {
        serverConnectionError: "Erro de conexão ao servidor",
        error: "Erro",
        loginWelcome: "Bem-vindo!",
        loginInsertCredentials: "Por favor, insira as suas credenciais.",

        loginFailed: "Ocorreu um erro enquanto iniciava sessão.",

        registerFailed: "Ocorreu um erro ao registar o utilizador.",
        registerSuccess: "Novo utilizador registado com sucesso.",

        errorFillAllFields: "Por favor, preencha todos os campos.",
        invalidUsernameOrPassword: "Utilizador ou palavra-passe inválida.",
        passwordRequirements: "A palavra-passe deve conter 8 caráteres, 1 letra maiúscula, 1 número e 1 caratér especial.",
        passwordsDoNotMatch: "As palavras-passe não coincidem!",
        currentPasswordInvalid: "Palavra-passe atual inválida.",
        newPasswordCannotBeSame: "A nova palavra-passe não pode ser a mesma que a atual.",

        resetTokenExpired: "O reset token expirou. Por favor, gere outro.",
        sessionExpired: "Sessão expirada. Por favor, inicie a sessão outra vez.",

        changePasswordError: "Alterar a palavra-passe falhou.",
        changePasswordSuccess: "Palavra-Passe alterada com sucesso.",
        
        systemNotCalibrated: "O sistema não foi calibrado.",
        systemCalibratedSuccess: "O sistema foi calibrado com sucesso.",
        centerPointNotAligned: "O centro ótico não está alinhado.",
        workspaceNotEmpty: "O espaço de trabalho não está vazio.",
        workspaceNotEmptyAndCenterPointNotAligned: "O centro ótico não está alinhado e o espaço de trabalho não está vazio.",

        saveMeasurementError: "Não foi possível guuardar a medição.",
        saveMeasurementSuccess: "Medição (#{{id}}) salva.",
        measurementLoadError: "Não foi possível carregar as medições.",
        measurementDeleteError: "Não foi possível apagar a medição.",
        measurementsDeleteError: "Não foi possível apagar todas as medições.",

        adminNeededError: "São necessários previlégios de administrador.",
        usersLoadError: "Não foi possível carregar os utilizadores.",
        userDeleteError: "Não foi possível apagar o utilizador.",
        userAlreadyExists: "Já existe esse utilizador.",
        userChangeRoleError: "Não foi possível atualizar o cargo do utilizador.",
        userNotFound: "Utilizador não encontrado.",

        exposureTimeValuesType: "Apenas valores inteiros são permitidos para o tempo de exposição.",
        exposureTimeValuesRange: "Os valores do tempo de exposição deve estar entre 100 e 2000.",
        exposureTimeSuccess: "O tempo de exposição foi alterado com sucesso.",

        countdownTimerValuesType: "Apenas valores inteiros são permitidos para o temporizador.",
        countdownTimerValuesRange: "Os valores do temporizador devem estar entre 0 e 10.",
        countdownTimerSuccess: "O valor do temporizador foi alterado com sucesso.",
    },
    login: {
        title: "Iniciar Sessão",
        username: "Utilizador",
        password: "Palavra-Passe",
        noAccount: "Não tem conta?",
        register: "Registar",
        loginButton: "Iniciar Sessão"
    },
    register: {
        title: "Registar",
        username: "Utilizador",
        password: "Palavra-Passe",
        confirmPassword: "Confirmar Palavra-Passe",
        haveAnAccount: "Já tem uma conta?",
        loginButton: "Iniciar Sessão",
        registerButton: "Registar"
    },
    changePassword: {
        title: "Alterar Palavra-Passe",
        username: "Utilizador",
        currentPassword: "Palavra-Passe Atual",
        newPassword: "Nova Palavra-Passe",
        confirmNewPassword: "Confirmar Nova Palavra-Passe",
        confirmButton: "Confirmar"
    },
    topBar:{
        volume: "Volume",
        calibration: "Calibração",
        measurementHistory: "Histórico de Medições"
    },
    calibration: {
        title: "Calibração",
        titleInfo: "Calibra o espaço de trabalho com base na área detetada",
        procedureSteps: "Passos para realizar a calibração:",
        procedureSteps1: "1 - No modo \"Picar Cor\", selecione um ponto na imagem que corresponda à cor da plataforma.",
        procedureSteps2: "2 - Se necessário, o modo \"Ajustar\" permite-o ajustar manualmente os pontos obtidos no passo anterior.",
        selectColorButton: "Picar Cor",
        adjustButton: "Ajustar",
        calibrateButton: "Calibrar"
    },
    confirmCalibration: {
        title: "Confirmar Calibração",
        subtitle: "Deseja confirmar as alterações?",
        confirmText: "Sim",
        cancelText: "Não"
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
        outOfWSArea: "Existem objetos fora do espaço de trabalho.",
        outOfWSArea_Help: "Para detetá-los, certifique-se de que estejam dentro.",
        failedToIdentify: "Falha ao identificar objetos."
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
        titleInfo: "Apresenta os dados das medições realizadas nos últimos 90 dias.",
        labelTimePeriod: "Período",
        labelSortBy: "Ordenar Por",
        labelSearchBy: "Procurar Por",
        labelSearchBar: "Procurar...",
        headerUser: "Utilizador",
        headerMeasurementMode: "Modo de Medição",
        headerObjects: "No. de Objetos",
        headerTotalVolume: "Volume Total",
        headerWeight: "Peso",
        headerMeasurementDate: "Data de Medição",
        deleteAllButton: "Apagar Tudo",
        deleteButton: "Apagar"
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
        objectNumber: "No. de Objetos",
        user: "Utilizador"
    },
    settings: {
        title: "Configurações",
        language: "Idioma",
        exposureType: "Tipo de Exposição",
        exposureTime: "Tempo de Exposição",
        volumeMode: "Modo de Medição",
        countdownTimer: "Temporizador",
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
    userMenu: {
        user: "Utilizador:",
        role: "Cargo:",
        changePassword: "Alterar Palavra-Passe",
        manageUsers: "Gerenciar Utilizadores",
        logout: "Encerrar Sessão",
        loading: "A carregar...",
        headerUser: "Utilizador",
        headerRole: "Cargo",
        generateToken: "Gerar Token",
        noUsers: "Não existem mais utilizadores."
    }
}

export default pt;