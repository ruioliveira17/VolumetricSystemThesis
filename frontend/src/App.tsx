import { useEffect, useRef, useState } from "react";
import "./styles/global.css";
import "./styles/common.css";

import SettingsIcon from '@assets/icons/settings.svg?react';
import UserIcon from '@assets/icons/user.svg?react';

// --------------------------------------------------------------------- //
// |                            Imports                                | //
// --------------------------------------------------------------------- //
import { QChangePassword, QChangePasswordModal, QLogin, QRegister } from "./components/QLogin";
import { QVolume } from "./components/QVolume";
import { QMeasureHistory } from "./components/QMeasureHistory";
import { QCalibration } from "./components/QCalibration";
import { QSettings } from "./components/QSettings";
import { QSystemLoader } from "./components/QSystemLoader";
import { QWindowResizer } from "./components/QWindowResizer";
import { QUserModal, QUserPanel } from "./components/QUser";
import QTopBar from "./components/QTopBar";
import { QToaster, notify } from "./components/QToast";

import {apiFetch, setOnAuthFailure, storeTokens} from "./api/client"
// --------------------------------------------------------------------- //
// |                           Interfaces                              | //
// --------------------------------------------------------------------- //

interface Message {
  type: string;
  text: string;
}

interface SavedUser {
  username: string;
  id: Int16Array;
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

    const TextServerConnection: Message = {text: "Server connection error", type: "error"};
    const TextError: Message = {text: "Error", type: "error"};
    const TextClear: Message = {text: "", type: "info"};

    const TextLoginWelcome: Message = {text: "Welcome!", type: "info"};
    const TextLoginCredentials: Message = {text: "Please insert your login credentials.", type: "info"};
    const TextFillAllFields: Message = {text: "Please fill all fields", type: "error"};

    const TextRegistrationError: Message = {text: "Registration failed", type: "error"};

    const TextResetTokenExpired: Message = {text: "Reset Token expired. Please generate another.", type: "error"};
    const TextChangePasswordError: Message = {text: "Changing Password failed", type: "error"}
    
    const TextNotCalibrated: Message = { text: "System was not Calibrated.", type: "error" };
    const TextCenterNotAligned: Message = { text: "Center Point isn't Aligned.", type: "error" };
    const TextWsNotEmpty: Message = { text: "Workspace isn't Empty.", type: "error" };
    const TextWsNotEmptyAndCenterNotAligned: Message = { text: "Center Point isn't Aligned and Workspace isn't Empty.", type: "error" };

    const ORIGINAL_CROP = { x: 0, y: 0, width: 1600, height: 1200 };
    const DEFAULT_CROP = { x: 15, y: 15, width: 1570, height: 1170 };

    // -----------------------------
    // Server variables
    // -----------------------------

    const [appReady, setAppReady] = useState<boolean>(false);

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
    // Change Password variables
    // -----------------------------

    const [changeUsername, setChangeUsername] = useState<string>("");
    const [changeUserId, setChangeUserId] = useState<string>("");
    const [changeEmail, setChangeEmail] = useState<string>("");

    const [changeCurrentPassword, setChangeCurrentPassword] = useState<string>("");
    const [changePassword, setChangePassword] = useState<string>("");
    const [changeConfirmPassword, setChangeConfirmPassword] = useState<string>("");

    const [changeCurrentPasswordFocus, setChangeCurrentPasswordFocus] = useState<boolean>(false);
    const [changePasswordFocus, setChangePasswordFocus] = useState<boolean>(false);
    const [changeConfirmPasswordFocus, setChangeConfirmPasswordFocus] = useState<boolean>(false);

    const [changeCurrentPasswordFormError, setChangeCurrentPasswordFormError] = useState<boolean>(false);
    const [changePasswordFormError, setChangePasswordFormError] = useState<boolean>(false);
    const [changeConfirmPasswordFormError, setChangeConfirmPasswordFormError] = useState<boolean>(false);
    
    // -----------------------------
    // Side Nav variables
    // -----------------------------
    const toggleMenu = () => setMenuSideNavOpen(prev => !prev);
    const [menuSideNavOpen, setMenuSideNavOpen] = useState<boolean>(false);

    // -----------------------------
    // Menu variables
    // -----------------------------
    const [currentMenu, setCurrentMenu] = useState<string>("login-menu");
    const [lastMenu, setLastMenu] = useState<string>("None");
    const [lockMenu, setLockMenu] = useState<boolean>(false);

    const appContainerRef = useRef<HTMLDivElement>(null);
    const [userAnchorEl, setUserAnchorEl] = useState<HTMLElement | null>(null);
    const [userAnchorRect, setUserAnchorRect] = useState<DOMRect | null>(null);
    const [settingsAnchorEl, setSettingsAnchorEl] = useState<HTMLElement | null>(null);
    const [settingsAnchorRect, setSettingsAnchorRect] = useState<DOMRect | null>(null);

    // -----------------------------
    // Config variables
    // -----------------------------
    const [expHDR, setExpHDR] = useState(false);
    const [volBundleMode, setVolBundleMode] = useState<boolean>(false);
    const [volumeMode, setVolumeMode] = useState<string>("multi_bundle");
    const [speedMode, setSpeedMode] = useState("fast");
    const [cropArea, setCropArea] = useState<any>(DEFAULT_CROP);
    const [lastVideoCrop, setLastVideoCrop] = useState(null);

    const [exposureTime, setExposureTime] = useState<string>("");
    const [countdownTimer, setCountdownTimer] = useState<string>("");

    const [showSettingsPopup, setShowSettingsPopup] = useState<boolean>(false);
    const [showCropWindow, setShowCropWindow] = useState<boolean>(false);
    const [videoCrop, setVideoCrop] = useState<any>(null);

    const ASPECT_RATIO = 4/3;
    const draggingCrop = useRef<boolean>(false);
    const dragOffset = useRef({x: 0, y:0});

    const cropVideo = useRef<HTMLVideoElement | null>(null);
    const cropCanvas = useRef<HTMLCanvasElement | null>(null);
    const selectedCorner = useRef<string | null>(null);

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
    const [measurementWeightInfo, setMeasurementWeightInfo] = useState<any>(null);

    const [weightStable, setWeightStable] = useState<boolean>(false);
    const [weightZero, setWeightZero] = useState<boolean>(false);

    const [multipleVolumeData, setVolumeData] = useState<any>(null);

    const [objCenters, setObjCenters] = useState<any[]>([]);
    const [objAngles, setObjAngles] = useState<any[]>([]);

    const [countdown, setCountdown] = useState<number | null>(null);

    const [noObjectsDetected, setNoObjectsDetected] = useState<boolean>(false);
    const [objectsOutOfLine, setObjectsOutOfLine] = useState<boolean>(false);

    // -----------------------------
    // Calibration variables
    // -----------------------------
    const [rgb, setRgb] = useState({
        r: 0,
        g: 0,
        b: 0
    });

    const [calibrationMode, setCalibrationMode] = useState<string>("auto");
    const [calibrationModalOpen, setCalibrationModalOpen] = useState<boolean>(false);
    const [loadingCalibration, setLoadingCalibration] = useState<boolean>(false);

    const detectionArea = useRef<any>([0, 0, 0, 0]);
    const selectedPoint = useRef<number | null>(null);
    const workspaceCanvas = useRef<HTMLCanvasElement | null>(null);
    const calibrationImage = useRef<HTMLImageElement | null>(null);
    const dragging = useRef<boolean>(false);
    const angleRef = useRef<number>(0.4);
    const lastX = useRef<number>(0);

    // -----------------------------
    // User variables
    // -----------------------------
    const [showUserPopup, setShowUserPopup] = useState<boolean>(false);
    const [showUsersPanel, setShowUsersPanel] = useState<boolean>(false);
    const [showChangePasswordModal, setShowChangePasswordModal] = useState<boolean>(false);
    const [usersList, setUsersList] = useState<any[]>([]);
    const [usersLoading, setUsersLoading] = useState<boolean>(false);
    const [usersMsg, setUsersMsg] = useState<string>("");

    const [resetTokensByUser, setResetTokensByUser] = useState<Record<number, string[]>>({});

    // -----------------------------
    // Measurement History variables
    // -----------------------------
    const [measurementsList, setMeasurementsList] = useState<any[]>([]);
    const [usersIDList, setUsersIDList] = useState<any[]>([]);

    const [sortField, setSortField] = useState<string>("created_at");
    const [sortOrder, setSortOrder] = useState<string>("desc");

    const sortOptions = [
        { label: "Date", value: "created_at" },
        { label: "Measurement Mode", value: "volume_mode" },
        { label: "No. of Objects", value: "object_count" },
        { label: "User", value: "user_id" },
    ];

    const sortedMeasurements = [...measurementsList].sort((a, b) => {
        let comparison = 0;

        switch (sortField) {
            case "created_at":
                comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
                break;
            case "volume_mode":
                comparison = a.volume_mode.localeCompare(b.volume_mode);
                break;
            case "object_count":
                comparison = a.object_count - b.object_count;
                break;
            case "user_id":
                comparison = a.id - b.id;
                break;
            default:
                break;
        }

        return sortOrder === "asc" ? comparison : -comparison;
    });

    const [searchBy, setSearchBy] = useState("all");
    const [searchValue, setSearchValue] = useState("");

    const searchByOptions = [
        { value: "all", label: "All" },
        { value: "mode", label: "Measurement Mode" },
        { value: "object", label: "No. of Objects" },
        { value: "user", label: "User" },
    ];

    const dateOptions = [
        { value: "today", label: "Today" },
        { value: "yesterday", label: "Yesterday" },
        { value: "this_week", label: "This Week" },
        { value: "this_month", label: "This Month" },
        { value: "last_3_months", label: "Last 3 Months" },
    ];

    const [dateFilter, setDateFilter] = useState("last_3_months");

    const isDateInRange = (dateString: string, filter: string) => {
        const date = new Date(dateString);
        const now = new Date();

        date.setHours(0, 0, 0, 0);
        now.setHours(0, 0, 0, 0);

        switch (filter) {
            case "today":
                return date.getTime() === now.getTime();

            case "yesterday": {
                const yesterday = new Date(now);
                yesterday.setDate(now.getDate() - 1);

                return date.getTime() === yesterday.getTime();
            }

            case "this_week": {
                const startOfWeek = new Date(now);
                const day = startOfWeek.getDay();

                const daysFromMonday = day === 0 ? 6 : day - 1;

                startOfWeek.setDate(
                    startOfWeek.getDate() - daysFromMonday
                );

                startOfWeek.setHours(0, 0, 0, 0);

                return date >= startOfWeek && date <= now;
            }

            case "this_month": {
                const startOfMonth = new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    1
                );

                return date >= startOfMonth && date <= now;
            }

            case "last_3_months": {
                const startOf3Months = new Date(now);
                startOf3Months.setMonth(
                    now.getMonth() - 3
                );

                return date >= startOf3Months && date <= now;
            }

            default:
                return true;
        }
    };

    const filteredMeasurements = sortedMeasurements.filter((measurement) => {
        const search = searchValue.trim().toLowerCase();

        const user = usersIDList.find(
            (u) => u.id === measurement.user_id
        );

        const formattedDate = new Date(measurement.created_at)
            .toLocaleString("pt-PT", {
                hour12: false,
            })
            .toLowerCase();

        let matchesSearch = true;

        if (search) {
            switch (searchBy) {
                case "id":
                    matchesSearch = measurement.id
                        .toString()
                        .includes(search);
                    break;

                case "user":
                    matchesSearch =
                        measurement.user_id
                            .toString()
                            .includes(search) ||
                        user?.username
                            .toLowerCase()
                            .includes(search);
                    break;

                case "mode":
                    matchesSearch = measurement.volume_mode
                        .toLowerCase()
                        .includes(search);
                    break;

                case "object":
                    matchesSearch = measurement.object_count
                        .toString()
                        .includes(search);
                    break;

                case "weight":
                    matchesSearch = measurement.weight
                        .toString()
                        .includes(search);
                    break;

                case "all":
                default:
                    matchesSearch =
                        measurement.id
                            .toString()
                            .includes(search) ||
                        measurement.user_id
                            .toString()
                            .includes(search) ||
                        user?.username
                            .toLowerCase()
                            .includes(search) ||
                        measurement.volume_mode
                            .toLowerCase()
                            .includes(search) ||
                        measurement.object_count
                            .toString()
                            .includes(search) ||
                        measurement.weight
                            .toString()
                            .includes(search) ||
                        formattedDate.includes(search);
                    break;
            }
        }

    // -------------------------
    // Date filter
    // -------------------------

    const matchesDate = isDateInRange(
        measurement.created_at,
        dateFilter
    );

    return matchesSearch && matchesDate;
});

    const [selectedID, setSelectedID] = useState<number | null>(null);

    const [measurementConfigModal, setShowMeasurementConfigModal] = useState<boolean>(false);
    const [measurementConfigModalPosition, setMeasurementModalPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
    const toggleMeasurementModal = () => setShowMeasurementConfigModal(prev => !prev);

    const [measurementsConfigModal, setShowMeasurementsConfigModal] = useState<boolean>(false);
    const [measurementsConfigModalPosition, setMeasurementsModalPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
    const toggleMeasurementsModal = () => setShowMeasurementsConfigModal(prev => !prev);

    const [showMeasurementInfo, setShowMeasurementInfo] = useState<boolean>(false);
    const [measureObjectImage, setMeasureObjectImage] = useState<string | null>(null);
    const [measurementMode, setMeasurementMode] = useState<string>("");
    const [measureSelectedObject, setMeasureSelectedObject] = useState<string>("");
    const [measureVolumeInfo, setMeasureVolumeInfo] = useState<any>(null);
    const [measureMultipleVolumeData, setMeasureMultipleVolumeData] = useState<any>(null);
    const [measureObjectList, setMeasureObjectList] = useState<any[]>([]);
    const [measureObjCenters, setMeasureObjCenters] = useState<any[]>([]);
    const [measureObjAngles, setMeasureObjAngles] = useState<any[]>([]);

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

        await loggedIn();

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

        setMessage([TextClear]);

        if (currentMenu === "calibration-menu") {
            workspaceDrawing();

            if (calibrationImage.current) {
                calibrationImage.current.crossOrigin = "anonymous";
                calibrationImage.current.src = `${API_URL}/calibrationCTD`;
            }
        }

        if (currentMenu === "measurementHistory-menu") {
            loadMeasurements();
        }

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
            handleCalibrationModeChange(false);
            const interval = setInterval(async () => {
            try {
                const dataResponse = await apiFetch("/weight");
                const weightData = await dataResponse.json();

                setWeightInfo(weightData);
                setWeightStable(weightData.flags["stable"]);
                setWeightZero(weightData.flags["zero"]);

            } catch (error) {
                console.error("Weight info error:", error);
            }

            }, 500);

            return () => {
            clearInterval(interval);
            };
        } else if (currentMenu === "measurementHistory-menu"){
            handleCalibrationModeChange(false);
        }

    }, [currentMenu]);

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
                const dataResponse = await apiFetch("/volume/status");
                const data = await dataResponse.json();

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

    // Calibration - Automatic color pick (click on the image)
    useEffect(() => {
        if (currentMenu !== "calibration-menu") return;

        const img = calibrationImage.current;
        if (!img) return;

        const handleClick = async (event: MouseEvent) => {
            try {
                const calibRes = await apiFetch("/calibrate/mode");
                const calibData = await calibRes.json();

                const rect = img.getBoundingClientRect();
                const x = Math.round((event.clientX - rect.left) * (img.naturalWidth / rect.width));
                const y = Math.round((event.clientY - rect.top) * (img.naturalHeight / rect.height));

                if (calibData["Calibrate Mode"] === "Automatic") {
                    await apiFetch(
                        "/mask/colorClick",
                        {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({ x, y })
                        }
                    );

                    const canvas = document.createElement("canvas");
                    const ctx = canvas.getContext("2d")!;

                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;
                    ctx.drawImage(img, 0, 0);

                    const pixel = ctx.getImageData(x, y, 1, 1).data;

                    setRgb({
                        r: pixel[0],
                        g: pixel[1],
                        b: pixel[2]
                    });

                    await new Promise<void>(r => setTimeout(r, 500));

                    handleCalibrationModeChange(true);
                }
            } catch (err) {
                console.warn("Erro colorClick:", err);
            }
        };

        img.addEventListener("click", handleClick);

        return () => {
            img.removeEventListener("click", handleClick);
        };

    }, [currentMenu]);

    // Calibration - Manual workspace editing (drag/keyboard on the overlay canvas)
    useEffect(() => {
        if (currentMenu !== "calibration-menu") return;
        if (calibrationMode !== "manual") return;

        const canvas = workspaceCanvas.current;
        const img = calibrationImage.current;

        if (!canvas || !img) return;

        canvas.style.touchAction = "none";

        const ctx = canvas.getContext("2d")!;

        const STEP = 1;

        function resizeCanvas() {
            canvas!.width = img!.naturalWidth;
            canvas!.height = img!.naturalHeight;

            canvas!.style.width = img!.clientWidth + "px";
            canvas!.style.height = img!.clientHeight + "px";

            drawWorkspace();
        }

        function drawWorkspace() {
            ctx.clearRect(0, 0, canvas!.width, canvas!.height);

            const points = detectionArea.current;

            if (!points || points.length === 0) return;

            ctx.beginPath();

            points.forEach((point: any, index: number) => {
                if (index === 0) ctx.moveTo(point[0], point[1]);
                else ctx.lineTo(point[0], point[1]);
            });

            ctx.closePath();

            ctx.strokeStyle = "blue";
            ctx.lineWidth = 5;
            ctx.stroke();

            points.forEach((point: any, index: number) => {
                const radius = selectedPoint.current === index ? 12 : 10;

                ctx.beginPath();
                ctx.arc(point[0], point[1], radius, 0, Math.PI * 2);
                ctx.fillStyle = "black";
                ctx.fill();

                ctx.beginPath();
                ctx.arc(point[0], point[1], radius - 2, 0, Math.PI * 2);
                ctx.fillStyle = selectedPoint.current === index ? "yellow" : "white";
                ctx.fill();

                ctx.globalCompositeOperation = "destination-out";

                ctx.beginPath();
                ctx.arc(point[0], point[1], radius - 6, 0, Math.PI * 2);
                ctx.fill();

                ctx.globalCompositeOperation = "source-over";
            });
        }

        function getPointerPos(e: PointerEvent) {
            const rect = canvas.getBoundingClientRect();

            return {
                x: (e.clientX - rect.left) * canvas.width / rect.width,
                y: (e.clientY - rect.top) * canvas.height / rect.height
            };
        }

        function pointerDown(e: PointerEvent) {
            e.preventDefault();

            const { x, y } = getPointerPos(e);

            let minDist = Infinity;
            let closest: number | null = null;

            detectionArea.current.forEach((point: any, index: number) => {
                const dist = Math.hypot(point[0] - x, point[1] - y);

                if (dist < minDist) {
                    minDist = dist;
                    closest = index;
                }
            });

            if (minDist <= 15 && closest !== null) {
                selectedPoint.current = closest;
                dragging.current = true;

                // Impede que o dedo "escape" do canvas
                canvas.setPointerCapture(e.pointerId);
            } else {
                selectedPoint.current = null;
                dragging.current = false;
            }

            drawWorkspace();
        }

        function pointerMove(e: PointerEvent) {
            if (!dragging.current) return;
            if (selectedPoint.current === null) return;

            e.preventDefault();

            const { x, y } = getPointerPos(e);

            detectionArea.current[selectedPoint.current] = [x, y];

            drawWorkspace();
        }

        function pointerUp(e: PointerEvent) {
            dragging.current = false;

            if (canvas.hasPointerCapture(e.pointerId)) {
                canvas.releasePointerCapture(e.pointerId);
            }

            drawWorkspace();
        }

        function keyDown(e: KeyboardEvent) {
            if (selectedPoint.current === null) return;

            const point = detectionArea.current[selectedPoint.current];

            switch (e.key) {
                case "ArrowLeft":
                    e.preventDefault();
                    point[0] = Math.max(0, point[0] - STEP);
                    break;
                case "ArrowRight":
                    e.preventDefault();
                    point[0] = Math.max(0, point[0] + STEP);
                    break;
                case "ArrowUp":
                    e.preventDefault();
                    point[1] = Math.max(0, point[1] - STEP);
                    break;
                case "ArrowDown":
                    e.preventDefault();
                    point[1] = Math.max(0, point[1] + STEP);
                    break;
                default:
                    return;
            }

            drawWorkspace();
        }

        canvas.addEventListener("pointerdown", pointerDown);
        canvas.addEventListener("pointermove", pointerMove);
        canvas.addEventListener("pointerup", pointerUp);
        canvas.addEventListener("pointercancel", pointerUp);

        window.addEventListener("keydown", keyDown);

        const resizeObserver = new ResizeObserver(() => {
            resizeCanvas();
        });

        resizeObserver.observe(img);

        resizeCanvas();

        return () => {
            canvas.removeEventListener("pointerdown", pointerDown);
            canvas.removeEventListener("pointermove", pointerMove);
            canvas.removeEventListener("pointerup", pointerUp);
            canvas.removeEventListener("pointercancel", pointerUp);
            
            window.removeEventListener("keydown", keyDown);

            resizeObserver.disconnect();

            selectedPoint.current = null;
            dragging.current = false;
        };

    }, [currentMenu, calibrationMode]);

    // Calibration - Load the current detection area (Manual only)
    useEffect(() => {
        if (currentMenu !== "calibration-menu") return;

        const loadWorkspace = async () => {
            const r = await apiFetch("/calibrate/mode");
            const calibData = await r.json();

            if (calibData["Calibrate Mode"] === "Manual") {
                const rParams = await apiFetch("/calibrate/params");
                detectionArea.current = (await rParams.json())["Detected Area"];
                workspaceDrawing();
            }
        };

        loadWorkspace();

    }, [currentMenu, calibrationMode]);

    useEffect(() => {
        if (currentMenu === "volume-menu" && lastVideoCrop !== null) {
            setVideoCrop({
                ...lastVideoCrop,
                videoWidth: cameraVideo.current.videoWidth,
                videoHeight: cameraVideo.current.videoHeight,
                displayWidth: cameraVideo.current.clientWidth,
                displayHeight: cameraVideo.current.clientHeight
            });

            setLastVideoCrop(null);
        }
    }, [currentMenu, cropVideoReady]);

    // Crop - feed the camera stream into the crop preview video
    useEffect(() => {
        if (!showCropWindow) return;

        if (cropVideo.current && cameraStream.current) {
            cropVideo.current.srcObject = cameraStream.current;
            cropVideo.current.play();
        }
    }, [showCropWindow]);

    // Crop - interactive rectangle editor (drag corners)
    useEffect(() => {
        if (currentMenu !== "volume-menu") return;

        const canvas = cropCanvas.current;
        const video = cropVideo.current;

        if (!canvas || !video) return;

        canvas.style.touchAction = "none";

        const ctx = canvas.getContext("2d")!;

        function resizeCanvas() {
            canvas!.width = video!.videoWidth;
            canvas!.height = video!.videoHeight;
            drawCrop();
        }

        function drawCrop() {
            ctx.clearRect(0, 0, canvas!.width, canvas!.height);

            ctx.strokeStyle = "red";
            ctx.lineWidth = 8;

            ctx.strokeRect(cropArea.x, cropArea.y, cropArea.width, cropArea.height);

            const corners = [
                { name: "tl", x: cropArea.x, y: cropArea.y },
                { name: "tr", x: cropArea.x + cropArea.width, y: cropArea.y },
                { name: "bl", x: cropArea.x, y: cropArea.y + cropArea.height },
                { name: "br", x: cropArea.x + cropArea.width, y: cropArea.y + cropArea.height }
            ];

            corners.forEach((corner) => {
                const radius = selectedCorner.current === corner.name ? 18 : 15;

                ctx.beginPath();
                ctx.arc(corner.x, corner.y, radius, 0, Math.PI * 2);
                ctx.fillStyle = "black";
                ctx.fill();

                ctx.beginPath();
                ctx.arc(corner.x, corner.y, radius - 2, 0, Math.PI * 2);
                ctx.fillStyle = selectedCorner.current === corner.name ? "yellow" : "white";
                ctx.fill();

                ctx.globalCompositeOperation = "destination-out";

                ctx.beginPath();
                ctx.arc(corner.x, corner.y, radius - 8, 0, Math.PI * 2);
                ctx.fill();

                ctx.globalCompositeOperation = "source-over";
            });
        }

        function getPointerPos(event: PointerEvent) {
            const rect = canvas!.getBoundingClientRect();

            return {
                x: (event.clientX - rect.left) * canvas!.width / rect.width,
                y: (event.clientY - rect.top) * canvas!.height / rect.height
            };
        }

        function pointerDown(event: PointerEvent) {
            const { x, y } = getPointerPos(event);

            const corners = [
                { name: "tl", x: cropArea.x, y: cropArea.y },
                { name: "tr", x: cropArea.x + cropArea.width, y: cropArea.y },
                { name: "bl", x: cropArea.x, y: cropArea.y + cropArea.height },
                { name: "br", x: cropArea.x + cropArea.width, y: cropArea.y + cropArea.height }
            ];

            const threshold = 25;

            for (const corner of corners) {
                const distance = Math.hypot(x - corner.x, y - corner.y);

                if (distance < threshold) {
                    selectedCorner.current = corner.name;
                    dragging.current = true;
                    drawCrop();
                    return;
                }

                if (
                    x >= cropArea.x &&
                    x <= cropArea.x + cropArea.width &&
                    y >= cropArea.y &&
                    y <= cropArea.y + cropArea.height
                ) {

                    draggingCrop.current = true;

                    dragOffset.current = {
                        x: x - cropArea.x,
                        y: y - cropArea.y
                    };

                    return;
                }
            }

            selectedCorner.current = null;
            dragging.current = false;
            drawCrop();
        }

        function pointerMove(event: PointerEvent) {
            if (draggingCrop.current) {

                const { x, y } = getPointerPos(event);

                setCropArea(prev => {

                    let newX = x - dragOffset.current.x;
                    let newY = y - dragOffset.current.y;

                    newX = Math.max(
                        0,
                        Math.min(newX, canvas.width - prev.width)
                    );

                    newY = Math.max(
                        0,
                        Math.min(newY, canvas.height - prev.height)
                    );


                    return {
                        ...prev,
                        x: newX,
                        y: newY
                    };

                });

                return;
            }

            if (!dragging.current) return;

            const { x, y } = getPointerPos(event);

            setCropArea((prev: any) => {
                const c = { ...prev };

                const centerX = prev.x + prev.width / 2;
                const centerY = prev.y + prev.height / 2;

                let newWidth = Math.abs(x - centerX) * 2;
                let newHeight = newWidth / ASPECT_RATIO;

                if (newWidth < 50) {
                    newWidth = 50;
                    newHeight = newWidth / ASPECT_RATIO;
                }

                let newX = centerX - newWidth / 2;
                let newY = centerY - newHeight / 2;

                const insideCanvas =
                    newX >= 5 &&
                    newY >= 5 &&
                    newX + newWidth <= canvas.width &&
                    newY + newHeight <= canvas.height;

                if (insideCanvas) {
                    c.x = newX;
                    c.y = newY;
                    c.width = newWidth;
                    c.height = newHeight;

                } else {
                    if (selectedCorner.current === "br") {
                        c.width = Math.min(newWidth, canvas.width - prev.x);
                        c.height = c.width / ASPECT_RATIO;
                    }

                    if (selectedCorner.current === "tl") {
                        c.width = Math.min(newWidth, prev.x + prev.width);
                        c.height = c.width / ASPECT_RATIO;
                        c.x = prev.x + prev.width - c.width;
                    }

                    if (selectedCorner.current === "tr") {
                        c.width = Math.min(newWidth, canvas.width - prev.x);
                        c.height = c.width / ASPECT_RATIO;
                        c.y = prev.y + prev.height - c.height;
                    }

                    if (selectedCorner.current === "bl") {
                        c.width = Math.min(newWidth, prev.x + prev.width);
                        c.height = c.width / ASPECT_RATIO;
                        c.x = prev.x + prev.width - c.width;
                    }
                }

                return c;
            });
        }

        function pointerUp() {
            dragging.current = false;
            draggingCrop.current = false;
            selectedCorner.current = null;
            drawCrop();
        }

        video.addEventListener("loadedmetadata", resizeCanvas);
        canvas.addEventListener("pointerdown", pointerDown);
        canvas.addEventListener("pointermove", pointerMove);
        canvas.addEventListener("pointerup", pointerUp);
        canvas.addEventListener("pointercancel", pointerUp);

        resizeCanvas();

        return () => {
            canvas.removeEventListener("pointerdown", pointerDown);
            canvas.removeEventListener("pointermove", pointerMove);
            canvas.removeEventListener("pointerup", pointerUp);
            canvas.removeEventListener("pointercancel", pointerUp);
        };

    }, [currentMenu, showCropWindow, cropArea]);

    // Crop - apply the crop transform to the live camera video
    useEffect(() => {
        if (!videoCrop) return;

        const video = cameraVideo.current;
        if (!video) return;

        setCropTransform(getCropTransform());

    }, [videoCrop]);

    // Calibration - keep redrawing the workspace while on the calibration menu
    useEffect(() => {
        if (currentMenu !== "calibration-menu") return;

        let active = true;

        const loop = async () => {
            if (!active) return;

            await workspaceDrawing();

            if (active) {
                setTimeout(loop, 200);
            }
        };

        loop();

        return () => {
            active = false;
        };
    }, [currentMenu]);

    // Drawing the Boxes (3D wireframe of the measured objects)
    useEffect(() => {
        if (currentMenu !== "volume-menu" && currentMenu !== "measurementHistory-menu") return;

        if (currentMenu === "volume-menu") {
            if (!volBundleMode) {
                if (!selectedObject) return;
            }

            if (volBundleMode) {
                if (multipleVolumeData) return;
            }
        }

        if (currentMenu === "measurementHistory-menu") {
            if (measurementMode === "Single Bundle") {
                if (measureMultipleVolumeData) return;
            } else {
                if (!measureSelectedObject) return;
            }
        }

        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d")!;

        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        ctx.setTransform(1, 0, 0, 1, 0, 0);

        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;

        ctx.scale(dpr, dpr);

        ctx.lineJoin = "round";
        ctx.lineCap = "round";

        if (!volInfo && !measureVolumeInfo) {
            ctx.clearRect(0, 0, rect.width, rect.height);
            return;
        }

        const project = (x: number, y: number, z: number, cx: number, cy: number, scale: number) => {
            const angle = angleRef.current;

            const cos = Math.cos(angle);
            const sin = Math.sin(angle);

            const rx = x * cos - y * sin;
            const ry = x * sin + y * cos;

            const tiltAngle = 0.35;
            const tiltCos = Math.cos(tiltAngle);
            const tiltSin = Math.sin(tiltAngle);

            const screenY = z * tiltCos - ry * tiltSin;
            const screenZ = z * tiltSin + ry * tiltCos;

            return {
                x: cx + rx * scale,
                y: cy - screenY * scale,
                z: screenZ
            };
        };

        const drawEdge = (a: any, b: any, color: string) => {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.stroke();
        };

        const draw = () => {
            const W = rect.width;
            const H = rect.height;

            ctx.clearRect(0, 0, W, H);

            let boxes: any[] = [];
            let centers: any[] = [];
            let angles: any[] = [];

            if (currentMenu === "volume-menu") {
                boxes = volumeMode === "real"
                    ? volInfo.width.slice(1).map((_: any, i: number) => ({
                        width: volInfo.width[i + 1],
                        length: volInfo.length[i + 1],
                        height: volInfo.height[i + 1],
                    })).reverse()
                    : [volInfo];
            } else if (currentMenu === "measurementHistory-menu") {
                boxes = measurementMode === "Real"
                    ? measureVolumeInfo.width.slice(1).map((_: any, i: number) => ({
                        width: measureVolumeInfo.width[i + 1],
                        length: measureVolumeInfo.length[i + 1],
                        height: measureVolumeInfo.height[i + 1],
                    })).reverse()
                    : [measureVolumeInfo];
            }

            if (currentMenu === "volume-menu") {
                centers = volumeMode === "real" ? objCenters.slice().reverse() : objCenters;
                angles = volumeMode === "real" ? objAngles.slice().reverse() : objAngles;
            } else if (currentMenu === "measurementHistory-menu") {
                centers = measurementMode === "Real" ? measureObjCenters.slice().reverse() : measureObjCenters;
                angles = measurementMode === "Real" ? measureObjAngles.slice().reverse() : measureObjAngles;
            }

            const maxWidth = Math.max(...boxes.map((b: any) => b.width));
            const maxLength = Math.max(...boxes.map((b: any) => b.length));
            const maxHeight = Math.max(...boxes.map((b: any) => b.height));
            const totalHeight = boxes.reduce((sum: number, b: any) => sum + b.height, 0);

            const maxDim = Math.max(maxWidth, maxLength, maxHeight);

            const scale = Math.min(W, H) * 0.6;
            const fontSize = Math.max(15, Math.min(22, scale * 0.04));
            ctx.font = `${fontSize}px Inter Regular`;

            const cx = W / 2;
            const cy = H / 2;

            const rotCenter = centers[0] ?? [0, 0];
            const pivot_cx = rotCenter[0] / maxDim;
            const pivot_cy = rotCenter[1] / maxDim;

            let baseHeight = 0;

            if (volumeMode === "real" || measurementMode === "Real") {
                baseHeight = -maxHeight / 2;
            } else {
                baseHeight = -totalHeight / 2;
            }

            let prevTop = 0;

            boxes.forEach((box: any, i: number) => {
                let bottom, top;
                const [center_x, center_y] = centers[i] ?? [0, 0];

                const w = box.width;
                const d = box.length;
                const h = box.height;

                const nw = w / maxDim;
                const nd = d / maxDim;

                const hw = nw / 2;
                const hd = nd / 2;

                const angle = (angles[i] ?? 0) * Math.PI / 180;

                const ca = Math.cos(angle);
                const sa = Math.sin(angle);

                const rotate = (x: number, y: number) => ({
                    x: x * ca - y * sa,
                    y: x * sa + y * ca,
                });

                const clipBottom = i === 0 ? 0 : prevTop;

                bottom = (baseHeight + clipBottom) / maxDim;
                top = (baseHeight + h) / maxDim;

                prevTop = h;

                const isStacked = i > 0;

                const p0 = rotate(-hw, -hd);
                const p1 = rotate(hw, -hd);
                const p2 = rotate(hw, hd);
                const p3 = rotate(-hw, hd);

                const center = {
                    x: (center_x / maxDim) - pivot_cx,
                    y: (center_y / maxDim) - pivot_cy
                };

                const offX = center.x;
                const offY = center.y;

                const v = [
                    project(p0.x + offX, p0.y + offY, bottom, cx, cy, scale),
                    project(p1.x + offX, p1.y + offY, bottom, cx, cy, scale),
                    project(p2.x + offX, p2.y + offY, bottom, cx, cy, scale),
                    project(p3.x + offX, p3.y + offY, bottom, cx, cy, scale),

                    project(p0.x + offX, p0.y + offY, top, cx, cy, scale),
                    project(p1.x + offX, p1.y + offY, top, cx, cy, scale),
                    project(p2.x + offX, p2.y + offY, top, cx, cy, scale),
                    project(p3.x + offX, p3.y + offY, top, cx, cy, scale),
                ];

                const X = "#6CD08A"; // width
                const Y = "#C66D6D"; // length
                const Z = "#9EB0FD"; // height

                const faces = [
                    [0, 1, 2, 3],
                    [4, 5, 6, 7],
                    [0, 1, 5, 4],
                    [2, 3, 7, 6],
                    [1, 2, 6, 5],
                    [0, 3, 7, 4],
                ].filter((_, idx) => !(isStacked && idx === 0));

                const faceDepth = faces.map((face) => ({
                    face,
                    z: face.reduce((s, idx) => s + v[idx].z, 0) / 4
                }));

                faceDepth.sort((a, b) => a.z - b.z);

                faceDepth.forEach(({ face }) => {
                    const [a, b, c, dd] = face;

                    ctx.beginPath();
                    ctx.moveTo(v[a].x, v[a].y);
                    ctx.lineTo(v[b].x, v[b].y);
                    ctx.lineTo(v[c].x, v[c].y);
                    ctx.lineTo(v[dd].x, v[dd].y);
                    ctx.closePath();

                    ctx.fillStyle = "rgba(186,186,231,0.03)";
                    ctx.fill();

                    ctx.strokeStyle = "#aaa";
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                });

                const edges: any[] = [
                    [0, 1, X, "Width"], [3, 2, X], [4, 5, X], [7, 6, X],
                    [0, 3, Y, "Length"], [1, 2, Y], [4, 7, Y], [5, 6, Y],
                    [0, 4, Z, "Height"], [1, 5, Z], [2, 6, Z], [3, 7, Z],
                ].filter(([a, b]) => !(isStacked && a < 4 && b < 4));

                edges.forEach(([a, b, color]) => {
                    drawEdge(v[a], v[b], color);
                });
            });
        };

        let frameId = 0;

        const animate = () => {
            if (!dragging.current) angleRef.current += 0.005;

            draw();
            frameId = requestAnimationFrame(animate);
        };

        animate();

        const down = (e: MouseEvent) => {
            dragging.current = true;
            lastX.current = e.clientX;
        };

        const move = (e: MouseEvent) => {
            if (!dragging.current) return;
            angleRef.current -= (e.clientX - lastX.current) * 0.01;
            lastX.current = e.clientX;
        };

        const up = () => (dragging.current = false);

        canvas.addEventListener("mousedown", down);
        window.addEventListener("mousemove", move);
        window.addEventListener("mouseup", up);

        return () => {
            cancelAnimationFrame(frameId);
            canvas.removeEventListener("mousedown", down);
            window.removeEventListener("mousemove", move);
            window.removeEventListener("mouseup", up);
        };
    }, [volInfo, measureVolumeInfo, currentMenu]);

      // Updates Current Menu on Backend
    useEffect(() => {
        async function updateMenu() {
            if (currentMenu === "config-menu"){
                await apiFetch("/currentMenu", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({currentMenu: lastMenu})
                });
            } else if (currentMenu !== "login-menu" && currentMenu !== "register" && currentMenu != "changePassword-menu") {
                await apiFetch("/currentMenu", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({currentMenu: currentMenu})
                });
            } 
            setLastMenu(currentMenu);
        }

        updateMenu();
        
    }, [currentMenu]);

    useEffect(() => {
        if (!measureSelectedObject || !measureMultipleVolumeData) return;
            const objData = measureMultipleVolumeData[measureSelectedObject];
        if (!objData) return;

            setMeasureVolumeInfo({
                volume_m: objData.volume_m,
                volume_cm: objData.volume_cm,
                width: objData.width,
                length: objData.length,
                height: objData.height
            });

            setMeasureObjCenters(objData.centers ?? []);
            setMeasureObjAngles(objData.angles ?? []);
    }, [measureSelectedObject, measureMultipleVolumeData]);

    // --------------------------------------------------------------------- //
    // |                           Functions                               | //
    // --------------------------------------------------------------------- //

    // Server Starting Helper
    const waitForServer = async (maxAttempts: number = 20, delay: number = 1000): Promise<boolean> => {
        for (let i = 0; i < maxAttempts; i++) {
            try {
                const res = await apiFetch("/status");

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

    async function loggedIn(){
        const access_token = localStorage.getItem("access_token");
        const refresh_token = localStorage.getItem("refresh_token");

        if (!access_token && !refresh_token) {
            logout();
            return;
        }

        await restoreSession();
    }

    // Restore Session Algorithm
    async function restoreSession() {
        try {
            await checkCalibration();

            const config_res = await apiFetch("/configuration/status");

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
        const access_token = localStorage.getItem("access_token");

        if (!access_token) {
            throw new Error("No access token");
        }

        const res = await apiFetch("/calibration/status");

        if (!res.ok) {
            logout();
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
        setChangeCurrentPassword("");
        setChangePassword("");
        setChangeConfirmPassword("");
        setMenuSideNavOpen(false);
        setUsernameFocus(false);
        setPasswordFocus(false);
        setShowChangePasswordModal(false);
        setUsernameFormError(false);
        setPasswordFormError(false);
    }

    function showChangePasswordScreen(): void {
        setCurrentMenu("changePassword-menu");
        setMessage([TextClear]);
        setUsername("");
        setPassword("");
        setChangePasswordFocus(false);
        setChangeConfirmPasswordFocus(false);

        setChangePasswordFormError(false);
        setChangeConfirmPasswordFormError(false);
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

                if(data.resetTokenExpired){
                    setMessage([TextResetTokenExpired]);
                }else if (data.changePassword){
                    localStorage.setItem("access_token", data.access_token);
                    setChangeUserId(data.user_id);
                    setChangeUsername(data.username);
                    showChangePasswordScreen();
                }else{
                    const role: string = data.role;
                    const savedUsername: string = data.username;
                    const userId: Int16Array = data.user_id;

                    const currentUser = {
                        username: savedUsername,
                        id: userId,
                        role
                    }

                    localStorage.setItem(
                        "current_user",
                        JSON.stringify(currentUser)
                    );

                    setSavedUser(currentUser);

                    storeTokens(data.access_token, data.refresh_token);

                    await restoreSession();

                    setMenuSideNavOpen(true);

                    setMessage([TextClear]);

                };

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

        notify.success("New user registered with success");

        showLoginScreen();
    }

    // Change Password Algorithm
    async function confirmChangePassword(): Promise<void> {
        if(currentMenu === "changePassword-menu"){
            if (!changeUserId || !changePassword || !changeConfirmPassword) {
                setMessage([TextFillAllFields]);

                setChangePasswordFormError(true);
                setChangeConfirmPasswordFormError(true);
                return;
            }

            if (changePassword !== changeConfirmPassword) {
                setMessage([
                    {
                    text: "Passwords do not match!",
                    type: "error",
                    },
                ]);

                setChangePasswordFormError(true);
                setChangeConfirmPasswordFormError(true);
                return;
            }

            try {
                const response = await apiFetch("/users/changePassword", {method: "POST", headers: {"Content-Type": "application/json",},
                    body: JSON.stringify({
                        password: changePassword,
                        confirm_password: changeConfirmPassword,
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    setMessage([
                        {
                        text: errorText(data.detail, TextChangePasswordError.text),
                        type: "error",
                        },
                    ]);

                    setChangePasswordFormError(true);
                    setChangeConfirmPasswordFormError(true);
                    return;
                }

                notify.success("Changed password with success");

                setResetTokensByUser((prev) => {
                    const updated = { ...prev };
                    delete updated[data.user_id];
                    return updated;
                });

                showLoginScreen();

            } catch (error) {
                setMessage([TextServerConnection]);

                setChangePasswordFormError(true);
                setChangeConfirmPasswordFormError(true);
                return;
            }
        } else if (currentMenu !== "login-menu" && currentMenu !== "register" && currentMenu !== "changePassword-menu"){
            if (!changeUserId || !changeCurrentPassword || !changePassword || !changeConfirmPassword) {
                setMessage([TextFillAllFields]);

                setChangeCurrentPasswordFormError(true);
                setChangePasswordFormError(true);
                setChangeConfirmPasswordFormError(true);
                return;
            }

            if (changePassword !== changeConfirmPassword) {
                setMessage([
                    {
                    text: "Passwords do not match!",
                    type: "error",
                    },
                ]);

                setChangePasswordFormError(true);
                setChangeConfirmPasswordFormError(true);
                return;
            }

            try {
                const response = await apiFetch("/users/changePassword", {method: "POST", headers: {"Content-Type": "application/json",},
                    body: JSON.stringify({
                        current_password: changeCurrentPassword,
                        password: changePassword,
                        confirm_password: changeConfirmPassword,
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    setMessage([
                        {
                        text: errorText(data.detail, TextChangePasswordError.text),
                        type: "error",
                        },
                    ]);

                    setChangeCurrentPasswordFormError(true);
                    setChangePasswordFormError(true);
                    setChangeConfirmPasswordFormError(true);
                    return;
                }

                notify.success("Changed password with success");

                setResetTokensByUser((prev) => {
                    const updated = { ...prev };
                    delete updated[data.user_id];
                    return updated;
                });

                logout();
                showLoginScreen();

            } catch (error) {
                setMessage([TextServerConnection]);

                setChangePasswordFormError(true);
                setChangeConfirmPasswordFormError(true);
                return;
            }
        }

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
        setObjectImage(null);
        setObjectList([]);
        setSelectedObject("");
        setShowCamera(true);
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
        setChangePassword("");
        setChangeConfirmPassword("");
        setChangeCurrentPasswordFocus(false);
        setChangePasswordFocus(false);
        setChangeConfirmPasswordFocus(false);
        setChangeCurrentPasswordFormError(false);
        setChangePasswordFormError(false);
        setChangeConfirmPasswordFormError(false);
        }

    useEffect(() => {
        setOnAuthFailure(() => {
            notify.error("Session expired. Login once again.")
            logout();
        });

        return () => setOnAuthFailure(null);
    }, []);


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

        const response = await apiFetch("/offer", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
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
            setNoObjectsDetected(false);
            setObjectsOutOfLine(false);

            const access_token = localStorage.getItem("access_token");

            if (!access_token) {
                throw new Error("No access token");
            }

            const response = await apiFetch("/volume/mode");

            if (response.status === 401) {
                throw new Error("Session expired");
            }

            const countResp = await apiFetch("/countdown/value");

            const countData = await countResp.json();

            for (let i = countData.countdown; i > 0; i--) {
                setCountdown(i);

                await new Promise<void>(resolve =>
                    setTimeout(resolve, 1000)
                );
            }

            await apiFetch("/volume/clickTimestamp",
                {
                    method: "POST"
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

    // Save the current measurement (objects + snapshot images) in the database
    async function saveMeasurement(measurementData: MeasurementData): Promise<void> {
        try {
            setMessage([TextClear]);

            const access_token = localStorage.getItem("access_token");

            if (!access_token) {
                throw new Error("No access token");
            }

            const res = await apiFetch("/saveMeasurements", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(measurementData)
            });


            if (res.ok) {
                const data = await res.json();

                notify.success(`Measurement saved (#${data.id}).`);

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

        }
    }

    // Load the measurement history (and the users list for the "User" column)
    async function loadMeasurements(): Promise<void> {
        try {
            const res = await apiFetch("/measurements");
            if (res.ok) {
                const data = await res.json();
                setMeasurementsList(data.measurements || []);
            } else {
                setMessage([{ text: "Could not load measurements.", type: "error" }]);
            }

            const user_res = await apiFetch("/users");
            if (user_res.ok) {
                const data = await user_res.json();
                setUsersIDList(data.users || []);
            } else if (user_res.status === 403) {
                setMessage([{ text: "Admin privileges required.", type: "error" }]);
            } else {
                setMessage([{ text: "Could not load users.", type: "error" }]);
            }
        } catch (e) {
            setMessage([{ text: "Server connection error.", type: "error" }]);
        }
    }

    // Delete a single measurement by id
    async function deleteMeasurement(measurementID: number | null): Promise<void> {
        try {
            const res = await apiFetch(`/measurements/delete/${measurementID}`, {
                method: "DELETE"
            });

            if (res.ok) {
                setMeasurementsList(prev => prev.filter((u) => u.id !== measurementID));
            } else {
                setMessage([{ text: "Could not delete measurement.", type: "error" }]);
            }
        } catch (e) {
            setMessage([{ text: "Server connection error.", type: "error" }]);
        }
    }

    async function deleteAllMeasurements(): Promise<void> {
        try {
            const res = await apiFetch("/measurements/deleteall", {
                method: "DELETE"
            });

            if (res.ok) {
                setMeasurementsList([]);
            } else {
                setMessage([{ text: "Could not delete measurement.", type: "error" }]);
                setMessage([{ text: "Could not delete all measurements.", type: "error" }]);
            }
        } catch (e) {
            setMessage([{ text: "Server connection error.", type: "error" }]);
        }
    }

    // Load the detail of one measurement into the info popup
    async function viewMeasurement(selectedID: number): Promise<void> {
        try {
            const res_archived = await apiFetch("/measurements/archived");

            const res = await apiFetch(`/measurements/${selectedID}`);

            if (!res.ok) {
                throw new Error("Failed to load measurement");
            }

            const data = await res.json();

            setMeasurementMode(data.measurement?.volume_mode);

            if (data.measurement?.volume_mode === "Single Bundle") {
                setMeasureVolumeInfo({
                    volume_m: data.measurement?.total_volume_m,
                    volume_cm: data.measurement?.total_volume_cm,
                    width: data.objects?.[0]?.x_cm,
                    length: data.objects?.[0]?.y_cm,
                    height: data.objects?.[0]?.z_cm,
                    weight: data.measurement?.weight
                });
                setMeasureMultipleVolumeData(null);
            } else {
                const objects = data.objects ?? [];
                const measureData: any = {};

                if (objects.length === 1) {
                    const obj = objects[0];

                    setMeasureObjectList(["1"]);
                    setMeasureSelectedObject("1");

                    if (data.measurement?.volume_mode === "Multi Bundle") {
                        objects.forEach((obj: any, index: number) => {
                            measureData[`${index + 1}`] = {
                                volume_m: obj.volume_m,
                                volume_cm: obj.volume_cm,
                                width: obj.x_cm,
                                length: obj.y_cm,
                                height: obj.z_cm,
                            };
                        });

                        setMeasureVolumeInfo({
                            volume_m: data.measurement?.total_volume_m,
                            volume_cm: data.measurement?.total_volume_cm,
                            width: data.objects?.[0]?.x_cm,
                            length: data.objects?.[0]?.y_cm,
                            height: data.objects?.[0]?.z_cm,
                            weight: data.measurement?.weight
                        });
                    } else if (data.measurement?.volume_mode === "Real") {
                        objects.forEach((obj: any, index: number) => {
                            measureData[`${index + 1}`] = {
                                volume_m: obj.volume_m,
                                volume_cm: obj.volume_cm,
                                width: obj.extra.x,
                                length: obj.extra.y,
                                height: obj.extra.z,
                                angles: obj.extra.angles,
                                centers: obj.extra.centers
                            };
                        });

                        setMeasureVolumeInfo({
                            volume_m: data.measurement?.total_volume_m,
                            volume_cm: data.measurement?.total_volume_cm,
                            width: data.objects?.[0]?.extra.x,
                            length: data.objects?.[0]?.extra.y,
                            height: data.objects?.[0]?.extra.z,
                            weight: data.measurement?.weight
                        });

                        setMeasureObjAngles(data.objects?.[0]?.extra.angles);
                        setMeasureObjCenters(data.objects?.[0]?.extra.centers);
                    }
                } else {
                    if (data.measurement?.volume_mode === "Multi Bundle") {
                        objects.forEach((obj: any, index: number) => {
                            measureData[`${index + 1}`] = {
                                volume_m: obj.volume_m,
                                volume_cm: obj.volume_cm,
                                width: obj.x_cm,
                                length: obj.y_cm,
                                height: obj.z_cm,
                            };
                        });
                    } else if (data.measurement?.volume_mode === "Real") {
                        objects.forEach((obj: any, index: number) => {
                            measureData[`${index + 1}`] = {
                                volume_m: obj.volume_m,
                                volume_cm: obj.volume_cm,
                                width: obj.extra.x,
                                length: obj.extra.y,
                                height: obj.extra.z,
                                angles: obj.extra.angles,
                                centers: obj.extra.centers
                            };
                        });
                    }

                    setMeasureObjectList(Object.keys(measureData).filter((key) => key !== "Total"));
                    setMeasureSelectedObject("1");
                    setMeasureVolumeInfo(null);
                }

                measureData.Total = {
                    volume_m: data.measurement?.total_volume_m,
                    volume_cm: data.measurement?.total_volume_cm,
                    weight: data.measurement?.weight
                };

                setMeasureMultipleVolumeData(measureData);
            }

            setMeasureObjectImage(data.images?.data ?? null);

        } catch (err) {
            console.error(err);
        } finally {
            setShowMeasurementInfo(true);
        }
    }

    // Single Bundle Volume Algorithm
    async function volumeSingleBundle(access_token: string): Promise<void> {
        const measurementWeight = weightInfo;
        setMeasurementWeightInfo(weightInfo);
        try {
            await apiFetch("/volume/singleBundle",
                {
                    method: "POST",
                }
            );

            const response = await apiFetch("/getObjectsOutOfLine");

            const data = await response.json();

            const objectsDetected = data.objects_outOfLine.length > 0;
            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);

            setNoObjectsDetected(!objectsDetected);

            if(objectsDetected){
                if (objectsOutOfLine.length > 0) {
                    setObjectsOutOfLine(true);
                } else {
                    setMessage([TextClear]);

                    const dataResponse = await apiFetch("/volume/singleBundle/results");

                    const volumeData = await dataResponse.json();

                    const bundle = volumeData.Bundle;


                    if (
                        bundle.volume_m === 0 ||
                        bundle.volume_cm === 0 ||
                        bundle.x === 0 ||
                        bundle.y === 0 ||
                        bundle.z === 0
                    ) {
                        setNoObjectsDetected(true);

                    } else {

                        const measurementData = {
                            volume_mode: "Single Bundle",
                            weight: Number(measurementWeight),
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

                        await saveMeasurement(measurementData);

                        setVolInfo({
                            volume_m: bundle.volume_m,
                            volume_cm: bundle.volume_cm,
                            width: bundle.x,
                            length: bundle.y,
                            height: bundle.z
                        });
                    }
                
                    const imgResp = await apiFetch("/getFrame/detectedObjectsFrame");

                    if (imgResp.status === 404) {
                        throw new Error("Frame not Available");
                    }


                    const blob = await imgResp.blob();

                    const url = URL.createObjectURL(blob);

                    setObjectImage(url);
                    setShowCamera(false);
                
                }
            }

        } catch (error) {
            setMessage([TextError]);
            console.error(error);

        } finally {
            setLoadingVolume(false);
        }
    }

    // Multi Bundle Volume Algorithm
    async function volumeMultiBundle(access_token: string): Promise<void> {
        const measurementWeight = weightInfo;
        setMeasurementWeightInfo(weightInfo);
        try {
            await apiFetch("/volume/multiBundle", { method: "POST"});

            const response = await apiFetch("/getObjectsOutOfLine");
            const data = await response.json();

            const objectsDetected = data.objects_outOfLine.length > 0;
            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);

            setNoObjectsDetected(!objectsDetected);

            if(objectsDetected){
                if (objectsOutOfLine.length > 0) {
                    setObjectsOutOfLine(true);
                } else {
                    const dataResponse = await apiFetch("/volume/multiBundle/results");
                    const volumeData = await dataResponse.json();

                    setVolumeData(volumeData);

                    const imgResp = await apiFetch("/getFrame/detectedObjectsFrame");
                    if (imgResp.status === 404) throw new Error("Frame not Available");

                    const blob = await imgResp.blob();
                    const url = URL.createObjectURL(blob);
                    setObjectImage(url);
                    setShowCamera(false);

                    const objIdentified = Object.keys(volumeData).filter((key: string) => key !== "Total");

                    if (objIdentified.length === 0) {
                        setNoObjectsDetected(true);
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
                        setSelectedObject(objIdentified[0]);
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
                            weight: Number(measurementWeight),
                            objects
                        };

                        await saveMeasurement(measurementData);
                    }

                    setMessage([TextClear]);
                }
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
        const measurementWeight = weightInfo;
        setMeasurementWeightInfo(weightInfo);
        try {
            await apiFetch("/volume/real", { method: "POST"});

            const response = await apiFetch("/getObjectsOutOfLine");
            const data = await response.json();

            const objectsDetected = data.objects_outOfLine.length > 0;
            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);

            setNoObjectsDetected(!objectsDetected);

            if(objectsDetected){
                if (objectsOutOfLine.length > 0) {
                    setObjectsOutOfLine(true);
                } else {
                    const dataResponse = await apiFetch("/volume/real/results");
                    const volumeData = await dataResponse.json();

                    setVolumeData(volumeData);

                    const imgResp = await apiFetch("/getFrame/detectedObjectsFrame");
                    if (imgResp.status === 404) throw new Error("Frame not Available");

                    const blob = await imgResp.blob();
                    const url = URL.createObjectURL(blob);
                    setObjectImage(url);
                    setShowCamera(false);

                    const objIdentified = Object.keys(volumeData).filter((key: string) => key !== "Total");

                    if (objIdentified.length === 0) {
                        setNoObjectsDetected(true);
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
                        setSelectedObject(objIdentified[0]);
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
                            weight: Number(measurementWeight),
                            objects
                        };

                        await saveMeasurement(measurementData);
                    }

                    setMessage([TextClear]);
                }
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
            await apiFetch("/volume/individual", { method: "POST"});

            const response = await apiFetch("/getObjectsOutOfLine");
            const data = await response.json();

            const objectsDetected = data.objects_outOfLine.length > 0;
            const objectsOutOfLine = data.objects_outOfLine
                .map((val: boolean, i: number) => val ? i + 1 : null)
                .filter((v: number | null) => v !== null);

            setNoObjectsDetected(!objectsDetected);

            if(objectsDetected){
                if (objectsOutOfLine.length > 0) {
                    setObjectsOutOfLine(true);
                } else {
                    const dataResponse = await apiFetch("/volume/individual/results");
                    const volumeData = await dataResponse.json();

                    setVolumeData(volumeData);

                    const imgResp = await apiFetch("/getFrame/detectedObjectsFrame");
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

                    setMessage([TextClear]);
                }
            } 

        } catch (error) {
            setVolInfo(null);
            setMessage([TextError]);
            console.error(error);
        } finally {
            setLoadingVolume(false);
        }
    }

    // Draw the detected workspace (auto applies mask, manual draws the polygon)
    async function workspaceDrawing(): Promise<void> {
        try {
            const access_token = localStorage.getItem("access_token");
            const r = await apiFetch("/calibrate/mode");
            const calibData = await r.json();
            if (calibData["Calibrate Mode"] === "Automatic") {
                if (currentMenu !== "calibration-menu") return;
                applyMask(access_token!);
            } else if (calibData["Calibrate Mode"] === "Manual") {
                applyManualWorkspace();
            }
        } catch (err) {
            console.warn("Erro drawing Workspace:", err);
        }
    }

    async function applyMask(access_token: string): Promise<void> {
        try {
            const r = await apiFetch("/mask");
            const maskValues = await r.json();
            await apiFetch("/applyMask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(maskValues)
            });

            const params = await apiFetch("/calibrate/params");

            const data = await params.json();
            detectionArea.current = data["Detected Area"];

        } catch (err) {
            console.warn("Erro applyMask:", err);
        }
    }

    function applyManualWorkspace(): void {
        const canvas = workspaceCanvas.current;
        const img = calibrationImage.current;

        if (!canvas || !img) return;

        canvas.style.touchAction = "none";

        const ctx = canvas.getContext("2d")!;

        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const points = detectionArea.current;

        if (!points || points.length === 0) return;

        ctx.beginPath();

        points.forEach((point: any, index: number) => {
            if (index === 0) ctx.moveTo(point[0], point[1]);
            else ctx.lineTo(point[0], point[1]);
        });

        ctx.closePath();

        ctx.strokeStyle = "blue";
        ctx.lineWidth = 4;
        ctx.stroke();

        points.forEach((point: any, index: number) => {
            const radius = selectedPoint.current === index ? 12 : 10;

            ctx.beginPath();
            ctx.arc(point[0], point[1], radius, 0, Math.PI * 2);
            ctx.fillStyle = "black";
            ctx.fill();

            ctx.beginPath();
            ctx.arc(point[0], point[1], radius - 2, 0, Math.PI * 2);
            ctx.fillStyle = selectedPoint.current === index ? "yellow" : "white";
            ctx.fill();

            ctx.globalCompositeOperation = "destination-out";

            ctx.beginPath();
            ctx.arc(point[0], point[1], radius - 6, 0, Math.PI * 2);
            ctx.fill();

            ctx.globalCompositeOperation = "source-over";
        });
    }

    // Calibrate Click Algorithm
    async function calibrate_click(): Promise<void> {
        try {
            setLoadingCalibration(true);
            setMessage([TextClear]);

            await apiFetch("/applyManualWorkspace", {
                method: "POST",
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify({ detection_area: detectionArea.current })
            });

            const maskResponse = await apiFetch("/mask");
            if (!maskResponse.ok) throw new Error("Mask request failed");
            const maskValues = await maskResponse.json();

            const calibrateResponse = await apiFetch("/calibrate", {
                method: "POST",
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify(maskValues)
            });

            if (!calibrateResponse.ok) throw new Error("Calibrate request failed");

            const flagsResponse = await apiFetch("/calibrate/flags");
            if (!flagsResponse.ok) throw new Error("Flags request failed");

            const data = await flagsResponse.json();

            const center_aligned = data["Center Aligned"];
            const ws_clear = data["Workspace Clear"];

            if (center_aligned && ws_clear) {
                setCalibrationModalOpen(true);
            } else if (center_aligned && !ws_clear) {
                setMessage([TextNotCalibrated, TextWsNotEmpty]);
            } else if (!center_aligned && ws_clear) {
                setMessage([TextNotCalibrated, TextCenterNotAligned]);
            } else {
                setMessage([TextNotCalibrated, TextWsNotEmptyAndCenterNotAligned]);
            }

            selectedPoint.current = null;

        } catch (error) {
            setMessage([TextError]);
            console.error(error);
        } finally {
            setLoadingCalibration(false);
        }
    }

    // Confirm Calibration Algorithm
    async function confirm_calibration(confirm: boolean): Promise<void> {
        try {
            setCalibrationModalOpen(false);

            if (confirm) {
                const calibrateResponse = await apiFetch("/saveCalibration", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });

                if (!calibrateResponse.ok) throw new Error("Save calibration request failed");
                setLockMenu(false);
                setCurrentMenu("volume-menu");
                notify.success("System was calibrated with success.");
            }

        } catch (error) {
            setMessage([TextError]);
            console.error(error);
        }
    }

    // Change Calibration Mode (Automatic / Manual)
    async function handleCalibrationModeChange(Manual: boolean): Promise<void> {
        if (Manual) {
            setCalibrationMode("manual");
            await apiFetch("/calibrate/mode/manual", { method: "POST"});
        } else {
            setCalibrationMode("auto");
            await apiFetch("/calibrate/mode/automatic", { method: "POST"});
        }
    }

    // Load all users (admin only) for the Manage Users panel
    async function loadUsers(): Promise<void> {
        try {
            setUsersLoading(true);
            setMessage([TextClear]);
            const res = await apiFetch("/users");
            if (res.ok) {
                const data = await res.json();
                setUsersList(data.users || []);
            } else if (res.status === 403) {
                setMessage([{ text: "Admin privileges required.", type: "error" }]);
            } else {
                setMessage([{ text: "Could not load users.", type: "error" }]);
            }
        } catch (e) {
            setMessage([{ text: "Server connection error.", type: "error" }]);
        } finally {
            setUsersLoading(false);
        }
    }

    async function openUsersPanel(): Promise<void> {
        // setShowUserPopup(false);
        setShowUsersPanel(true);
        await loadUsers();
    }

    async function openChangePasswordModal(): Promise<void> {
        setChangeUserId(savedUser?.id);
        setChangeUsername(savedUser?.username);
        setShowChangePasswordModal(true);
    }

    async function closeChangePasswordModal(): Promise<void> {
        setMessage([TextClear]);
        setShowChangePasswordModal(false); 
        setChangeCurrentPassword(""); 
        setChangePassword(""), 
        setChangeConfirmPassword("")

        setChangeCurrentPasswordFocus(false);
        setChangePasswordFocus(false);
        setChangeConfirmPasswordFocus(false);

        setChangeCurrentPasswordFormError(false);
        setChangePasswordFormError(false);
        setChangeConfirmPasswordFormError(false);
    }

    async function changeUserRole(userId: number, role: string): Promise<void> {
        try {
            const res = await apiFetch(`/users/${userId}/role`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify({ role })
            });
            if (res.ok) {
                setUsersList(prev => prev.map((u) => (u.id === userId ? { ...u, role } : u)));
            } else {
                notify.error("Could not update the user role");
            }
        } catch (e) {
            setUsersMsg("Server connection error.");
        }
    }

    async function generateResetToken(userId: number): Promise<void> {
        const response = await apiFetch(`/users/${userId}/resetToken`, {
            method: "POST",
            headers: { "Content-Type": "application/json"},
        });

        const data: { token: string } = await response.json();

        setResetTokensByUser((prev) => ({
            ...prev,
            [userId]: [
                ...(prev[userId] ?? []),
                data.token
            ],
        }));
    }

    async function deleteUserById(userId: number): Promise<void> {
        try {
            const res = await apiFetch(`/users/${userId}`, {
                method: "DELETE"
            });
            if (res.ok) {
                setUsersList(prev => prev.filter((u) => u.id !== userId));
            } else {
                setMessage([{ text: "Could not delete user.", type: "error" }]);
            }
        } catch (e) {
            setMessage([{ text: "Server connection error.", type: "error" }]);
        }
    }

    // Change Exposure Mode (Fixed Exposition / HDR)
    async function handleExpHDR_toggle(e: React.ChangeEvent<HTMLInputElement>): Promise<void> {
        const checked = e.target.value === "true";
        setExpHDR(checked);

        if (checked) {
            await apiFetch("/exposition/mode/hdr", { method: "POST"});
        } else {
            await apiFetch("/exposition/mode/fixed", { method: "POST"});
        }

        await apiFetch("/saveInfo", { method: "POST" });
    }

    // Change Volume Mode (Single Bundle / Multi Bundle / Real / Individual)
    async function handleVolumeMode(e: React.ChangeEvent<HTMLInputElement>): Promise<void> {
        const mode = e.target.value;
        setVolumeMode(mode);
        setShowCamera(true);
        setObjectImage(null);
        setObjectList([]);
        setSelectedObject("");
        setVolInfo(null);
        setVolumeData(null);
        setNoObjectsDetected(false);
        setObjectsOutOfLine(false);

        switch (mode) {
            case "single_bundle":
                await apiFetch("/volume/mode/singleBundle", { method: "POST"});
                setVolBundleMode(true);
                break;
            case "multi_bundle":
                await apiFetch("/volume/mode/multiBundle", { method: "POST"});
                setVolBundleMode(false);
                break;
            case "real":
                await apiFetch("/volume/mode/real", { method: "POST"});
                setVolBundleMode(false);
                break;
            case "individual":
                await apiFetch("/volume/mode/individual", { method: "POST"});
                setVolBundleMode(false);
                break;
        }

        await apiFetch("/saveInfo", { method: "POST" });
    }

    // Change System Speed (Slow / Intermedium / Fast)
    async function handleSpeedMode(e: React.ChangeEvent<HTMLInputElement>): Promise<void> {
        const mode = e.target.value;
        setSpeedMode(mode);

        switch (mode) {
            case "slow":
                await apiFetch("/speed/mode/slow", { method: "POST"});
                break;
            case "intermedium":
                await apiFetch("/speed/mode/intermedium", { method: "POST"});
                break;
            case "fast":
                await apiFetch("/speed/mode/fast", { method: "POST"});
                break;
        }

        await apiFetch("/saveInfo", { method: "POST"});
    }

    // Change Exposure Time (only for Fixed Exposition)
    async function exposureSet_click(): Promise<void> {
        const value = Number(exposureTime);

        if (!Number.isInteger(value)) {
            notify.error("Only integer values are allowed for exposure time");
            return;
        }

        if (value < 100 || value > 2000) {
            notify.error("Exposure Time value must be between 100 and 2000");
            return;
        }

        try {

            await apiFetch("/update_systemInfo", { method: "POST", headers: { "Content-Type": "application/json"}, body: JSON.stringify({ exposureTime: value }) });

            await apiFetch("/saveInfo", { method: "POST"});

            notify.success("Exposure Time updated successfully");
        } catch (error) {
            console.error("Exposure set error:", error);
        }
    }

    // Change Countdown Timer
    async function countdownTimerSet_click(): Promise<void> {
        const value = Number(countdownTimer);

        if (!Number.isInteger(value)) {
            notify.error("Only integer values are allowed for the Countdown Timer");
            return;
        }

        if (value < 0 || value > 10) {
            notify.error("Countdown Timer value must be between 0 and 10");
            return;
        }

        try {

            await apiFetch("/update_systemInfo", {
                method: "POST",
                headers: { "Content-Type": "application/json"},
                body: JSON.stringify({ countdown: value })
            });

            await apiFetch("/saveInfo", { method: "POST"});

            notify.success("Countdown Timer updated successfully");
        } catch (error) {
            console.error("Countdown set error:", error);
        }
    }

    // Persist the crop window / area on the backend
    async function cropWindow_Set(valueWindow: any, valueArea: any): Promise<void> {
        try {
            const access_token = localStorage.getItem("access_token");

            await apiFetch("/update_systemInfo", { method: "POST", headers: { "Content-Type": "application/json"}, body: JSON.stringify({ cropWindow: valueWindow, cropArea: valueArea }) });

            await apiFetch("/saveInfo", { method: "POST"});
        } catch (error) {
            console.error("CropWindow set error:", error);
        }
    }

    // Compute the CSS transform that fits the crop area to the live video
    function getCropTransform(): React.CSSProperties {
        const video = cameraVideo.current;

        if (!video || !videoCrop) return {};

        const scaleX = videoCrop.videoWidth / videoCrop.width;
        const scaleY = videoCrop.videoHeight / videoCrop.height;

        const scale = Math.min(scaleX, scaleY);

        const scaleCentersX = video.clientWidth / videoCrop.videoWidth;
        const scaleCentersY = video.clientHeight / videoCrop.videoHeight;

        const cropCenterX = (videoCrop.x + videoCrop.width / 2) * scaleCentersX;
        const cropCenterY = (videoCrop.y + videoCrop.height / 2) * scaleCentersY;

        const videoCenterX = video.clientWidth / 2;
        const videoCenterY = video.clientHeight / 2;

        let translateX = videoCenterX - cropCenterX * scale;
        let translateY = videoCenterY - cropCenterY * scale;

        const transformedWidth = video.clientWidth * scale;
        const transformedHeight = video.clientHeight * scale;

        const left = translateX;
        const top = translateY;
        const right = translateX + transformedWidth;
        const bottom = translateY + transformedHeight;

        if (left > 0) translateX -= left;
        if (top > 0) translateY -= top;
        if (right < video.clientWidth) translateX += video.clientWidth - right;
        if (bottom < video.clientHeight) translateY += video.clientHeight - bottom;

        const translateXPercent =
            (translateX / video.clientWidth) * 100;

        const translateYPercent =
            (translateY / video.clientHeight) * 100;


        return {
            transform: `translate(${translateXPercent}%, ${translateYPercent}%) scale(${scale})`,
            transformOrigin: "top left"
        };
    }

    const isAuthScreen = currentMenu === "login-menu" || currentMenu === "register";

    const navItems = [
        {
            key: 'volume',
            label: 'Volume',
            menu: 'volume-menu',
        },
        {
            key: 'calibration',
            label: 'Calibration',
            menu: 'calibration-menu',
        },
        {
            key: 'measurement',
            label: 'Measurement History',
            menu: 'measurementHistory-menu',
        },
    ];

    const primaryNav = navItems
        .filter(item => item.menu === currentMenu)
        .map(item => ({
            key: item.key,
            label: item.label,
            active: true,
            order: navItems.indexOf(item),
            onClick: () => setCurrentMenu(item.menu),
        }));

    const collapsibleNav = navItems
        .filter(item => item.menu !== currentMenu)
        .map(item => ({
            key: item.key,
            label: item.label,
            active: false,
            order: navItems.indexOf(item),
            onClick: () => setCurrentMenu(item.menu),
        }));

    const [isPortrait, setIsPortrait] = useState(
        screen.orientation.type.startsWith("portrait")
    );

    useEffect(() => {
        const handleOrientationChange = () => {
            setIsPortrait(
                screen.orientation.type.startsWith("portrait")
            );
        };

        screen.orientation.addEventListener(
            "change",
            handleOrientationChange
        );

        return () => {
            screen.orientation.removeEventListener(
                "change",
                handleOrientationChange
            );
        };
    }, []);

    useEffect(() => {
        console.log("USER POPUP EFFECT", {
            showUserPopup,
            userAnchorEl,
        });
        if (!showUserPopup || !userAnchorEl) return;

        const update = () => {
            const iconRect = userAnchorEl.getBoundingClientRect();
            const containerRect = appContainerRef.current!.getBoundingClientRect();

            setUserAnchorRect(
                new DOMRect(
                    iconRect.left - containerRect.left,
                    iconRect.top - containerRect.top,
                    iconRect.width,
                    iconRect.height,
                )
            );
        };

        window.addEventListener('resize', update);
        window.addEventListener('scroll', update, true);

        update();

        return () => {
            window.removeEventListener('resize', update);
            window.removeEventListener('scroll', update, true);
        };
    }, [showUserPopup, userAnchorEl]);

    useEffect(() => {
        console.log("USER POPUP EFFECT", {
            showSettingsPopup,
            settingsAnchorEl,
        });
        if (!showSettingsPopup || !settingsAnchorEl) return;

        const update = () => {
            const settingsIconRect = settingsAnchorEl.getBoundingClientRect();
            const settingsContainerRect = appContainerRef.current!.getBoundingClientRect();

            setSettingsAnchorRect(
                new DOMRect(
                    settingsIconRect.left - settingsContainerRect.left,
                    settingsIconRect.top - settingsContainerRect.top,
                    settingsIconRect.width,
                    settingsIconRect.height,
                )
            );
        };

        window.addEventListener('resize', update);
        window.addEventListener('scroll', update, true);

        update();

        return () => {
            window.removeEventListener('resize', update);
            window.removeEventListener('scroll', update, true);
        };
    }, [showSettingsPopup, settingsAnchorEl]);

    if (appReady){
        return (
            <>
                
                <div className="app-container" ref={appContainerRef}>
                    {currentMenu !== "login-menu" && currentMenu !== "register" && currentMenu !== "changePassword-menu" && (
                        <QTopBar
                            primaryNav={primaryNav}
                            collapsibleNav={collapsibleNav}

                            collapsibleActions={[
                                {
                                    key: 'settings',
                                    label: 'Settings',
                                    icon: <SettingsIcon />,
                                    onClick: (e) => {
                                        const settingsIconRect = e.currentTarget.getBoundingClientRect();
                                        const settingsContainerRect = appContainerRef.current!.getBoundingClientRect();

                                        setSettingsAnchorEl(e.currentTarget);
                                        setSettingsAnchorRect(new DOMRect(
                                            settingsIconRect.left - settingsContainerRect.left,
                                            settingsIconRect.top - settingsContainerRect.top,
                                            settingsIconRect.width,
                                            settingsIconRect.height,
                                        ));

                                        setShowSettingsPopup(true);
                                        setShowUserPopup(false);
                                    },
                                    active: showSettingsPopup,
                                },
                            ]}

                            actions={[
                                {
                                    key: 'profile',
                                    label: 'User',
                                    icon: <UserIcon />,
                                    onClick: (e) => {
                                        const iconRect = e.currentTarget.getBoundingClientRect();
                                        const containerRect = appContainerRef.current!.getBoundingClientRect();

                                        setUserAnchorEl(e.currentTarget);
                                        setUserAnchorRect(new DOMRect(
                                            iconRect.left - containerRect.left,
                                            iconRect.top - containerRect.top,
                                            iconRect.width,
                                            iconRect.height,
                                        ));
                                        
                                        setShowUserPopup(true);
                                        setShowSettingsPopup(false);
                                    },
                                    active: showUserPopup,
                                },
                            ]}

                            showToggle={true}

                            onExpandedChange={(expanded) => {
                                if (!expanded) {
                                    setShowSettingsPopup(false);
                                }
                            }}
                        />
                    )}
                    
                    <QToaster />

                    {/* Login Menu */}
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

                    {/* Register Menu */}
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

                    {/* Register Menu */}
                    {currentMenu === "changePassword-menu" && (
                        <QChangePassword
                            message={message}
                            changeUsername={changeUsername}
                            changePassword={changePassword}
                            changeConfirmPassword={changeConfirmPassword}
                            setChangePassword={setChangePassword}
                            setChangeConfirmPassword={setChangeConfirmPassword}
                            changePasswordFormError={changePasswordFormError}
                            changeConfirmPasswordFormError={changeConfirmPasswordFormError}
                            setChangePasswordFormError={setChangePasswordFormError}
                            setChangeConfirmPasswordFormError={setChangeConfirmPasswordFormError}
                            changePasswordFocus={changePasswordFocus}
                            changeConfirmPasswordFocus={changeConfirmPasswordFocus}
                            setChangePasswordFocus={setChangePasswordFocus}
                            setChangeConfirmPasswordFocus={setChangeConfirmPasswordFocus}
                            confirmChangePassword={confirmChangePassword}
                            showLoginScreen={showLoginScreen}
                        />
                    )}

                    {/* Volume Menu */}
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
                            weightZero={weightZero}

                            volInfo={volInfo}
                            multipleVolumeData={multipleVolumeData}

                            canvasRef={canvasRef}

                            objectList={objectList}
                            selectedObject={selectedObject}
                            setSelectedObject={setSelectedObject}

                            countdown={countdown}

                            weightInfo={weightInfo}
                            measurementWeightInfo={measurementWeightInfo}

                            volumeMode={volumeMode}
                            toggleMenu={toggleMenu}
                            setVolInfo={setVolInfo}

                            noObjectsDetected={noObjectsDetected}
                            objectsOutOfLine={objectsOutOfLine}
                        />
                    )}

                    {/* Measurement History Menu */}
                    {currentMenu === "measurementHistory-menu" && (
                        <QMeasureHistory
                            message={message}

                            toggleMenu={toggleMenu}

                            sortField={sortField}
                            setSortField={setSortField}
                            sortOrder={sortOrder}
                            setSortOrder={setSortOrder}
                            sortOptions={sortOptions}
                            sortedMeasurements={sortedMeasurements}

                            searchBy = {searchBy}
                            setSearchBy = {setSearchBy}
                            searchValue = {searchValue}
                            setSearchValue = {setSearchValue}
                            filteredMeasurements = {filteredMeasurements}
                            searchByOptions = {searchByOptions}

                            dateFilter = {dateFilter}
                            setDateFilter = {setDateFilter}
                            dateOptions = {dateOptions}

                            usersIDList={usersIDList}

                            measurementConfigModal={measurementConfigModal}
                            toggleMeasurementModal={toggleMeasurementModal}
                            measurementConfigModalPosition={measurementConfigModalPosition}
                            setMeasurementModalPosition={setMeasurementModalPosition}

                            measurementsConfigModal={measurementsConfigModal}
                            toggleMeasurementsModal={toggleMeasurementsModal}
                            measurementsConfigModalPosition={measurementsConfigModalPosition}
                            setMeasurementsModalPosition={setMeasurementsModalPosition}

                            selectedID={selectedID}
                            setSelectedID={setSelectedID}

                            viewMeasurement={viewMeasurement}
                            deleteMeasurement={deleteMeasurement}
                            deleteAllMeasurements={deleteAllMeasurements}

                            showMeasurementInfo={showMeasurementInfo}
                            setShowMeasurementInfo={setShowMeasurementInfo}
                            measureObjectImage={measureObjectImage}
                            measurementMode={measurementMode}
                            measureVolumeInfo={measureVolumeInfo}
                            setMeasureVolumeInfo={setMeasureVolumeInfo}
                            measureMultipleVolumeData={measureMultipleVolumeData}
                            measureObjectList={measureObjectList}
                            measureSelectedObject={measureSelectedObject}
                            setMeasureSelectedObject={setMeasureSelectedObject}

                            canvasRef={canvasRef}
                        />
                    )}

                    {/* Calibration Menu */}
                    {currentMenu === "calibration-menu" && (
                        <QCalibration
                            message={message}

                            toggleMenu={toggleMenu}

                            calibrationImage={calibrationImage}
                            workspaceCanvas={workspaceCanvas}

                            calibrationMode={calibrationMode}
                            rgb={rgb}

                            loadingCalibration={loadingCalibration}
                            calibrationModalOpen={calibrationModalOpen}

                            handleCalibrationModeChange={handleCalibrationModeChange}
                            calibrate_click={calibrate_click}
                            confirm_calibration={confirm_calibration}
                            portalContainer={appContainerRef.current}
                        />
                    )}

                    {/* User Panel */}
                    {showUserPopup && (
                        <QUserModal
                            savedUser={savedUser}
                            setShowUserPopup={setShowUserPopup}
                            userAnchorRect={userAnchorRect}
                            openChangePasswordModal={openChangePasswordModal}
                            openUsersPanel={openUsersPanel}
                            logout={logout}
                        />
                    )}

                    {/* Manage Users */}
                    {showUsersPanel && (
                        <QUserPanel
                            usersList={usersList}
                            usersLoading={usersLoading}
                            usersMsg={usersMsg}
                            savedUser={savedUser}

                            setShowUsersPanel={setShowUsersPanel}

                            changeUserRole={changeUserRole}
                            generateResetToken={generateResetToken}
                            resetTokensByUser={resetTokensByUser}
                            deleteUserById={deleteUserById}
                        />
                    )}

                    {showChangePasswordModal && (
                        <QChangePasswordModal
                            message={message}
                            closeChangePasswordModal={closeChangePasswordModal}
                            changeUsername={changeUsername}
                            changeCurrentPassword={changeCurrentPassword}
                            changePassword={changePassword}
                            changeConfirmPassword={changeConfirmPassword}
                            setChangeCurrentPassword={setChangeCurrentPassword}
                            setChangePassword={setChangePassword}
                            setChangeConfirmPassword={setChangeConfirmPassword}
                            changeCurrentPasswordFormError={changeCurrentPasswordFormError}
                            changePasswordFormError={changePasswordFormError}
                            changeConfirmPasswordFormError={changeConfirmPasswordFormError}
                            setChangeCurrentPasswordFormError={setChangeCurrentPasswordFormError}
                            setChangePasswordFormError={setChangePasswordFormError}
                            setChangeConfirmPasswordFormError={setChangeConfirmPasswordFormError}
                            changeCurrentPasswordFocus={changeCurrentPasswordFocus}
                            changePasswordFocus={changePasswordFocus}
                            changeConfirmPasswordFocus={changeConfirmPasswordFocus}
                            setChangeCurrentPasswordFocus={setChangeCurrentPasswordFocus}
                            setChangePasswordFocus={setChangePasswordFocus}
                            setChangeConfirmPasswordFocus={setChangeConfirmPasswordFocus}
                            confirmChangePassword={confirmChangePassword}
                            showLoginScreen={showLoginScreen}
                        />
                    )}

                    {/* Settings Panel */}
                    {showSettingsPopup && (
                        <QSettings
                            settingsAnchorRect={settingsAnchorRect}
                            setShowSettingsPopup={setShowSettingsPopup}

                            expHDR={expHDR}
                            handleExpHDR_toggle={handleExpHDR_toggle}
                            exposureTime={exposureTime}
                            setExposureTime={setExposureTime}
                            exposureSet_click={exposureSet_click}

                            volumeMode={volumeMode}
                            handleVolumeMode={handleVolumeMode}

                            countdownTimer={countdownTimer}
                            setCountdownTimer={setCountdownTimer}
                            countdownTimerSet_click={countdownTimerSet_click}

                            currentMenu={currentMenu}
                            setShowCropWindow={setShowCropWindow}

                            speedMode={speedMode}
                            handleSpeedMode={handleSpeedMode}
                        />
                    )}

                    {/* Window Resizer Panel */}
                    {showCropWindow && (
                        <QWindowResizer
                            cropVideo={cropVideo}
                            cropCanvas={cropCanvas}

                            cropArea={cropArea}
                            setCropArea={setCropArea}

                            setVideoCrop={setVideoCrop}

                            setShowCropWindow={setShowCropWindow}
                            setShowSettingsPopup={setShowSettingsPopup}

                            cropWindow_Set={cropWindow_Set}

                            ORIGINAL_CROP={ORIGINAL_CROP}
                            DEFAULT_CROP={DEFAULT_CROP}
                        />
                    )}
                </div>
            </>
        );
    } else if (!appReady) {
        return <QSystemLoader />;
    }
}

export default App;