import React from "react";
import { type CSSProperties } from 'react';
import "./QSettings.css";
import { QConfirmationModal } from "../QConfirmationModal"

import CloseIcon from '@assets/icons/close.svg?react';
import PopupConnection from '@assets/icons/popup_connection.svg?react';
import PowerOff from '@assets/icons/power.svg?react';

import Qselect from "../Qselect"

import {apiFetch} from "../../api/client"

interface LanguageOption {
    label: string;
    flag: string;
}

interface QSettingsProps {
  t: (key: string) => string;

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

  language: string;
  supportedLanguages: string[];
  changeLanguage: (newLanguage: string) => Promise<void>;

  // Crop ("Define")
  currentMenu: string;
  setShowCropWindow: React.Dispatch<React.SetStateAction<boolean>>;
}

function QSettings({
  t,
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
  language,
  supportedLanguages,
  changeLanguage,
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

  const languageOptions = {
    en: {
      label: "English",
      flag: "🇬🇧",
    },
    pt: {
      label: "Português",
      flag: "🇵🇹",
    },
    es: {
      label: "Español",
      flag: "🇪🇸",
    },
    fr: {
      label: "Français",
      flag: "🇫🇷",
    },
  };

  const availableLanguages = supportedLanguages.map((code) => ({
    value: code,
    ...languageOptions[code],
  }));

  const [powerModalOpen, setPowerModalOpen] = React.useState(false);
  const [confirmModalOpen, setConfirmModalOpen] = React.useState(false);
  const [powerAction, setPowerAction] = React.useState<"shutdown" | "restart" | null>(null);

  const handlePowerAction = (action: "shutdown" | "restart") => {
    setPowerModalOpen(false);
    setPowerAction(action);
    setConfirmModalOpen(true);
  };

  const handleConfirmAction = async (action: "shutdown" | "restart") => {
    setConfirmModalOpen(false);

    try {
      if (action === "shutdown") {
        await apiFetch("/system/shutdown", {
          method: "POST",
        });
      } else if (action === "restart") {
        await apiFetch("/system/restart", {
          method: "POST",
        });
      }
    } catch (error) {
      console.error(`Failed to ${action} system:`, error);
    }
  };

  return (
    <>
      {/* Fundo Escuro */}
      <div className="popup-overlay" />

      {/* PopUp */}
      <div className="settings-popup-connection" style={connectionStyle}>
        <PopupConnection />
      </div>
      <div className="settings-popup" style={popupStyle}>
        <span className="text">{t("settings.title")}</span>
        <div className="close-button">
          <CloseIcon onClick={() => setShowSettingsPopup(false)}/>
        </div>
        <div className="settings-buttons-container">
          <span className="text">{t("settings.language")}</span>
          <div className="language-select">
            <Qselect
              label="Language"
              value={language}
              options={availableLanguages}
              onChange={(value) => changeLanguage(value)}
            />
          </div>
          
          {/* Exposition */}
          <span className="text">{t("settings.exposureType")}</span>
          <div className="radio-group">
            <label className="radio-option">
              <input type="radio" name="abertura" value="true" checked={expHDR} onChange={handleExpHDR_toggle} disabled={cameraStatus !== "online"} />
              <span className="label">HDR</span>
            </label>

            <label className="radio-option">
              <input type="radio" name="abertura" value="false" checked={!expHDR} onChange={handleExpHDR_toggle} disabled={cameraStatus !== "online"} />
              <span className="label">{t("settings.exposureTime")}</span>
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
          <span className="text">{t("settings.volumeMode")}</span>
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
          <span className="text">{t("settings.countdownTimer")}</span>
          <div className="countdown-controls">
            <input
              type="number"
              className="countdown-input"
              value={countdownTimer}
              onChange={(e) => setCountdownTimer(e.target.value)}
            />

            <button className="countdown-btn" onClick={countdownTimerSet_click}>
              <span className="set-text">{t("settings.set")}</span>
            </button>
          </div>

          <span className="text">{t("settings.preferences")}</span>
          <div className="image-crop-preference">
            <span className="video-size">{t("settings.videoSize")}</span>
            <button onClick={() => setShowCropWindow(true)} disabled={currentMenu !== "volume-menu" || cameraStatus !== "online"} className="define-button">
              <span className="define_text">{t("settings.set")}</span>
            </button>
          </div>

          <div className="poweroff-button" onClick={() => setPowerModalOpen(true)}>
            <div  className="poweroff-icon">
              <PowerOff/>
            </div>
          </div>
        </div>
      </div>

      {powerModalOpen}{
        <QConfirmationModal
          open={powerModalOpen}
          onClose={() =>  handlePowerAction("shutdown")}
          onConfirm={() => handlePowerAction("restart")}
          title={t("power.title")}
          subtitle={t("power.subtitle")}
          confirmText={t("power.restart")}
          cancelText={t("power.shutdown")}
        />
      }

      {confirmModalOpen && powerAction && (
        <QConfirmationModal
          open={confirmModalOpen}
          onClose={() => setConfirmModalOpen(false)}
          onConfirm={() => handleConfirmAction(powerAction)}
          title={t("power.title")}
          subtitle={
            powerAction === "shutdown"
              ? t("power.confirmShutdown")
              : t("power.confirmRestart")
          }
          confirmText={t("power.yes")}
          cancelText={t("power.no")}
        />
      )}

    </>
  );
}

export default QSettings;
