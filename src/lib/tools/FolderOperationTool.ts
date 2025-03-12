import { Tool } from '@/types';
import * as fs from 'fs/promises';
import * as path from 'path';

interface FolderOperation {
  type: 'create' | 'delete' | 'rename' | 'move';
  sourcePath: string;
  destinationPath?: string;
}

interface FolderStats {
  path: string;
  noteCount: number;
  subfolderCount: number;
}

export class FolderOperationTool implements Tool {
  name = 'folder_operation';
  description = 'Manages folders in the Obsidian vault';
  private vaultPath: string;

  constructor(vaultPath: string) {
    this.vaultPath = vaultPath;
  }

  async execute(operation: FolderOperation): Promise<{ success: boolean; stats: FolderStats }> {
    try {
      switch (operation.type) {
        case 'create':
          return await this.createFolder(operation.sourcePath);
        case 'delete':
          return await this.deleteFolder(operation.sourcePath);
        case 'rename':
        case 'move':
          if (!operation.destinationPath) {
            throw new Error('Destination path is required for rename/move operation');
          }
          return await this.moveFolder(operation.sourcePath, operation.destinationPath);
        default:
          throw new Error('Invalid folder operation');
      }
    } catch (error) {
      throw new Error(`Failed to perform folder operation: ${error}`);
    }
  }

  private async createFolder(folderPath: string): Promise<{ success: boolean; stats: FolderStats }> {
    const fullPath = path.join(this.vaultPath, folderPath);
    await fs.mkdir(fullPath, { recursive: true });
    const stats = await this.getFolderStats(folderPath);

    return {
      success: true,
      stats
    };
  }

  private async deleteFolder(folderPath: string): Promise<{ success: boolean; stats: FolderStats }> {
    const fullPath = path.join(this.vaultPath, folderPath);
    const stats = await this.getFolderStats(folderPath);
    await fs.rm(fullPath, { recursive: true, force: true });

    return {
      success: true,
      stats
    };
  }

  private async moveFolder(sourcePath: string, destinationPath: string): Promise<{ success: boolean; stats: FolderStats }> {
    const sourceFullPath = path.join(this.vaultPath, sourcePath);
    const destFullPath = path.join(this.vaultPath, destinationPath);

    // Create destination parent directory if it doesn't exist
    await fs.mkdir(path.dirname(destFullPath), { recursive: true });

    // Move the folder
    await fs.rename(sourceFullPath, destFullPath);

    // Update links in all notes
    await this.updateLinksInVault(sourcePath, destinationPath);

    const stats = await this.getFolderStats(destinationPath);

    return {
      success: true,
      stats
    };
  }

  private async getFolderStats(folderPath: string): Promise<FolderStats> {
    const fullPath = path.join(this.vaultPath, folderPath);
    let noteCount = 0;
    let subfolderCount = 0;

    try {
      const entries = await fs.readdir(fullPath, { withFileTypes: true });

      for (const entry of entries) {
        if (entry.isDirectory()) {
          subfolderCount++;
          const subStats = await this.getFolderStats(path.join(folderPath, entry.name));
          noteCount += subStats.noteCount;
          subfolderCount += subStats.subfolderCount;
        } else if (entry.isFile() && /\.md$/i.test(entry.name)) {
          noteCount++;
        }
      }
    } catch (error) {
      // Folder might not exist yet
      console.warn(`Could not get stats for folder ${folderPath}:`, error);
    }

    return {
      path: folderPath,
      noteCount,
      subfolderCount
    };
  }

  private async updateLinksInVault(oldPath: string, newPath: string): Promise<void> {
    try {
      const allFiles = await this.getAllMarkdownFiles(this.vaultPath);
      const oldPathPattern = this.pathToWikiLink(oldPath);
      const newPathPattern = this.pathToWikiLink(newPath);

      for (const file of allFiles) {
        const content = await fs.readFile(file, 'utf-8');
        const updatedContent = content.replace(
          new RegExp(`\\[\\[${oldPathPattern}[^\\]]*\\]\\]`, 'g'),
          (match) => match.replace(oldPathPattern, newPathPattern)
        );

        if (content !== updatedContent) {
          await fs.writeFile(file, updatedContent, 'utf-8');
        }
      }
    } catch (error) {
      console.error('Error updating links:', error);
    }
  }

  private async getAllMarkdownFiles(dir: string): Promise<string[]> {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    const files: string[] = [];

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        files.push(...(await this.getAllMarkdownFiles(fullPath)));
      } else if (entry.isFile() && /\.md$/i.test(entry.name)) {
        files.push(fullPath);
      }
    }

    return files;
  }

  private pathToWikiLink(filePath: string): string {
    return filePath
      .replace(/\.md$/i, '')
      .split('/')
      .map(part => part.replace(/\s+/g, '_'))
      .join('/');
  }
} 