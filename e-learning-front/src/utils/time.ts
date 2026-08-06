/**
 * Format seconds to MM:SS (sans crochets), pour indicateurs de progression.
 */
export function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Format seconds to [MM:SS] timecode string
 */
export function formatTimecode(seconds: number): string {
  return `[${formatTime(seconds)}]`;
}

/**
 * Parse [MM:SS] timecode string to seconds
 */
export function parseTimecode(timecode: string): number {
  const match = timecode.match(/\[(\d+):(\d+)\]/);
  if (!match) {
    return 0;
  }
  const minutes = Number.parseInt(match[1], 10);
  const seconds = Number.parseInt(match[2], 10);
  return minutes * 60 + seconds;
}
