import type { Clip, JobHistory, JobStatus, ProcessOptions, ReviewRequest, Statistics, UploadedVideo, VehicleTrack, Video } from "../types/api";
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(BASE_URL + path, init);
  if (!response.ok) { const body = await response.json().catch(() => null); throw new Error(body?.detail ?? "Request failed (" + response.status + ")"); }
  return response.json() as Promise<T>;
}
export const api = {
  uploadVideo: (file: File) => { const data = new FormData(); data.append("file", file); return request<UploadedVideo>("/videos", { method: "POST", body: data }); },
  getVideo: (id: string) => request<Video>("/videos/" + id),
  startProcessing: (id: string, options: ProcessOptions) => request<JobStatus>("/videos/" + id + "/process", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(options) }),
  getJob: (id: string) => request<JobStatus>("/jobs/" + id),
  getHistory: () => request<JobHistory[]>("/history/jobs"),
  getStatistics: () => request<Statistics>("/statistics"),
  getTracks: (id: string) => request<VehicleTrack[]>("/videos/" + id + "/tracks"),
  getClips: (id: string) => request<Clip[]>("/videos/" + id + "/clips"),
  reviewClip: (id: string, body: ReviewRequest) => request<Clip>("/clips/" + id + "/review", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
  fileUrl: (path: string) => "/storage/" + path,
};
