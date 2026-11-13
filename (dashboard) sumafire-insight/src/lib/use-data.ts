"use client";
import { useEffect, useState } from "react";
export function useData<T>(url: string | null, refresh = 0) {
  const [state, setState] = useState<{
    data: T | null;
    loading: boolean;
    error: string | null;
  }>({ data: null, loading: !!url, error: null });
  useEffect(() => {
    if (!url) return;
    const controller = new AbortController();
    queueMicrotask(() => {
      if (!controller.signal.aborted)
        setState((s) => ({ ...s, loading: true, error: null }));
    });
    fetch(url, { signal: controller.signal, cache: "no-store" })
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) throw Error(d.error || "Request failed");
        return d;
      })
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((e) => {
        if (e.name !== "AbortError")
          setState({ data: null, loading: false, error: e.message });
      });
    return () => controller.abort();
  }, [url, refresh]);
  return state;
}
