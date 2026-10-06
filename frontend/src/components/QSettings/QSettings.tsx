import React from "react";
import { useEffect, useState } from 'react';
import { type CSSProperties } from 'react';
import "./QSettings.css";
import { QConfirmationModal } from "../QConfirmationModal"
import { QPowerOptionsModal } from "../QPowerOptionsModal"

import CloseIcon from '@assets/icons/close.svg?react';
import PopupConnection from '@assets/icons/popup_connection.svg?react';
import PowerOff from '@assets/icons/power.svg?react';
import SystemUpdateIcon from '@assets/icons/systemUpdate.svg?react';

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

  newUpdateAvailable: boolean;
  setUpdating: React.Dispatch<React.SetStateAction<boolean>>;
  // Crop ("Define")
  currentMenu: string;
  setShowCropWindow: React.Dispatch<React.SetStateAction<boolean>>;

  portalContainer?: Element | null;
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
  newUpdateAvailable,
  setUpdating,
  currentMenu,
  setShowCropWindow,
  portalContainer,
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

  const [confirmUpdate, setConfirmUpdate] = React.useState(false);

  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await apiFetch('/system/version');
        const data = await response.json();

        setVersion(data.version);
      } catch (error) {
        console.error('Failed to get system version:', error);
      }
    };

    fetchVersion();

    const interval = setInterval(fetchVersion, 30_000);

    return () => clearInterval(interval);
  }, []);

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
        <div className="close-button" onClick={() => setShowSettingsPopup(false)}>
          <div  className="close-icon">
            <CloseIcon/>
          </div>
        </div>

        <div className="settings-buttons-container">
          <span className="text">{t("settings.language")}</span>
          <div className="language-select">
            <Qselect
              label={t("settings.language")}
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
          </div>

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
                <span className="set-text">{t("settings.set")}</span>
              </button>
            </div>
          )}

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

          <div className="version-update">
            <span className="version-text">{t("update.version")}: {version}</span>
            {newUpdateAvailable && (
              <div className="update-modal">
                <div className="background"></div>
                <div className="update-info">
                  <span className="newUpdate-text">{t("update.newUpdateAvailable")}</span>
                  <span className="about-update">{t("update.about")}</span>
                </div>
                <button
                  className="update-button"
                  onClick={() => setConfirmUpdate(true)}
                >
                  <span className="update-button-text">
                    {t("update.update")}
                  </span>
                </button>
              </div>
            )}
          </div>

          <div className="poweroff-button">
            <div  className="poweroff-icon" onClick={() => setPowerModalOpen(true)}>
              <PowerOff/>
            </div>
            <span className="poweroff-text">{t("power.title")}</span>
          </div>
        </div>
      </div>

      {powerModalOpen && (
        <QPowerOptionsModal
          open={powerModalOpen}
          onClose={() => setPowerModalOpen(false)}
          title={t('power.title')}
          subtitle={t('power.subtitle')}
          option1Text={t('power.restart')}
          option2Text={t('power.shutdown')}
          onOption1={() => handlePowerAction("restart")}
          onOption2={() =>  handlePowerAction("shutdown")}
          container={portalContainer}
        />
      )}

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
          icon={<PowerOff />}
          iconColor="#ff6666"
          confirmText={t("yes")}
          cancelText={t("no")}
          container={portalContainer}
        />
      )}

      {confirmUpdate && (
        <QConfirmationModal
          open={confirmUpdate}
          onClose={() => setConfirmUpdate(false)}
          onConfirm={() => {
            setUpdating(true);
            setConfirmUpdate(false);
          }}
          title={t("update.title")}
          subtitle={t("update.subtitle")}
          icon={<SystemUpdateIcon />}
          iconColor="#ffcc00"
          confirmText={t("yes")}
          cancelText={t("no")}
          container={portalContainer}
        />
      )}

    </>
  );
}

export default QSettings;
