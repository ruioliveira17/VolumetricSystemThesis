import React from "react";
import { type CSSProperties } from 'react';
import "./QNotifications.css";
import { QConfirmationModal } from "../QConfirmationModal"

import CloseIcon from '@assets/icons/close.svg?react';
import PopupConnection from '@assets/icons/popup_connection.svg?react';
import SystemUpdateIcon from '@assets/icons/systemUpdate.svg?react';

interface ReleaseInfo {
  version: string | null;
  mandatory: boolean;
  patchNotes: Record<string, unknown>;
}

interface QNotificationsProps {
  t: (key: string) => string;

  notificationsAnchorRect: DOMRect | null;

  setShowNotificationsPopup: React.Dispatch<React.SetStateAction<boolean>>;


  language: string;

  newUpdateAvailable: boolean;
  releaseInfo: ReleaseInfo | null;
  setUpdating: React.Dispatch<React.SetStateAction<boolean>>;
  setIsUpdateInitiator: React.Dispatch<React.SetStateAction<boolean>>;

  portalContainer?: Element | null;
}

function QNotifications({
  t,
  notificationsAnchorRect,
  setShowNotificationsPopup,
  language,
  newUpdateAvailable,
  releaseInfo,
  setUpdating,
  setIsUpdateInitiator,
  portalContainer,
}: QNotificationsProps) {
  const popupStyle: CSSProperties = notificationsAnchorRect
    ? {
        position: 'absolute',
        top: notificationsAnchorRect.bottom + 35,
        left: notificationsAnchorRect.left + notificationsAnchorRect.width / 2,
        transform: 'translate(-85%, 0)',
      }
    : {};

  const connectionStyle: CSSProperties = notificationsAnchorRect
    ? {
        position: 'absolute',
        top: notificationsAnchorRect.bottom + 10,
        left: notificationsAnchorRect.left + notificationsAnchorRect.width / 2,
        transform: 'translate(-50%, 0)',
      }
    : {};

  const [confirmUpdate, setConfirmUpdate] = React.useState(false);

  const [patchNotesOpen, setPatchNotesOpen] = React.useState(false);

  const getPatchNotes = (): string[] => {
    const notes =
      releaseInfo?.patchNotes?.[language] ??
      releaseInfo?.patchNotes?.en ??
      releaseInfo?.patchNotes;

    if (Array.isArray(notes)) return notes.map(String);
    if (typeof notes === "string" && notes.trim()) return [notes];
    return [];
  };

  return (
    <>
      {/* Fundo Escuro */}
      <div className="popup-overlay" />

      {/* PopUp */}
      <div className="notifications-popup-connection" style={connectionStyle}>
        <PopupConnection />
      </div>
      <div className="notifications-popup" style={popupStyle}>
        <span className="text">{t("notifications.title")}</span>
        <div className="close-button" onClick={() => setShowNotificationsPopup(false)}>
          <div  className="close-icon">
            <CloseIcon/>
          </div>
        </div>

        <div className="notifications-buttons-container">
          <div className="version-update">
            {newUpdateAvailable && (
              <div className="update-modal">
                <div className="background"></div>
                <div className="update-info">
                  <span className="newUpdate-text">{t("update.newUpdateAvailable")}{releaseInfo?.version ? ` (${releaseInfo.version})` : ""}</span>
                  <span className="about-update" onClick={() => setPatchNotesOpen(true)}>{t("update.about")}</span>
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

        </div>
      </div>


      {patchNotesOpen && (
        <div
          className="patch-notes-overlay"
        >
          <div
            className="patch-notes-modal"
          >
            <div className="close-button" onClick={() => setPatchNotesOpen(false)}>
              <div className="close-icon">
                <CloseIcon />
              </div>
            </div>

            <span className="patch-notes-title">
              {t("update.patchNotes")}
              {releaseInfo?.version ? ` (${releaseInfo.version})` : ""}
            </span>

            <div className="patch-notes-body">
              {getPatchNotes().length > 0 ? (
                getPatchNotes().map((note, i) => (
                  <p key={i}>{note}</p>
                ))
              ) : (
                <p>-</p>
              )}
            </div>
          </div>
        </div>
      )}

      {confirmUpdate && (
        <QConfirmationModal
          open={confirmUpdate}
          onClose={() => setConfirmUpdate(false)}
          onConfirm={() => {
            setUpdating(true);
            setIsUpdateInitiator(true);
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

export default QNotifications;
