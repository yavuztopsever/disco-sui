import { BaseAgent } from './BaseAgent';
import { Tool, TaskResult, Note } from '@/types';
import { HfInference } from '@huggingface/inference';
import * as fs from 'fs/promises';
import * as path from 'path';
import matter from 'gray-matter';

interface VaultAnalysisParams {
  type: 'relationships' | 'topics' | 'clusters' | 'timeline' | 'stats';
  scope?: string[];
  depth?: number;
  includeArchived?: boolean;
}

interface NoteRelationship {
  source: string;
  target: string;
  type: 'link' | 'backlink' | 'tag' | 'mention' | 'similar';
  strength: number;
}

interface VaultAnalysis {
  relationships?: NoteRelationship[];
  topics?: Array<{
    name: string;
    notes: string[];
    relevance: number;
  }>;
  clusters?: Array<{
    name: string;
    notes: string[];
    centroid: string;
  }>;
  timeline?: Array<{
    date: Date;
    notes: string[];
    events: string[];
  }>;
  stats?: {
    totalNotes: number;
    totalTags: number;
    totalLinks: number;
    avgLinksPerNote: number;
    topTags: Array<{ tag: string; count: number }>;
    mostLinkedNotes: Array<{ note: string; links: number }>;
  };
}

class VaultAnalysisTool implements Tool {
  name = 'vault_analysis';
  description = 'Analyzes vault content and relationships';
  private hf: HfInference;
  private vaultPath: string;

  constructor(vaultPath: string, hfToken?: string) {
    this.vaultPath = vaultPath;
    this.hf = new HfInference(hfToken);
  }

  async execute(params: VaultAnalysisParams): Promise<VaultAnalysis> {
    try {
      const notes = await this.loadNotes(params.scope, params.includeArchived);

      switch (params.type) {
        case 'relationships':
          return {
            relationships: await this.analyzeRelationships(notes, params.depth)
          };
        case 'topics':
          return {
            topics: await this.analyzeTopics(notes)
          };
        case 'clusters':
          return {
            clusters: await this.analyzeClusters(notes)
          };
        case 'timeline':
          return {
            timeline: await this.analyzeTimeline(notes)
          };
        case 'stats':
          return {
            stats: await this.analyzeStats(notes)
          };
        default:
          throw new Error('Invalid analysis type');
      }
    } catch (error) {
      throw new Error(`Failed to analyze vault: ${error}`);
    }
  }

  private async loadNotes(scope?: string[], includeArchived = false): Promise<Note[]> {
    const notes: Note[] = [];
    const files = await this.getAllMarkdownFiles(this.vaultPath);

    for (const file of files) {
      if (!includeArchived && file.includes('archive')) continue;
      if (scope && !scope.some(s => file.includes(s))) continue;

      const content = await fs.readFile(file, 'utf-8');
      const { data: frontmatter, content: noteContent } = matter(content);

      notes.push({
        path: file,
        title: frontmatter.title || path.basename(file, '.md'),
        content: noteContent,
        frontmatter,
        tags: frontmatter.tags || [],
        created: new Date(frontmatter.created || Date.now()),
        modified: new Date(frontmatter.modified || Date.now())
      });
    }

    return notes;
  }

  private async analyzeRelationships(notes: Note[], depth = 1): Promise<NoteRelationship[]> {
    const relationships: NoteRelationship[] = [];

    // Analyze direct links
    for (const note of notes) {
      const links = this.extractLinks(note.content);
      for (const link of links) {
        relationships.push({
          source: note.path,
          target: link,
          type: 'link',
          strength: 1
        });
      }
    }

    // Analyze tag relationships
    const tagGroups = new Map<string, string[]>();
    for (const note of notes) {
      for (const tag of note.tags) {
        const notes = tagGroups.get(tag) || [];
        notes.push(note.path);
        tagGroups.set(tag, notes);
      }
    }

    for (const [tag, taggedNotes] of tagGroups) {
      for (let i = 0; i < taggedNotes.length; i++) {
        for (let j = i + 1; j < taggedNotes.length; j++) {
          relationships.push({
            source: taggedNotes[i],
            target: taggedNotes[j],
            type: 'tag',
            strength: 0.5
          });
        }
      }
    }

    // Analyze semantic similarity if depth > 1
    if (depth > 1) {
      for (let i = 0; i < notes.length; i++) {
        for (let j = i + 1; j < notes.length; j++) {
          const similarity = await this.calculateSimilarity(notes[i], notes[j]);
          if (similarity > 0.7) {
            relationships.push({
              source: notes[i].path,
              target: notes[j].path,
              type: 'similar',
              strength: similarity
            });
          }
        }
      }
    }

    return relationships;
  }

  private async analyzeTopics(notes: Note[]): Promise<Array<{ name: string; notes: string[]; relevance: number }>> {
    // Use HuggingFace for topic modeling
    const topics: Array<{ name: string; notes: string[]; relevance: number }> = [];
    const combinedContent = notes.map(n => n.content).join('\n\n');

    try {
      const response = await this.hf.textGeneration({
        model: 'gpt2',
        inputs: `Extract main topics from:\n\n${combinedContent}`,
        parameters: {
          max_length: 200,
          temperature: 0.7
        }
      });

      // In a real implementation, you'd want to parse the response more intelligently
      return topics;
    } catch (error) {
      console.warn('Failed to analyze topics:', error);
      return topics;
    }
  }

  private async analyzeClusters(notes: Note[]): Promise<Array<{ name: string; notes: string[]; centroid: string }>> {
    // Implement clustering logic
    return [];
  }

  private async analyzeTimeline(notes: Note[]): Promise<Array<{ date: Date; notes: string[]; events: string[] }>> {
    const timeline: Array<{ date: Date; notes: string[]; events: string[] }> = [];
    const notesByDate = new Map<string, { notes: string[]; events: string[] }>();

    for (const note of notes) {
      const date = note.created.toISOString().split('T')[0];
      const existing = notesByDate.get(date) || { notes: [], events: [] };
      existing.notes.push(note.path);

      // Extract events from content
      const events = await this.extractEvents(note.content);
      existing.events.push(...events);

      notesByDate.set(date, existing);
    }

    for (const [date, data] of notesByDate) {
      timeline.push({
        date: new Date(date),
        notes: data.notes,
        events: data.events
      });
    }

    return timeline.sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  private async analyzeStats(notes: Note[]): Promise<VaultAnalysis['stats']> {
    const tagCounts = new Map<string, number>();
    const noteLinkCounts = new Map<string, number>();
    let totalLinks = 0;

    for (const note of notes) {
      // Count tags
      for (const tag of note.tags) {
        tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
      }

      // Count links
      const links = this.extractLinks(note.content);
      noteLinkCounts.set(note.path, links.length);
      totalLinks += links.length;
    }

    return {
      totalNotes: notes.length,
      totalTags: tagCounts.size,
      totalLinks,
      avgLinksPerNote: totalLinks / notes.length,
      topTags: Array.from(tagCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([tag, count]) => ({ tag, count })),
      mostLinkedNotes: Array.from(noteLinkCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([note, links]) => ({ note, links }))
    };
  }

  private extractLinks(content: string): string[] {
    const wikiLinkRegex = /\[\[([^\]]+)\]\]/g;
    const matches = content.match(wikiLinkRegex) || [];
    return matches.map(match => match.slice(2, -2));
  }

  private async calculateSimilarity(note1: Note, note2: Note): Promise<number> {
    try {
      const response = await this.hf.textGeneration({
        model: 'gpt2',
        inputs: `Calculate similarity between:\n\n1: ${note1.content}\n\n2: ${note2.content}`,
        parameters: {
          max_length: 50,
          temperature: 0.7
        }
      });

      // In a real implementation, you'd want to parse the response more intelligently
      return 0.5;
    } catch (error) {
      console.warn('Failed to calculate similarity:', error);
      return 0;
    }
  }

  private async extractEvents(content: string): Promise<string[]> {
    try {
      const response = await this.hf.textGeneration({
        model: 'gpt2',
        inputs: `Extract events from:\n\n${content}`,
        parameters: {
          max_length: 100,
          temperature: 0.7
        }
      });

      // In a real implementation, you'd want to parse the response more intelligently
      return [];
    } catch (error) {
      console.warn('Failed to extract events:', error);
      return [];
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
}

export class VaultAnalysisAgent extends BaseAgent {
  constructor(vaultPath: string, hfToken?: string) {
    const tools = [new VaultAnalysisTool(vaultPath, hfToken)];

    super(
      'vault_analysis',
      'Vault Analysis Agent',
      'Analyzes vault content, relationships, and patterns',
      tools,
      hfToken
    );
  }

  async analyzeVault(params: VaultAnalysisParams): Promise<TaskResult> {
    try {
      const analysisTool = this.tools.find(
        tool => tool.name === 'vault_analysis'
      );
      if (!analysisTool) {
        throw new Error('Vault analysis tool not found');
      }

      const result = await analysisTool.execute(params);

      return {
        success: true,
        message: 'Vault analysis completed successfully',
        data: result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to analyze vault',
        error: error as Error
      };
    }
  }

  async execute(task: string): Promise<TaskResult> {
    try {
      // Extract parameters from the task description
      const params = await this.extractAnalysisParams(task);
      return this.analyzeVault(params);
    } catch (error) {
      return {
        success: false,
        message: 'Failed to execute task',
        error: error as Error
      };
    }
  }

  private async extractAnalysisParams(task: string): Promise<VaultAnalysisParams> {
    const taskLower = task.toLowerCase();
    let type: VaultAnalysisParams['type'] = 'stats';
    let depth = 1;
    let includeArchived = false;

    if (taskLower.includes('relationship')) {
      type = 'relationships';
    } else if (taskLower.includes('topic')) {
      type = 'topics';
    } else if (taskLower.includes('cluster')) {
      type = 'clusters';
    } else if (taskLower.includes('timeline')) {
      type = 'timeline';
    }

    if (taskLower.includes('deep') || taskLower.includes('detailed')) {
      depth = 2;
    }

    if (taskLower.includes('archive')) {
      includeArchived = true;
    }

    // Use HuggingFace inference to extract parameters from the task description
    const response = await this.hf.textGeneration({
      model: 'gpt2',
      inputs: `Extract vault analysis parameters from: ${task}`,
      parameters: {
        max_length: 100,
        temperature: 0.7
      }
    });

    // For now, return basic parameters
    // In a real implementation, you'd want to parse the response more intelligently
    return {
      type,
      depth,
      includeArchived
    };
  }
} 