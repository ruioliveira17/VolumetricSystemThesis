import React from "react";
import { RefObject } from "react";
import "./QVolume.css";

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

  volInfo: any;
  multipleVolumeData: any;

  canvasRef: RefObject<HTMLCanvasElement | null>;

  objectList: any[];
  selectedObject: string;
  setSelectedObject: React.Dispatch<React.SetStateAction<string>>;

  countdown: number | null;

  weightInfo: any;

  volumeMode: string;

  toggleMenu: () => void;
  setVolInfo: (value: any) => void;
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

  volInfo,
  multipleVolumeData,

  canvasRef,

  objectList,
  selectedObject,
  setSelectedObject,

  countdown,

  weightInfo,

  volumeMode,

  toggleMenu,
  setVolInfo

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


        {loadingVolume && (
            <div className="warning">
            {processingMessage}
            </div>
        )}


        <div className="menu-wrapper">
            <div className="title-container">
                <div className="menu-title">Volume</div>
                <div className="menu-info">Calculates the volume of objects on the platform</div>
            </div>


            {/* Video & Image */}
            <div className="camera-container">
                <div className="camera-video-wrapper">
                    {showCamera ? (
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
                    ) : (
                        objectImage && (
                            <img className="object-img" src={objectImage} onLoad={() => {setCropVideoReady(true);}} style={cropTransform} alt="objects"/>
                        )
                    )}
                </div>

                <div className="switch-button-wrapper">
                    {objectImage && (
                        <button onClick={() => setShowCamera(prev => !prev)} className="switch-button"></button>
                    )}
                </div>
            </div>

            {volBundleMode ? (
                <>
                    {/* Button */}
                    <button onClick={volume_click} className="volumeBundle-button" disabled={loadingVolume || !weightStable}>
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
                        
                        {volInfo && !multipleVolumeData && (volInfo.width !== 0 || volInfo.length !== 0 || volInfo.height !== 0 || volInfo.volume_m !== 0 || volInfo.volume_cm !== 0) && (
                            <>
                                <canvas ref={canvasRef} className="volumeBundle-canvas" />

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

                                    <div style={{ color: "#FFFFFF" }} className="boxBundleInfo-text">
                                        <span className="label">Weight (kg):</span> 
                                        <span className="value">{weightInfo?.weight != null ? Number(weightInfo.weight).toFixed(2) : "0.00"} </span> 
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
                                    className={`object-item ${ selectedObject === obj ? "selected" : ""}`}
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
                                    <span className="arrow">{selectedObject === obj ? "▶" : ""}</span>
                                    <span className="object-name">Object {obj}</span>
                                </span>
                            ))}
                        </div>

                        <div className="object-total">
                            {multipleVolumeData ? (
                                <> 
                                    <div>TOTAL WEIGHT:</div>
                                    <div className="total-value">
                                        {weightInfo?.weight != null ? Number(weightInfo.weight).toFixed(2) : "0.00"} Kg
                                    </div>

                                    <div>TOTAL VOLUME:</div>
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

                        {!volInfo && !loadingVolume && multipleVolumeData &&(
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
            <div className="powered-by-text" translate="no">
                Powered by
            </div>

            <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo"/>
        </div>
    </div>
  );
}


export default QVolume;