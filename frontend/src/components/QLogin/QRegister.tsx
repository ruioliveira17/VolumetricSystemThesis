import React from "react";
import { useEffect, useRef, useState } from "react";
import "./QLogin.css";

import QBranding from "./QBranding";

interface QRegisterProps {
  message: {
    type: string;
    text: string;
  }[];

  regUsername: string;
  regPassword: string;
  regConfirmPassword: string;

  setRegUsername: (value: string) => void;
  setRegPassword: (value: string) => void;
  setRegConfirmPassword: (value: string) => void;

  regUsernameFormError: boolean;
  regPasswordFormError: boolean;
  regConfirmPasswordFormError: boolean;

  setRegUsernameFormError: (value: boolean) => void;
  setRegPasswordFormError: (value: boolean) => void;
  setRegConfirmPasswordFormError: (value: boolean) => void;

  regUsernameFocus: boolean;
  regPasswordFocus: boolean;
  regConfirmPasswordFocus: boolean;

  setRegUsernameFocus: (value: boolean) => void;
  setRegPasswordFocus: (value: boolean) => void;
  setRegConfirmPasswordFocus: (value: boolean) => void;

  register: () => void;
  showLoginScreen: () => void;
}

function QRegister({
  message,
  regUsername,
  regPassword,
  regConfirmPassword,
  setRegUsername,
  setRegPassword,
  setRegConfirmPassword,
  regUsernameFormError,
  regPasswordFormError,
  regConfirmPasswordFormError,
  setRegUsernameFormError,
  setRegPasswordFormError,
  setRegConfirmPasswordFormError,
  regUsernameFocus,
  regPasswordFocus,
  regConfirmPasswordFocus,
  setRegUsernameFocus,
  setRegPasswordFocus,
  setRegConfirmPasswordFocus,
  register,
  showLoginScreen,
}: QRegisterProps) {
  const regUsernameRef = useRef<HTMLInputElement>(null);
  const regPasswordRef = useRef<HTMLInputElement>(null);
  const regConfirmPasswordRef = useRef<HTMLInputElement>(null);
  const registerButtonRef = useRef<HTMLButtonElement | null>(null);
  return (
    <div>
      <QBranding />
      <div className="login-panel-register">
        <div className="login-panel-title">Register</div>

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
            register();
          }}
        >
          <div className="input-container">
            <input
              ref={regUsernameRef}
              className={`login-input ${regUsernameFormError ? "login-input-error" : ""}`}
              type="text"
              value={regUsername}
              onFocus={() => {
                setRegUsernameFocus(true);
                setRegUsernameFormError(false);
              }}
              onBlur={() => setRegUsernameFocus(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                  e.preventDefault();
                  regPasswordRef.current?.focus();
                }
              }}
              onChange={(e) => setRegUsername(e.target.value)}
            />
            <label className={regUsernameFocus || regUsername ? "active" : ""}>
              Username
            </label>
          </div>

          <div className="input-container">
            <input
              ref={regPasswordRef}
              className={`login-input ${regPasswordFormError ? "login-input-error" : ""}`}
              type="password"
              value={regPassword}
              onFocus={() => {
                setRegPasswordFocus(true)
                setRegPasswordFormError(false);
              }}
              onBlur={() => setRegPasswordFocus(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                  e.preventDefault();
                  regConfirmPasswordRef.current?.focus();
                }
              }}
              onChange={(e) => setRegPassword(e.target.value)}
            />
            <label className={regPasswordFocus || regPassword ? "active" : ""}>
              Password
            </label>
          </div>

          <div className="input-container">
            <input
              ref={regConfirmPasswordRef}
              className={`login-input ${regConfirmPasswordFormError ? "login-input-error" : ""}`}
              type="password"
              value={regConfirmPassword}
              onFocus={() => {
                setRegConfirmPasswordFocus(true);
                setRegConfirmPasswordFormError(false);
              }}
              onBlur={() => setRegConfirmPasswordFocus(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                  e.preventDefault();
                  registerButtonRef.current?.focus();
                }
              }}
              onChange={(e) => setRegConfirmPassword(e.target.value)}
            />
            <label
              className={
                regConfirmPasswordFocus || regConfirmPassword ? "active" : ""
              }
            >
              Confirm Password
            </label>
          </div>

          <div className="login-actions">
            <div className="login-options">
              <p onClick={showLoginScreen}>
                Already have an account? <span>Login</span>
              </p>
            </div>

            <button ref={registerButtonRef} className="login-button" type="submit">
              <div className="background"></div>
              <span className="text">Register</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default QRegister;