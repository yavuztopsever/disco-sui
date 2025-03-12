import { BaseAgent } from './BaseAgent';
import { Tool, TaskResult } from '@/types';
import { HfInference } from '@huggingface/inference';
import * as fs from 'fs/promises';
import * as path from 'path';
import matter from 'gray-matter';

interface AudioProcessingParams {
  audioPath: string;
  outputFormat: 'text' | 'markdown' | 'json';
  language?: string;
  shouldSegment?: boolean;
  includeTimestamps?: boolean;
  generateSummary?: boolean;
  generateTasks?: boolean;
  generateTags?: boolean;
  saveToVault?: boolean;
  vaultPath?: string;
}

interface ProcessedAudio {
  text: string;
  summary?: string;
  tasks?: string[];
  tags?: string[];
  segments?: Array<{ start: number; end: number; text: string }>;
  metadata: {
    filename: string;
    date: string;
    time: string;
    path?: string;
  };
}

class AudioTranscriptionTool implements Tool {
  name = 'audio_transcription';
  description = 'Transcribes audio files into text and processes them for the vault';
  private hf: HfInference;
  private vaultPath?: string;

  constructor(vaultPath?: string, hfToken?: string) {
    this.hf = new HfInference(hfToken);
    this.vaultPath = vaultPath;
  }

  async execute(params: AudioProcessingParams): Promise<ProcessedAudio> {
    const {
      audioPath,
      outputFormat,
      language = 'en',
      shouldSegment = true,
      includeTimestamps = true,
      generateSummary = true,
      generateTasks = true,
      generateTags = true,
      saveToVault = false,
      vaultPath = this.vaultPath
    } = params;

    try {
      // Read the audio file
      const audioBuffer = await fs.readFile(audioPath);
      const filename = path.basename(audioPath);
      const modificationDate = new Date((await fs.stat(audioPath)).mtime);
      const dateStr = modificationDate.toISOString().split('T')[0];
      const timeStr = modificationDate.toTimeString().split(' ')[0];

      // Use Whisper model for transcription
      const response = await this.hf.automaticSpeechRecognition({
        model: 'openai/whisper-large-v3',
        data: audioBuffer,
        parameters: {
          language,
          return_timestamps: includeTimestamps
        }
      });

      // Process the transcription
      const transcription = response.text;
      let summary: string | undefined;
      let tasks: string[] | undefined;
      let tags: string[] | undefined;

      if (generateSummary) {
        const summaryResponse = await this.hf.textGeneration({
          model: 'gpt2',
          inputs: `Summarize this transcript:\n\n${transcription}`,
          parameters: { max_length: 200, temperature: 0.7 }
        });
        summary = summaryResponse.generated_text;
      }

      if (generateTasks) {
        const tasksResponse = await this.hf.textGeneration({
          model: 'gpt2',
          inputs: `Extract actionable tasks from this transcript. Format as:\n- [ ] Task description:\n${transcription}`,
          parameters: { max_length: 200, temperature: 0.7 }
        });
        tasks = tasksResponse.generated_text
          .split('\n')
          .filter(line => line.startsWith('- [ ]'))
          .map(task => task.replace('- [ ] ', ''));
      }

      if (generateTags) {
        const tagsResponse = await this.hf.textGeneration({
          model: 'gpt2',
          inputs: `Generate relevant tags for this transcript with hashtags, separated by spaces:\n${transcription}`,
          parameters: { max_length: 100, temperature: 0.7 }
        });
        tags = tagsResponse.generated_text
          .split(' ')
          .filter(tag => tag.startsWith('#'))
          .map(tag => tag.slice(1));
      }

      const result: ProcessedAudio = {
        text: transcription,
        summary,
        tasks,
        tags,
        segments: response.chunks?.map(chunk => ({
          start: chunk.timestamp[0],
          end: chunk.timestamp[1],
          text: chunk.text
        })),
        metadata: {
          filename,
          date: dateStr,
          time: timeStr
        }
      };

      // Save to vault if requested
      if (saveToVault && vaultPath) {
        await this.saveToVault(result, audioPath, vaultPath);
      }

      return result;
    } catch (error) {
      throw new Error(`Failed to transcribe audio: ${error}`);
    }
  }

  private async saveToVault(result: ProcessedAudio, audioPath: string, vaultPath: string): Promise<void> {
    const { date } = result.metadata;
    const logFolder = path.join(vaultPath, date);
    await fs.mkdir(logFolder, { recursive: true });

    // Copy audio file to vault
    const audioFilename = path.basename(audioPath);
    await fs.copyFile(audioPath, path.join(logFolder, audioFilename));

    // Create or update note
    const notePath = path.join(vaultPath, `${date}.md`);
    const noteContent = this.formatNoteContent(result, audioFilename);

    try {
      const existingContent = await fs.readFile(notePath, 'utf-8');
      await fs.writeFile(notePath, `${existingContent}\n\n${noteContent}`);
    } catch {
      const initialContent = matter.stringify(noteContent, {
        file_type: '#Log',
        parent: '[[DailyLogs]]',
        tags: result.tags?.join(' ') || '',
        created_date: date
      });
      await fs.writeFile(notePath, initialContent);
    }

    result.metadata.path = notePath;
  }

  private formatNoteContent(result: ProcessedAudio, audioFilename: string): string {
    const { time, date } = result.metadata;
    let content = `## Recording at ${time}\n\n`;

    if (result.summary) {
      content += `### Summary\n${result.summary}\n\n`;
    }

    if (result.tasks && result.tasks.length > 0) {
      content += `### Action Items\n${result.tasks.map(task => `- [ ] ${task}`).join('\n')}\n\n`;
    }

    content += `### Full Transcript\n${result.text}\n\n`;
    content += `### Attached Audio File\n![[${date}/${audioFilename}]]`;

    return content;
  }
}

export class AudioProcessingAgent extends BaseAgent {
  constructor(vaultPath?: string, hfToken?: string) {
    const tools = [new AudioTranscriptionTool(vaultPath, hfToken)];

    super(
      'audio_processing',
      'Audio Processing Agent',
      'Processes audio files and transcribes them into notes',
      tools,
      hfToken
    );
  }

  async transcribeAudio(params: AudioProcessingParams): Promise<TaskResult> {
    try {
      const transcriptionTool = this.tools.find(
        tool => tool.name === 'audio_transcription'
      );
      if (!transcriptionTool) {
        throw new Error('Audio transcription tool not found');
      }

      const result = await transcriptionTool.execute(params);

      return {
        success: true,
        message: 'Audio transcribed successfully',
        data: result
      };
    } catch (error) {
      return {
        success: false,
        message: 'Failed to transcribe audio',
        error: error as Error
      };
    }
  }

  async execute(task: string): Promise<TaskResult> {
    try {
      // Extract parameters from the task description
      const params = await this.extractAudioParams(task);
      return this.transcribeAudio(params);
    } catch (error) {
      return {
        success: false,
        message: 'Failed to execute task',
        error: error as Error
      };
    }
  }

  private async extractAudioParams(task: string): Promise<AudioProcessingParams> {
    const taskLower = task.toLowerCase();
    let outputFormat: AudioProcessingParams['outputFormat'] = 'text';
    let shouldSegment = true;
    let includeTimestamps = true;
    let generateSummary = true;
    let generateTasks = true;
    let generateTags = true;
    let saveToVault = false;

    if (taskLower.includes('markdown')) {
      outputFormat = 'markdown';
    } else if (taskLower.includes('json')) {
      outputFormat = 'json';
    }

    if (taskLower.includes('no segment')) {
      shouldSegment = false;
    }

    if (taskLower.includes('no timestamp')) {
      includeTimestamps = false;
    }

    if (taskLower.includes('no summary')) {
      generateSummary = false;
    }

    if (taskLower.includes('no tasks')) {
      generateTasks = false;
    }

    if (taskLower.includes('no tags')) {
      generateTags = false;
    }

    if (taskLower.includes('save to vault') || taskLower.includes('save in vault')) {
      saveToVault = true;
    }

    // Use HuggingFace inference to extract parameters from the task description
    const response = await this.hf.textGeneration({
      model: 'gpt2',
      inputs: `Extract audio processing parameters from: ${task}`,
      parameters: {
        max_length: 100,
        temperature: 0.7
      }
    });

    // For now, return basic parameters
    // In a real implementation, you'd want to parse the response more intelligently
    return {
      audioPath: '',  // This should be extracted from the task
      outputFormat,
      shouldSegment,
      includeTimestamps,
      generateSummary,
      generateTasks,
      generateTags,
      saveToVault
    };
  }
} 