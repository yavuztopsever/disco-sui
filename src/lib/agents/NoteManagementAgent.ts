import { BaseAgent } from './BaseAgent';
import { NoteCreationTool } from '../tools/NoteCreationTool';
import { NoteUpdateTool } from '../tools/NoteUpdateTool';
import { NoteDeletionTool } from '../tools/NoteDeletionTool';
import { NoteMoveAndRenameTool } from '../tools/NoteMoveAndRenameTool';
import { TagManagementTool } from '../tools/TagManagementTool';
import { FolderOperationTool } from '../tools/FolderOperationTool';
import { TaskResult } from '@/types';

interface ExecuteOptions {
  uploadedFile?: {
    path: string;
    name: string;
    type: string;
  };
}

export class NoteManagementAgent extends BaseAgent {
  constructor(vaultPath: string) {
    const tools = [
      new NoteCreationTool(vaultPath),
      new NoteUpdateTool(vaultPath),
      new NoteDeletionTool(vaultPath),
      new NoteMoveAndRenameTool(vaultPath),
      new TagManagementTool(vaultPath),
      new FolderOperationTool(vaultPath)
    ];

    const systemPrompt = `You are an intelligent note management assistant that helps organize and manage notes in an Obsidian vault.
    You can create, update, delete, move notes, manage tags, and perform folder operations.
    Always provide responses in a structured JSON format and ensure all operations maintain data integrity.`;

    super(
      'note_management',
      'Note Management Agent',
      'Manages note creation, updates, organization, and folder operations in the Obsidian vault',
      tools,
      systemPrompt
    );
  }

  async execute(task: string, options?: ExecuteOptions): Promise<TaskResult> {
    try {
      if (options?.uploadedFile) {
        const { path: filePath, name: fileName, type: fileType } = options.uploadedFile;
        
        const createNoteResult = await this.createNote({
          title: fileName.replace(/\.[^/.]+$/, ''),
          content: `File uploaded: ${fileName}\nType: ${fileType}\nPath: ${filePath}`,
          tags: ['uploaded-file'],
          frontmatter: {
            originalFile: fileName,
            fileType: fileType,
            uploadPath: filePath,
            uploadDate: new Date().toISOString()
          }
        });

        if (!createNoteResult.success) {
          throw new Error(`Failed to create note for uploaded file: ${createNoteResult.error?.message}`);
        }
      }

      const taskAnalysis = await this.understandTask(task);
      
      switch (taskAnalysis.taskType) {
        case 'create':
          return this.createNote(taskAnalysis.parameters);
        case 'update':
          return this.updateNote(taskAnalysis.parameters);
        case 'delete':
          return this.deleteNote(taskAnalysis.parameters);
        case 'move':
          return this.moveNote(taskAnalysis.parameters);
        case 'tag':
          return this.manageTag(taskAnalysis.parameters);
        case 'folder':
          return this.manageFolder(taskAnalysis.parameters);
        default:
          return super.execute(task);
      }
    } catch (error) {
      return {
        success: false,
        message: 'Failed to execute task',
        error: error as Error
      };
    }
  }

  async createNote(params: {
    title: string;
    content?: string;
    template?: string;
    tags?: string[];
    folder?: string;
    frontmatter?: Record<string, any>;
  }): Promise<TaskResult> {
    try {
      const noteCreationTool = this.tools.find(tool => tool.name === 'note_creation');
      if (!noteCreationTool) {
        throw new Error('Note creation tool not found');
      }

      const note = await noteCreationTool.execute(params);

      return {
        success: true,
        message: 'Note created successfully',
        data: note
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to create note',
        error: error as Error
      };
    }
  }

  async updateNote(params: {
    notePath: string;
    title?: string;
    content?: string;
    tags?: string[];
    frontmatter?: Record<string, any>;
  }): Promise<TaskResult> {
    try {
      const noteUpdateTool = this.tools.find(tool => tool.name === 'note_update');
      if (!noteUpdateTool) {
        throw new Error('Note update tool not found');
      }

      const note = await noteUpdateTool.execute(params);

      return {
        success: true,
        message: 'Note updated successfully',
        data: note
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to update note',
        error: error as Error
      };
    }
  }

  async deleteNote(params: { notePath: string }): Promise<TaskResult> {
    try {
      const noteDeletionTool = this.tools.find(tool => tool.name === 'note_deletion');
      if (!noteDeletionTool) {
        throw new Error('Note deletion tool not found');
      }

      const result = await noteDeletionTool.execute(params);

      return {
        success: true,
        message: 'Note deleted successfully',
        data: result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to delete note',
        error: error as Error
      };
    }
  }

  async moveNote(params: {
    sourcePath: string;
    destinationPath: string;
    newTitle?: string;
    updateLinks?: boolean;
  }): Promise<TaskResult> {
    try {
      const noteMoveAndRenameTool = this.tools.find(tool => tool.name === 'note_move');
      if (!noteMoveAndRenameTool) {
        throw new Error('Note move tool not found');
      }

      const note = await noteMoveAndRenameTool.execute(params);

      return {
        success: true,
        message: 'Note moved successfully',
        data: note
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to move note',
        error: error as Error
      };
    }
  }

  async manageTag(params: {
    type: 'add' | 'remove' | 'rename';
    tag: string;
    newTag?: string;
    notePaths?: string[];
  }): Promise<TaskResult> {
    try {
      const tagManagementTool = this.tools.find(tool => tool.name === 'tag_management');
      if (!tagManagementTool) {
        throw new Error('Tag management tool not found');
      }

      const result = await tagManagementTool.execute(params);

      return {
        success: true,
        message: 'Tag operation completed successfully',
        data: result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to manage tag',
        error: error as Error
      };
    }
  }

  async manageFolder(params: {
    type: 'create' | 'delete' | 'rename' | 'move';
    sourcePath: string;
    destinationPath?: string;
  }): Promise<TaskResult> {
    try {
      const folderOperationTool = this.tools.find(tool => tool.name === 'folder_operation');
      if (!folderOperationTool) {
        throw new Error('Folder operation tool not found');
      }

      const result = await folderOperationTool.execute(params);

      return {
        success: true,
        message: 'Folder operation completed successfully',
        data: result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to manage folder',
        error: error as Error
      };
    }
  }

  private async extractNoteParams(task: string): Promise<any> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that extracts note creation parameters from user tasks. Return the parameters in a structured format."
        },
        {
          role: "user",
          content: `Extract note creation parameters from this task: ${task}`
        }
      ],
      temperature: 0.7,
      max_tokens: 500
    });

    try {
      const params = JSON.parse(completion.choices[0].message.content || '{}');
      return {
        title: params.title || 'New Note',
        content: params.content || '',
        tags: params.tags || [],
        folder: params.folder || '',
        frontmatter: params.frontmatter || {}
      };
    } catch (error) {
      return {
        title: 'New Note',
        content: '',
        tags: []
      };
    }
  }

  private async extractUpdateParams(task: string): Promise<any> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that extracts note update parameters from user tasks. Return the parameters in a structured format."
        },
        {
          role: "user",
          content: `Extract note update parameters from this task: ${task}`
        }
      ],
      temperature: 0.7,
      max_tokens: 500
    });

    try {
      const params = JSON.parse(completion.choices[0].message.content || '{}');
      return {
        notePath: params.notePath || '',
        title: params.title || '',
        content: params.content || '',
        tags: params.tags || []
      };
    } catch (error) {
      return {
        notePath: '',
        title: '',
        content: ''
      };
    }
  }

  private async extractDeleteParams(task: string): Promise<any> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that extracts note deletion parameters from user tasks. Return the parameters in a structured format."
        },
        {
          role: "user",
          content: `Extract note deletion parameters from this task: ${task}`
        }
      ],
      temperature: 0.7,
      max_tokens: 500
    });

    try {
      const params = JSON.parse(completion.choices[0].message.content || '{}');
      return {
        notePath: params.notePath || ''
      };
    } catch (error) {
      return {
        notePath: ''
      };
    }
  }

  private async extractMoveParams(task: string): Promise<any> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that extracts note move parameters from user tasks. Return the parameters in a structured format."
        },
        {
          role: "user",
          content: `Extract note move parameters from this task: ${task}`
        }
      ],
      temperature: 0.7,
      max_tokens: 500
    });

    try {
      const params = JSON.parse(completion.choices[0].message.content || '{}');
      return {
        sourcePath: params.sourcePath || '',
        destinationPath: params.destinationPath || '',
        newTitle: params.newTitle,
        updateLinks: params.updateLinks
      };
    } catch (error) {
      return {
        sourcePath: '',
        destinationPath: ''
      };
    }
  }

  private async extractTagParams(task: string): Promise<any> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that extracts tag management parameters from user tasks. Return the parameters in a structured format."
        },
        {
          role: "user",
          content: `Extract tag management parameters from this task: ${task}`
        }
      ],
      temperature: 0.7,
      max_tokens: 500
    });

    try {
      const params = JSON.parse(completion.choices[0].message.content || '{}');
      return {
        type: params.type || 'add',
        tag: params.tag || '',
        newTag: params.newTag,
        notePaths: params.notePaths
      };
    } catch (error) {
      return {
        type: 'add',
        tag: ''
      };
    }
  }

  private async extractFolderParams(task: string): Promise<any> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that extracts folder operation parameters from user tasks. Return the parameters in a structured format."
        },
        {
          role: "user",
          content: `Extract folder operation parameters from this task: ${task}`
        }
      ],
      temperature: 0.7,
      max_tokens: 500
    });

    try {
      const params = JSON.parse(completion.choices[0].message.content || '{}');
      return {
        type: params.type || 'create',
        sourcePath: params.sourcePath || '',
        destinationPath: params.destinationPath
      };
    } catch (error) {
      return {
        type: 'create',
        sourcePath: ''
      };
    }
  }
} 