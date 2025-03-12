import { Tool } from '@/types';
import * as fs from 'fs/promises';
import * as path from 'path';
import matter from 'gray-matter';

interface NoteUpdateParams {
  notePath: string;
  title?: string;
  content?: string;
  tags?: string[];
  frontmatter?: Record<string, any>;
}

export class NoteUpdateTool implements Tool {
  name = 'note_update';
  description = 'Updates existing notes in the vault';
  private vaultPath: string;

  constructor(vaultPath: string) {
    this.vaultPath = vaultPath;
  }

  async execute(params: NoteUpdateParams): Promise<any> {
    try {
      const fullPath = path.join(this.vaultPath, params.notePath);
      
      // Read existing note
      const content = await fs.readFile(fullPath, 'utf-8');
      const { data: existingFrontmatter, content: existingContent } = matter(content);

      // Update frontmatter
      const updatedFrontmatter = {
        ...existingFrontmatter,
        ...params.frontmatter,
        title: params.title || existingFrontmatter.title,
        tags: params.tags || existingFrontmatter.tags,
        modified: new Date().toISOString()
      };

      // Update content
      const updatedContent = params.content || existingContent;

      // Write updated note
      await fs.writeFile(
        fullPath,
        matter.stringify(updatedContent, updatedFrontmatter),
        'utf-8'
      );

      return {
        path: params.notePath,
        title: updatedFrontmatter.title,
        content: updatedContent,
        frontmatter: updatedFrontmatter
      };
    } catch (error) {
      throw new Error(`Failed to update note: ${error}`);
    }
  }
} 