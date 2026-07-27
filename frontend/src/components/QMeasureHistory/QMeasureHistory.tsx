import React from "react";
import { RefObject } from "react";
import "./QMeasureHistory.css";

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
  sortOpen: boolean;
  setSortOpen: React.Dispatch<React.SetStateAction<boolean>>;
  sortField: string;
  setSortField: React.Dispatch<React.SetStateAction<string>>;
  sortOrder: string;
  setSortOrder: React.Dispatch<React.SetStateAction<string>>;
  sortOptions: SortOption[];
  sortedMeasurements: any[];

  // Users (for the "User" column)
  usersIDList: any[];

  // Row actions modal
  measurementConfigModal: boolean;
  toggleMeasurementModal: () => void;
  measurementConfigModalPosition: Position;
  setMeasurementModalPosition: React.Dispatch<React.SetStateAction<Position>>;

  selectedID: number | null;
  setSelectedID: React.Dispatch<React.SetStateAction<number | null>>;

  viewMeasurement: (id: number) => void;
  deleteMeasurement: (id: number | null) => void;

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

  sortOpen,
  setSortOpen,
  sortField,
  setSortField,
  sortOrder,
  setSortOrder,
  sortOptions,
  sortedMeasurements,

  usersIDList,

  measurementConfigModal,
  toggleMeasurementModal,
  measurementConfigModalPosition,
  setMeasurementModalPosition,

  selectedID,
  setSelectedID,

  viewMeasurement,
  deleteMeasurement,

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
            <div className="sort-container">
              <div
                className="sort-selected"
                onClick={() => setSortOpen(!sortOpen)}
              >
                <div className="sort-title">
                  Sort By:
                </div>

                <div className="sort-value">
                  {sortOptions.find(x => x.value === sortField)?.label}

                  <span>
                    {sortOpen ? "▲" : "▼"}
                  </span>
                </div>
              </div>

              {sortOpen && (
                <div className="sort-dropdown">
                  {sortOptions.map(option => (
                    <div
                      key={option.value}
                      className="sort-option"
                      onClick={() => {
                        if (sortField === option.value) {
                          setSortOrder(sortOrder === "desc" ? "asc" : "desc");
                        } else {
                          setSortField(option.value);
                          setSortOrder("desc");
                        }
                      }}
                    >
                      <span>{option.label}</span>

                      {sortField === option.value && (
                        <span>{sortOrder === "desc" ? "▼" : "▲"}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
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
              {/* NOTE (port): no App.py havia aqui um botão "more_options" que
                  abria um modal com "Delete All" -> deleteAllMeasurements().
                  Essa função NUNCA foi definida no App.py (bug latente), por isso
                  o botão foi omitido de propósito para não inventar comportamento. */}
            </div>

            <div className="history-table">
              {sortedMeasurements.map((measurement, index) => (
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
              <div className="measurement-boxBundleInfo-container">
                <div className="background"></div>

                {measureVolumeInfo && !measureMultipleVolumeData && (
                  <>
                    <canvas ref={canvasRef} className="measurement-bundle-canvas" />
                    <div className="measurement-boxBundleInfoText-container">
                      <div style={{ color: "#6CD08A" }} className="measurement-boxBundleInfo-text">
                        <span className="label">Width (cm):</span>
                        <span className="value">{measureVolumeInfo.width.toFixed(1)}</span>
                      </div>

                      <div style={{ color: "#C66D6D" }} className="measurement-boxBundleInfo-text">
                        <span className="label">Length (cm):</span>
                        <span className="value">{measureVolumeInfo.length.toFixed(1)}</span>
                      </div>

                      <div style={{ color: "#9EB0FD" }} className="measurement-boxBundleInfo-text">
                        <span className="label">Height (cm):</span>
                        <span className="value">{measureVolumeInfo.height.toFixed(1)}</span>
                      </div>

                      <div style={{ color: "#FFFFFF" }} className="measurement-boxBundleInfo-text">
                        <span className="label">Volume (m³):</span>
                        <span className="value">{measureVolumeInfo.volume_m.toFixed(6)}</span>
                      </div>

                      <div style={{ color: "#FFFFFF" }} className="measurement-boxBundleInfo-text">
                        <span className="label">Volume (cm³):</span>
                        <span className="value">{measureVolumeInfo.volume_cm.toFixed(2)}</span>
                      </div>

                      <div style={{ color: "#FFFFFF" }} className="measurement-boxBundleInfo-text">
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
                <div className="measurement-object-selection-menu">
                  <div className="background"></div>

                  <div className="measurement-object-list">
                    {measureObjectList.map((obj) => (
                      <span
                        key={obj}
                        className={`object-item ${measureSelectedObject === obj ? "selected" : ""}`}
                        onClick={() => {
                          setMeasureSelectedObject(prev => {
                            const isSame = prev === obj;
                            if (isSame) {
                              setMeasureVolumeInfo(null);
                              return "";
                            }
                            return obj;
                          });
                        }}
                      >
                        <span className="measurement-arrow">
                          {measureSelectedObject === obj ? "▶" : ""}
                        </span>
                        <span className="measurement-object-name">Object {obj}</span>
                      </span>
                    ))}
                  </div>

                  <div className="measurement-object-total">
                    {measureMultipleVolumeData ? (
                      <>
                        <div>TOTAL WEIGHT:</div>
                        <div className="measurement-total-value">
                          {measureMultipleVolumeData?.Total?.weight != null ? Number(measureMultipleVolumeData?.Total?.weight).toFixed(2) : "0.00"} Kg
                        </div>

                        <div>TOTAL VOLUME:</div>
                        <div className="measurement-total-value">
                          {measureMultipleVolumeData?.Total?.volume_m ?? 0} m³
                        </div>
                      </>
                    ) : null}
                  </div>
                </div>

                <div className="measurement-boxInfo-container">
                  <div className="background"></div>

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

                  {!measureVolumeInfo && measureMultipleVolumeData && (
                    <div className="measurement-boxInfo-message">Selecione um objeto</div>
                  )}
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