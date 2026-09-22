import { React, RefObject, useEffect, useRef } from "react";
import "./QCalibration.css";
import { QConfirmationModal } from "../QConfirmationModal"
import WarningIcon from '@assets/icons/warning.svg?react';

import QBackgroundBranding from "../QBackgroundBranding";

type TranslationKey =
    | "settings"
    | "language"
    | "expositionType"
    | "expositionTime"
    | "volumeMode"
    | "countdownTimer"
    | "set"
    | "preferences"
    | "videoSize"
    | "define";

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
  t: (key: TranslationKey) => string;

  message: Message[];

  toggleMenu: () => void;

  cameraStatus: string;
  cameraVideo: RefObject<HTMLVideoElement | null>;
  workspaceCanvas: RefObject<HTMLCanvasElement | null>;

  calibrationMode: string;
  rgb: Rgb;

  loadingCalibration: boolean;
  calibrationModalOpen: boolean;

  selectedPoint: number | null;
  detectionArea: number[][];

  calibrationRender: number;

  handleCalibrationModeChange: (manual: boolean) => void;
  handleColorClick: (event: React.MouseEvent<HTMLVideoElement>) => void;
  calibrate_click: () => void;
  confirm_calibration: (confirm: boolean) => void;
  portalContainer?: Element | null;
}

function QCalibration({
  t,
  message,
  toggleMenu,
  cameraStatus,
  cameraVideo,
  handleColorClick,
  workspaceCanvas,
  calibrationMode,
  rgb,
  loadingCalibration,
  calibrationModalOpen,
  selectedPoint,
  detectionArea,
  calibrationRender,
  handleCalibrationModeChange,
  calibrate_click,
  confirm_calibration,
  portalContainer,
}: QCalibrationProps) {
  const magnifierCanvas = useRef<HTMLCanvasElement | null>(null);

  const selectedPointPosition =
    selectedPoint !== null
      ? detectionArea[selectedPoint]
      : null;

  const canvasWidth = workspaceCanvas.current?.width ?? 0;

  const magnifierSide =
    selectedPointPosition && canvasWidth > 0
      ? selectedPointPosition[0] < canvasWidth / 2
        ? "magnifier-right"
        : "magnifier-left"
      : "";

  useEffect(() => {
    if (calibrationMode !== "manual") return;
    if (selectedPoint === null) return;

    const video = cameraVideo.current;
    const canvas = magnifierCanvas.current;

    if (!video || !canvas) return;

    const ctx = canvas.getContext("2d");

    if (!ctx) return;

    const MAGNIFIER_SIZE = 180;
    const ZOOM = 4;

    canvas.width = MAGNIFIER_SIZE;
    canvas.height = MAGNIFIER_SIZE;

    let animationFrame: number;

    function drawMagnifier() {

        /*
        * Limpar sempre primeiro.
        */
        ctx.clearRect(
            0,
            0,
            MAGNIFIER_SIZE,
            MAGNIFIER_SIZE
        );

        const center = MAGNIFIER_SIZE / 2;

        /*
        * Se o vídeo ainda não estiver disponível,
        * tenta novamente no próximo frame.
        */
        if (
            video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA ||
            video.videoWidth === 0 ||
            video.videoHeight === 0
        ) {
            animationFrame =
                requestAnimationFrame(drawMagnifier);

            return;
        }

        const selected = detectionArea[selectedPoint];

        if (!selected) {
            animationFrame =
                requestAnimationFrame(drawMagnifier);

            return;
        }

        /*
        * detectionArea já está em coordenadas nativas
        * do vídeo.
        */
        const pointX = selected[0];
        const pointY = selected[1];

        /*
        * Área do vídeo original que será ampliada.
        */
        const sourceWidth =
            MAGNIFIER_SIZE / ZOOM;

        const sourceHeight =
            MAGNIFIER_SIZE / ZOOM;

        const sourceX =
            pointX - sourceWidth / 2;

        const sourceY =
            pointY - sourceHeight / 2;

        /*
        * Círculo de clipping da lupa.
        */
        ctx.save();

        ctx.beginPath();

        ctx.arc(
            center,
            center,
            center,
            0,
            Math.PI * 2
        );

        ctx.clip();

        /*
        * Fundo caso parte da região ampliada
        * esteja fora da imagem.
        */
        ctx.fillStyle = "black";

        ctx.fillRect(
            0,
            0,
            MAGNIFIER_SIZE,
            MAGNIFIER_SIZE
        );

        /*
        * Vídeo ampliado.
        */
        ctx.drawImage(
            video,
            sourceX,
            sourceY,
            sourceWidth,
            sourceHeight,
            0,
            0,
            MAGNIFIER_SIZE,
            MAGNIFIER_SIZE
        );

        /*
        * Transformação dos pontos para
        * o sistema de coordenadas da lupa.
        *
        * O ponto selecionado fica exatamente
        * no centro.
        */
        const scale =
            MAGNIFIER_SIZE / sourceWidth;

        const offsetX =
            center - pointX * scale;

        const offsetY =
            center - pointY * scale;

        /*
        * ============================
        * ÁREA DE TRABALHO
        * ============================
        */
        if (detectionArea.length > 0) {

            ctx.beginPath();

            detectionArea.forEach((point, index) => {

                const x =
                    point[0] * scale +
                    offsetX;

                const y =
                    point[1] * scale +
                    offsetY;

                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });

            ctx.closePath();

            ctx.strokeStyle = "blue";
            ctx.lineWidth = 5 * scale;
            ctx.stroke();
        }

        /*
        * ============================
        * PONTOS
        * ============================
        *
        * 1. círculo preto
        * 2. círculo branco/amarelo
        * 3. vídeo ampliado no centro
        */
        detectionArea.forEach((point, index) => {

            const x =
                point[0] * scale +
                offsetX;

            const y =
                point[1] * scale +
                offsetY;

            const radius =
                index === selectedPoint
                    ? 12 * scale
                    : 10 * scale;

            /*
            * ============================
            * CÍRCULO EXTERIOR
            * ============================
            */
            ctx.beginPath();

            ctx.arc(
                x,
                y,
                radius,
                0,
                Math.PI * 2
            );

            ctx.fillStyle = "black";
            ctx.fill();

            /*
            * ============================
            * CÍRCULO INTERIOR
            * ============================
            */
            ctx.beginPath();

            ctx.arc(
                x,
                y,
                radius - (2 * scale),
                0,
                Math.PI * 2
            );

            ctx.fillStyle =
                index === selectedPoint
                    ? "yellow"
                    : "white";

            ctx.fill();

            /*
            * ============================
            * BURACO NO CENTRO
            * ============================
            *
            * Em vez de usar destination-out,
            * voltamos a desenhar o mesmo vídeo
            * ampliado apenas dentro do círculo.
            */
            ctx.save();

            ctx.beginPath();

            ctx.arc(
                x,
                y,
                radius - (6 * scale),
                0,
                Math.PI * 2
            );

            ctx.clip();

            /*
            * Mesmo drawImage usado no fundo
            * da lupa.
            */
            ctx.drawImage(
                video,
                sourceX,
                sourceY,
                sourceWidth,
                sourceHeight,
                0,
                0,
                MAGNIFIER_SIZE,
                MAGNIFIER_SIZE
            );

            ctx.restore();
        });

        /*
        * Terminar o clipping circular
        * da lupa.
        */
        ctx.restore();

        /*
        * Borda da lupa.
        */
        ctx.beginPath();

        ctx.arc(
            center,
            center,
            center - 2,
            0,
            Math.PI * 2
        );

        ctx.strokeStyle = "white";
        ctx.lineWidth = 4;
        ctx.stroke();

        /*
        * Próximo frame.
        */
        animationFrame =
            requestAnimationFrame(drawMagnifier);
    }

    animationFrame =
        requestAnimationFrame(drawMagnifier);

    return () => {
        cancelAnimationFrame(animationFrame);
    };

  }, [
      calibrationMode,
      selectedPoint,
      detectionArea,
      cameraVideo,
      calibrationRender
  ]);
  return (
    <div>
      <QBackgroundBranding />
     
      {/* Menu */}
      <div className="menu-wrapper">
        <div className="title-container">
          <div className="menu-title"> {t("calibration.title")} </div>
          <div className="menu-info"> {t("calibration.titleInfo")} </div>
        </div>

        <div className="caliMenu-container">
          {/* Calibration Info*/}
          <div className="calibrationInfo-container">
            <div className="background"></div>
            <div className="calibration-instructions">
              <span className="bold">{t("calibration.procedureSteps")}</span>
              <span className="regular">
                {t("calibration.procedureSteps1")}
              </span>

              <span className="regular">
                {t("calibration.procedureSteps2")}
              </span>
            </div>
            <div className="btn-group"  disabled={cameraStatus !== "online"}>
              <button
                className={`btn-mode ${calibrationMode === "auto" ? "active" : ""}`}
                onClick={() => handleCalibrationModeChange(false)}
                disabled={cameraStatus !== "online"}
              >
                <div className="color-swatch" style={{ backgroundColor: `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})` }} />
                <div className="btn-content">
                  <img src="/picker.svg" alt="Picker" className="icon" />
                  <span className="text">{t("calibration.selectColorButton")}</span>
                </div>
              </button>

              <button
                className={`btn-mode ${calibrationMode === "manual" ? "active" : ""}`}
                onClick={() => handleCalibrationModeChange(true)}
                disabled={cameraStatus !== "online"}
              >
                <div className="btn-content">
                  <img src="/activity_zone.svg" alt="ACTIVITY_ZONE" className="icon" />
                  <span className="text">{t("calibration.adjustButton")}</span>
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
            <button onClick={calibrate_click} className="calibration-button" disabled={loadingCalibration || cameraStatus !== "online"}>
              <div className="calibration-button-info-container">
                <img src="/filter_zone.svg" alt="FILTER_ZONE" className="icon" />
                <span className="text">{t("calibration.calibrateButton")}</span>
              </div>
            </button>
          </div>

          {/* Video */}
          <div className="calibration-colorToDepthimg-container">
            <div className="background"></div>

            <div className="calibration-colorToDepthimg-wrapper">
              <video
                ref={cameraVideo}
                className="calibration-colorToDepthimg"
                data-manual={calibrationMode === "manual"}
                autoPlay
                playsInline
                muted
                onClick={handleColorClick}
                draggable={false}
              />

              {calibrationMode === "manual" &&
                selectedPoint !== null &&
                selectedPointPosition && (
                    <canvas
                        ref={magnifierCanvas}
                        className={`calibration-magnifier ${magnifierSide}`}
                    />
              )}

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
          title={t("confirmCalibration.title")}
          subtitle={t("confirmCalibration.subtitle")}
          confirmText={t("confirmCalibration.confirmText")}
          cancelText={t("confirmCalibration.cancelText")}
          container={portalContainer}
        />
      )}
    </div>
  );
}

export default QCalibration;
