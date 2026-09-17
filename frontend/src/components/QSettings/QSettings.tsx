import React from "react";
import { type CSSProperties } from 'react';
import "./QSettings.css";
import CloseIcon from '@assets/icons/close.svg?react';
import PopupConnection from '@assets/icons/popup_connection.svg?react';

interface QSettingsProps {
  settingsAnchorRect: DOMRect | null;

  setShowSettingsPopup: React.Dispatch<React.SetStateAction<boolean>>;

  cameraStatus: string;
  // Exposition
  expHDR: boolean;
  handleExpHDR_toggle: (e: React.ChangeEvent<HTMLInputElement>) => void;
  exposureTime: string;
  setExposureTime: React.Dispatch<React.SetStateAction<string>>;
  exposureSet_click: () => void;

  // Volume mode
  volumeMode: string;
  handleVolumeMode: (e: React.ChangeEvent<HTMLInputElement>) => void;

  // Countdown
  countdownTimer: string;
  setCountdownTimer: React.Dispatch<React.SetStateAction<string>>;
  countdownTimerSet_click: () => void;

  // Crop ("Define")
  currentMenu: string;
  setShowCropWindow: React.Dispatch<React.SetStateAction<boolean>>;
}

function QSettings({
  settingsAnchorRect,
  setShowSettingsPopup,
  cameraStatus,
  expHDR,
  handleExpHDR_toggle,
  exposureTime,
  setExposureTime,
  exposureSet_click,
  volumeMode,
  handleVolumeMode,
  countdownTimer,
  setCountdownTimer,
  countdownTimerSet_click,
  currentMenu,
  setShowCropWindow
}: QSettingsProps) {
  const popupStyle: CSSProperties = settingsAnchorRect
    ? {
        position: 'absolute',
        top: settingsAnchorRect.bottom + 35,
        left: settingsAnchorRect.left + settingsAnchorRect.width / 2,
        transform: 'translate(-85%, 0)',
      }
    : {};

  const connectionStyle: CSSProperties = settingsAnchorRect
    ? {
        position: 'absolute',
        top: settingsAnchorRect.bottom + 10,
        left: settingsAnchorRect.left + settingsAnchorRect.width / 2,
        transform: 'translate(-50%, 0)',
      }
    : {};

  return (
    <>
      {/* Fundo Escuro */}
      <div className="popup-overlay" />

      {/* PopUp */}
      <div className="settings-popup-connection" style={connectionStyle}>
        <PopupConnection />
      </div>
      <div className="settings-popup" style={popupStyle}>
        <span className="text">Settings</span>
        <div className="close-button">
          <CloseIcon onClick={() => setShowSettingsPopup(false)}/>
        </div>
        <div className="settings-buttons-container">
          {/* Exposition */}
          <span className="text">Exposition Type</span>
          <div className="radio-group">
            <label className="radio-option">
              <input type="radio" name="abertura" value="true" checked={expHDR} onChange={handleExpHDR_toggle} disabled={cameraStatus !== "online"} />
              <span className="label">HDR</span>
            </label>

            <label className="radio-option">
              <input type="radio" name="abertura" value="false" checked={!expHDR} onChange={handleExpHDR_toggle} disabled={cameraStatus !== "online"} />
              <span className="label">Exposure Time</span>
            </label>

            {!expHDR && (
              <div className="exposure-controls">
                <input
                  type="number"
                  className="exposure-input"
                  value={exposureTime}
                  onChange={(e) => setExposureTime(e.target.value)}
                  disabled={cameraStatus !== "online"}
                />

                <button className="exposure-btn" onClick={exposureSet_click} disabled={cameraStatus !== "online"}>
                  <span className="text">Set</span>
                </button>
              </div>
            )}
          </div>

          {/* Volume Mode */}
          <span className="text">Volume Mode</span>
          <div className="radio-group">
            <label className="radio-option">
              <input type="radio" name="volumeMode" value="single_bundle" checked={volumeMode === "single_bundle"} onChange={handleVolumeMode} />
              <span className="label">Single Bundle</span>
            </label>

            <label className="radio-option">
              <input type="radio" name="volumeMode" value="multi_bundle" checked={volumeMode === "multi_bundle"} onChange={handleVolumeMode} />
              <span className="label">Multi Bundle</span>
            </label>

            <label className="radio-option">
              <input type="radio" name="volumeMode" value="real" checked={volumeMode === "real"} onChange={handleVolumeMode} />
              <span className="label">Real</span>
            </label>

            {/* NOTE (port): o modo "Individual" estava comentado no App.py. */}
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

          <span className="text">Preferences</span>
          <div className="image-crop-preference">
            <span className="video-size"> Video Size </span>
            <button onClick={() => setShowCropWindow(true)} disabled={currentMenu !== "volume-menu" || cameraStatus !== "online"} className="define-button">
              <span className="define_text"> Define </span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default QSettings;
