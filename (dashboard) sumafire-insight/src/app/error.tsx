"use client";
import { Button } from "@/components/ui/button";
export default function Error({ reset }: { reset: () => void }) {
  return (
    <main className="error-page">
      <h1>The workspace could not load.</h1>
      <p>
        Your original research files are unaffected. Retry or inspect the local
        server log.
      </p>
      <Button onClick={reset}>Try again</Button>
    </main>
  );
}
