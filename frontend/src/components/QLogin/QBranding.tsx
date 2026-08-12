import React from "react";
import "./QLogin.css";

function QBranding() {
  return (
    <>
      <img src="/Qubic.svg" className="qubic-logo" alt="Qubic Logo" />

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