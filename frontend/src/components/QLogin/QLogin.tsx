import React from "react";
import { useEffect, useRef, useState } from "react";
import "./QLogin.css";

interface QLoginProps {
  message: {
    type: string;
    text: string;
  }[];

  username: string;
  setUsername: (value: string) => void;

  password: string;
  setPassword: (value: string) => void;

  usernameFormError: boolean;
  setUsernameFormError: (value: boolean) => void;

  passwordFormError: boolean;
  setPasswordFormError: (value: boolean) => void;

  usernameFocus: boolean;
  setUsernameFocus: (value: boolean) => void;

  passwordFocus: boolean;
  setPasswordFocus: (value: boolean) => void;

  login: () => void;
  showRegisterScreen: () => void;
}

function QLogin({
  message,
  username,
  setUsername,
  password,
  setPassword,
  usernameFormError,
  setUsernameFormError,
  passwordFormError,
  setPasswordFormError,
  usernameFocus,
  setUsernameFocus,
  passwordFocus,
  setPasswordFocus,
  login,
  showRegisterScreen
}: QLoginProps) {
  const usernameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const loginButtonRef = useRef<HTMLButtonElement | null>(null);
  return (
    <>
      <img src="/Qubic.svg" className="qubic-logo" alt="Qubic Logo"/> 

      <div className="login-panel-login">
        <div className="login-panel-title">
          Login
        </div>

        <div className="login-panel-error-or-info">
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
            login();
          }}
        >

          <div className="input-container">
            <input
              ref={usernameRef}
              className={`login-input ${usernameFormError ? "login-input-error" : ""}`}
              type="text"
              value={username}
              onFocus={() => {
                setUsernameFocus(true);
                setUsernameFormError(false);
              }}
              onBlur={() => setUsernameFocus(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                  e.preventDefault();
                  passwordRef.current?.focus();
                }
              }}
              onChange={(e) => setUsername(e.target.value)}
            />

            <label className={usernameFocus || username ? "active" : ""}>
              Username
            </label>
          </div>


          <div className="input-container">
            <input
              ref={passwordRef}
              className={`login-input ${passwordFormError ? "login-input-error" : ""}`}
              type="password"
              value={password}
              onFocus={() => {
                setPasswordFocus(true);
                setPasswordFormError(false);
              }}
              onBlur={() => setPasswordFocus(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.currentTarget.blur();
                  e.preventDefault();
                  loginButtonRef.current?.focus();
                }
              }}
              onChange={(e) => setPassword(e.target.value)}
            />

            <label className={passwordFocus || password ? "active" : ""}>
              Password
            </label>
          </div>


          <div className="login-actions">

            <div className="login-options">
              <p onClick={showRegisterScreen}>
                Don't have an account?{" "}
                <span>
                  Register
                </span>
              </p>
            </div>

            <button ref={loginButtonRef} className="login-button" type="submit">
              <div className="background"></div>
              <span className="text">
                Login
              </span>
            </button>

          </div>

        </form>
      </div>


      <div className="powered-by-panel-login">
        <div
          className="powered-by-text-login"
          translate="no"
        >
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

export default QLogin;