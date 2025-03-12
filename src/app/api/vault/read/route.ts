import { NextResponse } from 'next/server';
import { RAGProcessor } from '@/lib/rag/processor';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const vaultPath = searchParams.get('path');

    if (!vaultPath) {
      return NextResponse.json(
        { error: 'Vault path is required' },
        { status: 400 }
      );
    }

    // Initialize the RAG processor
    const processor = new RAGProcessor(vaultPath);
    
    // Process and retrieve vault documents
    const documents = await processor.processVault();

    return NextResponse.json({ documents });
  } catch (error) {
    console.error('Error processing vault:', error);
    return NextResponse.json(
      { error: 'Failed to process vault' },
      { status: 500 }
    );
  }
} 