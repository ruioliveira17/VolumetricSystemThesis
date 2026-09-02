import React from "react";
import QubicIcon from '@assets/icons/Qubic.svg?react';

function QBackgroundBranding() {
  return (
    <>
        <div className="logo">
          <QubicIcon />
        </div>

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