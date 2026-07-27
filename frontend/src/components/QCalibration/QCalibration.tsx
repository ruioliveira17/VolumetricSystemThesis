import { RefObject } from "react";
import "./QCalibration.css";

interface Message {
  type: string;
  text: string;
}

interface Rgb {
  r: number;
  g: number;
  b: number;
}

interface QCalibrationProps {
  message: Message[];

  toggleMenu: () => void;

  calibrationImage: RefObject<HTMLImageElement | null>;
  workspaceCanvas: RefObject<HTMLCanvasElement | null>;

  calibrationMode: string;
  rgb: Rgb;

  loadingCalibration: boolean;
  calibrationModalOpen: boolean;

  handleCalibrationModeChange: (manual: boolean) => void;
  calibrate_click: () => void;
  confirm_calibration: (confirm: boolean) => void;
}

function QCalibration({
  message,
  toggleMenu,
  calibrationImage,
  workspaceCanvas,
  calibrationMode,
  rgb,
  loadingCalibration,
  calibrationModalOpen,
  handleCalibrationModeChange,
  calibrate_click,
  confirm_calibration
}: QCalibrationProps) {

  return (
    <div>
      {/* Logo */}
      <div className="logo">
        <img src="/Qubic.svg" alt="BM Logo" />
      </div>

      {/* Menu */}
      <button className="menu-img" onClick={toggleMenu}>
        <img src="/menu-closed.svg" alt="Menu" />
      </button>

      {/* Warning */}
      <div className="warning">
        {message.map((msg, i) => (
          <p
            key={i}
            className={msg.type === "error" ? "error-message" : "info-message"}
          >
            {msg.text}
          </p>
        ))}
      </div>

      <div id="caliErrorLabel" className="warning" style={{ marginTop: "1.4vh" }}></div>

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

          {calibrationMode === "manual" && (
            <canvas ref={workspaceCanvas} className="workspace-overlay" />
          )}
        </div>

        {/* Calibration Info*/}
        <div className="calibrationInfo-container">
          <div className="background"></div>
          <div className="calibration-instructions">
            <span className="bold">Steps to perform the calibration:</span>
            <span className="regular">
              1 - In the "Select Color" mode, select the color in the camera image that corresponds to the platform's color.
            </span>

            <span className="regular">
              2 - If necessary, the "Adjust" mode grants you the option to manually adjust the points given in the previous step.
            </span>
          </div>
          <div className="btn-group">
            <button
              className={`btn-mode ${calibrationMode === "auto" ? "active" : ""}`}
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
          <button onClick={calibrate_click} className="calibration-button" disabled={loadingCalibration}>
            {loadingCalibration && (
              <div className="loadingCalibration-icon">
                <img src="/loading.svg" alt="loading" />
              </div>
            )}
            <div className="calibration-button-info-container">
              <img src="/filter_zone.svg" alt="FILTER_ZONE" className="icon" />
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
              <button onClick={() => confirm_calibration(true)}>Yes</button>
              <button onClick={() => confirm_calibration(false)}>No</button>
            </div>
          </div>
        </div>
      )}

      {/* Powered By */}
      <div className="powered-by-panel">
        <div className="powered-by-text" translate="no">Powered by</div>
        <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo" />
      </div>
    </div>
  );
}

export default QCalibration;
