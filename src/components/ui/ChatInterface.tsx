import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import FileUpload from './FileUpload';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  vaultPath: string;
  hfToken?: string;
  onReset?: () => void;
}

export default function ChatInterface({ vaultPath, hfToken, onReset }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = async (file: File) => {
    setUploadedFile(file);
    // Add a message to show the file was uploaded
    setMessages(prev => [...prev, {
      role: 'user',
      content: `Uploaded file: ${file.name}`,
      timestamp: new Date()
    }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !uploadedFile) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    try {
      // Here we'll implement the streaming functionality
      const formData = new FormData();
      formData.append('message', input);
      formData.append('vaultPath', vaultPath);
      if (hfToken) formData.append('hfToken', hfToken);
      if (uploadedFile) formData.append('file', uploadedFile);

      const response = await fetch('/api/chat', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to get response');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      let accumulatedContent = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = new TextDecoder().decode(value);
        accumulatedContent += text;

        setMessages(prev => {
          const newMessages = [...prev];
          const lastMessage = newMessages[newMessages.length - 1];
          
          if (lastMessage?.role === 'assistant') {
            lastMessage.content = accumulatedContent;
            return [...newMessages];
          } else {
            return [...newMessages, {
              role: 'assistant',
              content: accumulatedContent,
              timestamp: new Date()
            }];
          }
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request.',
        timestamp: new Date()
      }]);
    } finally {
      setIsStreaming(false);
      setUploadedFile(null);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setInput('');
    setUploadedFile(null);
    onReset?.();
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t p-4 space-y-4">
        {!uploadedFile && (
          <FileUpload onFileUpload={handleFileUpload} />
        )}
        
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming || (!input.trim() && !uploadedFile)}
            className={`px-6 py-2 rounded-lg bg-primary text-white font-medium
              ${isStreaming || (!input.trim() && !uploadedFile)
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:bg-primary/90'}`}
          >
            {isStreaming ? 'Processing...' : 'Send'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
          >
            Reset
          </button>
        </form>
      </div>
    </div>
  );
} 