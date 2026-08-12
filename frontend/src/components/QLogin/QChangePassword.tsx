import React from "react";
import { useEffect, useRef, useState } from "react";
import "./QLogin.css";

import QBranding from "./QBranding";

interface QChangePasswordProps {
  message: {
    type: string;
    text: string;
  }[];

  changeUsername: string;
  changePassword: string;
  changeConfirmPassword: string;

  setChangePassword: (value: string) => void;
  setChangeConfirmPassword: (value: string) => void;

  changePasswordFormError: boolean;
  changeConfirmPasswordFormError: boolean;

  setChangePasswordFormError: (value: boolean) => void;
  setChangeConfirmPasswordFormError: (value: boolean) => void;

  changePasswordFocus: boolean;
  changeConfirmPasswordFocus: boolean;

  setChangePasswordFocus: (value: boolean) => void;
  setChangeConfirmPasswordFocus: (value: boolean) => void;

  confirmChangePassword: () => void;
  showLoginScreen: () => void;
}

function QChangePassword({
  message,
  changeUsername,
  changePassword,
  changeConfirmPassword,
  setChangePassword,
  setChangeConfirmPassword,
  changePasswordFormError,
  changeConfirmPasswordFormError,
  setChangePasswordFormError,
  setChangeConfirmPasswordFormError,
  changePasswordFocus,
  changeConfirmPasswordFocus,
  setChangePasswordFocus,
  setChangeConfirmPasswordFocus,
  confirmChangePassword,
  showLoginScreen,
}: QChangePasswordProps) {
  const changeUsernameRef = useRef<HTMLInputElement>(null);
  const changePasswordRef = useRef<HTMLInputElement>(null);
  const changeConfirmPasswordRef = useRef<HTMLInputElement>(null);
  const changeButtonRef = useRef<HTMLButtonElement | null>(null);
  return (
    <div>
      <QBranding />
      <div className="login-panel-register">
        <div className="login-panel-title">Redefine Password</div>

        <div className="login-panel-register-error-or-info">
          {message.map((msg, i) => (
            <p
              key={i}
              className={msg.type === "error" ? "error-message" : "info-message"}
            >
              {msg.text}
            </p>
          ))}
        </div>

        <form
          className="login-form"
          onSubmit={(e) => {
            e.preventDefault();
            confirmChangePassword();
          }}
        >
          <div className="input-container">
            <input
              ref={changeUsernameRef}
              className={"changePassword-username-input"}
              type="text"
              value={changeUsername}
              readOnly
              tabIndex={-1}
              onMouseDown={(e) => e.preventDefault()}
            />
            <label className={changeUsername ? "active" : ""}>
              Username
            </label>
          </div>

          <div className="input-container">
            <input
              ref={changePasswordRef}
              className={`login-input ${changePasswordFormError ? "login-input-error" : ""}`}
              type="password"
              value={changePassword}
              onFocus={() => {
                setChangePasswordFocus(true)
                setChangePasswordFormError(false);
              }}
              onBlur={() => setChangePasswordFocus(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                  e.preventDefault();
                  changeConfirmPasswordRef.current?.focus();
                }
              }}
              onChange={(e) => setChangePassword(e.target.value)}
            />
            <label className={changePasswordFocus || changePassword ? "active" : ""}>
              Password
            </label>
          </div>

          <div className="input-container">
            <input
              ref={changeConfirmPasswordRef}
              className={`login-input ${changeConfirmPasswordFormError ? "login-input-error" : ""}`}
              type="password"
              value={changeConfirmPassword}
              onFocus={() => {
                setChangeConfirmPasswordFocus(true);
                setChangeConfirmPasswordFormError(false);
              }}
              onBlur={() => setChangeConfirmPasswordFocus(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                  e.preventDefault();
                  changeButtonRef.current?.focus();
                }
              }}
              onChange={(e) => setChangeConfirmPassword(e.target.value)}
            />
            <label
              className={
                changeConfirmPasswordFocus || changeConfirmPassword ? "active" : ""
              }
            >
              Confirm Password
            </label>
          </div>

          <div className="login-actions">
            <div className="login-options">
              <p onClick={showLoginScreen}>
                <span>Cancel</span>
              </p>
            </div>

            <button ref={changeButtonRef} className="login-button" type="submit">
              <div className="background"></div>
              <span className="text">Confirm</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default QChangePassword;