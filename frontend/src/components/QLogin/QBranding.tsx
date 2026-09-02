import React from "react";
import "./QLogin.css";

import QubicIcon from '@assets/icons/Qubic.svg?react';

function QBranding() {
  return (
    <>
      <div className="qubic-logo">
        <QubicIcon />
      </div>

      <div className="powered-by-panel-login">
        <div className="powered-by-text-login" translate="no">
          Powered by
        </div>
        <img
          src="/MarquesLogo.svg"
          className="powered-by-logo-login"
          alt="Marques Logo"
        />
      </div>
    </>
  );
}

export default QBranding;