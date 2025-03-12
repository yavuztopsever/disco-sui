export interface VaultConfig {
  path: string;
  templates: string[];
  defaultTemplate?: string;
}

export interface Note {
  path: string;
  title: string;
  content: string;
  frontmatter: Record<string, any>;
  tags: string[];
  created: Date;
  modified: Date;
}

export interface Tool {
  name: string;
  description: string;
  execute: (args: any) => Promise<any>;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  tools: Tool[];
  execute: (task: string) => Promise<any>;
}

export interface TaskResult {
  success: boolean;
  message: string;
  data?: any;
  error?: Error;
}

export interface FileUploadLog {
  fileName: string;
  uploadTime: Date;
  fileType: string;
  fileSize: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    fileUpload?: FileUploadLog;
    [key: string]: any;
  };
}

export interface VaultStats {
  totalNotes: number;
  totalTags: number;
  totalFolders: number;
  lastModified: Date;
}

export interface SearchResult {
  note: Note;
  relevance: number;
  matches: string[];
}

export type TaskType = 
  | 'create_note'
  | 'update_note'
  | 'delete_note'
  | 'move_note'
  | 'tag_management'
  | 'folder_operation'
  | 'generate_content'
  | 'process_audio'
  | 'process_email'
  | 'index_vault'
  | 'analyze_relationships'
  | 'reorganize_vault'
  | 'bulk_update';

export interface Task {
  type: TaskType;
  description: string;
  params: Record<string, any>;
  priority?: number;
  deadline?: Date;
}

export interface AgentConfig {
  vaultPath: string;
  hfToken?: string;
  allowedFileTypes?: string[];
  maxFileSize?: number; // in bytes
} 