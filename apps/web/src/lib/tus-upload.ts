// Upload TUS minimal (protocole 1.0.0) vers Bunny Stream, sans dépendance.
// L'API Neyla fournit une signature temporaire : la vidéo part directement du
// navigateur vers Bunny, sans transiter par nos serveurs.

export type BunnyUpload = {
  endpoint: string;
  library_id: string;
  video_id: string;
  expires: number;
  signature: string;
};

const CHUNK_SIZE = 5 * 1024 * 1024;

function b64(value: string): string {
  return btoa(unescape(encodeURIComponent(value)));
}

export async function tusUpload(
  file: File,
  params: BunnyUpload,
  title: string,
  onProgress: (fraction: number) => void,
  signal?: AbortSignal,
): Promise<void> {
  const auth = {
    AuthorizationSignature: params.signature,
    AuthorizationExpire: String(params.expires),
    VideoId: params.video_id,
    LibraryId: String(params.library_id),
  };
  const create = await fetch(params.endpoint, {
    method: "POST",
    signal,
    headers: {
      ...auth,
      "Tus-Resumable": "1.0.0",
      "Upload-Length": String(file.size),
      "Upload-Metadata": `filetype ${b64(file.type || "video/mp4")},title ${b64(title)}`,
    },
  });
  if (!create.ok) throw new Error(`TUS create ${create.status}`);
  const location = create.headers.get("Location");
  if (!location) throw new Error("TUS: Location manquante");
  const uploadUrl = new URL(location, params.endpoint).toString();

  let offset = 0;
  while (offset < file.size) {
    const chunk = file.slice(offset, Math.min(offset + CHUNK_SIZE, file.size));
    const res = await fetch(uploadUrl, {
      method: "PATCH",
      signal,
      headers: {
        ...auth,
        "Tus-Resumable": "1.0.0",
        "Upload-Offset": String(offset),
        "Content-Type": "application/offset+octet-stream",
      },
      body: chunk,
    });
    if (!res.ok) throw new Error(`TUS patch ${res.status}`);
    const next = Number(res.headers.get("Upload-Offset"));
    offset = Number.isFinite(next) && next > offset ? next : offset + chunk.size;
    onProgress(Math.min(1, offset / file.size));
  }
}

/** Durée (s) d'un fichier vidéo local, lue via un <video> hors DOM. */
export function videoDuration(file: File): Promise<number> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(video.duration || 0);
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(0);
    };
    video.src = url;
  });
}
