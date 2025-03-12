import { Tool, Note } from '@/types';
import * as fs from 'fs/promises';
import * as path from 'path';
import matter from 'gray-matter';

interface NoteCreationParams {
  title: string;
  content?: string;
  template?: string;
  tags?: string[];
  folder?: string;
  frontmatter?: Record<string, any>;
}

export class NoteCreationTool implements Tool {
  name = 'note_creation';
  description = 'Creates new notes in the Obsidian vault';
  private vaultPath: string;

  constructor(vaultPath: string) {
    this.vaultPath = vaultPath;
  }

  async execute(params: NoteCreationParams): Promise<Note> {
    try {
      const {
        title,
        content = '',
        template,
        tags = [],
        folder = '',
        frontmatter = {}
      } = params;

      // Create filename from title
      const filename = this.sanitizeFilename(title);
      const folderPath = path.join(this.vaultPath, folder);
      const filePath = path.join(folderPath, `${filename}.md`);

      // Ensure folder exists
      await fs.mkdir(folderPath, { recursive: true });

      // Load template if specified
      let noteContent = content;
      if (template) {
        const templatePath = path.join(this.vaultPath, '_templates', template);
        try {
          noteContent = await fs.readFile(templatePath, 'utf-8');
        } catch (error) {
          console.warn(`Template ${template} not found, using empty content`);
        }
      }

      // Prepare frontmatter
      const finalFrontmatter = {
        ...frontmatter,
        title,
        tags,
        created: new Date().toISOString(),
        modified: new Date().toISOString()
      };

      // Create note with frontmatter
      const noteWithFrontmatter = matter.stringify(noteContent, finalFrontmatter);
      await fs.writeFile(filePath, noteWithFrontmatter, 'utf-8');

      // Return created note
      return {
        path: filePath,
        title,
        content: noteContent,
        frontmatter: finalFrontmatter,
        tags,
        created: new Date(finalFrontmatter.created),
        modified: new Date(finalFrontmatter.modified)
      };
    } catch (error) {
      throw new Error(`Failed to create note: ${error}`);
    }
  }

  private sanitizeFilename(filename: string): string {
    return filename
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/(^-|-$)/g, '');
  }
} 