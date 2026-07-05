"use client";

import { type ReactNode, type SyntheticEvent } from "react";

type AuthPageSectionProps = {
  title: string;
  children: ReactNode;
  onSubmit: (event: SyntheticEvent<HTMLFormElement>) => void;
  submitLabel: string;
  message: string;
  errorMessage?: string;
  isSubmitting: boolean;
};

export function AuthPageSection({
  title,
  children,
  onSubmit,
  submitLabel,
  message,
  errorMessage,
  isSubmitting,
}: AuthPageSectionProps) {
  return (
    <section className="max-w-xl space-y-6">
      <h1 className="text-3xl font-semibold">{title}</h1>
      <form className="space-y-4" onSubmit={onSubmit}>
        {children}
        <button className="button-primary" disabled={isSubmitting} type="submit">
          {submitLabel}
        </button>
      </form>
      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      {errorMessage ? <p className="text-sm text-red-300">{errorMessage}</p> : null}
    </section>
  );
}
