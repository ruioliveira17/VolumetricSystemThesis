import React from "react";

function QBackgroundBranding() {
  return (
    <>
        <img src="/Qubic.svg" className="logo" alt="Qubic Logo" />

        <div className="powered-by-panel">
            <div className="powered-by-text" translate="no">
                Powered by
            </div>

            <img src="/MarquesLogo.svg" className="powered-by-logo" alt="Marques Logo"/>
        </div>
    </>
  );
}

export default QBackgroundBranding;