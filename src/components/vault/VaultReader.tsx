import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

interface VaultReaderProps {
  vaultPath: string;
}

interface VaultDocument {
  id: string;
  title: string;
  content: string;
  metadata: Record<string, unknown>;
}

export const VaultReader: React.FC<VaultReaderProps> = ({ vaultPath }) => {
  const [documents, setDocuments] = useState<VaultDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadVaultDocuments = async () => {
      try {
        setIsLoading(true);
        // TODO: Implement actual vault reading logic using the SmolagentsRAG approach
        // This will be connected to the backend service that handles vault processing
        const response = await fetch(`/api/vault/read?path=${encodeURIComponent(vaultPath)}`);
        if (!response.ok) {
          throw new Error('Failed to load vault documents');
        }
        const data = await response.json();
        setDocuments(data.documents);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    loadVaultDocuments();
  }, [vaultPath]);

  if (isLoading) {
    return <div className="flex justify-center items-center p-4">Loading vault...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Vault Documents</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((doc) => (
          <div key={doc.id} className="border rounded-lg p-4 shadow-sm">
            <h3 className="text-lg font-semibold mb-2">{doc.title}</h3>
            <p className="text-gray-600 line-clamp-3">{doc.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}; 