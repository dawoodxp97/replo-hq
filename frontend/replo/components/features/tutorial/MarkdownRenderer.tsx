'use client';

import { useEffect } from 'react';
import mermaid from 'mermaid';

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer = ({ content }: MarkdownRendererProps) => {
  useEffect(() => {
    // Initialize mermaid
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
    });
    
    // Render mermaid diagrams
    mermaid.run();
  }, [content]);

  // Function to process markdown content
  const processMarkdown = (markdown: string) => {
    // This is a simplified markdown processor
    // In a real implementation, you would use a library like react-markdown
    
    // Process headers
    let processed = markdown
      .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold my-4">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold my-3">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-medium my-2">$1</h3>');
    
    // Process code blocks
    processed = processed.replace(/```([\s\S]*?)```/g, (match, code) => {
      // Check if it's a mermaid diagram
      if (match.includes('```mermaid')) {
        return `<div class="mermaid my-4">${code.replace('mermaid\n', '')}</div>`;
      }
      
      // Regular code block
      return `<pre class="bg-gray-100 p-4 rounded my-4 overflow-x-auto"><code>${code}</code></pre>`;
    });
    
    // Process inline code
    processed = processed.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>');
    
    // Process lists
    processed = processed.replace(/^\s*\d+\.\s+(.*$)/gm, '<li class="ml-6 list-decimal">$1</li>');
    processed = processed.replace(/^\s*\*\s+(.*$)/gm, '<li class="ml-6 list-disc">$1</li>');
    
    // Process paragraphs
    processed = processed.replace(/^(?!<[hl]|<li|<pre|<div)(.*$)/gm, '<p class="my-2">$1</p>');
    
    // Process links
    processed = processed.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:underline">$1</a>');
    
    // Process emphasis
    processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    processed = processed.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    return processed;
  };

  return (
    <div 
      className="markdown-content prose max-w-none"
      dangerouslySetInnerHTML={{ __html: processMarkdown(content) }}
    />
  );
};

export default MarkdownRenderer;