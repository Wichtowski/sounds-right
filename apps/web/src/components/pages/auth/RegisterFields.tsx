"use client";

type RegisterFieldsProps = {
  email: string;
  username: string;
  password: string;
  onEmailChange: (value: string) => void;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
};

export function RegisterFields({
  email,
  username,
  password,
  onEmailChange,
  onUsernameChange,
  onPasswordChange,
}: RegisterFieldsProps) {
  return (
    <>
      <input
        className="field"
        onChange={(event) => onEmailChange(event.target.value)}
        placeholder="Email"
        value={email}
      />
      <input
        className="field"
        onChange={(event) => onUsernameChange(event.target.value)}
        placeholder="Username"
        value={username}
      />
      <input
        className="field"
        minLength={8}
        onChange={(event) => onPasswordChange(event.target.value)}
        placeholder="Password"
        type="password"
        value={password}
      />
    </>
  );
}
