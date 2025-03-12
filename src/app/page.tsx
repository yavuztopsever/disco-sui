'use client';

import { useState } from 'react';
import AgentInterface from '@/components/ui/AgentInterface';
import { VaultReader } from '@/components/vault/VaultReader';
import ChatInterface from '@/components/ui/ChatInterface';

export default function Home() {
  const [vaultPath, setVaultPath] = useState('');
  const [isConfigured, setIsConfigured] = useState(false);

  const handleSetup = (e: React.FormEvent) => {
    e.preventDefault();
    if (vaultPath) {
      setIsConfigured(true);
    }
  };

  if (!isConfigured) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24">
        <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
          <h1 className="text-4xl font-bold text-center mb-8">
            Welcome to DiscoSui
          </h1>
          <p className="text-center text-lg mb-8">
            A modern web application for Obsidian vault automation
          </p>
          
          <form onSubmit={handleSetup} className="max-w-md mx-auto space-y-4">
            <div>
              <label htmlFor="vaultPath" className="block text-sm font-medium text-gray-700">
                Obsidian Vault Path
              </label>
              <input
                type="text"
                id="vaultPath"
                value={vaultPath}
                onChange={(e) => setVaultPath(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
                placeholder="/path/to/your/vault"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Configure Vault
            </button>
          </form>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex flex-col">
      <header className="bg-primary text-white p-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold">DiscoSui</h1>
          <p className="text-sm opacity-80">Your AI-powered note management assistant</p>
        </div>
      </header>

      <div className="flex-1 container mx-auto p-4">
        <ChatInterface
          vaultPath={vaultPath}
          hfToken={process.env.NEXT_PUBLIC_OPENAI_API_KEY}
        />
      </div>

      <footer className="bg-gray-100 p-4 text-center text-sm text-gray-600">
        <p>Built with Next.js and SmolagentsUI</p>
      </footer>
    </main>
  );
} 