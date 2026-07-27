import { useEffect, useRef, useState } from "react";
import "./styles/global.css";
import "./styles/common.css";

// --------------------------------------------------------------------- //
// |                            Imports                                | //
// --------------------------------------------------------------------- //
import { QLogin, QRegister } from "./components/QLogin";
import { QVolume } from "./components/QVolume";
// --------------------------------------------------------------------- //
// |                           Interfaces                              | //
// --------------------------------------------------------------------- //

interface Message {
  type: string;
  text: string;
}

interface SavedUser {
  username: string;
  role: string;
}

interface MeasurementData {
    volume_mode: string;
    weight: number;
    objects: {
        idx: number;
        volume_m: number;
        volume_cm: number;
        x_cm: number;
        y_cm: number;
        z_cm: number;
        extra: unknown;
    }[];
}

// --------------------------------------------------------------------- //
// |                           Variables                               | //
// --------------------------------------------------------------------- //
function App(){
    const API_URL: string = import.meta.env.VITE_API_URL;

    // -----------------------------
    // Messages variables
    // -----------------------------

    const TextServerConnection: Message = {
        text: "Server connection error",
        type: "error"
    };

    const TextError: Message = {
        text: "Error", 
        type: "error"
    };

    const TextClear: Message = {
        text: "",
        type: "info"
    };

    const TextLoginWelcome: Message = {
        text: "Welcome!", 
        type: "info"
    };
    
    const TextLoginCredentials: Message = {
        text: "Please insert your login credentials.", 
        type: "info"
    };

    const TextFillAllFields: Message = {
        text: "Please fill all fields",
        type: "error"
    };

    const TextRegistrationError: Message = {
        text: "Registration failed", 
        type: "error"
    };
    
    const TextRegistrationSuccessfull: Message = {
        text: "Registration successful", 
        type: "info"
    };

    const TextNoObjectsDetected: Message = {
        text: "Failed to identify any object!", 
        type: "error"
    };

    const TextOutOfLine: Message = {
        text: "There are objects outside the workspace area. To detect them, make sure they are inside.",
        type: "error"
    };

    // -----------------------------
    // Server variables
    // -----------------------------

    const [appReady, setAppReady] = useState<boolean>(true);

    const [message, setMessage] = useState<Message[]>([]);

    // -----------------------------
    // Intervals
    // -----------------------------
    const tokenCheckInterval = useRef<ReturnType<typeof setInterval> | null>(null);
    const cameraLoopInterval = useRef<ReturnType<typeof setInterval> | null>(null);

    // -----------------------------
    // Login variables
    // -----------------------------
    const [username, setUsername] = useState<string>("");
    const [password, setPassword] = useState<string>("");

    const [savedUser, setSavedUser] = useState<SavedUser | null>(null);

    const [usernameFormError, setUsernameFormError] = useState<boolean>(false);
    const [passwordFormError, setPasswordFormError] = useState<boolean>(false);

    const [usernameFocus, setUsernameFocus] = useState<boolean>(false);
    const [passwordFocus, setPasswordFocus] = useState<boolean>(false);

    // -----------------------------
    // Register variables
    // -----------------------------
    const [regUsername, setRegUsername] = useState<string>("");
    const [regEmail, setRegEmail] = useState<string>("");
    const [regPassword, setRegPassword] = useState<string>("");
    const [regConfirmPassword, setRegConfirmPassword] = useState<string>("");

    const [regUsernameFocus, setRegUsernameFocus] = useState<boolean>(false);
    const [regPasswordFocus, setRegPasswordFocus] = useState<boolean>(false);
    const [regConfirmPasswordFocus, setRegConfirmPasswordFocus] = useState<boolean>(false);

    const [regUsernameFormError, setRegUsernameFormError] = useState<boolean>(false);
    const [regPasswordFormError, setRegPasswordFormError] = useState<boolean>(false);
    const [regConfirmPasswordFormError, setRegConfirmPasswordFormError] = useState<boolean>(false);

    // -----------------------------
    // Side Nav variables
    // -----------------------------
    const toggleMenu = () => setMenuSideNavOpen(prev => !prev);
    const [menuSideNavOpen, setMenuSideNavOpen] = useState<boolean>(false);

    // -----------------------------
    // Menu variables
    // -----------------------------
    const [currentMenu, setCurrentMenu] = useState<string>("login-menu");
    const [lockMenu, setLockMenu] = useState<boolean>(false);

    // -----------------------------
    // Config variables
    // -----------------------------
    const [expHDR, setExpHDR] = useState(false);
    const [volBundleMode, setVolBundleMode] = useState<boolean>(false);
    const [volumeMode, setVolumeMode] = useState<string>("multi_bundle");
    const [speedMode, setSpeedMode] = useState("fast");
    const [cropArea, setCropArea] = useState(null);
    const [lastVideoCrop, setLastVideoCrop] = useState(null);

    // -----------------------------
    // Video variables
    // -----------------------------

    const pc = useRef<RTCPeerConnection | null>(null);

    const cameraStream = useRef<MediaStream | null>(null);

    const cameraVideo = useRef<HTMLVideoElement | null>(null);

    // -----------------------------
    // Volume variables
    // -----------------------------
    const [objectList, setObjectList] = useState<any[]>([]);
    const [selectedObject, setSelectedObject] = useState<string>("");

    const [volInfo, setVolInfo] = useState<any>(null);

    const [loadingVolume, setLoadingVolume] = useState<boolean>(false);
    const [processingMessage, setProcessingMessage] = useState<string>("");

    const [showCamera, setShowCamera] = useState<boolean>(true);

    const [objectImage, setObjectImage] = useState<string | null>(null);

    const [cropVideoReady, setCropVideoReady] = useState<boolean>(false);

    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    const [cropTransform, setCropTransform] = useState<React.CSSProperties | undefined>(undefined);

    

    const [weightInfo, setWeightInfo] = useState<any>(null);

    const [weightStable, setWeightStable] = useState<boolean>(false);

    const [multipleVolumeData, setVolumeData] = useState<any>(null);

    const [objCenters, setObjCenters] = useState<any[]>([]);
    const [objAngles, setObjAngles] = useState<any[]>([]);

    const [countdown, setCountdown] = useState<number | null>(null);

    

    // -----------------------------
    // Saving Measurement variables
    // -----------------------------

    const [savingMeasurement, setSavingMeasurement] = useState<boolean>(false);

    // -----------------------------
    // Calibration variables
    // -----------------------------
    const [rgb, setRgb] = useState({
        r: 0,
        g: 0,
        b: 0
    });

    // -----------------------------
    // User variables
    // -----------------------------
    const [showUserPopup, setShowUserPopup] = useState<boolean>(false);

    // --------------------------------------------------------------------- //
    // |                          Use Effects                              | //
    // --------------------------------------------------------------------- //

    useEffect(() => {
        async function init() {
        let serverReady = false;

        while (!serverReady){
            serverReady = await waitForServer();

            if (!serverReady) {
            console.error("Servidor indisponível");
            }
        }

        const storedUser = localStorage.getItem("current_user");

        if (!storedUser) {
        setAppReady(true);
        return;
        }

        const user = JSON.parse(storedUser);

        setSavedUser(user);

        restoreSession();

        setAppReady(true);
        }

        init();
    }, []);

    useEffect(() => {
        if (currentMenu === "login-menu") {
            setMessage([TextLoginWelcome, TextLoginCredentials]);
        }

        if (currentMenu === "login-menu" || currentMenu === "register") {
            return;
        }

        refreshAccessToken();
        setMessage([TextClear]);

        // if (currentMenu === "calibration-menu") {
        //     workspaceDrawing();

        //     if (calibrationImage.current) {
        //         calibrationImage.current.crossOrigin = "anonymous";
        //         calibrationImage.current.src = `${API_URL}/calibrationCTD`;
        //     }
        // }

        // if (currentMenu === "measurementHistory-menu") {
        //     loadMeasurements();
        // }

        // if (
        //     currentMenu === "config-menu" ||
        //     currentMenu === "calibration-menu"
        // ) {
        //     refreshToggles();
        // }

        return () => {
            if (cameraLoopInterval.current) {
                clearInterval(cameraLoopInterval.current);
                cameraLoopInterval.current = null;
            }
        };

    }, [currentMenu]);

    useEffect(() => {
        if (currentMenu === "config-menu" || currentMenu === "calibration-menu") {

            // const interval = setInterval(async () => {
            //     refreshToggles();
            // }, 500);

            // return () => {
            // clearInterval(interval);
            // };

        } else if (currentMenu === "volume-menu") {

            const interval = setInterval(async () => {
            try {
                const access_token = localStorage.getItem("access_token");

                const dataResponse = await fetch(
                `${API_URL}/weight`,
                {
                    headers: {
                    "Authorization": `Bearer ${access_token}`
                    }
                }
                );

                const weightData = await dataResponse.json();

                setWeightInfo(weightData);
                setWeightStable(weightData.flags["stable"]);

            } catch (error) {
                console.error("Weight info error:", error);
            }

            }, 500);

            return () => {
            clearInterval(interval);
            };
        }

        }, [currentMenu]);

    useEffect(() => {
        if (savingMeasurement) {
            setMessage([
                {
                    text: "Saving...",
                    type: "info"
                }
            ]);
        }
    }, [savingMeasurement]);

    useEffect(() => {
        if (!showCamera) return;

        if (cameraVideo.current && pc.current?.getReceivers) {
            const receivers = pc.current.getReceivers();
            const stream = new MediaStream();

            receivers.forEach((r) => {
                if (r.track) {
                    stream.addTrack(r.track);
                }
            });

            cameraVideo.current.srcObject = stream;
        }
    }, [showCamera]);

    useEffect(() => {
        const handleMenu = async (): Promise<void> => {

            if (currentMenu === "volume-menu") {
                startWebRTC("volume");

            } else if (currentMenu === "calibration-menu") {
                startWebRTC("calibration");

            } else {
                stopWebRTC();
            }
        };

        handleMenu();

    }, [currentMenu]);

    useEffect(() => {
        if (!loadingVolume) return;

        const interval = setInterval(async () => {
            try {
                const access_token = localStorage.getItem("access_token");

                const response = await fetch(
                    `${API_URL}/volume/status`,
                    {
                        headers: {
                            Authorization: `Bearer ${access_token}`,
                        },
                    }
                );

                const data = await response.json();

                setProcessingMessage(data.status);

            } catch (error) {
                console.error(error);
            }
        }, 100);

        return () => clearInterval(interval);

    }, [loadingVolume]);

    // Show Volume Info Depending of the selected object
    useEffect(() => {
        if (!selectedObject || !multipleVolumeData) return;

        const objData = multipleVolumeData[selectedObject];
        if (!objData) return;

        setVolInfo({
            volume_m: objData.volume_m,
            volume_cm: objData.volume_cm,
            width: objData.x,
            length: objData.y,
            height: objData.z
        });

        setObjCenters(objData.obj_center ?? []);
        setObjAngles(objData.obj_angles ?? []);
    }, [selectedObject, multipleVolumeData]);

    // --------------------------------------------------------------------- //
    // |                           Functions                               | //
    // --------------------------------------------------------------------- //

    // Server Starting Helper
    const waitForServer = async (maxAttempts: number = 20, delay: number = 1000): Promise<boolean> => {
        for (let i = 0; i < maxAttempts; i++) {
            try {
                const res = await fetch(`${API_URL}/status`);

                if (res.ok) {
                    return true;
                }
            } catch (err) {
                // servidor ainda desligado
            }

            await new Promise<void>((resolve) => setTimeout(resolve, delay));
        }

        return false;
    };

    // Error Helper
    function errorText(
        detail: unknown,
        fallback: string
    ): string {

        if (typeof detail === "string") {
            return detail;
        }

        if (Array.isArray(detail)) {
            return detail
                .map(e => (e && typeof e === "object" && "msg" in e)
                ? String(e.msg)
                : JSON.stringify(e)
                )
                .join("; ");
        }

        return fallback;
    }
 
    // Token Functions
    async function refreshAccessToken(): Promise<boolean> {
        const refreshToken = localStorage.getItem("refresh_token");

        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${API_URL}/refresh`,{
                method: "POST",
                headers: {
                "Content-Type": "application/json"
                },
                body: JSON.stringify({
                refresh_token: refreshToken
                })
            });


            if (response.ok) {
                const data = await response.json();

                localStorage.setItem(
                    "access_token",
                    data.access_token
                );

                localStorage.setItem(
                    "refresh_token",
                    data.refresh_token
                );

                return true;
            }

        } catch (e) {
            console.warn("Refresh error:", e);
            logout();
            return false;
        }
            return false;
    }

    // Restore Session Algorithm
    async function restoreSession() {
        let access_token = localStorage.getItem("access_token");
        const refresh_token = localStorage.getItem("refresh_token");

        if (!access_token && !refresh_token) {
            logout();
            return;
        }

        try {
            let res = await fetch(`${API_URL}/calibration/status`, {
                headers: {
                "Authorization": `Bearer ${access_token}`
                }
            });

            if (res.status === 401) {
                const refreshed = await refreshAccessToken();
                if (!refreshed) {
                    setCurrentMenu("login-menu");
                    return;
                }
                access_token = localStorage.getItem("access_token");
                res = await fetch(`${API_URL}/calibration/status`, {
                    headers: {
                        "Authorization": `Bearer ${access_token}`
                    }
                });
                if (res.status === 401) {
                    setCurrentMenu("login-menu");
                    return;
                }
            }

            const data = await res.json();

            if (!data.calibrated) {
                setCurrentMenu("calibration-menu");
                setLockMenu(true);
            } else {
                setCurrentMenu("volume-menu");
                setLockMenu(false);
                setRgb({
                    r: data.colorRGB[0],
                    g: data.colorRGB[1],
                    b: data.colorRGB[2]
                });
            }

            const config_res = await fetch(`${API_URL}/configuration/status`, {
                headers: {
                "Authorization": `Bearer ${access_token}`
                }
            });

            if (config_res.status === 401) {
                return;
            }

            const config_data = await config_res.json();

            if (config_data.configured) {
                if (config_data.expositionMode === "HDR") {
                    setExpHDR(true);
                } else if (config_data.expositionMode === "Fixed Exposition") {
                    setExpHDR(false);
                }

                if (config_data.volumeMode === "Single Bundle") {
                    setVolumeMode("single_bundle");
                    setVolBundleMode(true);
                } else if (config_data.volumeMode === "Multi Bundle") {
                    setVolumeMode("multi_bundle");
                    setVolBundleMode(false);
                } else if (config_data.volumeMode === "Real") {
                    setVolumeMode("real");
                    setVolBundleMode(false);
                } else if (config_data.volumeMode === "Individual") {
                    setVolumeMode("individual");
                    setVolBundleMode(false);
                }

                if (config_data.speedMode === "Slow"){
                    setSpeedMode("slow");
                } else if (config_data.speedMode === "Intermedium"){
                    setSpeedMode("intermedium");
                } else if (config_data.speedMode === "Fast"){
                    setSpeedMode("fast");
                }

                if (config_data.cropArea && config_data.cropWindow){
                    setCropArea(config_data.cropArea);
                    setLastVideoCrop(config_data.cropWindow);
                }
            }

            setMenuSideNavOpen(true);

        } catch (err) {
            setCurrentMenu("login-menu");
        }
    }

    // Check Calibration Helper
    async function checkCalibration(): Promise<void> {
        refreshAccessToken();

        const access_token = localStorage.getItem("access_token");

        if (!access_token) {
            throw new Error("No access token");
        }

        const res = await fetch(
            `${API_URL}/calibration/status`,
            {
                headers: {
                "Authorization": `Bearer ${access_token}`
                }
            }
        );

        const data = await res.json();

        if (!data.calibrated) {
            setCurrentMenu("calibration-menu");
            setLockMenu(true);
        } else {
            setCurrentMenu("volume-menu");
            setLockMenu(false);

            setRgb({
                r: data.colorRGB[0],
                g: data.colorRGB[1],
                b: data.colorRGB[2]
            });
        }
    }

    // Show Screen Functions
    function showRegisterScreen(): void {
        setCurrentMenu("register");
        setMessage([TextClear]);
        setUsername("");
        setPassword("");
        setRegUsernameFocus(false);
        setRegPasswordFocus(false);
        setRegConfirmPasswordFocus(false);

        setRegUsernameFormError(false);
        setRegPasswordFormError(false);
        setRegConfirmPasswordFormError(false);
    }

    function showLoginScreen(): void {
        setCurrentMenu("login-menu");
        setMessage([TextClear]);
        setRegUsername("");
        setRegEmail("");
        setRegPassword("");
        setRegConfirmPassword("");
        setMenuSideNavOpen(false);
        setUsernameFocus(false);
        setPasswordFocus(false);

        setUsernameFormError(false);
        setPasswordFormError(false);
    }

    // Login Algorithm
    async function login(): Promise<void> {
        if (!username || !password) {
            setMessage([TextFillAllFields]);
            setUsernameFormError(true);
            setPasswordFormError(true);
            return;
        }

        try {
            const response = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();

                const role: string = data.role;
                const savedUsername: string = data.username;

                const currentUser = {
                    username: savedUsername,
                    role
            };

            localStorage.setItem(
                "current_user",
                JSON.stringify(currentUser)
            );

            setSavedUser(currentUser);

            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);

            await checkCalibration();

            setMenuSideNavOpen(true);

            setMessage([TextClear]);

            } else {
                const data = await response.json();

                setMessage([
                    {
                    text: errorText(data.detail, TextServerConnection.text),
                    type: "error"
                    }
                ]);

                setUsernameFormError(true);
                setPasswordFormError(true);
            }

        } catch {
            setMessage([TextServerConnection]);
        }
    }

    // Register Algorithm
    async function register(): Promise<void> {
        if (!regUsername || !regPassword || !regConfirmPassword) {
            setMessage([TextFillAllFields]);

            setRegUsernameFormError(true);
            setRegPasswordFormError(true);
            setRegConfirmPasswordFormError(true);
            return;
        }

        if (regPassword !== regConfirmPassword) {
            setMessage([
                {
                text: "Passwords do not match!",
                type: "error",
                },
            ]);

            setRegUsernameFormError(true);
            setRegPasswordFormError(true);
            setRegConfirmPasswordFormError(true);
            return;
        }

        try {
            const response = await fetch(`${API_URL}/register`, {method: "POST", headers: {"Content-Type": "application/json",},
                body: JSON.stringify({
                    username: regUsername,
                    email: regEmail,
                    password: regPassword,
                    confirm_password: regConfirmPassword,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                setMessage([
                    {
                    text: errorText(data.detail, TextRegistrationError.text),
                    type: "error",
                    },
                ]);

                setRegUsernameFormError(true);
                setRegPasswordFormError(true);
                setRegConfirmPasswordFormError(true);
                return;
            }

        } catch (error) {
            setMessage([TextServerConnection]);

            setRegUsernameFormError(true);
            setRegPasswordFormError(true);
            setRegConfirmPasswordFormError(true);
            return;
        }

        setMessage([TextRegistrationSuccessfull]);

        showLoginScreen();
    }

    // Logout Algorithm
    function logout(): void {
        if (tokenCheckInterval.current) {
            clearInterval(tokenCheckInterval.current);
            tokenCheckInterval.current = null;
        }

        if (cameraLoopInterval.current) {
            clearInterval(cameraLoopInterval.current);
            cameraLoopInterval.current = null;
        }

        localStorage.removeItem("current_user");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        setUsername("");
        setPassword("");
        setCurrentMenu("login-menu");
        setSavedUser(null);
        setMenuSideNavOpen(false);
        setShowUserPopup(false);
        setObjectList([]);
        setSelectedObject("");
        setVolInfo(null);
        setVolumeData(null);
        setRegUsernameFocus(false);
        setRegPasswordFocus(false);
        setRegConfirmPasswordFocus(false);
        setUsernameFormError(false);
        setPasswordFormError(false);
        setRegUsernameFormError(false);
        setRegPasswordFormError(false);
        setRegConfirmPasswordFormError(false);
        }

    // Start Video Connection Algorithm
    async function startWebRTC(streamType: string): Promise<void> {
        const access_token = localStorage.getItem("access_token");

        if (!access_token) {
            throw new Error("No access token");
        }

        pc.current = new RTCPeerConnection();

        pc.current.addTransceiver('video', { direction: 'recvonly' });

        pc.current.ontrack = async (event) => {
            cameraStream.current = event.streams[0];

            if(cameraVideo.current){
                cameraVideo.current.srcObject = cameraStream.current;
                cameraVideo.current.muted = true;

                try {
                    await cameraVideo.current.play();
                } catch (e) {
                    console.log("PLAY ERROR:", e);
                }
            }
        };

        const offer = await pc.current.createOffer();
        await pc.current.setLocalDescription(offer);

        const localDescription = pc.current.localDescription;

        if (!localDescription) {
            throw new Error("Local description not available");
        }

        const response = await fetch(`${API_URL}/offer`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${access_token}`
            },
            body: JSON.stringify({
                sdp: localDescription.sdp,
                type: localDescription.type,
                stream: streamType
            })
        });

        const answer = await response.json();

        await pc.current.setRemoteDescription(answer);
    }

    // Stop Video Connection Algorithm
    function stopWebRTC(): void {
        const video = cameraVideo.current;

        if (video && video.srcObject) {
            const stream = video.srcObject as MediaStream;

            stream.getTracks().forEach((track: MediaStreamTrack) => {
                track.stop();
            });
            video.srcObject = null;
        }

        if (pc.current) {
            pc.current.ontrack = null;
            pc.current.close();
            pc.current = null;
        }
    }

    // Volume Click Algorithm
    async function volume_click(): Promise<void> {
        try {
            const start = performance.now();

            setObjectList([]);
            setSelectedObject("");
            setMessage([TextClear]);
            setVolInfo(null);
            setVolumeData(null);
            setObjectImage(null);
            setShowCamera(true);

            refreshAccessToken();

            const access_token = localStorage.getItem("access_token");

            if (!access_token) {
                throw new Error("No access token");
            }

            const response = await fetch(
                `${API_URL}/volume/mode`,
                {
                    headers: {
                        "Authorization": `Bearer ${access_token}`
                    }
                }
            );

            if (response.status === 401) {
                throw new Error("Session expired");
            }

            const countResp = await fetch(
                `${API_URL}/countdown/value`,
                {
                    headers: {
                        "Authorization": `Bearer ${access_token}`
                    }
                }
            );

            const countData = await countResp.json();

            for (let i = countData.countdown; i > 0; i--) {
                setCountdown(i);

                await new Promise<void>(resolve =>
                    setTimeout(resolve, 1000)
                );
            }

            fetch(
                `${API_URL}/volume/clickTimestamp`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${access_token}`
                    }
                }
            );

            const aftercountdown = performance.now();

            setCountdown(null);

            setLoadingVolume(true);

            const volumeMode = await response.json();

            if (volumeMode["Volume Mode"] === "Single Bundle") {
                await volumeSingleBundle(access_token);
            } else if (volumeMode["Volume Mode"] === "Multi Bundle") {
                await volumeMultiBundle(access_token);
            } else if (volumeMode["Volume Mode"] === "Real") {
                await volumeReal(access_token);
            } else if (volumeMode["Volume Mode"] === "Individual") {
                await volumeIndividual(access_token);
            }

            const end = performance.now();

            console.log(
                "After Countdown UI TIME:",
                end - aftercountdown,
                "ms"
            );

            console.log(
                "TOTAL UI TIME:",
                end - start,
                "ms"
            );

        } catch (error) {
            console.warn(error);
        }
    }

    // Single Bundle Volume Algorithm
    async function volumeSingleBundle(access_token: string): Promise<void> {
        try {
            await fetch(
                `${API_URL}/volume/singleBundle`,
                {
                    method: "POST",
                    mode: "no-cors",
                    headers: {
                        "Authorization": `Bearer ${access_token}`
                    }
                }
            );

            const response = await fetch(
                `${API_URL}/getObjectsOutOfLine`,
                {
                    headers: {
                        "Authorization": `Bearer ${access_token}`
                    }
                }
            );

            const data = await response.json();

            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);


            if (objectsOutOfLine.length > 0) {
                setMessage([TextOutOfLine]);

            } else {
                setMessage([TextClear]);

                const dataResponse = await fetch(
                    `${API_URL}/volume/singleBundle/results`,
                    {
                        headers: {
                            "Authorization": `Bearer ${access_token}`
                        }
                    }
                );

                const volumeData = await dataResponse.json();

                const bundle = volumeData.Bundle;


                if (
                    bundle.volume_m === 0 ||
                    bundle.volume_cm === 0 ||
                    bundle.x === 0 ||
                    bundle.y === 0 ||
                    bundle.z === 0
                ) {
                    setMessage([TextNoObjectsDetected]);

                } else {

                    const measurementData = {
                        volume_mode: "Single Bundle",
                        weight: Number(weightInfo.weight),
                        objects: [
                            {
                                idx: 1,
                                volume_m: bundle.volume_m,
                                volume_cm: bundle.volume_cm,
                                x_cm: bundle.x,
                                y_cm: bundle.y,
                                z_cm: bundle.z,
                                extra: null
                            }
                        ]
                    };

                    saveMeasurement(measurementData);

                    setVolInfo({
                        volume_m: bundle.volume_m,
                        volume_cm: bundle.volume_cm,
                        width: bundle.x,
                        length: bundle.y,
                        height: bundle.z
                    });
                }
            }
            
            const imgResp = await fetch(
                `${API_URL}/getFrame/detectedObjectsFrame`,
                {
                    headers: {
                        "Authorization": `Bearer ${access_token}`
                    }
                }
            );

            if (imgResp.status === 404) {
                throw new Error("Frame not Available");
            }


            const blob = await imgResp.blob();

            const url = URL.createObjectURL(blob);

            setObjectImage(url);
            setShowCamera(false);


        } catch (error) {
            setMessage([TextError]);
            console.error(error);

        } finally {
            console.log("Finished");
            setLoadingVolume(false);
        }
    }

    // Save the current measurement (objects + snapshot images) in the database
    async function saveMeasurement(measurementData: MeasurementData): Promise<void> {
        try {
            setMessage([TextClear]);
            setSavingMeasurement(true);

            await refreshAccessToken();

            const access_token = localStorage.getItem("access_token");

            if (!access_token) {
                throw new Error("No access token");
            }

            const res = await fetch(`${API_URL}/saveMeasurements`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${access_token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(measurementData)
            });


            if (res.ok) {
                const data = await res.json();

                setMessage([
                    {
                        text: `Measurement saved (#${data.id}).`,
                        type: "info"
                    }
                ]);

            } else if (res.status === 401) {

                setMessage([
                    {
                        text: "Session expired. Please login again.",
                        type: "error"
                    }
                ]);

            } else {

                const data = await res.json().catch(() => ({}));

                setMessage([
                    {
                        text: errorText(
                            data.detail,
                            "Could not save the measurement."
                        ),
                        type: "error"
                    }
                ]);
            }


        } catch (e) {

            setMessage([
                {
                    text: "Server connection error.",
                    type: "error"
                }
            ]);

        } finally {
            setSavingMeasurement(false);
        }
    }

    // Multi Bundle Volume Algorithm
    async function volumeMultiBundle(access_token: string): Promise<void> {
        try {
            await fetch(`${API_URL}/volume/multiBundle`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });

            const response = await fetch(`${API_URL}/getObjectsOutOfLine`, { headers: { "Authorization": `Bearer ${access_token}` } });
            const data = await response.json();

            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);

            if (objectsOutOfLine.length > 0) {
                setMessage([TextOutOfLine]);
            } else {
                setMessage([TextClear]);
            }

            const dataResponse = await fetch(`${API_URL}/volume/multiBundle/results`, { headers: { "Authorization": `Bearer ${access_token}` } });
            const volumeData = await dataResponse.json();

            setVolumeData(volumeData);

            const imgResp = await fetch(`${API_URL}/getFrame/detectedObjectsFrame`, { headers: { "Authorization": `Bearer ${access_token}` } });
            if (imgResp.status === 404) throw new Error("Frame not Available");

            const blob = await imgResp.blob();
            const url = URL.createObjectURL(blob);
            setObjectImage(url);
            setShowCamera(false);

            const objIdentified = Object.keys(volumeData).filter((key: string) => key !== "Total");

            if (objIdentified.length === 0) {
                setMessage([TextNoObjectsDetected]);
            } else if (objIdentified.length === 1) {
                const key = objIdentified[0];
                const objData = volumeData[key];

                setSelectedObject(key);
                setObjectList([key]);
                setVolInfo({
                    volume_m: objData.volume_m,
                    volume_cm: objData.volume_cm,
                    width: objData.x,
                    length: objData.y,
                    height: objData.z
                });
            } else if (objIdentified.length > 1) {
                setObjectList(objIdentified);
                setSelectedObject("");
                setVolInfo(null);
            }

            if (objIdentified.length > 0) {
                const objects = Object.entries(volumeData)
                    .filter(([key]) => key !== "Total")
                    .map(([key, obj]: [string, any]) => ({
                        idx: Number(key),
                        volume_m: obj.volume_m,
                        volume_cm: obj.volume_cm,
                        x_cm: obj.x,
                        y_cm: obj.y,
                        z_cm: obj.z,
                        extra: null
                    }));

                const measurementData: MeasurementData = {
                    volume_mode: "Multi Bundle",
                    weight: Number(weightInfo.weight),
                    objects
                };

                saveMeasurement(measurementData);
            }

        } catch (error) {
            setVolInfo(null);
            setMessage([TextError]);
            console.error(error);
        } finally {
            setLoadingVolume(false);
        }
    }

    // Real Volume Algorithm
    async function volumeReal(access_token: string): Promise<void> {
        try {
            await fetch(`${API_URL}/volume/real`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });

            const response = await fetch(`${API_URL}/getObjectsOutOfLine`, { headers: { "Authorization": `Bearer ${access_token}` } });
            const data = await response.json();

            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);

            if (objectsOutOfLine.length > 0) {
                setMessage([TextOutOfLine]);
            } else {
                setMessage([TextClear]);
            }

            const dataResponse = await fetch(`${API_URL}/volume/real/results`, { headers: { "Authorization": `Bearer ${access_token}` } });
            const volumeData = await dataResponse.json();

            setVolumeData(volumeData);

            const imgResp = await fetch(`${API_URL}/getFrame/detectedObjectsFrame`, { headers: { "Authorization": `Bearer ${access_token}` } });
            if (imgResp.status === 404) throw new Error("Frame not Available");

            const blob = await imgResp.blob();
            const url = URL.createObjectURL(blob);
            setObjectImage(url);
            setShowCamera(false);

            const objIdentified = Object.keys(volumeData).filter((key: string) => key !== "Total");

            if (objIdentified.length === 0) {
                setMessage([TextNoObjectsDetected]);
            } else if (objIdentified.length === 1) {
                const key = objIdentified[0];
                const objData = volumeData[key];

                setObjCenters(objData.obj_center ?? []);
                setObjAngles(objData.obj_angles ?? []);

                setSelectedObject(key);
                setObjectList([key]);
                setVolInfo({
                    volume_m: objData.volume_m,
                    volume_cm: objData.volume_cm,
                    width: objData.x,
                    length: objData.y,
                    height: objData.z
                });
            } else if (objIdentified.length > 1) {
                setObjectList(objIdentified);
                setSelectedObject("");
                setVolInfo(null);
            }

            if (objIdentified.length > 0) {
                const objects = Object.entries(volumeData)
                    .filter(([key]) => key !== "Total")
                    .map(([key, obj]: [string, any]) => ({
                        idx: Number(key),
                        volume_m: obj.volume_m,
                        volume_cm: obj.volume_cm,
                        x_cm: obj.x,
                        y_cm: obj.y,
                        z_cm: obj.z,
                        extra: {
                            angles: obj.obj_angles,
                            centers: obj.obj_center
                        }
                    }));

                const measurementData: MeasurementData = {
                    volume_mode: "Real",
                    weight: Number(weightInfo.weight),
                    objects
                };

                saveMeasurement(measurementData);
            }

        } catch (error) {
            setVolInfo(null);
            setMessage([TextError]);
            console.error(error);
        } finally {
            setLoadingVolume(false);
        }
    }

    // Individual Volume Algorithm
    async function volumeIndividual(access_token: string): Promise<void> {
        try {
            await fetch(`${API_URL}/volume/individual`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });

            const response = await fetch(`${API_URL}/getObjectsOutOfLine`, { headers: { "Authorization": `Bearer ${access_token}` } });
            const data = await response.json();

            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);

            if (objectsOutOfLine.length > 0) {
                setMessage([TextOutOfLine]);
            } else {
                setMessage([TextClear]);
            }

            const dataResponse = await fetch(`${API_URL}/volume/individual/results`, { headers: { "Authorization": `Bearer ${access_token}` } });
            const volumeData = await dataResponse.json();

            setVolumeData(volumeData);

            const imgResp = await fetch(`${API_URL}/getFrame/detectedObjectsFrame`, { headers: { "Authorization": `Bearer ${access_token}` } });
            if (imgResp.status === 404) throw new Error("Frame not Available");

            const blob = await imgResp.blob();
            const url = URL.createObjectURL(blob);
            setObjectImage(url);
            setShowCamera(false);

            const objIdentified = Object.keys(volumeData).filter((key: string) => key !== "Total");

            if (objIdentified.length === 1) {
                const key = objIdentified[0];
                const objData = volumeData[key];

                setSelectedObject(key);
                setObjectList([key]);
                setVolInfo({
                    volume_m: objData.volume_m,
                    volume_cm: objData.volume_cm,
                    width: objData.x,
                    length: objData.y,
                    height: objData.z
                });
            } else if (objIdentified.length > 1) {
                setObjectList(objIdentified);
                setSelectedObject("");
                setVolInfo(null);
            }

            // NOTE (port): no App.py original o modo Individual chamava saveMeasurement()
            // sem argumentos (nunca construía measurementData) - guardar nunca chegou a
            // ser implementado para este modo. Deixado por implementar de propósito.

        } catch (error) {
            setVolInfo(null);
            setMessage([TextError]);
            console.error(error);
        } finally {
            setLoadingVolume(false);
        }
    }

    if (appReady){
        return (
            <>
                {currentMenu === "login-menu" && (
                    <QLogin
                        message={message}

                        username={username}
                        setUsername={setUsername}

                        password={password}
                        setPassword={setPassword}

                        usernameFormError={usernameFormError}
                        setUsernameFormError={setUsernameFormError}

                        passwordFormError={passwordFormError}
                        setPasswordFormError={setPasswordFormError}

                        usernameFocus={usernameFocus}
                        setUsernameFocus={setUsernameFocus}

                        passwordFocus={passwordFocus}
                        setPasswordFocus={setPasswordFocus}

                        login={login}

                        showRegisterScreen={showRegisterScreen}
                    />
                )}

                {currentMenu === "register" && (
                    <QRegister
                        message={message}
                        regUsername={regUsername}
                        regPassword={regPassword}
                        regConfirmPassword={regConfirmPassword}
                        setRegUsername={setRegUsername}
                        setRegPassword={setRegPassword}
                        setRegConfirmPassword={setRegConfirmPassword}
                        regUsernameFormError={regUsernameFormError}
                        regPasswordFormError={regPasswordFormError}
                        regConfirmPasswordFormError={regConfirmPasswordFormError}
                        setRegUsernameFormError={setRegUsernameFormError}
                        setRegPasswordFormError={setRegPasswordFormError}
                        setRegConfirmPasswordFormError={setRegConfirmPasswordFormError}
                        regUsernameFocus={regUsernameFocus}
                        regPasswordFocus={regPasswordFocus}
                        regConfirmPasswordFocus={regConfirmPasswordFocus}
                        setRegUsernameFocus={setRegUsernameFocus}
                        setRegPasswordFocus={setRegPasswordFocus}
                        setRegConfirmPasswordFocus={setRegConfirmPasswordFocus}
                        register={register}
                        showLoginScreen={showLoginScreen}
                    />
                )}

                {currentMenu === "volume-menu" && (
                    <QVolume
                        message={message}

                        loadingVolume={loadingVolume}
                        processingMessage={processingMessage}

                        showCamera={showCamera}
                        setShowCamera={setShowCamera}

                        cameraVideo={cameraVideo}
                        objectImage={objectImage}
                        cropVideoReady={cropVideoReady}
                        setCropVideoReady={setCropVideoReady}
                        cropTransform={cropTransform}

                        volBundleMode={volBundleMode}

                        volume_click={volume_click}

                        weightStable={weightStable}

                        volInfo={volInfo}
                        multipleVolumeData={multipleVolumeData}

                        canvasRef={canvasRef}

                        objectList={objectList}
                        selectedObject={selectedObject}
                        setSelectedObject={setSelectedObject}

                        countdown={countdown}

                        weightInfo={weightInfo}

                        volumeMode={volumeMode}
                        toggleMenu={toggleMenu}
                        setVolInfo={setVolInfo}
                    />
                )}
            </>
        );
    }
}

export default App;