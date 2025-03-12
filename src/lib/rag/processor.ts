import { readFile, readdir } from 'fs/promises';
import { join, extname } from 'path';
import { VaultDocument } from '@/types/vault';

export class RAGProcessor {
  private vaultPath: string;
  private supportedExtensions = ['.md', '.mdx', '.txt'];

  constructor(vaultPath: string) {
    this.vaultPath = vaultPath;
  }

  async processVault(): Promise<VaultDocument[]> {
    try {
      const documents: VaultDocument[] = [];
      const files = await this.getVaultFiles(this.vaultPath);

      for (const file of files) {
        const content = await readFile(file, 'utf-8');
        const doc = await this.processDocument(content, file);
        if (doc) {
          documents.push(doc);
        }
      }

      return documents;
    } catch (error) {
      console.error('Error processing vault:', error);
      throw new Error('Failed to process vault');
    }
  }

  private async getVaultFiles(dir: string): Promise<string[]> {
    const entries = await readdir(dir, { withFileTypes: true });
    const files: string[] = [];

    for (const entry of entries) {
      const fullPath = join(dir, entry.name);
      
      if (entry.isDirectory()) {
        files.push(...(await this.getVaultFiles(fullPath)));
      } else if (
        entry.isFile() &&
        this.supportedExtensions.includes(extname(entry.name).toLowerCase())
      ) {
        files.push(fullPath);
      }
    }

    return files;
  }

  private async processDocument(
    content: string,
    filePath: string
  ): Promise<VaultDocument | null> {
    try {
      // Extract metadata from frontmatter if present
      const metadata = this.extractFrontmatter(content);
      const cleanContent = this.removeFrontmatter(content);

      return {
        id: Buffer.from(filePath).toString('base64'),
        title: this.extractTitle(cleanContent, filePath),
        content: cleanContent,
        metadata,
      };
    } catch (error) {
      console.error(`Error processing document ${filePath}:`, error);
      return null;
    }
  }

  private extractFrontmatter(content: string): Record<string, unknown> {
    const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
    const match = content.match(frontmatterRegex);
    
    if (!match) return {};

    try {
      const frontmatter = match[1];
      const metadata: Record<string, unknown> = {};
      
      frontmatter.split('\n').forEach(line => {
        const [key, ...values] = line.split(':');
        if (key && values.length > 0) {
          metadata[key.trim()] = values.join(':').trim();
        }
      });

      return metadata;
    } catch {
      return {};
    }
  }

  private removeFrontmatter(content: string): string {
    return content.replace(/^---\n[\s\S]*?\n---\n/, '').trim();
  }

  private extractTitle(content: string, filePath: string): string {
    // Try to extract title from first heading
    const headingMatch = content.match(/^#\s+(.+)$/m);
    if (headingMatch) {
      return headingMatch[1].trim();
    }

    // Fallback to filename without extension
    const fileName = filePath.split('/').pop() || '';
    return fileName.replace(/\.[^/.]+$/, '');
  }
} 