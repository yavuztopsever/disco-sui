import { Tool } from '@/types';
import * as fs from 'fs/promises';
import * as path from 'path';

interface NoteDeletionParams {
  notePath: string;
}

export class NoteDeletionTool implements Tool {
  name = 'note_deletion';
  description = 'Deletes notes from the vault';
  private vaultPath: string;

  constructor(vaultPath: string) {
    this.vaultPath = vaultPath;
  }

  async execute(params: NoteDeletionParams): Promise<any> {
    try {
      const fullPath = path.join(this.vaultPath, params.notePath);
      
      // Check if file exists
      await fs.access(fullPath);
      
      // Delete the file
      await fs.unlink(fullPath);

      return {
        success: true,
        deletedPath: params.notePath
      };
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new Error(`Note not found: ${params.notePath}`);
      }
      throw new Error(`Failed to delete note: ${error}`);
    }
  }
} 