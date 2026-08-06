import type { BackgroundJob, Video } from '../types';

/** Retrouve le job actif du kind donné (queued/running). */
export function findActiveJob(video: Video, kind: string): BackgroundJob | undefined {
  return (video.active_jobs ?? []).find(
    (job) =>
      job.kind === kind && (job.status === 'queued' || job.status === 'running')
  );
}

export function jobProgressLabel(job: BackgroundJob | undefined, fallback: string): string {
  if (!job) return fallback;
  const pct = Math.max(0, Math.min(100, job.progress ?? 0));
  return `${fallback} ${pct}%`;
}
