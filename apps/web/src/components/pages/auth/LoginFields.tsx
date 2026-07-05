"use client";

type LoginFieldsProps = {
  emailOrUsername: string;
  password: string;
  onEmailOrUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
};

export function LoginFields({
  emailOrUsername,
  password,
  onEmailOrUsernameChange,
  onPasswordChange,
}: LoginFieldsProps) {
  return (
    <>
      <input
        className="field"
        onChange={(event) => onEmailOrUsernameChange(event.target.value)}
        placeholder="Email or username"
        value={emailOrUsername}
      />
      <input
        className="field"
        onChange={(event) => onPasswordChange(event.target.value)}
        placeholder="Password"
        type="password"
        value={password}
      />
    </>
  );
}
