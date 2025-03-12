import { BaseAgent } from './BaseAgent';
import { Tool, TaskResult } from '@/types';
import { HfInference } from '@huggingface/inference';
import * as fs from 'fs/promises';
import * as path from 'path';
import { simpleParser, ParsedMail } from 'mailparser';

interface EmailProcessingParams {
  emailPath: string;
  outputFormat: 'text' | 'markdown' | 'json';
  includeAttachments?: boolean;
  extractTasks?: boolean;
  categorize?: boolean;
}

interface ProcessedEmail {
  subject: string;
  from: string;
  to: string[];
  date: Date;
  content: string;
  attachments?: Array<{
    filename: string;
    content: Buffer;
    contentType: string;
  }>;
  tasks?: string[];
  category?: string;
}

class EmailParsingTool implements Tool {
  name = 'email_parsing';
  description = 'Parses email files and converts them into structured data';
  private hf: HfInference;

  constructor(hfToken?: string) {
    this.hf = new HfInference(hfToken);
  }

  async execute(params: EmailProcessingParams): Promise<ProcessedEmail> {
    const {
      emailPath,
      outputFormat,
      includeAttachments = true,
      extractTasks = true,
      categorize = true
    } = params;

    try {
      // Read and parse the email file
      const emailContent = await fs.readFile(emailPath);
      const parsed = await simpleParser(emailContent);

      // Extract tasks if requested
      let tasks: string[] = [];
      if (extractTasks) {
        tasks = await this.extractTasks(parsed);
      }

      // Categorize email if requested
      let category = '';
      if (categorize) {
        category = await this.categorizeEmail(parsed);
      }

      // Format the content based on the requested format
      const content = this.formatContent(parsed, outputFormat);

      // Process attachments if requested
      const attachments = includeAttachments ? this.processAttachments(parsed) : undefined;

      return {
        subject: parsed.subject || '',
        from: parsed.from?.text || '',
        to: parsed.to?.text ? [parsed.to.text] : [],
        date: parsed.date || new Date(),
        content,
        attachments,
        tasks: tasks.length > 0 ? tasks : undefined,
        category: category || undefined
      };
    } catch (error) {
      throw new Error(`Failed to process email: ${error}`);
    }
  }

  private async extractTasks(email: ParsedMail): Promise<string[]> {
    try {
      const response = await this.hf.textGeneration({
        model: 'gpt2',
        inputs: `Extract tasks from email:\n\n${email.text}`,
        parameters: {
          max_length: 200,
          temperature: 0.7
        }
      });

      // In a real implementation, you'd want to parse the response more intelligently
      return [];
    } catch (error) {
      console.warn('Failed to extract tasks:', error);
      return [];
    }
  }

  private async categorizeEmail(email: ParsedMail): Promise<string> {
    try {
      const response = await this.hf.textGeneration({
        model: 'gpt2',
        inputs: `Categorize email:\n\n${email.subject}\n\n${email.text}`,
        parameters: {
          max_length: 50,
          temperature: 0.7
        }
      });

      return response.generated_text.trim();
    } catch (error) {
      console.warn('Failed to categorize email:', error);
      return '';
    }
  }

  private formatContent(email: ParsedMail, format: string): string {
    switch (format) {
      case 'markdown':
        return this.formatMarkdown(email);
      case 'json':
        return JSON.stringify(email, null, 2);
      default:
        return email.text || '';
    }
  }

  private formatMarkdown(email: ParsedMail): string {
    let markdown = `# ${email.subject || 'No Subject'}\n\n`;
    markdown += `**From:** ${email.from?.text || 'Unknown'}\n`;
    markdown += `**To:** ${email.to?.text || 'Unknown'}\n`;
    markdown += `**Date:** ${email.date?.toISOString() || 'Unknown'}\n\n`;
    markdown += '---\n\n';
    markdown += email.text || '';

    if (email.attachments?.length) {
      markdown += '\n\n## Attachments\n\n';
      email.attachments.forEach(attachment => {
        markdown += `- ${attachment.filename}\n`;
      });
    }

    return markdown;
  }

  private processAttachments(email: ParsedMail) {
    return email.attachments?.map(attachment => ({
      filename: attachment.filename || 'unnamed',
      content: attachment.content,
      contentType: attachment.contentType
    }));
  }
}

export class EmailProcessingAgent extends BaseAgent {
  constructor(hfToken?: string) {
    const tools = [new EmailParsingTool(hfToken)];

    super(
      'email_processing',
      'Email Processing Agent',
      'Processes emails and converts them into notes',
      tools,
      hfToken
    );
  }

  async processEmail(params: EmailProcessingParams): Promise<TaskResult> {
    try {
      const emailParsingTool = this.tools.find(
        tool => tool.name === 'email_parsing'
      );
      if (!emailParsingTool) {
        throw new Error('Email parsing tool not found');
      }

      const result = await emailParsingTool.execute(params);

      return {
        success: true,
        message: 'Email processed successfully',
        data: result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to process email',
        error: error as Error
      };
    }
  }

  async execute(task: string): Promise<TaskResult> {
    try {
      // Extract parameters from the task description
      const params = await this.extractEmailParams(task);
      return this.processEmail(params);
    } catch (error) {
      return {
        success: false,
        message: 'Failed to execute task',
        error: error as Error
      };
    }
  }

  private async extractEmailParams(task: string): Promise<EmailProcessingParams> {
    const taskLower = task.toLowerCase();
    let outputFormat: EmailProcessingParams['outputFormat'] = 'text';
    let includeAttachments = true;
    let extractTasks = true;
    let categorize = true;

    if (taskLower.includes('markdown')) {
      outputFormat = 'markdown';
    } else if (taskLower.includes('json')) {
      outputFormat = 'json';
    }

    if (taskLower.includes('no attachments')) {
      includeAttachments = false;
    }

    if (taskLower.includes('no tasks')) {
      extractTasks = false;
    }

    if (taskLower.includes('no category')) {
      categorize = false;
    }

    // Use HuggingFace inference to extract parameters from the task description
    const response = await this.hf.textGeneration({
      model: 'gpt2',
      inputs: `Extract email processing parameters from: ${task}`,
      parameters: {
        max_length: 100,
        temperature: 0.7
      }
    });

    // For now, return basic parameters
    // In a real implementation, you'd want to parse the response more intelligently
    return {
      emailPath: '',  // This should be extracted from the task
      outputFormat,
      includeAttachments,
      extractTasks,
 