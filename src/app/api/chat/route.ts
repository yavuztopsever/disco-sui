import { NextRequest } from 'next/server';
import { NoteManagementAgent } from '@/lib/agents/NoteManagementAgent';
import { writeFile } from 'fs/promises';
import { join } from 'path';
import { v4 as uuidv4 } from 'uuid';

const UPLOAD_DIR = join(process.cwd(), 'uploads');

export async function POST(req: NextRequest) {
  const encoder = new TextEncoder();
  const formData = await req.formData();
  
  const message = formData.get('message') as string;
  const vaultPath = formData.get('vaultPath') as string;
  const file = formData.get('file') as File;

  const stream = new TransformStream();
  const writer = stream.writable.getWriter();

  const noteAgent = new NoteManagementAgent(vaultPath);

  // Function to write chunks to the stream
  const writeChunk = async (chunk: string) => {
    await writer.write(encoder.encode(chunk + '\n'));
  };

  // Start processing in the background
  (async () => {
    try {
      let filePath: string | undefined;
      
      // If there's a file, handle it first
      if (file) {
        await writeChunk('Processing uploaded file...');
        
        // Create a unique filename
        const fileName = `${uuidv4()}-${file.name}`;
        filePath = join(UPLOAD_DIR, fileName);
        
        // Ensure upload directory exists
        await writeFile(filePath, Buffer.from(await file.arrayBuffer()));
        
        await writeChunk(`File uploaded successfully: ${file.name}`);
      }

      // Execute the task with the agent
      const result = await noteAgent.execute(message, {
        uploadedFile: filePath ? {
          path: filePath,
          name: file?.name,
          type: file?.type
        } : undefined
      });

      // Stream the result
      if (result.success) {
        await writeChunk(result.message);
        if (result.data) {
          await writeChunk('\nAdditional data:\n' + JSON.stringify(result.data, null, 2));
        }
      } else {
        await writeChunk('Error: ' + (result.error?.message || 'Unknown error occurred'));
      }
    } catch (error) {
      console.error('Error:', error);
      await writeChunk('Error: ' + (error instanceof Error ? error.message : 'Unknown error occurred'));
    } finally {
      writer.close();
    }
  })();

  return new Response(stream.readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
} 