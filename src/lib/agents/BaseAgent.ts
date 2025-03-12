import { Agent, Tool, TaskResult } from '@/types';
import OpenAI from 'openai';

export class BaseAgent implements Agent {
  id: string;
  name: string;
  description: string;
  tools: Tool[];
  protected openai: OpenAI;
  protected systemPrompt: string;

  constructor(
    id: string,
    name: string,
    description: string,
    tools: Tool[],
    systemPrompt?: string
  ) {
    this.id = id;
    this.name = name;
    this.description = description;
    this.tools = tools;
    this.systemPrompt = systemPrompt || "You are a helpful AI assistant that helps manage and organize notes in an Obsidian vault.";
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  }

  async execute(task: string): Promise<TaskResult> {
    try {
      // 1. Parse and understand the task
      const taskUnderstanding = await this.understandTask(task);

      // 2. Select appropriate tools
      const selectedTools = this.selectTools(taskUnderstanding);

      // 3. Create execution plan
      const executionPlan = await this.createExecutionPlan(taskUnderstanding, selectedTools);

      // 4. Execute the plan
      const result = await this.executePlan(executionPlan);

      return {
        success: true,
        message: 'Task completed successfully',
        data: result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Task execution failed',
        error: error as Error
      };
    }
  }

  protected async understandTask(task: string): Promise<any> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: this.systemPrompt
        },
        {
          role: "user",
          content: `Analyze this task and provide a structured JSON response with the following fields:
          {
            "taskType": "string (create|update|delete|move|tag|folder)",
            "parameters": object,
            "requiredTools": string[],
            "steps": string[]
          }
          
          Task: ${task}`
        }
      ],
      temperature: 0.2,
      response_format: { type: "json_object" }
    });

    return JSON.parse(completion.choices[0].message.content || '{}');
  }

  protected selectTools(taskUnderstanding: any): Tool[] {
    return this.tools.filter(tool => 
      taskUnderstanding.requiredTools?.includes(tool.name)
    );
  }

  protected async createExecutionPlan(taskUnderstanding: any, tools: Tool[]): Promise<any[]> {
    const completion = await this.openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: this.systemPrompt
        },
        {
          role: "user",
          content: `Create a detailed execution plan in JSON format for this task analysis:
          ${JSON.stringify(taskUnderstanding)}
          
          Available tools: ${tools.map(t => t.name).join(', ')}
          
          Return the plan as a JSON array of steps, where each step has:
          {
            "toolName": string,
            "parameters": object,
            "description": string
          }`
        }
      ],
      temperature: 0.2,
      response_format: { type: "json_object" }
    });

    return JSON.parse(completion.choices[0].message.content || '[]').steps;
  }

  protected async executePlan(plan: any[]): Promise<any> {
    const results = [];
    for (const step of plan) {
      const result = await this.executeStep(step);
      results.push(result);
    }
    return results;
  }

  protected async executeStep(step: any): Promise<any> {
    const tool = this.tools.find(t => t.name === step.toolName);
    if (!tool) {
      throw new Error(`Tool ${step.toolName} not found`);
    }
    return await tool.execute(step.parameters);
  }
} 