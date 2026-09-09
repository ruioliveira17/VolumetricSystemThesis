import { RefObject } from "react";
import "./QCalibration.css";
import { QConfirmationModal } from "../QConfirmationModal"
import WarningIcon from '@assets/icons/warning.svg?react';

import QBackgroundBranding from "../QBackgroundBranding";

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
  portalContainer?: Element | null;
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
  confirm_calibration,
  portalContainer,
}: QCalibrationProps) {

  return (
    <div>
      <QBackgroundBranding />
     
      {/* Menu */}
      <div className="menu-wrapper">
        <div className="title-container">
          <div className="menu-title"> Calibration </div>
          <div className="menu-info"> Calibrates the workspace based on the detected area </div>
        </div>

        <div className="caliMenu-container">
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

            {loadingCalibration && (
              <div className="loadingCalibration-icon">
                <img src="/loading.svg" alt="loading" />
              </div>
            )}

            {message.length > 0 && message[0].type === "error" && (
              <div className="error-modal">
                  <div className="background"></div>
                  <div className="icon">
                      <WarningIcon />
                  </div>
                  <div className="text">
                      {message
                        .filter(msg => msg.type === "error")
                        .map((msg, index) => (
                            <span key={index}>{msg.text}</span>
                        ))}
                  </div>
              </div>
            )}

            {/* Button */}
            <button onClick={calibrate_click} className="calibration-button" disabled={loadingCalibration}>
              <div className="calibration-button-info-container">
                <img src="/filter_zone.svg" alt="FILTER_ZONE" className="icon" />
                <span className="text">Calibrate</span>
              </div>
            </button>
          </div>

          {/* Video */}
          <div className="calibration-colorToDepthimg-container">
            <div className="background"></div>

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
          </div>

        </div>
      </div>

      {/* Modal */}
      {calibrationModalOpen && (
        <QConfirmationModal
          open={calibrationModalOpen}
          onClose={() => confirm_calibration(false)}
          onConfirm={() => confirm_calibration(true)}
          title="Confirm Calibration"
          subtitle="Do you want to confirm the changes?"
          confirmText="Yes"
          cancelText="No"
          container={portalContainer}
        />
      )}
    </div>
  );
}

export default QCalibration;
