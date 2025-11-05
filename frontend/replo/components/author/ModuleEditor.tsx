'use client';

import { useEffect, useState } from 'react';
import { Editor } from '@monaco-editor/react';
import { Card } from 'antd';
import { Code, FileText, GitBranch, Save } from 'lucide-react';

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
  const [contentMarkdown, setContentMarkdown] = useState(
    module.content_markdown
  );
  const [codeSnippet, setCodeSnippet] = useState(module.code_snippet || '');
  const [diagramMermaid, setDiagramMermaid] = useState(
    module.diagram_mermaid || ''
  );
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
      diagram_mermaid: diagramMermaid || undefined,
    });

    setIsDirty(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 flex flex-col gap-4">
      {/* Title */}
      <Card
        className="border-0 shadow-lg bg-gradient-to-br from-white via-indigo-50/30 to-purple-50/20 backdrop-blur-sm"
        bodyStyle={{ padding: '24px' }}
      >
        <div className="space-y-2">
          <label
            htmlFor="title"
            className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
          >
            <FileText className="w-4 h-4 text-indigo-500" />
            Module Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={e => {
              setTitle(e.target.value);
              setIsDirty(true);
            }}
            className="w-full px-4 py-3 border border-indigo-200/50 rounded-xl bg-white/80 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-400 transition-all duration-200 shadow-sm hover:shadow-md"
            required
          />
        </div>
      </Card>

      {/* Content Markdown */}
      <Card
        className="border-0 shadow-lg bg-gradient-to-br from-white via-indigo-50/30 to-purple-50/20 backdrop-blur-sm"
        bodyStyle={{ padding: '24px' }}
      >
        <div className="space-y-3">
          <label
            htmlFor="content"
            className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
          >
            <FileText className="w-4 h-4 text-purple-500" />
            Content (Markdown)
          </label>
          <div className="border border-indigo-200/50 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200 bg-white/90 backdrop-blur-sm">
            <Editor
              height="300px"
              language="markdown"
              value={contentMarkdown}
              onChange={value => {
                setContentMarkdown(value || '');
                setIsDirty(true);
              }}
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                fontSize: 14,
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                lineNumbers: 'on',
                renderLineHighlight: 'all',
                scrollbar: {
                  vertical: 'auto',
                  horizontal: 'auto',
                },
              }}
              theme="vs"
            />
          </div>
        </div>
      </Card>

      {/* Code Snippet */}
      <Card
        className="border-0 shadow-lg bg-gradient-to-br from-white via-indigo-50/30 to-purple-50/20 backdrop-blur-sm"
        bodyStyle={{ padding: '24px' }}
      >
        <div className="space-y-3">
          <label
            htmlFor="code"
            className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
          >
            <Code className="w-4 h-4 text-pink-500" />
            Code Snippet
          </label>
          <div className="border border-indigo-200/50 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200 bg-white/90 backdrop-blur-sm">
            <Editor
              height="300px"
              language="javascript"
              value={codeSnippet}
              onChange={value => {
                setCodeSnippet(value || '');
                setIsDirty(true);
              }}
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 14,
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                lineNumbers: 'on',
                renderLineHighlight: 'all',
                scrollbar: {
                  vertical: 'auto',
                  horizontal: 'auto',
                },
              }}
              theme="vs"
            />
          </div>
        </div>
      </Card>

      {/* Mermaid Diagram */}
      <Card
        className="border-0 shadow-lg bg-gradient-to-br from-white via-indigo-50/30 to-purple-50/20 backdrop-blur-sm"
        bodyStyle={{ padding: '24px' }}
      >
        <div className="space-y-3">
          <label
            htmlFor="diagram"
            className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"
          >
            <GitBranch className="w-4 h-4 text-indigo-500" />
            Mermaid Diagram{' '}
            <span className="text-gray-500 font-normal">(Optional)</span>
          </label>
          <div className="border border-indigo-200/50 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200 bg-white/90 backdrop-blur-sm">
            <Editor
              height="200px"
              language="markdown"
              value={diagramMermaid}
              onChange={value => {
                setDiagramMermaid(value || '');
                setIsDirty(true);
              }}
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 14,
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                lineNumbers: 'on',
                renderLineHighlight: 'all',
              }}
              theme="vs"
            />
          </div>
        </div>
      </Card>

      {/* Submit Button */}
      <div className="flex justify-end pt-4">
        <button
          type="submit"
          disabled={isUpdating || !isDirty}
          className={`
            relative px-8 py-3 rounded-xl font-semibold text-white
            transition-all duration-300 transform
            ${
              isUpdating || !isDirty
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed opacity-60'
                : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:via-purple-500 hover:to-pink-500 shadow-lg hover:shadow-xl hover:scale-105 active:scale-100'
            }
            overflow-hidden group
          `}
        >
          <span className="relative z-10 flex items-center gap-2">
            <Save className={`w-4 h-4 ${isUpdating ? 'animate-spin' : ''}`} />
            {isUpdating ? 'Saving...' : 'Save Changes'}
          </span>
          {!isUpdating && isDirty && (
            <span className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></span>
          )}
        </button>
      </div>
    </form>
  );
};

export default ModuleEditor;
