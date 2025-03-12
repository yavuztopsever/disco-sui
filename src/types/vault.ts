export interface VaultDocument {
  id: string;
  title: string;
  content: string;
  metadata: Record<string, unknown>;
} 