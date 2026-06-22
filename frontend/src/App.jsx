import { useEffect, useRef, useState } from 'react';
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

function App() {
  const API_URL = import.meta.env.VITE_API_URL;

  // Errors and Info
  const TextLoginWelcome = "Welcome!"
  const TextLoginCredentials = "Please insert your login credentials.";

  const TextClear = "";
  const TextError = "Error";
  const TextServerConnection = "Server connection error";
  
  const TextFillAllFields = "Please fill in all fields";
  const TextRegistrationError = "Registration failed";
  const TextRegistrationSuccessfull = "Registration successful";

  const TextCalibrated = "System Calibrated";
  const TextNotCalibrated = "System was not Calibrated";
  const TextCenterNotAligned = "Center Point isn't Aligned";
  const TextWsNotEmpty = "Workspace isn't Empty";
  const TextWsNotEmptyAndCenterNotAligned = "Center Point isn't Aligned and Workspace isn't Empty";
  
  const TextOutOfLine = "There are objects outside the yellow stripes. To detect them, make sure they are inside the stripes.";

  const TextColorSlopeCaracters = "Only integer values are allowed for color slope";
  const TextColorSlopeValues = "Color Slope value must be between 150 and 5000";
  const TextColorSlopeUpdateSuccessfull = "Color Slope updated successfully";

  const TextExposureCaracters = "Only integer values are allowed for exposure time";
  const TextExposureValues = "Exposure Time value must be between 100 and 4000";
  const TextExposureUpdateSuccessfull = "Exposure Time updated successfully";

  const TextCountdownCaracters = "Only integer values are allowed for the Countdown Timer";
  const TextCountdownValues = "Countdown Timer value must be between 0 and 10";
  const TextCountdownUpdateSuccessfull = "Countdown Timer updated successfully";

  const [currentMenu, setCurrentMenu] = useState("login");

  const detectionArea = useRef([0, 0, 0, 0]);
  const selectedPoint = useRef(null);

  const cameraLoopInterval = useRef(null);
  const tokenCheckInterval = useRef(null);
  
  const step = 2;

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState([TextLoginWelcome, TextLoginCredentials]);

  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regRole, setRegRole] = useState("user");
  const [regCode, setRegCode] = useState("");

  const [ExpHDR_toggle, setExpHDR] = useState(true);
  const [volumeMode, setVolumeMode] = useState("multi_bundle");
  const [StaticDynamic_toggle, setStaticDynamic] = useState(false);
  const [DebugMode_toggle, setDebugMode] = useState(false);

  const [menuSideNav, setMenuSideNavOpen] = useState(false);
  const toggleMenu = () => setMenuSideNavOpen(prev => !prev);

  const [volInfo, setVolInfo] = useState(null);
  const [objCenters, setObjCenters] = useState([]);
  const [objAngles, setObjAngles] = useState([]);
  const [objOverlappedHeights, setOverlappedObjHeights] = useState([]);
  const [objectImage, setObjectImage] = useState(null);

  const [objectList, setObjectList] = useState([]);
  const [selectedObject, setSelectedObject] = useState("");
  const [multipleVolumeData, setVolumeData] = useState(null);

  const [savedUser, setSavedUser] = useState(null);

  const [exposureTime, setExposureTime] = useState("");
  const [colorSlope, setColorSlope] = useState("");

  const pc = useRef(null);
  const cameraVideo = useRef(null);

  const calibrationImage = useRef(null);

  const isAuthScreen = currentMenu === "login" || currentMenu === "register";

  const [rgb, setRgb] = useState({ r: 171, g: 170, b: 46 });

  const [calibrationModalOpen, setCalibrationModalOpen] = useState(false);
  const [showSettingsPopup, setShowSettingsPopup] = useState(false);
  const [showUserPopup, setShowUserPopup] = useState(false);

  const [loadingVolume, setLoadingVolume] = useState(false);
  const [loadingCalibration, setLoadingCalibration] = useState(false);

  const canvasRef = useRef(null);
  const angleRef = useRef(0.4);
  const dragging = useRef(false);
  const lastX = useRef(0);

  const [volBundleMode, setVolBundleMode] = useState(false);
  const [calibrationMode, setCalibrationMode] = useState("auto");

  const isDragging = useRef(false);
  const dragIndex = useRef(null);

  const [lockMenu, setLockMenu] = useState(false);

  const [countdownTimer, setCountdownTimer] = useState("");
  const [countdown, setCountdown] = useState(null);

  const [showCamera, setShowCamera] = useState(true);

  useEffect(() => {
    if (!showCamera) return;

    if (cameraVideo.current && pc.current?.getReceivers) {
      const receivers = pc.current.getReceivers();
      const stream = new MediaStream();

      receivers.forEach(r => {
        if (r.track) stream.addTrack(r.track);
      });

      cameraVideo.current.srcObject = stream;
    }
  }, [showCamera]);

  useEffect(() => {
    console.log(API_URL);
    const user = JSON.parse(localStorage.getItem("current_user"));

    if (!user) return;

    setSavedUser(user);
    restoreSession();
  }, []);

  async function restoreSession() {
    const access_token = localStorage.getItem("access_token");

    if (!access_token) {
      logout();
    }

    try {
      const res = await fetch(`${API_URL}/calibration/status`, {
        headers: {
          "Authorization": `Bearer ${access_token}`
        }
      });

      if (res.status === 401) {
        setCurrentMenu("login-menu");
        return;
      }

      const data = await res.json();

      if (!data.calibrated) {
        setCurrentMenu("calibration-menu");
        setLockMenu(true);
      } else {
        setCurrentMenu("volume-menu");
        setLockMenu(false);
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
      }

    } catch (err) {
      setCurrentMenu("login-menu");
    }
  }

  function showLoginScreen() {
      setCurrentMenu("login");

      setError([TextClear]);
      setRegUsername("");
      setRegPassword("");
      setRegRole("user");
      setRegCode("");
      setMenuSideNavOpen("false");
  }

  async function login() {
    if (!username || !password) {
      setError([TextFillAllFields]);
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

        const role = data.role;

        localStorage.setItem(
          "current_user",
          JSON.stringify({ username, role })
        );

        setSavedUser(JSON.parse(localStorage.getItem("current_user")));

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        await checkCalibration();

        setError([TextClear]);

      } else {
        const data = await response.json();
        setError([data.detail]);
      }

    } catch (error) {
      setError([TextServerConnection]);
    }
  }

  async function checkCalibration() {
    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");

    const res = await fetch(`${API_URL}/calibration/status`, {
      headers: {
        "Authorization": `Bearer ${access_token}`
      }
    });

    const data = await res.json();

    if (!data.calibrated) {
      setCurrentMenu("calibration-menu");
      setLockMenu(true);
    } else {
      setCurrentMenu("volume-menu");
      setLockMenu(false);
    }
  }

  function showRegisterScreen() {
      setCurrentMenu("register");
      setError([TextClear]);
      setUsername("");
      setPassword("");
  }

  async function register() {
      if (!regUsername || !regPassword || (regRole === "admin" && !regCode)) {
          setError([TextFillAllFields]);
          return;
      }

      try {
          const response = await fetch(`${API_URL}/register`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ username: regUsername, password: regPassword, role: regRole, code: regCode })
          });
          
          const data = await response.json();

          if (!response.ok) {
            setError([data.detail || TextRegistrationError]);
            return;
          }

      } catch (error) {
          setError([TextServerConnection]);
          return;
      }

      setError([TextRegistrationSuccessfull]);
      showLoginScreen();
  }

  function logout() {
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
    setCurrentMenu("login");
    setSavedUser(null);

    setMenuSideNavOpen(false)
    setShowUserPopup(false)

    setObjectList([]);
    setSelectedObject("");
    setVolInfo(null);
    setVolumeData(null);
  }

  // Change Menu Functions
  useEffect(() => {
    if (currentMenu === "login") {
      setError([TextLoginWelcome, TextLoginCredentials]);
    }

    if (currentMenu === "login" || currentMenu === "register") return;

    refreshAccessToken();
    setError([TextClear]);

    if (currentMenu === "calibration-menu") {
      workspaceDrawing();
      if (calibrationImage.current) {
        calibrationImage.current.crossOrigin = "anonymous";
        calibrationImage.current.src = `${API_URL}/calibrationCTD`;
      }
    }

    if (
      currentMenu === "config-menu" ||
      currentMenu === "calibration-menu"
    ) {
      refreshToggles();
    }

    return () => {
      if (cameraLoopInterval.current) {
        clearInterval(cameraLoopInterval.current);
        cameraLoopInterval.current = null;
      }
    };
  }, [currentMenu]);

  async function volume_click(){
      try{
        const start = performance.now();
        setObjectList([]);
        setSelectedObject("");
        setVolInfo(null);
        setVolumeData(null);
        setObjectImage(null);
        setShowCamera(true);
        refreshAccessToken();
        const access_token = localStorage.getItem("access_token");

        const response = await fetch(`${API_URL}/volume/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});

        if (response.status === 401) {
          throw new Error("Session expired");
        }

        const countResp = await fetch(`${API_URL}/countdown/value`, {headers: { "Authorization": `Bearer ${access_token}`}});
        const countData = await countResp.json();

        for (let i = countData.countdown; i > 0; i--) {
          setCountdown(i);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }

        setCountdown(null);

        setLoadingVolume(true);

        let volumeMode = await response.json();
        if (volumeMode["Volume Mode"] === "Single Bundle"){
          await volumeSingleBundle(access_token);
        } else if (volumeMode["Volume Mode"] === "Multi Bundle"){
          await volumeMultiBundle(access_token);
        } else if (volumeMode["Volume Mode"] === "Real"){
          await volumeReal(access_token);
        } else if (volumeMode["Volume Mode"] === "Individual"){
          await volumeIndividual(access_token);
        }
        const end = performance.now();
        console.log("TOTAL UI TIME:", end - start, "ms");
      } catch (error) {
        console.warn(error);
      }
  }

  async function volumeSingleBundle(access_token) {
    try {
      await fetch(`${API_URL}/volume/singleBundle`, { method: 'POST', headers: { "Authorization": `Bearer ${access_token}` } });

      const response = await fetch(`${API_URL}/getObjectsOutOfLine`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const data = await response.json();
      console.log(data.objects_outOfLine)
      const objectsOutOfLine = data.objects_outOfLine.map((val, i) => val ? i + 1 : null).filter(v => v !== null);
      if (objectsOutOfLine.length > 0) {
          setError([TextOutOfLine]);
      } else {
          setError([TextClear]);

          const dataResponse = await fetch(`${API_URL}/volume/singleBundle/results`, {headers: { "Authorization": `Bearer ${access_token}`}});
          const volumeData = await dataResponse.json();

          setVolInfo({
            volume_m: volumeData.Bundle.volume_m,
            volume_cm: volumeData.Bundle.volume_cm,
            width: volumeData.Bundle.x,
            length: volumeData.Bundle.y,
            height: volumeData.Bundle.z
          })
      }

      const imgResp = await fetch(`${API_URL}/getFrame/detectedObjectsFrame`, {headers: { "Authorization": `Bearer ${access_token}` }});
      if (imgResp.status === 404) throw new Error("Frame not Available");

      const blob = await imgResp.blob();
      const url = URL.createObjectURL(blob);
      setObjectImage(url);
      setShowCamera(false);
      //document.getElementById("object-img").removeAttribute("hidden");

    } catch (error) {
      setError([TextError]);
      console.error(error);
    } finally {
      setLoadingVolume(false);
    }
  }

  // Show Volume Depending of the selected object
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
    setOverlappedObjHeights(objData.obj_overlappedHeights ?? []);
  }, [selectedObject, multipleVolumeData]);

  async function volumeMultiBundle(access_token) {
    try {
      await fetch(`${API_URL}/volume/multiBundle`, { method: 'POST', headers: { "Authorization": `Bearer ${access_token}` } });
      const response = await fetch(`${API_URL}/getObjectsOutOfLine`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const data = await response.json();
      const objectsOutOfLine = data.objects_outOfLine.map((val, i) => val ? i + 1 : null).filter(v => v !== null);
      if (objectsOutOfLine.length > 0) {
          setError([TextOutOfLine]);
      } else {
          setError([TextClear]);
      }

      const dataResponse = await fetch(`${API_URL}/volume/multiBundle/results`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const volumeData = await dataResponse.json();

      setVolumeData(volumeData);

      const imgResp = await fetch(`${API_URL}/getFrame/detectedObjectsFrame`, {headers: { "Authorization": `Bearer ${access_token}` }});
      if (imgResp.status === 404) throw new Error("Frame not Available");

      const blob = await imgResp.blob();
      const url = URL.createObjectURL(blob);
      setObjectImage(url);
      setShowCamera(false);
      //document.getElementById("object-img").removeAttribute("hidden");

      const objIdentified = Object.keys(volumeData).filter(key => key !== "Total");
      
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
        })
      } else if (objIdentified.length > 1) {
        setObjectList(objIdentified);
        setSelectedObject("");
        setVolInfo(null);
      }
    } catch (error) {
      setVolInfo(null);
      setError([TextError]);
      console.error(error);
    } finally {
      setLoadingVolume(false);
    }
  }

  async function volumeReal(access_token) {
    try {
      await fetch(`${API_URL}/volume/real`, { method: 'POST', headers: { "Authorization": `Bearer ${access_token}` } });
      const response = await fetch(`${API_URL}/getObjectsOutOfLine`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const data = await response.json();
      const objectsOutOfLine = data.objects_outOfLine.map((val, i) => val ? i + 1 : null).filter(v => v !== null);
      if (objectsOutOfLine.length > 0) {
          setError([TextOutOfLine]);
      } else {
          setError([TextClear]);
      }

      const dataResponse = await fetch(`${API_URL}/volume/real/results`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const volumeData = await dataResponse.json();

      setVolumeData(volumeData);

      const imgResp = await fetch(`${API_URL}/getFrame/detectedObjectsFrame`, {headers: { "Authorization": `Bearer ${access_token}` }});
      if (imgResp.status === 404) throw new Error("Frame not Available");

      const blob = await imgResp.blob();
      const url = URL.createObjectURL(blob);
      setObjectImage(url);
      setShowCamera(false);
      //document.getElementById("object-img").removeAttribute("hidden");

      const objIdentified = Object.keys(volumeData).filter(key => key !== "Total");

      if (objIdentified.length === 1) {
        
        const key = objIdentified[0];
        const objData = volumeData[key];

        setObjCenters(objData.obj_center ?? []);
        setObjAngles(objData.obj_angles ?? []);
        setOverlappedObjHeights(objData.obj_overlappedHeights ?? []);

        setSelectedObject(key);

        setObjectList([key]);
        setVolInfo({
          volume_m: objData.volume_m,
          volume_cm: objData.volume_cm,
          width: objData.x,
          length: objData.y,
          height: objData.z
        })
      } else if (objIdentified.length > 1) {
        setObjectList(objIdentified);
        setSelectedObject("");
        setVolInfo(null);
      }
    } catch (error) {
      setVolInfo(null);
      setError([TextError]);
      console.error(error);
    } finally {
      setLoadingVolume(false);
    }
  }

  async function volumeIndividual(access_token) {
    try {
      await fetch(`${API_URL}/volume/individual`, { method: 'POST', headers: { "Authorization": `Bearer ${access_token}` } });
      const response = await fetch(`${API_URL}/getObjectsOutOfLine`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const data = await response.json();
      const objectsOutOfLine = data.objects_outOfLine.map((val, i) => val ? i + 1 : null).filter(v => v !== null);
      if (objectsOutOfLine.length > 0) {
          setError([TextOutOfLine]);
      } else {
          setError([TextClear]);
      }

      const dataResponse = await fetch(`${API_URL}/volume/individual/results`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const volumeData = await dataResponse.json();

      setVolumeData(volumeData);

      const imgResp = await fetch(`${API_URL}/getFrame/detectedObjectsFrame`, {headers: { "Authorization": `Bearer ${access_token}` }});
      if (imgResp.status === 404) throw new Error("Frame not Available");

      const blob = await imgResp.blob();
      const url = URL.createObjectURL(blob);
      setObjectImage(url);
      setShowCamera(false);
      //document.getElementById("object-img").removeAttribute("hidden");

      const objIdentified = Object.keys(volumeData).filter(key => key !== "Total");
      
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
        })
      } else if (objIdentified.length > 1) {
        setObjectList(objIdentified);
        setSelectedObject("");
        setVolInfo(null);
      }
    } catch (error) {
      setVolInfo(null);
      setError([TextError]);
      console.error(error);
    } finally {
      setLoadingVolume(false);
    }
  }

  // 3D Box
  useEffect(() => {
    if (currentMenu !== "volume-menu") return;

    if (!volBundleMode){
      if(!selectedObject) return;
    }

    if(volBundleMode){
      if(multipleVolumeData) return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    ctx.setTransform(1, 0, 0, 1, 0, 0);

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    ctx.scale(dpr, dpr);

    ctx.lineJoin = "round";
    ctx.lineCap = "round";

    if (!volInfo) {
      ctx.clearRect(0, 0, rect.width, rect.height);
      return;
    }

    const project = (x, y, z, cx, cy, scale) => {
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

    const drawEdge = (a, b, color) => {
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    };

    const drawLabel = (a, b, text, color, edgeType) => {
      const midX = (a.x + b.x) / 2;
      const midY = (a.y + b.y) / 2;

      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const len = Math.sqrt(dx * dx + dy * dy);

      let ox = 0, oy = 0;

      if (edgeType === 'height') {
        const nx = -(dy / len);
        ox = nx * 22 + 18;
        oy = 0;
      } else if (edgeType === 'width'){
        const ux = dx / len;
        const uy = dy / len;
        let nx = -uy;
        let ny = ux;
        const bias = -1;
        nx *= bias;
        ny *= bias;
        ox = nx * 28;
        oy = ny * 22;
      } else if (edgeType === 'length'){
        const ux = dx / len;
        const uy = dy / len;
        let nx = -uy;
        let ny = ux;
        const bias = 1;
        nx *= bias;
        ny *= bias;
        ox = nx * 28;
        oy = ny * 22;
      }
      
      ctx.fillStyle = color;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, midX + ox, midY + oy);
    };

    const draw = () => {
      const W = rect.width;
      const H = rect.height;

      ctx.clearRect(0, 0, W, H);

      const boxes = volumeMode === "real"
        ? volInfo.width.slice(1).map((_, i) => ({
            width: volInfo.width[i + 1],
            length: volInfo.length[i + 1],
            height: volInfo.height[i + 1],
          })).reverse()
        : [volInfo];

      //console.log("Obj Centers", objCenters)
      const centers = volumeMode === "real"
        ? objCenters.slice().reverse()
        : objCenters;

      const angles = volumeMode === "real"
        ? objAngles.slice().reverse()
        : objAngles;

      const overlappedHeights = volumeMode === "real"
        ? objOverlappedHeights.slice().reverse()
        : objOverlappedHeights;

      const maxWidth = Math.max(...boxes.map(b => b.width));
      const maxLength = Math.max(...boxes.map(b => b.length));
      const totalHeight = boxes.reduce((sum, b) => sum + b.height, 0);

      const maxDim = Math.max(maxWidth, maxLength, totalHeight);

      const scale = Math.min(W, H) * 0.7;
      const fontSize = Math.max(15, Math.min(22, scale * 0.04));
      ctx.font = `${fontSize}px Inter Regular`;

      const cx = W / 2;
      const cy = H / 2;

      const rotCenter = centers[0] ?? [0, 0];
      const pivot_cx = rotCenter[0] / maxDim
      const pivot_cy = rotCenter[1] / maxDim

      let baseHeight = -totalHeight / 2;

      boxes.forEach((box, i) => {
        let bottom, top
        const [center_x, center_y] = centers[i] ?? [0, 0];
        //console.log(center_x, center_y);

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

        const rotate = (x,y) => ({
          x: x * ca - y * sa,
          y: x * sa + y * ca,
        });

        const bottomHeight = overlappedHeights[i] ?? 0;
        if (i === 0 || bottomHeight === 0){
          bottom = baseHeight / maxDim;
          top = (baseHeight + h) / maxDim;
        } else{
          bottom = (baseHeight + bottomHeight * 100) / maxDim;
          top = (baseHeight + bottomHeight * 100 + h) / maxDim;
        }

        console.log("OverlappedHeights", overlappedHeights)
        console.log("BottomHeight", bottomHeight * 100);
        console.log("Bottom", bottom);
        console.log("Top", top);
        console.log("BaseHeight", baseHeight);

        const p0 = rotate(-hw, -hd);
        const p1 = rotate(hw, -hd);
        const p2 = rotate(hw, hd);
        const p3 = rotate(-hw, hd);
        
        const center = rotate(
          (center_x / maxDim) - pivot_cx,
          (center_y / maxDim) - pivot_cy
        );

        const offX = center.x;
        const offY = center.y;

        const v = [
          project(p0.x + offX, p0.y + offY, bottom, cx , cy, scale),
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
          [0,1,2,3],
          [4,5,6,7],
          [0,1,5,4],
          [2,3,7,6],
          [1,2,6,5],
          [0,3,7,4],
        ];

        const faceDepth = faces.map(face => ({
          face,
          z: face.reduce((s, i) => s + v[i].z, 0) / 4
        }));

        faceDepth.sort((a, b) => a.z - b.z);

        faceDepth.forEach(({ face }) => {
          const [a,b,c,d] = face;

          ctx.beginPath();
          ctx.moveTo(v[a].x, v[a].y);
          ctx.lineTo(v[b].x, v[b].y);
          ctx.lineTo(v[c].x, v[c].y);
          ctx.lineTo(v[d].x, v[d].y);
          ctx.closePath();

          ctx.fillStyle = "rgba(186,186,231,0.03)";
          ctx.fill();

          ctx.strokeStyle = "#aaa";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        });

        const edges = [
          [0,1,X,"Width"], [3,2,X], [4,5,X], [7,6,X],
          [0,3,Y,"Length"], [1,2,Y], [4,7,Y], [5,6,Y],
          [0,4,Z,"Height"], [1,5,Z], [2,6,Z], [3,7,Z],
        ];

        edges.forEach(([a,b,color,type]) => {
          drawEdge(v[a], v[b], color);

          const value =
            type === "Width" ? volInfo.width :
            type === "Length" ? volInfo.length:
            type === "Height" ? volInfo.height :
            ""

          {/*if (type == "Width"){
            drawLabel(v[a], v[b], `${value} cm`, color, "width");
          } else if (type == "Length"){
            drawLabel(v[a], v[b], `${value} cm`, color, "length");
          } else if (type == "Height"){
            drawLabel(v[a], v[b], `${value} cm`, color, "height");
          }*/}
        });

        //accumulatedHeight += h;
      
      });
    };

    let frameId;

    const animate = () => {
      if (!dragging.current) angleRef.current += 0.005;

      draw();
      frameId = requestAnimationFrame(animate);
    };

    animate();

    const down = (e) => {
      dragging.current = true;
      lastX.current = e.clientX;
    };

    const move = (e) => {
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
  }, [volInfo, currentMenu]);
              
  async function handleExpHDR_toggle(e) {
    const checked = e.target.value === "true";
    setExpHDR(checked);
    
    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");
    
    if (checked) {
        await fetch(`${API_URL}/exposition/mode/hdr`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    } else {
        await fetch(`${API_URL}/exposition/mode/fixed`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    }

    await fetch(`${API_URL}/saveInfo`, {method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });
  }

  async function handleVolumeMode(e) {
    const mode = e.target.value;
    setVolumeMode(mode);
    setShowCamera(true);
    setObjectImage(null);
    setObjectList([]);
    setSelectedObject("");
    setVolInfo(null);
    setVolumeData(null);

    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");

    switch (mode) {
      case "single_bundle":
          await fetch(`${API_URL}/volume/mode/singleBundle`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
          setVolBundleMode(true);
          break;
      case "multi_bundle":
          await fetch(`${API_URL}/volume/mode/multiBundle`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
          setVolBundleMode(false);
          break;
      case "real":
          await fetch(`${API_URL}/volume/mode/real`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
          setVolBundleMode(false);
          break;
      case "individual":
          await fetch(`${API_URL}/volume/mode/individual`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
          setVolBundleMode(false);
          break;
    }

    await fetch(`${API_URL}/saveInfo`, {method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });
  }

  async function handleStaticDynamic_toggle(e) {
    const checked = e.target.checked;
    setStaticDynamic(checked);
      
    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");

    if (checked) {
        await fetch(`${API_URL}/working/mode/dynamic`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    } else {
        await fetch(`${API_URL}/working/mode/static`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    }
  }

  async function handleDebugMode_toggle(e) {
    const checked = e.target.checked;
    setDebugMode(checked);

    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");

    if (checked) {
        await fetch(`${API_URL}/debug/mode/on`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });
    } else {
        await fetch(`${API_URL}/debug/mode/off`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });
    }
  }

  async function exposureSet_click() {
    const value = Number(exposureTime);
    
    if (!Number.isInteger(value)) {
        setError([TextExposureCaracters]);
        return;
    }

    if (value < 100 || value > 4000) {
        setError([TextExposureValues]);
        return;
    }

    try {
        refreshAccessToken();
        const access_token = localStorage.getItem("access_token");

        await fetch(`${API_URL}/update_systemInfo`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json", "Authorization": `Bearer ${access_token}`
            },
            body: JSON.stringify({ exposureTime: value })
        });

        await fetch(`${API_URL}/saveInfo`, {method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });

        setError([TextExposureUpdateSuccessfull]);
    } catch (error) {
        console.error("Exposure set error:", error);
    }
  }

  async function countdownTimerSet_click() {
    const value = Number(countdownTimer);
    
    if (!Number.isInteger(value)) {
        setError([TextCountdownCaracters]);
        return;
    }

    if (value < 0 || value > 10) {
        setError([TextCountdownValues]);
        return;
    }

    try {
        refreshAccessToken();
        const access_token = localStorage.getItem("access_token");

        await fetch(`${API_URL}/update_systemInfo`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json", "Authorization": `Bearer ${access_token}`
            },
            body: JSON.stringify({ countdown: value })
        });

        await fetch(`${API_URL}/saveInfo`, {method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });

        setError([TextCountdownUpdateSuccessfull]);
    } catch (error) {
        console.error("Countdown set error:", error);
    }
  }

  async function colorSlopeSet_click() {
    const value = Number(colorSlope);
    if (!Number.isInteger(value)) {
        setError([TextColorSlopeCaracters]);
        return;
    }

    if (value < 150 || value > 5000) {
        setError([TextColorSlopeValues]);
        return;
    }

    try {
        refreshAccessToken();
        const access_token = localStorage.getItem("access_token");

        await fetch(`${API_URL}/update_systemInfo`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json", "Authorization": `Bearer ${access_token}`
            },
            body: JSON.stringify({ colorSlope: value })
        });

        setError([TextColorSlopeUpdateSuccessfull]);
    } catch (error) {
        console.error("Color slope set error:", error);
    }
  }

  // Repeat Toggle Status every 500ms
  useEffect(() => {
    if (currentMenu !== "config-menu" && currentMenu !== "calibration-menu") {
      return;
    }

    const interval = setInterval(() => {
      refreshToggles();
    }, 500);

    return () => {
      clearInterval(interval);
    };
  }, [currentMenu]);

  async function refreshToggles() {
    try {
      const access_token = localStorage.getItem("access_token");

      if(currentMenu === "config-menu") {
          // EXPOSITION MODE
          const r1 = await fetch(`${API_URL}/exposition/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});
          const expData = await r1.json();

          setExpHDR(expData["Exposition Mode"] === "HDR");

          // VOLUME MODE
          const r2 = await fetch(`${API_URL}/volume/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});
          const volumeData = await r2.json();

          setVolumeMode(volumeData["Volume Mode"]);

         // MODE (Static / Dynamic)
          const r3 = await fetch(`${API_URL}/working/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});
          const modeData = await r3.json();

          setStaticDynamic(modeData["Mode"] === "Dynamic");

          // DEBUG MODE
          const r4 = await fetch(`${API_URL}/debug/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});
          const debugData = await r4.json();

          setDebugMode(debugData["Debug Mode"] === "On");
        }
      } catch (error) {
          console.log("Toggle refresh error:", error);
      }
  }

  async function applyMask(access_token) {
    try {
      const r = await fetch(`${API_URL}/mask`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const maskValues = await r.json();
      await fetch(`${API_URL}/applyMask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${access_token}` },
          body: JSON.stringify(maskValues)
      });
    } catch (err) { console.warn("Erro applyMask:", err); }
  }

  async function applyManualWSDraw(access_token) {
    try {
      if (selectedPoint.current === null) {
          const r = await fetch(`${API_URL}/calibrate/params`, { headers: { "Authorization": `Bearer ${access_token}` } });
          detectionArea.current = (await r.json())["Detected Area"];
      }
      await fetch(`${API_URL}/applyManualWorkspace`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${access_token}` },
          body: JSON.stringify({ detection_area: detectionArea.current, selected_point: selectedPoint.current })
      });
    } catch (err) { console.warn("Erro applyManualWSDraw:", err); }
  }

  // Workspace Drawing Loop
  useEffect(() => {
    if(currentMenu !== "calibration-menu") return;

    let active = true;

    const loop = async () => {
      if (!active) return;

      workspaceDrawing();

      if (active) {
        setTimeout(loop, 500);
      }
    };

    loop();

    return () => {
      active = false;
    };
  }, [currentMenu]);

  async function workspaceDrawing(){
    try{
      const access_token = localStorage.getItem("access_token");
      const r = await fetch(`${API_URL}/calibrate/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});
      const calibData = await r.json();
      if (calibData["Calibrate Mode"] === "Automatic") {
        if (currentMenu !== "calibration-menu") return;
        applyMask(access_token);
      } else if (calibData["Calibrate Mode"] === "Manual") {
        applyManualWSDraw(access_token);
      }
    } catch (err) { console.warn("Erro drawing Workspace:", err); }
  }

  // Screen Click
  useEffect(() => {
    if (currentMenu !== "calibration-menu") return;

    const img = calibrationImage.current;
    if (!img) return;

    const handleClick = async (event) => {
      try {
        const access_token = localStorage.getItem("access_token");

        const calibRes = await fetch(
          `${API_URL}/calibrate/mode`,
          { headers: { "Authorization": `Bearer ${access_token}` } }
        );

        const calibData = await calibRes.json();

        const rect = img.getBoundingClientRect();
        const x = Math.round((event.clientX - rect.left) * (img.naturalWidth / rect.width));
        const y = Math.round((event.clientY - rect.top) * (img.naturalHeight / rect.height));

        if (calibData["Calibrate Mode"] === "Automatic") {

          await fetch(
            `${API_URL}/mask/colorClick`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${access_token}`
              },
              body: JSON.stringify({ x, y })
            }
          );

          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");

          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
          ctx.drawImage(img, 0, 0);

          const pixel = ctx.getImageData(x, y, 1, 1).data;
          const r_color = pixel[0];
          const g_color = pixel[1];
          const b_color = pixel[2];

          setRgb({
            r: r_color,
            g: g_color,
            b: b_color
          });

          await new Promise(r => setTimeout(r, 500));

          handleCalibrationModeChange(true);

        } else if (calibData["Calibrate Mode"] === "Manual") {

          const r = await fetch(
            `${API_URL}/calibrate/params`,
            { headers: { "Authorization": `Bearer ${access_token}` } }
          );

          const response = await r.json();
          const points = response["Detected Area"];

          let minDist = Infinity;
          let closestPoint = null;

          points.forEach((point, index) => {
            const dist = Math.sqrt(
              (point[0] - x) ** 2 + (point[1] - y) ** 2
            );

            if (dist < minDist) {
              minDist = dist;
              closestPoint = index;
            }
          });

          if (minDist <= 10) {
            selectedPoint.current = closestPoint;
            console.log("Selected point:", closestPoint);
          } else {
            selectedPoint.current = null;
            console.log("None of the points were selected");
          }
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

  // Key Press for Manual Workspace Adjustment
  useEffect(() => {
    if (currentMenu !== "calibration-menu") return;

    const access_token = localStorage.getItem("access_token");

    let active = true;

    const init = async () => {
      if (!active) return;

      console.log("detectionAreaKey:", detectionArea.current);
      console.log("selectedPointKey:", selectedPoint.current);
      console.log("pointKey:", detectionArea.current[selectedPoint.current]);

      const handleKeyDown = async (event) => {
        try{
          const r_mode = await fetch(`${API_URL}/calibrate/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});
          const calibData = await r_mode.json();

          if (calibData["Calibrate Mode"] !== "Manual") return;

          if (selectedPoint.current === null) return;

          //const r = await fetch(`${API_URL}/calibrate/params`, {headers: { "Authorization": `Bearer ${access_token}`}});
          //let data = await r.json();
          //let detection_area = data["Detected Area"]; // [x1, y1, x2, y2]

          const img = calibrationImage.current;
          const maxX = img.naturalWidth;
          const maxY = img.naturalHeight;

          let point = detectionArea.current[selectedPoint.current];
          if (event.key === "ArrowLeft") {
            point[0] = Math.max(0, point[0] - step);

          } else if (event.key === "ArrowRight") {
            point[0] = Math.min(maxX, point[0] + step);

          } else if (event.key === "ArrowUp") {
            point[1] = Math.max(0, point[1] - step);

          } else if (event.key === "ArrowDown") {
            point[1] = Math.min(maxY, point[1] + step);

          }

          detectionArea.current[selectedPoint.current] = point;
          console.log("detectionAreaKey:", detectionArea.current);
          console.log("selectedPointKey:", selectedPoint.current);
          console.log("pointKey:", detectionArea.current[selectedPoint.current]);
        } catch (error) {
          console.warn("Erro key_pressed:", error);
        }
     };

      document.addEventListener("keydown", handleKeyDown);

      return () => {
        document.removeEventListener("keydown", handleKeyDown);
      };
    };

    let cleanup;

    init().then((fn) => {
      cleanup = fn;
    });

    return () => {
      active = false;
      if (cleanup) cleanup();
    };
    
  }, [currentMenu, selectedPoint]);

  useEffect(() => {
    if (currentMenu !== "calibration-menu") return;

    if (calibrationMode !== "manual") return;

    const img = calibrationImage.current;
    if (!img) return;

    img.addEventListener("pointerdown", handleMouseDown);
    img.addEventListener("pointermove", handleMouseMove);
    window.addEventListener("pointerup", handleMouseUp);
    window.addEventListener("pointercancel", handleMouseUp);

    return () => {
      img.removeEventListener("pointerdown", handleMouseDown);
      img.removeEventListener("pointermove", handleMouseMove);
      window.removeEventListener("pointerup", handleMouseUp);
      window.removeEventListener("pointercancel", handleMouseUp);
    };
  }, [currentMenu, calibrationMode]);
  
  function getMousePos(event, img) {
    const rect = img.getBoundingClientRect();

    const clientX = event.clientX ?? event.touches?.[0]?.clientX;
    const clientY = event.clientY ?? event.touches?.[0]?.clientY;

    const x = Math.round(
      (clientX - rect.left) * (img.naturalWidth / rect.width)
    );

    const y = Math.round(
      (clientY - rect.top) * (img.naturalHeight / rect.height)
    );

    return { x, y };
  }

  const handleMouseDown = (event) => {
    if (currentMenu !== "calibration-menu") return;

    const img = calibrationImage.current;
    if (!img) return;

    img.setPointerCapture?.(event.pointerId);

    const { x, y } = getMousePos(event, img);

    const points = detectionArea.current;

    let minDist = Infinity;
    let closest = null;

    points.forEach((p, i) => {
      const dist = Math.hypot(p[0] - x, p[1] - y);
      if (dist < minDist) {
        minDist = dist;
        closest = i;
      }
    });

    if (minDist <= 10) {
      isDragging.current = true;
      dragIndex.current = closest;
      selectedPoint.current = closest;
    }
  };

  const handleMouseMove = (event) => {
    if (!isDragging.current) return;
    if (dragIndex.current === null) return;

    const img = calibrationImage.current;
    if (!img) return;

    const { x, y } = getMousePos(event, img);

    const points = detectionArea.current;

    points[dragIndex.current] = [x, y];

    detectionArea.current = [...points];
  };

  const handleMouseUp = () => {
    isDragging.current = false;
    dragIndex.current = null;
  };

  function startCalibration(){
    calibrate_click();
  }

  async function handleCalibrationModeChange(Manual){
      refreshAccessToken();
      const access_token = localStorage.getItem("access_token");
      
      if (Manual){
        setCalibrationMode("manual");
        await fetch(`${API_URL}/calibrate/mode/manual`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` }});
      } else {
        setCalibrationMode("auto");
        await fetch(`${API_URL}/calibrate/mode/automatic`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` }});
      }
  }

  async function calibrate_click() {
    try {
      setLoadingCalibration(true);
      setError([TextClear]);
      refreshAccessToken();
      const access_token = localStorage.getItem("access_token");

      const maskResponse = await fetch(`${API_URL}/mask`, {headers: { "Authorization": `Bearer ${access_token}`}});
      if (!maskResponse.ok) throw new Error("Mask request failed");
      const maskValues = await maskResponse.json();

      const calibrateResponse = await fetch(`${API_URL}/calibrate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json", "Authorization": `Bearer ${access_token}`
        },
        body: JSON.stringify(maskValues)
      });

      if (!calibrateResponse.ok) throw new Error("Calibrate request failed");

      const flagsResponse = await fetch(`${API_URL}/calibrate/flags`, { headers: { "Authorization": `Bearer ${access_token}` } });
      if (!flagsResponse.ok) throw new Error("Flags request failed");

      const data = await flagsResponse.json();

      const center_aligned = data["Center Aligned"];
      const ws_clear = data["Workspace Clear"];

      if (center_aligned && ws_clear) {
        setError([TextCalibrated, TextClear]);
        setCalibrationModalOpen(true);
      }
      else if (center_aligned && !ws_clear) {
        setError([TextNotCalibrated, TextWsNotEmpty]);
      }
      else if (!center_aligned && ws_clear) {
        setError([TextNotCalibrated, TextCenterNotAligned]);
      }
      else {
        setError([TextNotCalibrated, TextWsNotEmptyAndCenterNotAligned]);
      }

      /*const r = await fetch(`${API_URL}/calibrate/mode`, {headers: { "Authorization": `Bearer ${access_token}`}});
      let calibData = await r.json();
      if (calibData["Calibrate Mode"] === "Manual") {
        await fetch(`${API_URL}/calibrate/mode/automatic`, { method: "POST", headers: { "Authorization": `Bearer ${access_token}` }});
      }*/

      selectedPoint.current = null;

    } catch (error) {
      setError([TextError]);
      console.error(error);
    } finally {
      setLoadingCalibration(false);
    }
  }
 
  async function confirm_calibration(confirm) {
    try {
      setCalibrationModalOpen(false);
      setError([TextClear]);
      refreshAccessToken();
      const access_token = localStorage.getItem("access_token");

      if(confirm){
        const calibrateResponse = await fetch(`${API_URL}/saveCalibration`, {
          method: "POST",
          headers: {
              "Content-Type": "application/json", "Authorization": `Bearer ${access_token}`
          }
        });

        if (!calibrateResponse.ok) throw new Error("Save calibration request failed");
        setLockMenu(false);
        setCurrentMenu("volume-menu");
        setError([TextCalibrated, TextClear]);
      }else{
        setError([TextNotCalibrated, TextClear]);
      }

    } catch (error) {
      setError([TextError]);
      console.error(error);
    }
  }

  // Start Token Check Loop
  useEffect(() => {
    const timer = 5 * 60 * 1000;

    if (!localStorage.getItem("access_token")) return;

    const interval = setInterval(() => {
      const access_token = localStorage.getItem("access_token");
      if (!access_token) {
        logout();
        return;
      }

      const refresh_token = localStorage.getItem("refresh_token");

      try {
        const payloadBase64 = refresh_token.split('.')[1];
        const payload = JSON.parse(atob(payloadBase64));
        const exp = payload.exp;
        const currentTime = Math.floor(Date.now() / 1000);

        if (currentTime >= exp) {
          logout();
        }

      } catch (e) {
        console.warn("Token parse error:", e);
        logout();
      }

    }, timer);

    return () => clearInterval(interval);
  }, [currentMenu]);

  async function refreshAccessToken() {
      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) return false;

      try {
          const response = await fetch(`${API_URL}/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken })
          });

          if (response.ok) {
              const data = await response.json();

              localStorage.setItem("access_token", data.access_token);
              localStorage.setItem("refresh_token", data.refresh_token);
              
              return true;
          }
      } catch (e) {
        console.warn("Refresh error:", e);
        logout();
        return false;
      }
  }

  useEffect(() => {
    const handleMenu = async () => {
      if (currentMenu === "volume-menu") {
        startWebRTC("volume");
        await fetch(`${API_URL}/menu/volume/open`, {method: "POST"});
      } else if (currentMenu === "calibration-menu") {
        startWebRTC("calibration");
        await fetch(`${API_URL}/menu/volume/close`, {method: "POST"});
      } else {
        stopWebRTC();
        await fetch(`${API_URL}/menu/volume/close`, {method: "POST"});
      }
    };

    handleMenu();
    
  }, [currentMenu]);

  async function startWebRTC(streamType) {
    const access_token = localStorage.getItem("access_token");

    pc.current = new RTCPeerConnection();

    pc.current.addTransceiver('video', { direction: 'recvonly' });

    pc.current.ontrack = async (event) => {
      if (cameraVideo.current) {
        cameraVideo.current.srcObject = event.streams[0];

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

    const response = await fetch(`${API_URL}/offer`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${access_token}`
        },
        body: JSON.stringify({
            sdp: pc.current.localDescription.sdp,
            type: pc.current.localDescription.type,
            stream: streamType
        })
    });

    const answer = await response.json();

    await pc.current.setRemoteDescription(answer);
  }

  function stopWebRTC() {
    const video = cameraVideo.current;

    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }

    if (pc.current) {
      pc.current.ontrack = null;
      pc.current.close();
      pc.current = null;
    }
  }

  return (
    <>
      {/* Menu Side Nav */}
      <div className={`menuSideNav ${(!isAuthScreen && menuSideNav) ? "open" : ""}`}>
        {!lockMenu && (
          <div
            className={`nav-item ${currentMenu === "volume-menu" ? "active" : ""}`}
            onClick={() => setCurrentMenu("volume-menu")}
          >
            VOLUME
          </div>
        )}

        <div
          className={`nav-item ${currentMenu === "calibration-menu" ? "active" : ""}`}
          onClick={() => setCurrentMenu("calibration-menu")}
        >
          CALIBRATION
        </div>
        {/*<div className={`nav-item ${currentMenu === "about-menu" ? "active" : ""}`}>
          ABOUT
        </div>*/}

        <img
          src="/settings.svg"
          className={`nav-icon ${!menuSideNav ? "hidden" : ""}`}
          onClick={() => setShowSettingsPopup(true)}
        />

        <img
          src="/user.svg"
          className={`nav-icon ${currentMenu === "login" ? "hidden" : ""}`}
          /*onClick={toggleUserMenu}*/
          onClick={() => setShowUserPopup(true)}
        />

      </div>

      {/* Login Screen Panel */}
      {currentMenu === "login" && (
        <div>
          <img src="/Qubic.svg" className="qubic-logo" alt="Qubic Logo"/> 

          <div className="login-panel">
            <div className="login-panel-title">Login</div>

            <div className="login-panel-error-or-info">
              {error.map((err, i) => (<p key={i}>{err}</p>))}
            </div>

            <form className="login-form" onSubmit={(e) => { e.preventDefault(); login(); }}>
              <input
                className="login-input username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
              />

              <input
                className="login-input password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
              />

              <button className="login-button" type="submit">
                <div className="background"></div>
                <span className="text">Login</span>
              </button>
            </form>

            {/*<p style={{ marginTop: "15px" }}>
              Don't have an account?{" "}
              <span
                onClick={showRegisterScreen}
                style={{
                  color: "black",
                  cursor: "pointer",
                  textDecoration: "underline"
                }}
              >
                Register
              </span>
            </p>*/}

          </div>

          <div className="powered-by-panel-login">
              <div className="powered-by-text-login" translate="no">Powered by</div>
              <img src="/MarquesLogo.svg" className="powered-by-logo-login" alt="Marques Logo"/>
          </div>
        </div>
      )}

      {/* Register Screen Panel */}
      {/*{currentMenu === "register" && (
        <div className="menu">
          <h2>Register</h2>

          <form onSubmit={(e) => { e.preventDefault(); register(); }}>
            <input
              type="text"
              value={regUsername}
              onChange={(e) => setRegUsername(e.target.value)}
              placeholder="Username"
            />
            <br />
            <br />

            <input
              type="password"
              value={regPassword}
              onChange={(e) => setRegPassword(e.target.value)}
              placeholder="Password"
            />
            <br />
            <br />

            <select
              value={regRole}
              onChange={(e) => setRegRole(e.target.value)}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
            <br />
            <br />

            <input
              type="text"
              value={regCode}
              onChange={(e) => setRegCode(e.target.value)}
              placeholder="Admin Code"
              disabled={regRole !== "admin"}
            />
            <br />
            <br />

            <button type="submit">
              Register
            </button>
          </form>

          <p style={{ marginTop: "15px" }}>
            Already have an account?{" "}
            <span
              onClick={showLoginScreen}
              style={{
                color: "black",
                cursor: "pointer",
                textDecoration: "underline"
              }}
            >
              Login
            </span>
          </p>

          <div style={{ color: "red" }}>{error.map((err, i) => (<p key={i}>{err}</p>))}</div>
        </div>
      )}*/}
        
      {/* Volume Panel */}
      {currentMenu === "volume-menu" && (
        <div>
          {/* Logo */}
          <button className="logo">
            <img src="/Qubic.svg" alt="BM Logo" />
          </button>

          {/* Menu */}
          <button className="menu-img" onClick={toggleMenu}>
            <img src="/menu-closed.svg" alt="Menu" />
          </button>

          {/* Warning */}
          <div className="warning">
            {error.map((err, i) => (
              <p key={i}>{err}</p>
            ))}
          </div>

          <div className="menu-wrapper">
            <div className="title-container">
              <div className="menu-title">Volume</div>
              <div className="menu-info">Calculates the volume of objects on the platform</div>
            </div>

            {/* Video & Image */}
            <div className="camera-container">
              <div className="camera-video-wrapper">
                {showCamera ? (
                  <div>
                    <video
                      ref={cameraVideo}
                      autoPlay
                      playsInline
                      className="camera-video"
                    />
                  </div>
                ) : (
                  objectImage && (
                    <div>
                      <img className="object-img" src={objectImage} alt="objects"/>
                    </div>
                  )
                )}
              </div>

              <div className="switch-button-wrapper">
                {objectImage && (
                  <button onClick={() => setShowCamera(prev => !prev)} className="switch-button"></button>
                )}
              </div>
            </div>

            {volBundleMode && (
              <>
                {/* Button */}
                <button onClick={volume_click} className="volumeBundle-button" disabled={loadingVolume}>
                  {loadingVolume && (
                    <div className="loadingVolume-icon">  
                      <img src="/loading.svg" alt="loading"/>
                    </div>
                  )}
                  <div className="volumeBundle-button-info-container">
                    <img src="/VIEW_IN_AR.svg" alt="VIEW_IN_AR" className="icon"/>
                    <span className="text">Get Volume</span>
                  </div>
                </button>

                {/* Info Objects */}
                <div className="boxBundleInfo-container">
                  <div className="background"></div>

                  {volInfo && !multipleVolumeData && (
                    <>
                      <canvas ref={canvasRef} className="volumeBundle-canvas"/>
                      <div className="boxBundleInfoText-container">
                        <div style={{ color: "#6CD08A" }} className="boxBundleInfo-text">
                          <span className="label">Width (cm):</span>
                          <span className="value">{volInfo.width.toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#C66D6D" }} className="boxBundleInfo-text">
                          <span className="label">Length (cm):</span>
                          <span className="value">{volInfo.length.toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#9EB0FD" }} className="boxBundleInfo-text">
                          <span className="label">Height (cm):</span>
                          <span className="value">{volInfo.height.toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="boxBundleInfo-text">
                          <span className="label">Volume (m³):</span>
                          <span className="value">{volInfo.volume_m.toFixed(6)}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="boxBundleInfo-text">
                          <span className="label">Volume (cm³):</span>
                          <span className="value">{volInfo.volume_cm.toFixed(2)}</span>
                        </div>

                      </div>
                    </>
                  )}

                  {countdown && (
                    <div className="countdown">
                      {countdown}
                    </div>
                  )}
                </div>
              </>
            )}

            {!volBundleMode && (
              <>
                {/* Button */}
                <button onClick={volume_click} className="volume-button" disabled={loadingVolume}>
                  {loadingVolume && (
                    <div className="loadingVolume-icon">  
                      <img src="/loading.svg" alt="loading"/>
                    </div>
                  )}
                  <div className="volume-button-info-container">
                    <img src="/VIEW_IN_AR.svg" alt="VIEW_IN_AR" className="icon"/>
                    <span className="text">Get Volume</span>
                  </div>
                </button>

                {/* Menu Select Object */}
                <div className="object-selection-menu">
                  <div className="background"></div>

                  <div className="object-list">
                    {objectList.map((obj) => (
                      <span
                        key={obj}
                        className={`object-item ${selectedObject === obj ? "selected" : ""}`}
                        onClick={() => {
                          setSelectedObject(prev => {
                            const isSame = prev === obj;

                            if (isSame) {
                              setVolInfo(null);
                              return "";
                            }

                            return obj;
                          });
                        }}
                      >
                        <span className="arrow">
                          {selectedObject === obj ? "▶" : ""}
                        </span>
                        <span className="object-name">Object {obj}</span>
                      </span>
                    ))}
                  </div>

                  <div className="object-total">
                    {multipleVolumeData ? (
                      <> 
                        <div>TOTAL:</div>
                        <div className="total-value">
                          {multipleVolumeData?.Total?.volume_m ?? 0} m³
                        </div>
                      </>
                    ) : null}
                  </div>

                  {countdown && (
                    <div className="countdown">
                      {countdown}
                    </div>
                  )}

                </div>

                {/* Info Objects */}
                <div className="boxInfo-container">
                  <div className="background"></div>
                  
                  {volInfo && selectedObject &&(
                    <>
                      <canvas ref={canvasRef} className="volume-canvas"/>
                      <div className="boxInfoText-container">
                        <div style={{ color: "#6CD08A" }} className="boxInfo-text">
                          <span className="label">Width (cm):</span>
                          <span className="value">{(volumeMode === "real" ? volInfo.width?.[0] : volInfo.width).toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#C66D6D" }} className="boxInfo-text">
                          <span className="label">Length (cm):</span>
                          <span className="value">{(volumeMode === "real" ? volInfo.length?.[0] : volInfo.length).toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#9EB0FD" }} className="boxInfo-text">
                          <span className="label">Height (cm):</span>
                          <span className="value">{(volumeMode === "real" ? volInfo.height?.[0] : volInfo.height).toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="boxInfo-text">
                          <span className="label">Volume (m³):</span>
                          <span className="value">{volInfo.volume_m.toFixed(6)}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="boxInfo-text">
                          <span className="label">Volume (cm³):</span>
                          <span className="value">{volInfo.volume_cm.toFixed(2)}</span>
                        </div>

                      </div>
                    </>
                  )}

                  {!volInfo && !loadingVolume &&(
                    <>
                      <div className="boxInfo-message">Selecione um objeto</div>
                    </>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Powered By */}
          <div className="powered-by-panel">
            <div className="powered-by-text" translate="no">Powered by</div>
            <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo"/>
          </div>
        </div>
      )}

      {/* Calibration Panel */}
      {currentMenu === "calibration-menu" && (
        <div>
          {/* Logo */}
          <button className="logo">
            <img src="/Qubic.svg" alt="BM Logo" />
          </button>

          {/* Menu */}
          <button className="menu-img" onClick={toggleMenu}>
            <img src="/menu-closed.svg" alt="Menu" />
          </button>

          {/* Warning */}
          <div className="warning">
            {error.map((err, i) => (
              <p key={i}>{err}</p>
            ))}
          </div>

          <div
            id="caliErrorLabel"
            className="warning"
            style={{ marginTop: "1.4vh" }}
          ></div>

          <div className="menu-wrapper">
            {/* Menu Title */}
            <div className="title-container">
              <div className="menu-title"> Calibration </div>
              <div className="menu-info"> Calibrates the workspace based on the detected area </div>
            </div>

            {/* Video */}
            <div className="calibration-colorToDepthimg-wrapper">
              <img
                ref={calibrationImage}
                className="calibration-colorToDepthimg"
                data-manual={calibrationMode === "manual"}
                alt="Workspace Detected"
                draggable={false}
              />
            </div>

            {/* Calibration Info*/}
            <div className="calibrationInfo-container">
              <div className="background"></div>
              <div className="calibration-instructions">
                <span className="bold">To perform the calibration:</span>
                <span className="regular">
                  1 - In the "Select Color" button, select the color in the camera image that corresponds to the platform's boundary tape.
                </span>

                <span className="regular">
                  2 - If necessary, manually adjust the points calculated in the previous step.
                </span>
              </div>
              <div className="btn-group">
                <button className={`btn-mode ${calibrationMode === "auto" ? "active" : ""}`}
                  onClick={() => handleCalibrationModeChange(false)}
                >
                  <div className="color-swatch" style={{ backgroundColor: `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})` }} />
                  <div className="btn-content">
                    <img src="/picker.svg" alt="Picker" className="icon" />
                    <span className="text">Select Color</span>
                  </div>
                </button>

                <button
                  className={`btn-mode ${calibrationMode === "manual" ? "active" : ""}`}
                  onClick={() => handleCalibrationModeChange(true)}
                >
                  <div className="btn-content">
                    <img src="/activity_zone.svg" alt="ACTIVITY_ZONE" className="icon" />
                    <span className="text">Adjust</span>
                  </div>
                </button>
              </div>

              {/* Button */}
              <button onClick={startCalibration} className="calibration-button" disabled={loadingCalibration}>
                {loadingCalibration && (
                  <div className="loadingCalibration-icon">  
                    <img src="/loading.svg" alt="loading"/>
                  </div>
                )}
                <div className="calibration-button-info-container">
                  <img src="/filter_zone.svg" alt="FILTER_ZONE" className="icon"/>
                  <span className="text">Calibrate</span>
                </div>
              </button>              
            </div>
          </div>

          {/* Modal */}
          {calibrationModalOpen && (
            <div className="calibration-modal">
              <div className="background"></div>
              <div className="calibration-modal-content">
                <p>Do you want to confirm the changes?</p>

                <div className="calibration-modal-buttons">
                  <button onClick={() => confirm_calibration(true)}>
                    Yes
                  </button>

                  <button onClick={() => confirm_calibration(false)}>
                    No
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Powered By */}
          <div className="powered-by-panel">
            <div className="powered-by-text" translate="no">Powered by</div>
            <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo"/>
          </div>

        </div>
      )}

      {/* Settings PopUp */}
      {showSettingsPopup && (
        <>
          {/* Fundo Escuro */}
          <div className="popup-overlay" onClick={() => setShowSettingsPopup(false)}/>

          {/* PopUp */}
          <div className="settings-popup">
            <span className="text">Configurations</span>
            <div className="settings-buttons-container">
              {/* Exposition */}
              <span className="text">Exposition Type</span>
              <div className="radio-group">
                <label className="radio-option">
                  <input type="radio" name="abertura" value="true" checked={ExpHDR_toggle} onChange={handleExpHDR_toggle}/>
                  <span className="label">HDR</span>
                </label>

                <label className="radio-option">
                  <input type="radio" name="abertura" value="false" checked={!ExpHDR_toggle} onChange={handleExpHDR_toggle}/>
                  <span className="label">Exposure Time</span>
                </label>

                {!ExpHDR_toggle && (
                    <div className="exposure-controls">
                      <input
                        type="number"
                        className="exposure-input"
                        value={exposureTime}
                        onChange={(e) => setExposureTime(e.target.value)}
                      />

                      <button className="exposure-btn" onClick={exposureSet_click}>
                        <span className="text">Set</span>
                      </button>
                    </div>
                  )}
              </div>

              {/* Volume Mode */}
              <span className="text">Volume Mode</span>
              <div className="radio-group">
                <label className="radio-option">
                  <input type="radio" name="volumeMode" value="single_bundle" checked={volumeMode === "single_bundle"} onChange={handleVolumeMode}/>
                  <span className="label">Single Bundle</span>
                </label>

                <label className="radio-option">
                  <input type="radio" name="volumeMode" value="multi_bundle" checked={volumeMode === "multi_bundle"} onChange={handleVolumeMode}/>
                  <span className="label">Multi Bundle</span>
                </label>

                <label className="radio-option">
                  <input type="radio" name="volumeMode" value="real" checked={volumeMode === "real"} onChange={handleVolumeMode}/>
                  <span className="label">Real</span>
                </label>

                {/*<label className="radio-option">
                  <input type="radio" name="volumeMode" value="individual" checked={volumeMode === "individual"} onChange={handleVolumeMode}/>
                  <span className="label">Individual</span>
                </label>*/}
              </div>

              {/* Countdown Value */}
              <span className="text">Countdown Timer</span>
              <div className="countdown-controls">
                <input
                  type="number"
                  className="countdown-input"
                  value={countdownTimer}
                  onChange={(e) => setCountdownTimer(e.target.value)}
                />

                <button className="countdown-btn" onClick={countdownTimerSet_click}>
                  <span className="text">Set</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* User PopUp */}
      {showUserPopup && (
        <>
          {/* Fundo Escuro */}
          <div className="popup-overlay" onClick={() => setShowUserPopup(false)}/>

          {/* PopUp */}
          <div className="user-popup">
            <div className="user-info-container">
              <div className="user-row">
                <img src="/user.svg" className="user-icon"/>

                <div className="user-texts">
                  <span className="text-user"> User: {savedUser?.username} </span>
                  <span className="text-role"> Role: {savedUser?.role} </span>
                </div>
              </div>
            </div>

            <div className="logout-option" onClick={logout}>
              Logout
            </div>
          </div>
            
        </>
      )}

      {/* Configuration Panel */}
      {/*{currentMenu === "config-menu" && (
        <div>
          <div
            className="switch-row"
            style={{ position: "absolute", top: "47vh", left: "10vw" }}
          >
            <span>Static</span>

            <label className="switch">
              <input
                type="checkbox"
                checked={StaticDynamic_toggle}
                onChange={handleStaticDynamic_toggle}
              />
              <span className="slider round"></span>
            </label>

            <span>Dynamic</span>
          </div>

          <span
            style={{
              fontSize: "1vw",
              position: "absolute",
              top: "63vh",
              left: "10.5vw"
            }}
          >
            Debug Mode
          </span>

          <div
            className="switch-row"
            style={{ position: "absolute", top: "66vh", left: "10vw" }}
          >
            <span>On</span>

            <label className="switch">
              <input
                type="checkbox"
                checked={DebugMode_toggle}
                onChange={handleDebugMode_toggle}
              />
              <span className="slider round"></span>
            </label>

            <span>Off</span>
          </div>

          <div
            className="input-box"
            style={{ position: "absolute", top: "29vh", left: "52vw" }}
          >
            <label>Exposure Time:</label>
            <input
              type="text"
              value={exposureTime}
              onChange={(e) => setExposureTime(e.target.value)}
            />
            <button onClick={exposureSet_click}>Set</button>
          </div>

          <div
            className="input-box"
            style={{ position: "absolute", top: "34vh", left: "52vw" }}
          >
            <label>Color Slope:</label>
            <input
              type="text"
              value={colorSlope}
              onChange={(e) => setColorSlope(e.target.value)}
            />
            <button onClick={colorSlopeSet_click}>Set</button>
          </div>
          <div className="powered-by-panel">
            <div className="powered-by-text" translate="no">Powered by</div>
            <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo"/>
          </div>

        </div>
      )}*/}
    </>
  )
}

export default App