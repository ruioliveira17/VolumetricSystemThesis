import React from "react";
import { RefObject } from "react";
import "./QMeasureHistory.css";
import Qselect from "../Qselect"
import Qsearch from "../Qsearch"

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
  message: Message[];

  toggleMenu: () => void;

  // Sort
  sortField: string;
  setSortField: React.Dispatch<React.SetStateAction<string>>;
  sortOrder: string;
  setSortOrder: React.Dispatch<React.SetStateAction<string>>;
  sortOptions: SortOption[];
  sortedMeasurements: any[];

  searchValue: string;
  setSearchValue: React.Dispatch<React.SetStateAction<string>>;
  filteredMeasurements: any[];

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
  message,
  toggleMenu,

  sortField,
  setSortField,
  sortOrder,
  setSortOrder,
  sortOptions,
  sortedMeasurements,

  searchValue,
  setSearchValue,
  filteredMeasurements,

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

      <div className="menu-wrapper">
        <div className="title-container">
          <div className="menu-title">Measurement History</div>
          <div className="menu-info">Shows the data of the measurements made on the last 90 days</div>
        </div>

        {/* Measurement Info*/}
        <div className="measurementHistory-container">
          <div className="background"></div>
          <div className="searchBar">
            <Qsearch
              placeholder="Search..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
            />
            <Qselect
              label="Sort By"
              value={sortField}
              options={sortOptions}
              onChange={handleSortChange}
            />
          </div>

          <div className="history-container">
            <div className="history-header">
              <div className="history-header-text">ID</div>
              <div className="history-header-text">User</div>
              <div className="history-header-text">Measurement Mode</div>
              <div className="history-header-text">No. of Objects</div>
              <div className="history-header-text">Total Volume</div>
              <div className="history-header-text">Weight</div>
              <div className="history-header-text">Measurement Date</div>
              <img
                src="/more_options.svg"
                className={`more-options-button ${measurementsConfigModal ? "active" : ""}`}
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setMeasurementsModalPosition({ x: rect.right, y: rect.top });
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
                    src="/more_options.svg"
                    className={`more-options-button ${measurementConfigModal && selectedID === measurement.id ? "active" : ""}`}
                    onClick={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      setMeasurementModalPosition({ x: rect.right, y: rect.top });
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
          style={{ left: `${measurementsConfigModalPosition.x}px`, top: `${measurementsConfigModalPosition.y}px` }}
        >
          <div className="background"></div>
          <div
            className="menu-item"
            onClick={() => { deleteAllMeasurements(); toggleMeasurementsModal(); }}
          >
            <img src="/delete_forever.svg" className="deleteMeasurements-icon" />
            <div className="deleteMeasurements-text">Delete All</div>
          </div>
        </div>
      )}

      {measurementConfigModal && (
        <div
          className="measurement-config-modal"
          style={{ left: `${measurementConfigModalPosition.x}px`, top: `${measurementConfigModalPosition.y}px` }}
        >
          <div className="background"></div>
          <div
            className="menu-item"
            onClick={() => { deleteMeasurement(selectedID); toggleMeasurementModal(); }}
          >
            <img src="/delete_forever.svg" className="deleteMeasurement-icon" />
            <div className="deleteMeasurement-text">Delete</div>
          </div>
        </div>
      )}

      {showMeasurementInfo && (
        <div className="measurement-info-popup">
          <div className="measurement-info-window">
            <div className="measurement-info-title">
              <span> Measurement Info </span>
            </div>

            <div className="measurement-info-img-wrapper">
              {measureObjectImage && (
                <img className="measurement-object-img" src={measureObjectImage} alt="objects" />
              )}
            </div>

            {measurementMode === "Single Bundle" && (
              <div className="measurement-boxInfo-container">
                <div className="background"></div>

                {measureVolumeInfo && !measureMultipleVolumeData && (
                  <>
                    <canvas ref={canvasRef} className="measurement-canvas" />
                    <div className="measurement-boxInfoText-container">
                      <div style={{ color: "#6CD08A" }} className="measurement-boxInfo-text">
                        <span className="label">Width (cm):</span>
                        <span className="value">{measureVolumeInfo.width.toFixed(1)}</span>
                      </div>

                      <div style={{ color: "#C66D6D" }} className="measurement-boxInfo-text">
                        <span className="label">Length (cm):</span>
                        <span className="value">{measureVolumeInfo.length.toFixed(1)}</span>
                      </div>

                      <div style={{ color: "#9EB0FD" }} className="measurement-boxInfo-text">
                        <span className="label">Height (cm):</span>
                        <span className="value">{measureVolumeInfo.height.toFixed(1)}</span>
                      </div>

                      <div style={{ color: "#FFFFFF" }} className="measurement-boxInfo-text">
                        <span className="label">Volume (m³):</span>
                        <span className="value">{measureVolumeInfo.volume_m.toFixed(6)}</span>
                      </div>

                      <div style={{ color: "#FFFFFF" }} className="measurement-boxInfo-text">
                        <span className="label">Volume (cm³):</span>
                        <span className="value">{measureVolumeInfo.volume_cm.toFixed(2)}</span>
                      </div>

                      <div style={{ color: "#FFFFFF" }} className="measurement-boxInfo-text">
                        <span className="label">Weight (kg):</span>
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
                              Obj. {obj}
                          </button>
                      ))}
                  </div>

                  {measureVolumeInfo && measureSelectedObject && (
                    <>
                      <canvas ref={canvasRef} className="measurement-volume-canvas" />
                      <div className="measurement-boxInfoText-container">
                        <div style={{ color: "#6CD08A" }} className="measurement-boxInfo-text">
                          <span className="label">Width (cm):</span>
                          <span className="value">{measurementMode === "Real" ? measureVolumeInfo.width?.[0] : measureVolumeInfo?.width}</span>
                        </div>

                        <div style={{ color: "#C66D6D" }} className="measurement-boxInfo-text">
                          <span className="label">Length (cm):</span>
                          <span className="value">{measurementMode === "Real" ? measureVolumeInfo.length?.[0] : measureVolumeInfo?.length}</span>
                        </div>

                        <div style={{ color: "#9EB0FD" }} className="measurement-boxInfo-text">
                          <span className="label">Height (cm):</span>
                          <span className="value">{measurementMode === "Real" ? measureVolumeInfo.height?.[0] : measureVolumeInfo?.height}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="measurement-boxInfo-text">
                          <span className="label">Volume (m³):</span>
                          <span className="value">{measureVolumeInfo?.volume_m}</span>
                        </div>

                        <div style={{ color: "#FFFFFF" }} className="measurement-boxInfo-text">
                          <span className="label">Volume (cm³):</span>
                          <span className="value">{measureVolumeInfo?.volume_cm}</span>
                        </div>
                      </div>
                    </>
                  )}

                  {measureMultipleVolumeData && (
                    <div className="measurement-object-total">
                        <div className="measurement-total-divider"></div>
                        <div className="measurement-total-row">
                            <span className="measurement-total-label">TOTAL WEIGHT:</span>
                            <span className="measurement-total-value">
                                {measureMultipleVolumeData?.Total?.weight != null ? Number(measureMultipleVolumeData?.Total?.weight).toFixed(2) : "0.00"} Kg
                            </span>
                        </div>
                        <div className="measurement-total-row">
                            <span className="measurement-total-label">TOTAL VOLUME:</span>
                            <span className="measurement-total-value">
                                {measureMultipleVolumeData?.Total?.volume_m ?? 0} m³
                            </span>
                        </div>
                    </div>
                  )}
                  {/*{!measureVolumeInfo && measureMultipleVolumeData && (
                    <div className="measurement-boxInfo-message">Selecione um objeto</div>
                  )}*/}
                </div>
              </>
            )}

            <div className="measurement-info-button">
              <img src="/close.svg" onClick={() => { setShowMeasurementInfo(false); setMeasureVolumeInfo(null); }} />
            </div>
          </div>
        </div>
      )}

      {/* Powered By */}
      <div className="powered-by-panel">
        <div className="powered-by-text" translate="no">Powered by</div>
        <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo" />
      </div>
    </div>
  );
}

export default QMeasureHistory;