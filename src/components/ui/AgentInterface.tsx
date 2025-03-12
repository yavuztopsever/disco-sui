import { useState } from 'react';
import { TaskResult } from '@/types';
import { NoteManagementAgent } from '@/lib/agents/NoteManagementAgent';

interface AgentInterfaceProps {
  vaultPath: string;
  hfToken?: string;
}

export default function AgentInterface({ vaultPath, hfToken }: AgentInterfaceProps) {
  const [task, setTask] = useState('');
  const [result, setResult] = useState<TaskResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const noteAgent = new NoteManagementAgent(vaultPath, hfToken);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const taskResult = await noteAgent.execute(task);
      setResult(taskResult);
    } catch (error) {
      setResult({
        success: false,
        message: 'Failed to execute task',
        error: error as Error
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-4">DiscoSui Agent Interface</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="task" className="block text-sm font-medium text-gray-700">
            Enter your task
          </label>
          <textarea
            id="task"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
            rows={4}
            placeholder="e.g., Create a new note about project ideas"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !task}
          className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary ${
            isLoading || !task ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isLoading ? 'Processing...' : 'Execute Task'}
        </button>
      </form>

      {result && (
        <div className={`mt-6 p-4 rounded-md ${result.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <h3 className={`text-lg font-medium ${result.success ? 'text-green-800' : 'text-red-800'}`}>
            {result.success ? 'Task Completed' : 'Task Failed'}
          </h3>
          <p className="mt-2 text-sm text-gray-600">{result.message}</p>
          {result.data && (
            <pre className="mt-2 p-2 bg-gray-100 rounded overflow-x-auto">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          )}
          {result.error && (
            <p className="mt-2 text-sm text-red-600">{result.error.message}</p>
          )}
        </div>
      )}
    </div>
  );
} 