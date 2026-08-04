import React from "react";
import { RefObject } from "react";
import "./QVolume.css";
import WarningIcon from '@assets/icons/warning.svg?react';
import ZeroIcon from '@assets/icons/zeroIcon.svg?react';
import StableIcon from '@assets/icons/stableIcon.svg?react';

interface Message {
  type: string;
  text: string;
}

interface QVolumeProps {
  message: Message[];

  loadingVolume: boolean;
  processingMessage: string;

  showCamera: boolean;
  setShowCamera: React.Dispatch<React.SetStateAction<boolean>>;

  cameraVideo: RefObject<HTMLVideoElement | null>;
  objectImage: string | null;
  cropVideoReady: boolean;
  setCropVideoReady: React.Dispatch<React.SetStateAction<boolean>>;
  cropTransform: React.CSSProperties | undefined;

  volBundleMode: boolean;

  volume_click: () => void;

  weightStable: boolean;
  weightZero: boolean;

  volInfo: any;
  multipleVolumeData: any;

  canvasRef: RefObject<HTMLCanvasElement | null>;

  objectList: any[];
  selectedObject: string;
  setSelectedObject: React.Dispatch<React.SetStateAction<string>>;

  countdown: number | null;

  weightInfo: any;
  measurementWeightInfo: any;

  volumeMode: string;
  toggleMenu: () => void;
  setVolInfo: (value: any) => void;

  noObjectsDetected: boolean;
  objectsOutOfLine: boolean;
}

function QVolume({
  message,
  loadingVolume,
  processingMessage,

  showCamera,
  setShowCamera,

  cameraVideo,
  objectImage,
  cropVideoReady,
  setCropVideoReady,
  cropTransform,

  volBundleMode,

  volume_click,

  weightStable,
  weightZero,

  volInfo,
  multipleVolumeData,

  canvasRef,

  objectList,
  selectedObject,
  setSelectedObject,

  countdown,

  weightInfo,
  measurementWeightInfo,

  volumeMode,
  toggleMenu,
  setVolInfo,

  noObjectsDetected,
  objectsOutOfLine

}: QVolumeProps) {

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

        <div className="menu-wrapper">
            <div className="title-container">
                <div className="menu-title">Volume</div>
                <div className="menu-info">Calculates the volume of objects on the platform</div>
            </div>


            {/* Video & Image */}
            <div className="camera-container">
                {/* Weight Overlay Bar */}
                <div className="weightBar-container">
                    <div className="background"></div>

                    <div className="weightBar-icons">
                        <ZeroIcon className={`weightBar-icon ${weightZero ? "active" : ""}`}/>
                        <StableIcon className={`weightBar-icon ${weightStable ? "active" : ""}`}/>
                    </div>

                    <div className="weightBar-value">
                        <span className="label">WEIGHT:</span>
                        <span className="value">
                            {weightInfo?.weight != null ? Number(weightInfo.weight).toFixed(2) : "0.00"} kg
                        </span>
                    </div>
                </div>

                <div className="camera-video-wrapper">
                    <video
                        ref={cameraVideo}
                        autoPlay
                        playsInline
                        className="camera-video"
                        onLoadedMetadata={() => {
                            setCropVideoReady(true);
                        }}
                        style={cropTransform}
                    />
                    
                    {objectImage && (
                        <img className={`object-img ${showCamera ? "hidden" : "visible"}`} src={objectImage} onLoad={() => {setCropVideoReady(true);}} style={cropTransform} alt="objects"/>
                    )}
                </div>

                <div className="switch-button-wrapper">
                    {objectImage && (
                        <>
                            <div className="switch-group">
                                <button
                                    className={`switch-mode ${!showCamera ? "active" : ""}`}
                                    onClick={() => setShowCamera(false)}
                                >
                                    <img src="/image.svg" alt="Image" className="icon" />
                                </button>

                                <button
                                    className={`switch-mode ${showCamera ? "active" : ""}`}
                                    onClick={() => setShowCamera(true)}
                                >
                                    <img src="/live_tv.svg" alt="Camera" className="icon" />
                                </button>                                
                            </div>
                        </>
                    )}
                </div>
            </div>

            {volBundleMode ? (
                <>
                    {/* Button */}
                    <button onClick={volume_click} className="volume-button" disabled={loadingVolume || !weightStable}>
                        {loadingVolume && (
                            <>
                                <div className="loadingVolume-icon">
                                    <img src="/loading.svg" alt="loading"/>
                                </div>
                                <div className="volume-processing">
                                    {processingMessage}
                                </div>
                            </>
                        )}

                        <div className="volume-button-info-container">
                            <img src="/VIEW_IN_AR.svg" alt="VIEW_IN_AR" className="icon"/>
                            <span className="text">Get Volume</span>
                        </div>
                    </button>

                    {/* Info Objects */}
                    <div className="boxInfo-container">
                        <div className="background"></div>
                        
                        {volInfo && !multipleVolumeData && (volInfo.width !== 0 || volInfo.length !== 0 || volInfo.height !== 0 || volInfo.volume_m !== 0 || volInfo.volume_cm !== 0) && (
                            <>
                                <canvas ref={canvasRef} className="volume-canvas" />

                                <div className="boxInfoText-container">
                                    <div style={{ color: "#6CD08A" }} className="boxInfo-text">
                                        <span className="label">Width (cm):</span>
                                        <span className="value">{volInfo.width.toFixed(1)}</span> 
                                    </div>

                                    <div style={{ color: "#C66D6D" }} className="boxInfo-text">
                                        <span className="label">Length (cm):</span> 
                                        <span className="value">{volInfo.length.toFixed(1)}</span> 
                                    </div>

                                    <div style={{ color: "#9EB0FD" }} className="boxInfo-text">
                                        <span className="label">Height (cm):</span> 
                                        <span className="value">{volInfo.height.toFixed(1)}</span>     
                                    </div>

                                    <div style={{ color: "#FFFFFF" }} className="boxInfo-text">
                                        <span className="label">Volume (m³):</span> 
                                        <span className="value">{volInfo.volume_m.toFixed(6)}</span> 
                                    </div>

                                    <div style={{ color: "#FFFFFF" }} className="boxInfo-text">
                                        <span className="label">Volume (cm³):</span> 
                                        <span className="value">{volInfo.volume_cm.toFixed(2)}</span> 
                                    </div>

                                    <div style={{ color: "#FFFFFF" }} className="boxInfo-text">
                                        <span className="label">Weight (kg):</span> 
                                        <span className="value">{measurementWeightInfo?.weight != null ? Number(measurementWeightInfo.weight).toFixed(2) : "0.00"} </span> 
                                    </div>

                                </div>
                            </>
                        )}

                        {objectsOutOfLine && (
                            <>
                                <div className="error-modal">
                                    <div className="background"></div>
                                    <div className="icon">
                                        <WarningIcon />
                                    </div>
                                    <div className="text">
                                        <span>There are objects outside the workspace area.</span>
                                        <span>To detect them, make sure they are inside.</span>
                                    </div>
                                </div>
                            </>
                        )}

                        {noObjectsDetected && (
                            <>
                                <div className="error-modal">
                                    <div className="background"></div>
                                    <div className="icon">
                                        <WarningIcon />
                                    </div>
                                    <div className="text">
                                        <span>Failed to identify any objects.</span>
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

            ) : (
                <>
                    {/* Button */}
                    <button onClick={volume_click} className="volume-button" disabled={loadingVolume || !weightStable}>
                        {loadingVolume && (
                            <>
                                <div className="loadingVolume-icon">
                                    <img src="/loading.svg" alt="loading"/>
                                </div>
                                <div className="volume-processing">
                                    {processingMessage}
                                </div>
                            </>
                        )}
                        <div className="volume-button-info-container">
                            <img src="/VIEW_IN_AR.svg" alt="VIEW_IN_AR" className="icon"/>
                            <span className="text">Get Volume</span>
                        </div>
                    </button>

                    {/* Info Objects */}
                    <div className="boxInfo-container">
                        <div className="background"></div>
                        
                        <div className="object-tabs">
                            {objectList.map((obj) => (
                                <button
                                    key={obj}
                                    className={`object-tab ${selectedObject === obj ? "active" : ""}`}
                                    onClick={() => setSelectedObject(obj)}
                                >
                                    Obj. {obj}
                                </button>
                            ))}
                        </div>

                        {volInfo && selectedObject && (
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

                        {multipleVolumeData && (multipleVolumeData?.Total?.volume_m ?? 0) > 0 && (
                            <div className="object-total">
                                <div className="total-divider"></div>
                                <div className="total-row">
                                    <span className="total-label">TOTAL WEIGHT:</span>
                                    <span className="total-value">
                                        {measurementWeightInfo?.weight != null ? Number(measurementWeightInfo.weight).toFixed(2) : "0.00"} kg
                                    </span>
                                </div>
                                <div className="total-row">
                                    <span className="total-label">TOTAL VOLUME:</span>
                                    <span className="total-value">
                                        {multipleVolumeData?.Total?.volume_m ?? 0} m³
                                    </span>
                                </div>
                            </div>
                        )}

                        {objectsOutOfLine && (
                            <>
                                <div className="error-modal">
                                    <div className="background"></div>
                                    <div className="icon">
                                        <WarningIcon />
                                    </div>
                                    <div className="text">
                                        <span>There are objects outside the workspace area.</span>
                                        <span>To detect them, make sure they are inside.</span>
                                    </div>
                                </div>
                            </>
                        )}

                        {noObjectsDetected && (
                            <>
                                <div className="error-modal">
                                    <div className="background"></div>
                                    <div className="icon">
                                        <WarningIcon />
                                    </div>
                                    <div className="text">
                                        <span>Failed to identify any objects.</span>
                                    </div>
                                </div>
                            </>
                        )}

                        {/*{!volInfo && !loadingVolume && multipleVolumeData && (multipleVolumeData?.Total?.volume_m ?? 0) !== 0 && (
                            <>
                                <div className="boxInfo-message">Selecione um objeto</div>
                            </>
                        )}*/}
                    </div>
                </>
            )}
        </div>

      {/* Powered By */}
        <div className="powered-by-panel">
            <div className="powered-by-text" translate="no">
                Powered by
            </div>

            <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo"/>
        </div>
    </div>
  );
}


export default QVolume;