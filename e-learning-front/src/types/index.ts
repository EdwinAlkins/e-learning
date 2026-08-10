export interface Formation {
  id: string;
  name: string;
  slug?: string;
  chapters: Chapter[];
}

export interface Document {
  id: string;
  title: string;
  position: number;
  filename: string;
  mime_type?: string | null;
  video_id?: string | null;
}

export interface Chapter {
  id: string;
  name: string;
  slug?: string;
  position?: number;
  videos: Video[];
  documents?: Document[];
}

export interface BackgroundJob {
  id: string;
  kind: 'media_conversion' | 'transcription' | 'summary' | 'rag_index_video' | 'rag_index_formation' | string;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled' | string;
  progress: number;
  message?: string;
}

export interface Video {
  id: string;
  title: string;
  duration: number;
  /** Ordre API (ChapterResponse / VideoResponse). */
  position?: number;
  /** Alias UI dérivé de `position` pour le tri local. */
  sortOrder?: number;
  kind?: 'video' | 'audio';
  processing_status?: 'ready' | 'processing' | 'failed';
  transcription_status?: 'none' | 'processing' | 'ready' | 'failed';
  summary_status?: 'none' | 'processing' | 'ready' | 'failed';
  active_jobs?: BackgroundJob[];
}

export interface CatalogResponse {
  formations: Formation[];
}

export interface MoveVideoRequest {
  position?: number | null;
  after_video_id?: string | null;
}

export interface PatchFormationPayload {
  name?: string;
}

export interface PatchChapterPayload {
  name?: string;
}

export interface PatchVideoPayload {
  title?: string;
  file?: File;
}

export interface Note {
  id: string;
  video_id: string;
  timecode: number;
  content: string;
  created_at: string;
}

export interface ProgressResponse {
  last_position: number;
}

export interface FormationsProgressResponse {
  progress: Record<string, FormationProgress>;
}

export interface AuthResponse {
  uid: string;
}

export interface VideoProgress {
  id: string;
  title: string;
  progress_percentage: number;
}

export interface ChapterProgress {
  name: string;
  videos: VideoProgress[];
  progress_percentage: number;
}

export interface FormationProgress {
  name: string;
  chapters: ChapterProgress[];
  progress_percentage: number;
}

export interface RagCitation {
  video_id?: string | null;
  document_id?: string | null;
  title: string;
  source: string;
  excerpt: string;
}

export interface AskFormationResponse {
  answer: string;
  citations: RagCitation[];
}
