import React from "react";
import { useEffect, useRef } from "react";
import { RefObject } from "react";
import "./QMeasureHistory.css";
import Qselect from "../Qselect"
import Qsearch from "../Qsearch"
import DeleteForeverIcon from "@assets/icons/delete_forever.svg?react";

import QBackgroundBranding from "../QBackgroundBranding";

interface Message {
  type: string;
  text: string;
}

interface SortOption {
  label: string;
  value: string;
}

interface Position {
  x: number;
  y: number;
}

interface QMeasureHistoryProps {
  t: (key: string) => string;

  message: Message[];

  toggleMenu: () => void;

  // Sort
  sortField: string;
  setSortField: React.Dispatch<React.SetStateAction<string>>;
  sortOrder: string;
  setSortOrder: React.Dispatch<React.SetStateAction<string>>;
  sortOptions: SortOption[];
  sortedMeasurements: any[];

  searchBy: string;
  setSearchBy: React.Dispatch<React.SetStateAction<string>>;
  searchValue: string;
  setSearchValue: React.Dispatch<React.SetStateAction<string>>;
  searchByOptions: SortOption[];
  filteredMeasurements: any[];

  dateFilter: string;
  setDateFilter: React.Dispatch<React.SetStateAction<string>>;
  dateOptions: SortOption[];

  // Users (for the "User" column)
  usersIDList: any[];

  // Row actions modal
  measurementConfigModal: boolean;
  toggleMeasurementModal: () => void;
  measurementConfigModalPosition: Position;
  setMeasurementModalPosition: React.Dispatch<React.SetStateAction<Position>>;

  measurementsConfigModal: boolean;
  toggleMeasurementsModal: () => void;
  measurementsConfigModalPosition: Position;
  setMeasurementsModalPosition: React.Dispatch<React.SetStateAction<Position>>;

  selectedID: number | null;
  setSelectedID: React.Dispatch<React.SetStateAction<number | null>>;

  viewMeasurement: (id: number) => void;
  deleteMeasurement: (id: number | null) => void;
  deleteAllMeasurements: () => void;

  // Measurement info popup
  showMeasurementInfo: boolean;
  setShowMeasurementInfo: React.Dispatch<React.SetStateAction<boolean>>;
  measureObjectImage: string | null;
  measurementMode: string;
  measureVolumeInfo: any;
  setMeasureVolumeInfo: React.Dispatch<React.SetStateAction<any>>;
  measureMultipleVolumeData: any;
  measureObjectList: any[];
  measureSelectedObject: string;
  setMeasureSelectedObject: React.Dispatch<React.SetStateAction<string>>;

  canvasRef: RefObject<HTMLCanvasElement | null>;
}

function QMeasureHistory({
  t, 
  message,
  toggleMenu,

  sortField,
  setSortField,
  sortOrder,
  setSortOrder,
  sortOptions,
  sortedMeasurements,

  searchBy,
  setSearchBy,
  searchValue,
  setSearchValue,
  searchByOptions,
  filteredMeasurements,

  dateFilter,
  setDateFilter,
  dateOptions,

  usersIDList,

  measurementConfigModal,
  toggleMeasurementModal,
  measurementConfigModalPosition,
  setMeasurementModalPosition,

  measurementsConfigModal,
  toggleMeasurementsModal,
  measurementsConfigModalPosition,
  setMeasurementsModalPosition,

  selectedID,
  setSelectedID,

  viewMeasurement,
  deleteMeasurement,
  deleteAllMeasurements,

  showMeasurementInfo,
  setShowMeasurementInfo,
  measureObjectImage,
  measurementMode,
  measureVolumeInfo,
  setMeasureVolumeInfo,
  measureMultipleVolumeData,
  measureObjectList,
  measureSelectedObject,
  setMeasureSelectedObject,

  canvasRef

}: QMeasureHistoryProps) {
  const measurementsMoreOptionsRef = useRef<HTMLImageElement>(null);
  const measurementMoreOptionsRef = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    if (!measurementsConfigModal) return;

    const updatePosition = () => {
      if (!measurementsMoreOptionsRef.current) return;

      const rect = measurementsMoreOptionsRef.current.getBoundingClientRect();

      setMeasurementsModalPosition({
        x: rect.right,
        y: rect.bottom + 5,
      });
    };

    updatePosition();

    window.addEventListener("resize", updatePosition);

    return () => {
      window.removeEventListener("resize", updatePosition);
    };
  }, [
    measurementsConfigModal,
    setMeasurementsModalPosition,
  ]);

  useEffect(() => {
    if (!measurementConfigModal) return;

    const updatePosition = () => {
      if (!measurementMoreOptionsRef.current) return;

      const rect = measurementMoreOptionsRef.current.getBoundingClientRect();

      setMeasurementModalPosition({
        x: rect.right,
        y: rect.bottom + 5,
      });
    };

    updatePosition();

    window.addEventListener("resize", updatePosition);

    return () => {
      window.removeEventListener("resize", updatePosition);
    };
  }, [
    measurementConfigModal,
    setMeasurementModalPosition,
  ]);

  function handleSortChange(value: string) {
    if (sortField === value) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortField(value);
      setSortOrder("desc");
    }
  }

  return (
    <div>
      <QBackgroundBranding />

      <div className="menu-wrapper">
        <div className="title-container">
          <div className="menu-title">{t("measurementHistory.title")}</div>
          <div className="menu-info">{t("measurementHistory.titleInfo")}</div>
        </div>

        {/* Measurement Info*/}
        <div className="measurementHistory-container">
          <div className="background"></div>
          <div className="searchBar">
            <Qselect
              label={t("measurementHistory.labelTimePeriod")}
              value={dateFilter}
              options={dateOptions}
              onChange={(value) => setDateFilter(value)}
            />
            <Qselect
              label={t("measurementHistory.labelSortBy")}
              value={sortField}
              options={sortOptions}
              onChange={handleSortChange}
            />
            <Qselect
              label={t("measurementHistory.labelSearchBy")}
              value={searchBy}
              options={searchByOptions}
              onChange={(value) => setSearchBy(value)}
            />
            <Qsearch
              placeholder={t("measurementHistory.labelSearchBar")}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
            />
          </div>

          <div className="history-container">
            <div className="history-header">
              <div className="history-header-text">ID</div>
              <div className="history-header-text">{t("measurementHistory.headerUser")}</div>
              <div className="history-header-text">{t("measurementHistory.headerMeasurementMode")}</div>
              <div className="history-header-text">{t("measurementHistory.headerObjects")}</div>
              <div className="history-header-text">{t("measurementHistory.headerTotalVolume")}</div>
              <div className="history-header-text">{t("measurementHistory.headerWeight")}</div>
              <div className="history-header-text">{t("measurementHistory.headerMeasurementDate")}</div>
              <img
                ref={measurementsMoreOptionsRef}
                src="/more_options.svg"
                className={`more-options-button ${measurementsConfigModal ? "active" : ""}`}
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setMeasurementsModalPosition({
                    x: rect.right,
                    y: rect.bottom + 5,
                  });
                  toggleMeasurementsModal();
                }}
              />
            </div>

            <div className="history-table">
              {filteredMeasurements.map((measurement, index) => (
                <div
                  key={measurement.id}
                  className={`history-row ${index % 2 === 0 ? "even" : "odd"}`}
                  onClick={(e) => {
                    if ((e.target as HTMLElement).closest(".more-options-button")) return;
                    viewMeasurement(measurement.id);
                  }}
                >
                  <div className="history-row-text">{measurement.id}</div>
                  <div className="history-row-text">
                    {(() => {
                      const user = usersIDList.find((u) => u.id === measurement.user_id);
                      return user ? `[${user.id}] ${user.username}` : `[${measurement.user_id}]`;
                    })()}
                  </div>
                  <div className="history-row-text">{measurement.volume_mode}</div>
                  <div className="history-row-text">{measurement.object_count}</div>
                  <div className="history-row-text">{measurement.total_volume_m.toFixed(6)} m³</div>
                  <div className="history-row-text">{measurement.weight} kg</div>
                  <div className="history-row-text">{new Date(measurement.created_at).toLocaleString()}</div>
                  <img
                    ref={measurementConfigModal && selectedID === measurement.id
                      ? measurementMoreOptionsRef
                      : null}
                    src="/more_options.svg"
                    className={`more-options-button ${measurementConfigModal && selectedID === measurement.id ? "active" : ""}`}
                    onClick={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      setMeasurementModalPosition({
                        x: rect.right,
                        y: rect.bottom + 5
                      });
                      toggleMeasurementModal();
                      setSelectedID(measurement.id);
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {measurementsConfigModal && (
        <div
          className="measurements-config-modal"
          style={{
            position: "fixed",
            left: `${measurementsConfigModalPosition.x}px`,
            top: `${measurementsConfigModalPosition.y}px`,
            transform: "translateX(-100%)",
          }}        
        >
          <div className="background"></div>
          <div
            className="menu-item"
            onClick={() => { deleteAllMeasurements(); toggleMeasurementsModal(); }}
          >
            <DeleteForeverIcon className="deleteMeasurements-icon" />
            <div className="deleteMeasurements-text">{t("measurementHistory.deleteAllButton")}</div>
          </div>
        </div>
      )}

      {measurementConfigModal && (
        <div
          className="measurement-config-modal"
          style={{
            position: "fixed",
            left: `${measurementConfigModalPosition.x}px`,
            top: `${measurementConfigModalPosition.y}px`,
            transform: "translateX(-100%)",
          }}
        >
          <div className="background"></div>
          <div
            className="menu-item"
            onClick={() => { deleteMeasurement(selectedID); toggleMeasurementModal(); }}
          >
            <DeleteForeverIcon className="deleteMeasurement-icon" />
            <div className="deleteMeasurement-text">{t("measurementHistory.deleteButton")}</div>
          </div>
        </div>
      )}

      {showMeasurementInfo && (
        <div className="measurement-info-popup">
          <div className="measurement-info-window">
            <div className="measurement-info-title">
              <span> {t("measurementInfo.title")} </span>
            </div>

            <div className="measurement-info-container">
              <div className="measurementImg-container">
                <div className="background"></div>

                <div className="measurement-info-img-wrapper">
                  {measureObjectImage && (
                    <img className="measurement-object-img" src={measureObjectImage} alt="objects" />
                  )}
                </div>
              </div>

              {measurementMode === "Single Bundle" && (
                <div className="measurement-boxInfo-container">
                  <div className="background"></div>

                  {measureVolumeInfo && !measureMultipleVolumeData && (
                    <>
                      <canvas ref={canvasRef} className="measurement-volume-bundle-canvas" />
                      <div className="measurement-boxBundleInfoText-container">
                        <div style={{ color: "#6CD08A" }} className="measurement-boxBundleInfo-text">
                          <span className="label">{t("measurementInfo.width")}</span>
                          <span className="value">{measureVolumeInfo.width.toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#C66D6D" }} className="measurement-boxBundleInfo-text">
                          <span className="label">{t("measurementInfo.length")}</span>
                          <span className="value">{measureVolumeInfo.length.toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#9EB0FD" }} className="measurement-boxBundleInfo-text">
                          <span className="label">{t("measurementInfo.height")}</span>
                          <span className="value">{measureVolumeInfo.height.toFixed(1)}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="measurement-boxBundleInfo-text">
                          <span className="label">{t("measurementInfo.volume_m")}</span>
                          <span className="value">{measureVolumeInfo.volume_m.toFixed(6)}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="measurement-boxBundleInfo-text">
                          <span className="label">{t("measurementInfo.volume_cm")}</span>
                          <span className="value">{measureVolumeInfo.volume_cm.toFixed(2)}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="measurement-boxBundleInfo-text">
                          <span className="label">{t("measurementInfo.weight")}</span>
                          <span className="value">{measureVolumeInfo?.weight != null ? Number(measureVolumeInfo.weight).toFixed(2) : "0.00"}</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}

              {(measurementMode === "Multi Bundle" || measurementMode === "Real") && (
                <>
                  <div className="measurement-boxInfo-container">
                    <div className="background"></div>
                    <div className="measurement-objects-text">
                      {t("measurementInfo.objects")}
                    </div>                  

                    <div className="measurement-object-tabs">
                        {measureObjectList.map((obj) => (
                            <button
                                key={obj}
                                className={`measurement-object-tab ${measureSelectedObject === obj ? "active" : ""}`}
                                onClick={() => {
                                  setMeasureSelectedObject(() => {
                                    return obj;
                                });
                              }}
                            >
                              {obj}
                            </button>
                        ))}
                    </div>

                    {measureVolumeInfo && measureSelectedObject && (
                      <>
                        <canvas ref={canvasRef} className="measurement-volume-canvas" />
                        <div className="measurement-boxInfoText-container">
                          <div style={{ color: "#6CD08A" }} className="measurement-boxInfo-text">
                            <span className="label">{t("measurementInfo.width")}</span>
                            <span className="value">{measurementMode === "Real" ? measureVolumeInfo.width?.[0] : measureVolumeInfo?.width}</span>
                          </div>

                          <div style={{ color: "#C66D6D" }} className="measurement-boxInfo-text">
                            <span className="label">{t("measurementInfo.length")}</span>
                            <span className="value">{measurementMode === "Real" ? measureVolumeInfo.length?.[0] : measureVolumeInfo?.length}</span>
                          </div>

                          <div style={{ color: "#9EB0FD" }} className="measurement-boxInfo-text">
                            <span className="label">{t("measurementInfo.height")}</span>
                            <span className="value">{measurementMode === "Real" ? measureVolumeInfo.height?.[0] : measureVolumeInfo?.height}</span>
                          </div>

                          <div style={{ color: "#FFFFFF" }} className="measurement-boxInfo-text">
                            <span className="label">{t("measurementInfo.volume_m")}</span>
                            <span className="value">{measureVolumeInfo?.volume_m}</span>
                          </div>

                          <div style={{ color: "#FFFFFF" }} className="measurement-boxInfo-text">
                            <span className="label">{t("measurementInfo.volume_cm")}</span>
                            <span className="value">{measureVolumeInfo?.volume_cm}</span>
                          </div>
                        </div>
                      </>
                    )}

                    {measureMultipleVolumeData && (
                      <div className="measurement-object-total">
                          <div className="measurement-total-divider"></div>
                          <div className="measurement-total-row">
                              <span className="measurement-total-label">{t("measurementInfo.totalWeight")}</span>
                              <span className="measurement-total-value">
                                  {measureMultipleVolumeData?.Total?.weight != null ? Number(measureMultipleVolumeData?.Total?.weight).toFixed(2) : "0.00"} Kg
                              </span>
                          </div>
                          <div className="measurement-total-row">
                              <span className="measurement-total-label">{t("measurementInfo.totalVolume")}</span>
                              <span className="measurement-total-value">
                                  {measureMultipleVolumeData?.Total?.volume_m ?? 0} m³
                              </span>
                          </div>
                      </div>
                    )}
                    
                  </div>
                </>
              )}
            </div>

            <div className="measurement-info-button">
              <img src="/close.svg" onClick={() => { setShowMeasurementInfo(false); setMeasureVolumeInfo(null); }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default QMeasureHistory;