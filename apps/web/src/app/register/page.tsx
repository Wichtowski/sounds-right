"use client";

import { useMutation } from "@tanstack/react-query";
import { type SyntheticEvent, useState } from "react";

import { AppShell } from "@components/AppShell";
import { AuthPageSection } from "@components/pages/auth/AuthPageSection";
import { RegisterFields } from "@components/pages/auth/RegisterFields";
import { api, setToken } from "@lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      return api.auth.register({ email, username, password });
    },
    onSuccess: (data) => {
      setToken(data.access_token);
      setMessage("Registered and signed in");
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
        submitLabel="Create account"
        title="Register"
      >
        <RegisterFields
          email={email}
          onEmailChange={setEmail}
          onPasswordChange={setPassword}
          onUsernameChange={setUsername}
          password={password}
          username={username}
        />
      </AuthPageSection>
    </AppShell>
  );
}
