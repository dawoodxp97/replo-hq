'use client';

import { useState, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';

interface Module {
  module_id: string;
  title: string;
  content_markdown: string;
  code_snippet: string | null;
  diagram_mermaid?: string | null;
}

interface ModuleEditorProps {
  module: Module;
  onUpdate: (moduleData: {
    title: string;
    content_markdown: string;
    code_snippet: string;
    diagram_mermaid?: string;
  }) => void;
  isUpdating: boolean;
}

const ModuleEditor = ({ module, onUpdate, isUpdating }: ModuleEditorProps) => {
  const [title, setTitle] = useState(module.title);
  const [contentMarkdown, setContentMarkdown] = useState(module.content_markdown);
  const [codeSnippet, setCodeSnippet] = useState(module.code_snippet || '');
  const [diagramMermaid, setDiagramMermaid] = useState(module.diagram_mermaid || '');
  const [isDirty, setIsDirty] = useState(false);

  // Update state when module changes
  useEffect(() => {
    setTitle(module.title);
    setContentMarkdown(module.content_markdown);
    setCodeSnippet(module.code_snippet || '');
    setDiagramMermaid(module.diagram_mermaid || '');
    setIsDirty(false);
  }, [module]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    onUpdate({
      title,
      content_markdown: contentMarkdown,
      code_snippet: codeSnippet,
      diagram_mermaid: diagramMermaid || undefined
    });
    
    setIsDirty(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Title */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
          Module Title
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            setIsDirty(true);
          }}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>
      
      {/* Content Markdown */}
      <div>
        <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
          Content (Markdown)
        </label>
        <div className="border border-gray-300 rounded-md overflow-hidden">
          <Editor
            height="300px"
            language="markdown"
            value={contentMarkdown}
            onChange={(value) => {
              setContentMarkdown(value || '');
              setIsDirty(true);
            }}
            options={{
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              wordWrap: 'on'
            }}
          />
        </div>
      </div>
      
      {/* Code Snippet */}
      <div>
        <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-1">
          Code Snippet
        </label>
        <div className="border border-gray-300 rounded-md overflow-hidden">
          <Editor
            height="300px"
            language="javascript" // Default to JavaScript, could be dynamic based on file extension
            value={codeSnippet}
            onChange={(value) => {
              setCodeSnippet(value || '');
              setIsDirty(true);
            }}
            options={{
              minimap: { enabled: false },
              scrollBeyondLastLine: false
            }}
          />
        </div>
      </div>
      
      {/* Mermaid Diagram */}
      <div>
        <label htmlFor="diagram" className="block text-sm font-medium text-gray-700 mb-1">
          Mermaid Diagram (Optional)
        </label>
        <div className="border border-gray-300 rounded-md overflow-hidden">
          <Editor
            height="200px"
            language="markdown"
            value={diagramMermaid}
            onChange={(value) => {
              setDiagramMermaid(value || '');
              setIsDirty(true);
            }}
            options={{
              minimap: { enabled: false },
              scrollBeyondLastLine: false
            }}
          />
        </div>
      </div>
      
      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isUpdating || !isDirty}
          className={`px-4 py-2 rounded-md ${
            isUpdating || !isDirty
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isUpdating ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
};

export default ModuleEditor;