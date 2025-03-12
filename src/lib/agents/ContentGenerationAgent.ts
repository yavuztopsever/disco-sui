import { BaseAgent } from './BaseAgent';
import { Tool, TaskResult } from '@/types';
import { HfInference } from '@huggingface/inference';

interface ContentGenerationParams {
  prompt: string;
  type: 'text' | 'summary' | 'outline' | 'expansion';
  context?: string;
  maxLength?: number;
  temperature?: number;
}

class ContentGenerationTool implements Tool {
  name = 'content_generation';
  description = 'Generates content using AI models';
  private hf: HfInference;

  constructor(hfToken?: string) {
    this.hf = new HfInference(hfToken);
  }

  async execute(params: ContentGenerationParams): Promise<string> {
    const {
      prompt,
      type,
      context = '',
      maxLength = 500,
      temperature = 0.7
    } = params;

    let input = prompt;
    if (context) {
      input = `Context: ${context}\n\nTask: ${type}\n\nPrompt: ${prompt}`;
    }

    try {
      const response = await this.hf.textGeneration({
        model: 'gpt2',
        inputs: input,
        parameters: {
          max_length: maxLength,
          temperature,
          top_p: 0.9,
          repetition_penalty: 1.2
        }
      });

      return response.generated_text;
    } catch (error) {
      throw new Error(`Failed to generate content: ${error}`);
    }
  }
}

export class ContentGenerationAgent extends BaseAgent {
  constructor(hfToken?: string) {
    const tools = [new ContentGenerationTool(hfToken)];

    super(
      'content_generation',
      'Content Generation Agent',
      'Generates various types of content using AI models',
      tools,
      hfToken
    );
  }

  async generateContent(params: ContentGenerationParams): Promise<TaskResult> {
    try {
      const contentGenerationTool = this.tools.find(
        tool => tool.name === 'content_generation'
      );
      if (!contentGenerationTool) {
        throw new Error('Content generation tool not found');
      }

      const content = await contentGenerationTool.execute(params);

      return {
        success: true,
        message: 'Content generated successfully',
        data: { content }
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to generate content',
        error: error as Error
      };
    }
  }

  async execute(task: string): Promise<TaskResult> {
    try {
      // Extract parameters from the task description
      const params = await this.extractGenerationParams(task);
      return this.generateContent(params);
    } catch (error) {
      return {
        success: false,
        message: 'Failed to execute task',
        error: error as Error
      };
    }
  }

  private async extractGenerationParams(task: string): Promise<ContentGenerationParams> {
    const taskLower = task.toLowerCase();
    let type: ContentGenerationParams['type'] = 'text';

    if (taskLower.includes('summarize') || taskLower.includes('summary')) {
      type = 'summary';
    } else if (taskLower.includes('outline')) {
      type = 'outline';
    } else if (taskLower.includes('expand') || taskLower.includes('elaborate')) {
      type = 'expansion';
    }

    // Use HuggingFace inference to extract parameters from the task description
    const response = await this.hf.textGeneration({
      model: 'gpt2',
      inputs: `Extract content generation parameters from: ${task}`,
      parameters: {
        max_length: 100,
        temperature: 0.7
      }
    });

    // For now, return basic parameters
    // In a real implementation, you'd want to parse the response more intelligently
    return {
      prompt: task,
      type,
      maxLength: 500,
      temperature: 0.7
    };
  }
} 