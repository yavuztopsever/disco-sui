import { Tool, Note } from '@/types';
import * as fs from 'fs/promises';
import * as path from 'path';
import matter from 'gray-matter';

interface NoteMoveParams {
  sourcePath: string;
  destinationPath: string;
  newTitle?: string;
  updateLinks?: boolean;
}

export class NoteMoveAndRenameTool implements Tool {
  name = 'note_move';
  description = 'Moves and renames notes in the Obsidian vault';
  private vaultPath: string;

  constructor(vaultPath: string) {
    this.vaultPath = vaultPath;
  }

  async execute(params: NoteMoveParams): Promise<Note> {
    try {
      const { sourcePath, destinationPath, newTitle, updateLinks = true } = params;
      const sourceFullPath = path.join(this.vaultPath, sourcePath);
      const destFullPath = path.join(this.vaultPath, destinationPath);

      // Read source note
      const content = await fs.readFile(sourceFullPath, 'utf-8');
      const { data: frontmatter, content: noteContent } = matter(content);

      // Update frontmatter
      const updatedFrontmatter = {
        ...frontmatter,
        title: newTitle || frontmatter.title,
        modified: new Date().toISOString()
      };

      // Create destination directory if it doesn't exist
      await fs.mkdir(path.dirname(destFullPath), { recursive: true });

      // Write note to new location
      const updatedContent = matter.stringify(noteContent, updatedFrontmatter);
      await fs.writeFile(destFullPath, updatedContent, 'utf-8');

      // Delete source file
      await fs.unlink(sourceFullPath);

      // Update links in other notes if requested
      if (updateLinks) {
        await this.updateLinksInVault(sourcePath, destinationPath);
      }

      return {
        path: destFullPath,
        title: updatedFrontmatter.title,
        content: noteContent,
        frontmatter: updatedFrontmatter,
        tags: updatedFrontmatter.tags || [],
        created: new Date(frontmatter.created),
        modified: new Date(updatedFrontmatter.modified)
      };
    } catch (error) {
      throw new Error(`Failed to move note: ${error}`);
    }
  }

  private async updateLinksInVault(oldPath: string, newPath: string): Promise<void> {
    try {
      const files = await this.getAllMarkdownFiles(this.vaultPath);
      const oldLink = this.pathToWikiLink(oldPath);
      const newLink = this.pathToWikiLink(newPath);

      for (const file of files) {
        const content = await fs.readFile(file, 'utf-8');
        const updatedContent = content.replace(
          new RegExp(`\\[\\[${oldLink}(\\|[^\\]]*)?\\]\\]`, 'g'),
          `[[${newLink}$1]]`
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