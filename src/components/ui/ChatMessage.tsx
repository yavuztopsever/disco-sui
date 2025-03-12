import React from 'react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export default function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[70%] rounded-lg p-4 ${
          role === 'user'
            ? 'bg-primary text-white ml-4'
            : 'bg-gray-100 text-gray-900 mr-4'
        }`}
      >
        <div className="flex items-center mb-2">
          <span className="font-medium">
            {role === 'user' ? 'You' : 'Assistant'}
          </span>
          {timestamp && (
            <span className="text-xs ml-2 opacity-70">
              {timestamp.toLocaleTimeString()}
            </span>
          )}
        </div>
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
} 