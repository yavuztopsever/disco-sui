import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  allowedTypes?: string[];
}

export default function FileUpload({ onFileUpload, allowedTypes = ['.pdf', '.docx', '.txt'] }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0]);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: allowedTypes.reduce((acc, type) => ({
      ...acc,
      [type]: []
    }), {}),
    multiple: false
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
        ${isDragActive ? 'border-primary bg-primary/10' : 'border-gray-300 hover:border-primary'}`}
    >
      <input {...getInputProps()} />
      <div className="space-y-2">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M24 14v14m7-7H17m21 7v10a2 2 0 01-2 2H12a2 2 0 01-2-2V28m14-14l7-7m0 0l7 7m-7-7v14"
          />
        </svg>
        <p className="text-sm text-gray-600">
          Drag and drop a file here, or click to select a file
        </p>
        <p className="text-xs text-gray-500">
          Supported file types: {allowedTypes.join(', ')}
        </p>
      </div>
    </div>
  );
} 