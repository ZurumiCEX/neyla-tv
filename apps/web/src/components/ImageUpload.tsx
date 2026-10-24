"use client";

import { useRef, useState } from "react";
import { Avatar } from "@/components/Avatar";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export function ImageUpload({
  label,
  currentUrl,
  uploadPath,
  onUploaded,
  variant = "image",
  name = "",
}: {
  label: string;
  currentUrl?: string;
  uploadPath: string;
  onUploaded: (url: string) => void;
  /** `avatar` : aperçu rond avec repli sur l'initiale. */
  variant?: "image" | "avatar";
  name?: string;
}) {
  const t = useT();
  const { authUpload } = useAuth();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await authUpload<{ url: string }>(uploadPath, fd);
      onUploaded(res.url);
    } catch (err) {
      const ex = err as { data?: { errors?: { file?: string | string[] }; detail?: string } };
      const fileErr = ex.data?.errors?.file;
      setError(
        (Array.isArray(fileErr) ? fileErr[0] : fileErr) ?? ex.data?.detail ?? t("upload.error"),
      );
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div>
      <p className="mb-1 text-xs uppercase tracking-wider text-neutral-500">{label}</p>
      <div className="flex items-center gap-3">
        {variant === "avatar" ? (
          <Avatar src={currentUrl} name={name} size={56} className="border border-neutral-800" />
        ) : currentUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={currentUrl}
            alt=""
            className="h-14 w-14 rounded-lg border border-neutral-800 object-cover"
          />
        ) : (
          <span className="flex h-14 w-14 items-center justify-center rounded-lg border border-dashed border-neutral-700 text-xs text-neutral-600">
            —
          </span>
        )}
        <button
          type="button"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
          className="rounded-lg border border-neutral-700 px-3 py-1.5 text-sm text-neutral-200 hover:border-secondary hover:text-secondary-light disabled:opacity-50"
        >
          {busy ? t("upload.sending") : t("upload.choose")}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={onPick}
          className="hidden"
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-300">{error}</p>}
    </div>
  );
}
