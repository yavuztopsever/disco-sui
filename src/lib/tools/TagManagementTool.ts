import { Tool } from '@/types';
import * as fs from 'fs/promises';
import * as path from 'path';
import matter from 'gray-matter';

interface TagOperation {
  type: 'add' | 'remove' | 'rename';
  tag: string;
  newTag?: string;
  notePaths?: string[];
}

interface TagStats {
  tag: string;
  count: number;
  notes: string[];
}

export class TagManagementTool implements Tool {
  name = 'tag_management';
  description = 'Manages tags across the Obsidian vault';
  private vaultPath: string;

  constructor(vaultPath: string) {
    this.vaultPath = vaultPath;
  }

  async execute(operation: TagOperation): Promise<{ success: boolean; stats: TagStats }> {
    try {
      switch (operation.type) {
        case 'add':
          return await this.addTag(operation.tag, operation.notePaths);
        case 'remove':
          return await this.removeTag(operation.tag, operation.notePaths);
        case 'rename':
          if (!operation.newTag) {
            throw new Error('New tag name is required for rename operation');
          }
          return await this.renameTag(operation.tag, operation.newTag);
        default:
          throw new Error('Invalid tag operation');
      }
    } catch (error) {
      throw new Error(`Failed to manage tags: ${error}`);
    }
  }

  private async addTag(tag: string, notePaths?: string[]): Promise<{ success: boolean; stats: TagStats }> {
    const files = notePaths || await this.getAllMarkdownFiles(this.vaultPath);
    const updatedNotes: string[] = [];

    for (const file of files) {
      const fullPath = path.join(this.vaultPath, file);
      const content = await fs.readFile(fullPath, 'utf-8');
      const { data: frontmatter, content: noteContent } = matter(content);

      const tags = new Set(frontmatter.tags || []);
      if (!tags.has(tag)) {
        tags.add(tag);
        const updatedFrontmatter = {
          ...frontmatter,
          tags: Array.from(tags),
          modified: new Date().toISOString()
        };
        await fs.writeFile(fullPath, matter.stringify(noteContent, updatedFrontmatter), 'utf-8');
        updatedNotes.push(file);
      }
    }

    return {
      success: true,
      stats: {
        tag,
        count: updatedNotes.length,
        notes: updatedNotes
      }
    };
  }

  private async removeTag(tag: string, notePaths?: string[]): Promise<{ success: boolean; stats: TagStats }> {
    const files = notePaths || await this.getAllMarkdownFiles(this.vaultPath);
    const updatedNotes: string[] = [];

    for (const file of files) {
      const fullPath = path.join(this.vaultPath, file);
      const content = await fs.readFile(fullPath, 'utf-8');
      const { data: frontmatter, content: noteContent } = matter(content);

      const tags = new Set(frontmatter.tags || []);
      if (tags.has(tag)) {
        tags.delete(tag);
        const updatedFrontmatter = {
          ...frontmatter,
          tags: Array.from(tags),
          modified: new Date().toISOString()
        };
        await fs.writeFile(fullPath, matter.stringify(noteContent, updatedFrontmatter), 'utf-8');
        updatedNotes.push(file);
      }
    }

    return {
      success: true,
      stats: {
        tag,
        count: updatedNotes.length,
        notes: updatedNotes
      }
    };
  }

  private async renameTag(oldTag: string, newTag: string): Promise<{ success: boolean; stats: TagStats }> {
    const files = await this.getAllMarkdownFiles(this.vaultPath);
    const updatedNotes: string[] = [];

    for (const file of files) {
      const fullPath = path.join(this.vaultPath, file);
      const content = await fs.readFile(fullPath, 'utf-8');
      const { data: frontmatter, content: noteContent } = matter(content);

      const tags = new Set(frontmatter.tags || []);
      if (tags.has(oldTag)) {
        tags.delete(oldTag);
        tags.add(newTag);
        const updatedFrontmatter = {
          ...frontmatter,
          tags: Array.from(tags),
          modified: new Date().toISOString()
        };
        await fs.writeFile(fullPath, matter.stringify(noteContent, updatedFrontmatter), 'utf-8');
        updatedNotes.push(file);
      }
    }

    return {
      success: true,
      stats: {
        tag: newTag,
        count: updatedNotes.length,
        notes: updatedNotes
      }
    };
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
} 