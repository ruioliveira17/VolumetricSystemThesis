import { useEffect, useRef, useState } from 'react';
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

function App() {
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

  const [currentMenu, setCurrentMenu] = useState("login");

  const [calibrationPending, setCalibrationPending] = useState(false);
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

  const [ExpHDR_toggle, setExpHDR] = useState(false);
  const [BundleReal_toggle, setBundleReal] = useState(false);
  const [StaticDynamic_toggle, setStaticDynamic] = useState(false);
  const [DebugMode_toggle, setDebugMode] = useState(false);

  const [menuSideNav, setMenuSideNavOpen] = useState(false);
  const toggleMenu = () => setMenuSideNavOpen(prev => !prev);

  const [userSideNav, setUserSideNavOpen] = useState(false);
  const toggleUserMenu = () => setUserSideNavOpen(prev => !prev);

  const [volInfo, setVolInfo] = useState(null);
  const [objectImage, setObjectImage] = useState(null);

  const [objectList, setObjectList] = useState([]);
  const [selectedObject, setSelectedObject] = useState("");
  const [realVolumeData, setVolumeData] = useState(null);

  const [savedUser, setSavedUser] = useState(null);

  const [exposureTime, setExposureTime] = useState("");
  const [colorSlope, setColorSlope] = useState("");

  const pc = useRef(null);
  const cameraVideo = useRef(null);

  const isAuthScreen = currentMenu === "login" || currentMenu === "register";

  const [rgb, setRgb] = useState({ r: 0, g: 0, b: 0 });

  const [calibrationModalOpen, setCalibrationModalOpen] = useState(false);
  const [loadingVolume, setLoadingVolume] = useState(false);
  const [loadingCalibration, setLoadingCalibration] = useState(false);

  const canvasRef = useRef(null);
  const angleRef = useRef(0.4);
  const dragging = useRef(false);
  const lastX = useRef(0);

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("current_user"));

    if (user) {
      setSavedUser(user);
      setCurrentMenu("volume-menu");
    }
  }, []);

  function showLoginScreen() {
      setCurrentMenu("login");

      setError([TextClear]);
      setRegUsername("");
      setRegPassword("");
      setRegRole("user");
      setRegCode("");
  }

  async function login() {
    if (!username || !password) {
      setError([TextFillAllFields]);
      return;
    }

    try {
      const response = await fetch("http://10.0.30.175:8000/login", {
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

        setCurrentMenu("volume-menu");

        setError([TextClear]);

      } else {
        const data = await response.json();
        setError([data.detail]);
      }

    } catch (error) {
      setError([TextServerConnection]);
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
          const response = await fetch('http://10.0.30.175:8000/register', {
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
    setUserSideNavOpen(false)

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
      if (cameraVideo.current) {
        cameraVideo.current.src = "http://10.0.30.175:8000/calibrationCTD";
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
        setLoadingVolume(true);
        setObjectImage(null);
        refreshAccessToken();
        const access_token = localStorage.getItem("access_token");

        const response = await fetch("http://10.0.30.175:8000/volume/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
        let volumeMode = await response.json();
        if (volumeMode["Volume Mode"] === "Bundle"){
            volumeBundle(access_token);
        } else if (volumeMode["Volume Mode"] === "Real"){
            volumeReal(access_token);
        }

      } catch (error) {
        console.warn(error);
      }
  }

  async function volumeBundle(access_token) {
    try {
      setObjectList([]);
      setSelectedObject("");
      setVolInfo(null);
      setVolumeData(null);

      await fetch('http://10.0.30.175:8000/volume/bundle', { method: 'POST', headers: { "Authorization": `Bearer ${access_token}` } });

      const response = await fetch('http://10.0.30.175:8000/getObjectsOutOfLine', {headers: { "Authorization": `Bearer ${access_token}`}});
      const data = await response.json();
      const objectsOutOfLine = data.objects_outOfLine.map((val, i) => val ? i + 1 : null).filter(v => v !== null);
      if (objectsOutOfLine.length > 0) {
          setError([TextOutOfLine]);
      } else {
          setError([TextClear]);

          const dataResponse = await fetch('http://10.0.30.175:8000/volume/bundle/results', {headers: { "Authorization": `Bearer ${access_token}`}});
          const volumeData = await dataResponse.json();

          setVolInfo({
            volume_m: volumeData.Bundle.volume_m,
            volume_cm: volumeData.Bundle.volume_cm,
            width: volumeData.Bundle.x,
            length: volumeData.Bundle.y,
            height: volumeData.Bundle.z
          })
      }

      const imgResp = await fetch("http://10.0.30.175:8000/getFrame/detectedObjectsFrame", {headers: { "Authorization": `Bearer ${access_token}` }});
      if (imgResp.status === 404) throw new Error("Frame not Available");

      const blob = await imgResp.blob();
      const url = URL.createObjectURL(blob);
      setObjectImage(url);
      //document.getElementById("object-img").removeAttribute("hidden");

    } catch (error) {
      setVolInfo(null);
      setVolumeData(null);
      setError([TextError]);
      console.error(error);
    } finally {
      setLoadingVolume(false);
    }
  }

  // Show Volume Depending of the selected object
  useEffect(() => {
    if (!selectedObject || !realVolumeData) return;

    const objData = realVolumeData[selectedObject];
    if (!objData) return;

    setVolInfo({
      volume_m: objData.volume_m,
      volume_cm: objData.volume_cm,
      width: objData.x,
      length: objData.y,
      height: objData.z
    });
  }, [selectedObject, realVolumeData]);

  async function volumeReal(access_token) {
      try {
        setObjectList([]);
        setSelectedObject("");
        setVolInfo(null);
        setVolumeData(null);

        await fetch('http://10.0.30.175:8000/volume/real', { method: 'POST', headers: { "Authorization": `Bearer ${access_token}` } });

        const response = await fetch('http://10.0.30.175:8000/getObjectsOutOfLine', {headers: { "Authorization": `Bearer ${access_token}`}});
        const data = await response.json();
        const objectsOutOfLine = data.objects_outOfLine.map((val, i) => val ? i + 1 : null).filter(v => v !== null);
        if (objectsOutOfLine.length > 0) {
            setError([TextOutOfLine]);
        } else {
            setError([TextClear]);
        }

        const dataResponse = await fetch('http://10.0.30.175:8000/volume/real/results', {headers: { "Authorization": `Bearer ${access_token}`}});
        const volumeData = await dataResponse.json();

        setVolumeData(volumeData);

        const imgResp = await fetch("http://10.0.30.175:8000/getFrame/detectedObjectsFrame", {headers: { "Authorization": `Bearer ${access_token}` }});
        if (imgResp.status === 404) throw new Error("Frame not Available");

        const blob = await imgResp.blob();
        const url = URL.createObjectURL(blob);
        setObjectImage(url);
        //document.getElementById("object-img").removeAttribute("hidden");

        const objIdentified = Object.keys(volumeData).filter(key => key !== "Total");
        
        if (objIdentified.length === 1) {
          const objData = volumeData[objIdentified[0]];
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

useEffect(() => {
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
      ox = nx * 26;
      oy = ny * 20;
    } else if (edgeType === 'length'){
      const ux = dx / len;
      const uy = dy / len;
      let nx = -uy;
      let ny = ux;
      const bias = 1;
      nx *= bias;
      ny *= bias;
      ox = nx * 26;
      oy = ny * 20;
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

    const w = volInfo.width;
    const d = volInfo.length;
    const h = volInfo.height;

    const maxDim = Math.max(w, d, h);

    const nw = w / maxDim;
    const nd = d / maxDim;
    const nh = h / maxDim;

    const scale = Math.min(W, H) * 0.45;

    const hw = nw / 2;
    const hd = nd / 2;
    const hh = nh / 2;

    const cx = W / 2;
    const cy = H / 2;

    const v = [
      project(-hw, -hd, -hh, cx, cy, scale),
      project(hw, -hd, -hh, cx, cy, scale),
      project(hw, hd, -hh, cx, cy, scale),
      project(-hw, hd, -hh, cx, cy, scale),
      project(-hw, -hd, hh, cx, cy, scale),
      project(hw, -hd, hh, cx, cy, scale),
      project(hw, hd, hh, cx, cy, scale),
      project(-hw, hd, hh, cx, cy, scale),
    ];

    const X = "#E24B4A"; // width
    const Y = "#1D9E75"; // length
    const Z = "#378ADD"; // height

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

      if (type == "Width"){
        drawLabel(v[a], v[b], `${value} cm`, color, "width");
      } else if (type == "Length"){
        drawLabel(v[a], v[b], `${value} cm`, color, "length");
      } else if (type == "Height"){
        drawLabel(v[a], v[b], `${value} cm`, color, "height");
      }
    });
  };

  let frameId;

  const animate = () => {
    if (!volInfo) return;

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
}, [volInfo]);
              
  async function handleExpHDR_toggle(e) {
    const checked = e.target.checked;
    setExpHDR(checked);
    
    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");
    
    if (checked) {
        await fetch("http://10.0.30.175:8000/exposition/mode/hdr", { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    } else {
        await fetch("http://10.0.30.175:8000/exposition/mode/fixed", { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    }
  }

  async function handleBundleReal_toggle(e) {
    const checked = e.target.checked;
    setBundleReal(checked);

    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");

    if (checked) {
        await fetch("http://10.0.30.175:8000/volume/mode/real", { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    } else {
        await fetch("http://10.0.30.175:8000/volume/mode/bundle", { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    }
  }

  async function handleStaticDynamic_toggle(e) {
    const checked = e.target.checked;
    setStaticDynamic(checked);
      
    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");

    if (checked) {
        await fetch("http://10.0.30.175:8000/working/mode/dynamic", { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    } else {
        await fetch("http://10.0.30.175:8000/working/mode/static", { method: "POST", headers: { "Authorization": `Bearer ${access_token}`} });
    }
  }

  async function handleDebugMode_toggle(e) {
    const checked = e.target.checked;
    setDebugMode(checked);

    refreshAccessToken();
    const access_token = localStorage.getItem("access_token");

    if (checked) {
        await fetch("http://10.0.30.175:8000/debug/mode/on", { method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });
    } else {
        await fetch("http://10.0.30.175:8000/debug/mode/off", { method: "POST", headers: { "Authorization": `Bearer ${access_token}` } });
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

        await fetch("http://10.0.30.175:8000/update_systemInfo", {
            method: "POST",
            headers: {
                "Content-Type": "application/json", "Authorization": `Bearer ${access_token}`
            },
            body: JSON.stringify({ exposureTime: value })
        });

        setError([TextExposureUpdateSuccessfull]);
    } catch (error) {
        console.error("Exposure set error:", error);
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

        await fetch("http://10.0.30.175:8000/update_systemInfo", {
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
          const r1 = await fetch("http://10.0.30.175:8000/exposition/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
          const expData = await r1.json();

          setExpHDR(expData["Exposition Mode"] === "HDR");

          // VOLUME MODE
          const r2 = await fetch("http://10.0.30.175:8000/volume/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
          const volumeData = await r2.json();

          setBundleReal(volumeData["Volume Mode"] === "Real");

         // MODE (Static / Dynamic)
          const r3 = await fetch("http://10.0.30.175:8000/working/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
          const modeData = await r3.json();

          setStaticDynamic(modeData["Mode"] === "Dynamic");

          // DEBUG MODE
          const r4 = await fetch("http://10.0.30.175:8000/debug/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
          const debugData = await r4.json();

          setDebugMode(debugData["Debug Mode"] === "On");
        }
      } catch (error) {
          console.log("Toggle refresh error:", error);
      }
  }

  async function applyMask(access_token) {
    try {
      const r = await fetch("http://10.0.30.175:8000/mask", {headers: { "Authorization": `Bearer ${access_token}`}});
      const maskValues = await r.json();
      await fetch("http://10.0.30.175:8000/applyMask", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${access_token}` },
          body: JSON.stringify(maskValues)
      });
    } catch (err) { console.warn("Erro applyMask:", err); }
  }

  async function applyManualWSDraw(access_token) {
    try {
      if (selectedPoint.current === null) {
          const r = await fetch("http://10.0.30.175:8000/calibrate/params", { headers: { "Authorization": `Bearer ${access_token}` } });
          detectionArea.current = (await r.json())["Detected Area"];
      }
      await fetch("http://10.0.30.175:8000/applyManualWorkspace", {
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
      const r = await fetch("http://10.0.30.175:8000/calibrate/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
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

    const img = cameraVideo.current;
    if (!img) return;

    const handleClick = async (event) => {
      try {
        const access_token = localStorage.getItem("access_token");

        const calibRes = await fetch(
          "http://10.0.30.175:8000/calibrate/mode",
          { headers: { "Authorization": `Bearer ${access_token}` } }
        );

        const calibData = await calibRes.json();

        const rect = img.getBoundingClientRect();
        const x = Math.round((event.clientX - rect.left) * (img.videoWidth / rect.width));
        const y = Math.round((event.clientY - rect.top) * (img.videoHeight / rect.height));

        if (calibData["Calibrate Mode"] === "Automatic") {

          await fetch(
            "http://10.0.30.175:8000/mask/colorClick",
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

          canvas.width = img.videoWidth;
          canvas.height = img.videoHeight;
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

          const preview = document.getElementById("color-preview");

          const pixel = ctx.getImageData(x, y, 1, 1).data;
          const r_color = pixel[0];
          const g_color = pixel[1];
          const b_color = pixel[2];

          setRgb({
            r: r_color,
            g: g_color,
            b: b_color
          });

          if (preview) {
            preview.style.backgroundColor = `rgb(${r_color}, ${g_color}, ${b_color})`;
          }
        } else if (calibData["Calibrate Mode"] === "Manual") {

          const r = await fetch(
            "http://10.0.30.175:8000/calibrate/params",
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
          const r_mode = await fetch("http://10.0.30.175:8000/calibrate/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
          const calibData = await r_mode.json();

          if (calibData["Calibrate Mode"] !== "Manual") return;

          if (selectedPoint.current === null) return;

          //const r = await fetch("http://10.0.30.175:8000/calibrate/params", {headers: { "Authorization": `Bearer ${access_token}`}});
          //let data = await r.json();
          //let detection_area = data["Detected Area"]; // [x1, y1, x2, y2]

          const img = cameraVideo.current;
          const maxX = img.videoWidth;
          const maxY = img.videoHeight;

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

  function startCalibration(){
    if (calibrationPending === false){
      setCalibrationModalOpen(true);
    } else {
      const img = cameraVideo.current;
      img.dataset.manual = "false";
      setCalibrationPending(false);
      calibrate_click();
    }
  }

  async function setCalibrationMode(Manual){
      refreshAccessToken();
      const access_token = localStorage.getItem("access_token");

      setCalibrationModalOpen(false);

      if (Manual){
        setCalibrationPending(true);
        const img = cameraVideo.current;
        img.dataset.manual = "true";
        await fetch("http://10.0.30.175:8000/calibrate/mode/manual", { method: "POST", headers: { "Authorization": `Bearer ${access_token}` }});
      } else{
        calibrate_click();
      }
  }

  async function calibrate_click() {
    try {
      setLoadingCalibration(true);
      setError([TextClear]);
      refreshAccessToken();
      const access_token = localStorage.getItem("access_token");

      const maskResponse = await fetch("http://10.0.30.175:8000/mask", {headers: { "Authorization": `Bearer ${access_token}`}});
      if (!maskResponse.ok) throw new Error("Mask request failed");
      const maskValues = await maskResponse.json();

      const calibrateResponse = await fetch("http://10.0.30.175:8000/calibrate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json", "Authorization": `Bearer ${access_token}`
        },
        body: JSON.stringify(maskValues)
      });

      if (!calibrateResponse.ok) throw new Error("Calibrate request failed");

      const flagsResponse = await fetch("http://10.0.30.175:8000/calibrate/flags", { headers: { "Authorization": `Bearer ${access_token}` } });
      if (!flagsResponse.ok) throw new Error("Flags request failed");

      const data = await flagsResponse.json();

      const center_aligned = data["Center Aligned"];
      const ws_clear = data["Workspace Clear"];

      if (center_aligned && ws_clear) {
        setError([TextCalibrated, TextClear]);
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

      const r = await fetch("http://10.0.30.175:8000/calibrate/mode", {headers: { "Authorization": `Bearer ${access_token}`}});
      let calibData = await r.json();
      if (calibData["Calibrate Mode"] === "Manual") {
        await fetch("http://10.0.30.175:8000/calibrate/mode/automatic", { method: "POST", headers: { "Authorization": `Bearer ${access_token}` }});
      }

      selectedPoint.current = null;

    } catch (error) {
      setError([TextError]);
      console.error(error);
    } finally {
      setLoadingCalibration(false);
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
          const response = await fetch('http://10.0.30.175:8000/refresh', {
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
    if (currentMenu === "volume-menu") {
      startWebRTC("volume");
    } else if (currentMenu === "calibration-menu") {
      startWebRTC("calibration");
    } else {
      stopWebRTC();
    }
  }, [currentMenu]);

  async function startWebRTC(streamType) {
    const access_token = localStorage.getItem("access_token");

    pc.current = new RTCPeerConnection();

    pc.current.addTransceiver('video', { direction: 'recvonly' });

    pc.current.ontrack = (event) => {
      if (cameraVideo.current) {
        cameraVideo.current.srcObject = event.streams[0];
      }
    };

    const offer = await pc.current.createOffer();
    await pc.current.setLocalDescription(offer);

    const response = await fetch("http://10.0.30.175:8000/offer", {
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
        <div className="nav-item" onClick={() => setCurrentMenu("volume-menu")}>
          Volume
        </div>

        <div className="nav-item" onClick={() => setCurrentMenu("calibration-menu")}>
          Calibration
        </div>

        <div className="nav-item" onClick={() => setCurrentMenu("config-menu")}>
          Configurations
        </div>

        <div className="nav-item">
          About
        </div>
      </div>

      {/* User Side Nav */}
      <div className={`userSideNav ${(!isAuthScreen && userSideNav) ? "open" : ""}`}>
        <div className="navUser-item">
          User: {savedUser?.username}
        </div>

        <div className="navUser-item">
          Role: {savedUser?.role}
        </div>

        <div className="navUser-item" onClick={logout}>
          Logout
        </div>
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
            <img src="/menu.svg" alt="Menu" />
          </button>

          {/* User */}
          <button className="user-img" onClick={toggleUserMenu}>
            <img src="/user.png" alt="User" />
          </button>

          {/* Warning */}
          <div className="warning">
            {error.map((err, i) => (
              <p key={i}>{err}</p>
            ))}
          </div>

          <div className="volume-menu-wrapper">
            {/* Video */}
            <div className="camera-video-wrapper">
              <video
                ref={cameraVideo}
                autoPlay
                playsInline
                className="camera-video"
              />
            </div>

            {/* Button */}
            <button onClick={volume_click} className="volume-button" disabled={loadingVolume}>
              <div className="background"></div>
              {loadingVolume && (
                <div className="loadingVolume-icon">  
                  <img src="/loading.svg" alt="loading"/>
                </div>
              )}
              <span className="text">Get Volume</span>
            </button>

            {/* Menu Select Object */}
            <div className="object-selection-menu">
              <div className="object-list">
                {objectList.map((obj) => (
                  <span
                    key={obj}
                    className={`object-item ${selectedObject === obj ? "selected" : ""}`}
                    onClick={() => setSelectedObject(obj)}
                  >
                    <span className="arrow">
                      {selectedObject === obj ? "▶" : ""}
                    </span>
                    <span className="object-name">{obj}</span>
                  </span>
                ))}
              </div>

              <div className="object-total">
                {realVolumeData ? (
                  <div>
                    TOTAL: {realVolumeData?.Total?.volume_m ?? 0} m³
                  </div>
                  /*<div>
                    {realVolumeData?.Total?.volume_cm ?? 0} cm³
                  </div>*/
                ) : null}
              </div>

            </div>

            {/* Image */}
            {objectImage && (
              <div className="camera-video-wrapper">
                <img className="object-img" src={objectImage} alt="objects"/>
              </div>
            )}

            {/* Info Objects */}
            <div className="boxInfo-container">
              {volInfo && (
                <canvas
                  ref={canvasRef}
                  className="volume-canvas"
                />
              )}
            </div>
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
            <img src="/menu.svg" alt="Menu" />
          </button>

          {/* User */}
          <button className="user-img" onClick={toggleUserMenu}>
            <img src="/user.png" alt="User" />
          </button>

          {/* Menu Title */}
          <div className="title-container">
            <div className="menu-title">Calibration</div>
          </div>

          {/* Avisos */}
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

          {/* Video */}
          <video
            ref={cameraVideo}
            autoPlay
            playsInline
            className="calibration-video"
          />

          {/* Cor */}
          <div className="color-menu">
            <div id="color-preview" className="color-preview"></div>

            <div id="rgb-values" className="rgb-values">
              R: <span>{rgb.r}</span>{" "}
              G: <span>{rgb.g}</span>{" "}
              B: <span>{rgb.b}</span>
            </div>
          </div>

          {/* Button */}
          <button onClick={startCalibration} className="calibration-button" disabled={loadingCalibration}>
            <div className="background"></div>
            {loadingCalibration && (
              <div className="loadingCalibration-icon">  
                <img src="/loading.svg" alt="loading"/>
              </div>
            )}
            <span className="text">Calibrate</span>
          </button>

          {/* Modal */}
          {calibrationModalOpen && (
            <div className="calibration-modal">
              <div className="background"></div>
              <div className="calibration-modal-content">
                <p>Pretende ajustar manualmente?</p>

                <div className="calibration-modal-buttons">
                  <button onClick={() => setCalibrationMode(true)}>
                    Sim
                  </button>

                  <button onClick={() => setCalibrationMode(false)}>
                    Não
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

      {/* Configuration Panel */}
      {currentMenu === "config-menu" && (
        <div>
          {/* Logo */}
          <button className="logo">
            <img src="/Qubic.svg" alt="BM Logo" />
          </button>

          {/* Menu */}
          <button className="menu-img" onClick={toggleMenu}>
            <img src="/menu.svg" alt="Menu" />
          </button>

          {/* User */}
          <button className="user-img" onClick={toggleUserMenu}>
            <img src="/user.png" alt="User" />
          </button>

          {/* Menu Title */}
          <div className="title-container">
            <div className="menu-title">Configurations</div>
          </div>

          {/* Aviso */}
          <div className="warning">
            {error.map((err, i) => (
              <p key={i}>{err}</p>
            ))}
          </div>

          {/* Exposure / HDR Switch */}
          <div
            className="switch-row"
            style={{ position: "absolute", top: "29vh", left: "10vw" }}
          >
            <span>Exposition</span>

            <label className="switch">
              <input
                type="checkbox"
                checked={ExpHDR_toggle}
                onChange={handleExpHDR_toggle}
              />
              <span className="slider round"></span>
            </label>

            <span>HDR</span>
          </div>

          {/* Bundle / Real Switch */}
          <div
            className="switch-row"
            style={{ position: "absolute", top: "38vh", left: "10vw" }}
          >
            <span>Bundle</span>

            <label className="switch">
              <input
                type="checkbox"
                checked={BundleReal_toggle}
                onChange={handleBundleReal_toggle}
              />
              <span className="slider round"></span>
            </label>

            <span>Real Volume</span>
          </div>

          {/* Static / Dynamic Switch */}
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

          {/* Debug Mode Switch */}
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

          {/* Exposure Time Set */}
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

          {/* Color Slope Set */}
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

          {/* Powered By */}
          <div className="powered-by-panel">
            <div className="powered-by-text" translate="no">Powered by</div>
            <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo"/>
          </div>

        </div>
      )}


    </>
  )
}

export default App
