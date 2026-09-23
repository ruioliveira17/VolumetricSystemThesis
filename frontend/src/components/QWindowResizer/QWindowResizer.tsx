import React, { RefObject } from "react";
import "./QWindowResizer.css";

interface QWindowResizerProps {
    t: (key: string) => string;
    cropVideo: RefObject<HTMLVideoElement>;
    cropCanvas: RefObject<HTMLCanvasElement>;

    cropArea: any;
    setCropArea: (value: any) => void;

    setVideoCrop: (value: any) => void;

    setShowCropWindow: (value: boolean) => void;
    setShowSettingsPopup: (value: boolean) => void;

    cropWindow_Set: (original: any, crop: any) => void;

    ORIGINAL_CROP: any;
    DEFAULT_CROP: any;
}

function QWindowResizer({
    t,
    cropVideo,
    cropCanvas,
    cropArea,
    setCropArea,
    setVideoCrop,
    setShowCropWindow,
    setShowSettingsPopup,
    cropWindow_Set,
    ORIGINAL_CROP,
    DEFAULT_CROP
}: QWindowResizerProps) {

    return (
        <div className="crop-popup">
            <div className="crop-window">

                <div className="crop-title">
                    <span>{t("windowResizer.title")}</span>
                </div>

                <div className="crop-video-wrapper">
                    <video
                        ref={cropVideo}
                        autoPlay
                        playsInline
                        className="crop-video"
                    />

                    <canvas
                        ref={cropCanvas}
                        className="crop-overlay"
                    />
                </div>

                <div className="crop-buttons">

                    <button
                        className="crop-button"
                        onClick={() => setShowCropWindow(false)}
                    >
                        <span className="text">{t("windowResizer.cancelButton")}</span>
                    </button>


                    <button
                        className="crop-button"
                        onClick={() => {
                            setVideoCrop({
                                ...ORIGINAL_CROP,
                                videoWidth: cropVideo.current!.videoWidth,
                                videoHeight: cropVideo.current!.videoHeight,
                                displayWidth: cropVideo.current!.clientWidth,
                                displayHeight: cropVideo.current!.clientHeight
                            });

                            setCropArea(DEFAULT_CROP);

                            setShowCropWindow(false);
                            setShowSettingsPopup(false);

                            cropWindow_Set(
                                ORIGINAL_CROP,
                                DEFAULT_CROP
                            );
                        }}
                    >
                        <span className="text">{t("windowResizer.revertButton")}</span>
                    </button>


                    <button
                        className="crop-button"
                        onClick={() => {
                            setVideoCrop({
                                ...cropArea,
                                videoWidth: cropVideo.current!.videoWidth,
                                videoHeight: cropVideo.current!.videoHeight,
                                displayWidth: cropVideo.current!.clientWidth,
                                displayHeight: cropVideo.current!.clientHeight
                            });

                            setShowCropWindow(false);
                            setShowSettingsPopup(false);

                            cropWindow_Set(
                                cropArea,
                                cropArea
                            );
                        }}
                    >
                        <span className="text">{t("windowResizer.confirmButton")}</span>
                    </button>

                </div>
            </div>
        </div>
    );
}

export default QWindowResizer;