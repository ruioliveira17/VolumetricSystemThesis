import React from "react";
import { useEffect, useRef, useState } from "react";
import "./QLogin.css";
import "../QUser/QUser.css";
import CloseIcon from '@assets/icons/close.svg?react';

interface QChangePasswordModalProps {
  message: {
    type: string;
    text: string;
  }[];

  closeChangePasswordModal: () => void;

  changeUsername: string;
  changeCurrentPassword: string;
  changePassword: string;
  changeConfirmPassword: string;

  setChangeCurrentPassword: (value: string) => void;
  setChangePassword: (value: string) => void;
  setChangeConfirmPassword: (value: string) => void;

  changeCurrentPasswordFormError: boolean;
  changePasswordFormError: boolean;
  changeConfirmPasswordFormError: boolean;

  setChangeCurrentPasswordFormError: (value: boolean) => void;
  setChangePasswordFormError: (value: boolean) => void;
  setChangeConfirmPasswordFormError: (value: boolean) => void;

  changeCurrentPasswordFocus: boolean;
  changePasswordFocus: boolean;
  changeConfirmPasswordFocus: boolean;

  setChangeCurrentPasswordFocus: (value: boolean) => void;
  setChangePasswordFocus: (value: boolean) => void;
  setChangeConfirmPasswordFocus: (value: boolean) => void;

  confirmChangePassword: () => void;
  showLoginScreen: () => void;
}

function QChangePasswordModal({
  message,
  closeChangePasswordModal,
  changeUsername,
  changeCurrentPassword,
  changePassword,
  changeConfirmPassword,
  setChangeCurrentPassword,
  setChangePassword,
  setChangeConfirmPassword,
  changeCurrentPasswordFormError,
  changePasswordFormError,
  changeConfirmPasswordFormError,
  setChangeCurrentPasswordFormError,
  setChangePasswordFormError,
  setChangeConfirmPasswordFormError,
  changeCurrentPasswordFocus,
  changePasswordFocus,
  changeConfirmPasswordFocus,
  setChangeCurrentPasswordFocus,
  setChangePasswordFocus,
  setChangeConfirmPasswordFocus,
  confirmChangePassword,
  showLoginScreen,
}: QChangePasswordModalProps) {
  const changeUsernameRef = useRef<HTMLInputElement>(null);
  const changeCurrentPasswordRef = useRef<HTMLInputElement>(null);
  const changePasswordRef = useRef<HTMLInputElement>(null);
  const changeConfirmPasswordRef = useRef<HTMLInputElement>(null);
  const changeButtonRef = useRef<HTMLButtonElement | null>(null);
  return (
    <div>
        <div className="darker-popup"/>

        <div className="changePassword-panel">
        
            <div className="login-panel-title">Redefine Password</div>

            <div className="changePassword-close-button">
                <CloseIcon onClick={closeChangePasswordModal}/>
            </div>

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
                        ref={changeCurrentPasswordRef}
                        className={`login-input ${changeCurrentPasswordFormError ? "login-input-error" : ""}`}
                        type="password"
                        value={changeCurrentPassword}
                        onFocus={() => {
                            setChangeCurrentPasswordFocus(true)
                            setChangeCurrentPasswordFormError(false);
                        }}
                        onBlur={() => setChangeCurrentPasswordFocus(false)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                            e.currentTarget.blur();
                            e.preventDefault();
                            changePasswordRef.current?.focus();
                            }
                        }}
                        onChange={(e) => setChangeCurrentPassword(e.target.value)}
                    />
                    <label className={changeCurrentPasswordFocus || changeCurrentPassword ? "active" : ""}>
                        Current Password
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
                        New Password
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
                        Confirm New Password
                    </label>
                </div>

                <div className="changePassword-actions">
                    <button ref={changeButtonRef} className="confirmChangePassword-button" type="submit">
                        <div className="background"></div>
                        <span className="text">Confirm</span>
                    </button>
                </div>
            </form>
        </div>

    </div>
  );
};

export default QChangePasswordModal;