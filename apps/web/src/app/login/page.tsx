"use client";

import { useMutation } from "@tanstack/react-query";
import { type SyntheticEvent, useState } from "react";

import { AppShell } from "@components/AppShell";
import { AuthPageSection } from "@components/pages/auth/AuthPageSection";
import { LoginFields } from "@components/pages/auth/LoginFields";
import { api, setToken } from "@lib/api";

export default function LoginPage() {
  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      return api.auth.login({ email_or_username: emailOrUsername, password });
    },
    onSuccess: (data) => {
      setToken(data.access_token);
      setMessage("Signed in");
    },
  });

  function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <AppShell>
      <AuthPageSection
        errorMessage={mutation.error?.message}
        isSubmitting={mutation.isPending}
        message={message}
        onSubmit={submit}
        submitLabel="Sign in"
        title="Login"
      >
        <LoginFields
          emailOrUsername={emailOrUsername}
          onEmailOrUsernameChange={setEmailOrUsername}
          onPasswordChange={setPassword}
          password={password}
        />
      </AuthPageSection>
    </AppShell>
  );
}
