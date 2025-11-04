'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer = ({ content }: MarkdownRendererProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [processedContent, setProcessedContent] = useState<string>('');
  const mermaidInitialized = useRef(false);

  // Initialize mermaid once
  useEffect(() => {
    if (!mermaidInitialized.current) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
      });
      mermaidInitialized.current = true;
    }
  }, []);

  // Function to sanitize/fix common Mermaid syntax issues
  const sanitizeMermaidCode = (code: string): string => {
    let sanitized = code;

    // Fix node labels with special characters that need to be quoted
    // Pattern: nodeId[label] where label contains special chars like (), ., etc.
    // Examples: C[ReactDOM.render()] -> C["ReactDOM.render()"]
    //           D[React.StrictMode] -> D["React.StrictMode"]
    sanitized = sanitized.replace(
      /(\w+)\[([^\]]+)\]/g,
      (match, nodeId, label) => {
        // Skip if already quoted
        if (
          (label.startsWith('"') && label.endsWith('"')) ||
          (label.startsWith("'") && label.endsWith("'"))
        ) {
          return match;
        }

        // Check if label contains special characters that need quoting
        // Characters that cause issues in Mermaid: parentheses, dots before capitals, etc.
        const needsQuoting =
          /[().]/.test(label) || // Contains parentheses or dots
          /[A-Z]\.[A-Z]/.test(label); // Pattern like "React.StrictMode"

        if (needsQuoting) {
          // Escape any existing quotes and backslashes in the label
          // Must escape backslashes first, then quotes
          const escapedLabel = label
            .replace(/\\/g, '\\\\') // Escape backslashes first
            .replace(/"/g, '\\"'); // Then escape quotes
          return `${nodeId}["${escapedLabel}"]`;
        }

        return match;
      }
    );

    return sanitized;
  };

  // Function to process markdown content and extract mermaid diagrams
  const processMarkdown = (markdown: string) => {
    let diagramCounter = 0;
    const mermaidDiagrams: Array<{ id: string; content: string }> = [];

    // Process headers
    let processed = markdown
      .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold my-4">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold my-3">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-medium my-2">$1</h3>');

    // Process mermaid code blocks first (before other code blocks)
    // Match ```mermaid followed by optional whitespace/newline, then content, then closing ```
    processed = processed.replace(
      /```mermaid\s*([\s\S]*?)```/g,
      (match, diagramContent) => {
        const id = `mermaid-${Date.now()}-${diagramCounter++}`;
        // Sanitize the diagram content to fix common syntax issues
        const sanitizedContent = sanitizeMermaidCode(diagramContent.trim());
        mermaidDiagrams.push({
          id,
          content: sanitizedContent,
        });
        return `<div id="${id}" class="mermaid-diagram my-4 min-h-[200px] flex items-center justify-center bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div class="text-gray-500">Loading diagram...</div>
        </div>`;
      }
    );

    // Process regular code blocks (non-mermaid) - only match if not already processed
    // This regex will not match mermaid blocks since they've already been replaced with HTML
    processed = processed.replace(/```([\s\S]*?)```/g, (match, code) => {
      // Regular code block
      return `<pre class="bg-gray-100 p-4 rounded my-4 overflow-x-auto"><code>${code.trim()}</code></pre>`;
    });

    // Process inline code
    processed = processed.replace(
      /`([^`]+)`/g,
      '<code class="rl-code bg-gray-100 px-1 rounded">$1</code>'
    );

    // Process lists
    processed = processed.replace(
      /^\s*\d+\.\s+(.*$)/gm,
      '<li class="ml-6 list-decimal">$1</li>'
    );
    processed = processed.replace(
      /^\s*\*\s+(.*$)/gm,
      '<li class="ml-6 list-disc">$1</li>'
    );

    // Process paragraphs
    processed = processed.replace(
      /^(?!<[hl]|<li|<pre|<div)(.*$)/gm,
      '<p class="my-2">$1</p>'
    );

    // Process links
    processed = processed.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" class="text-blue-600 hover:underline">$1</a>'
    );

    // Process emphasis
    processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    processed = processed.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    return { processed, mermaidDiagrams };
  };

  // Store mermaid diagrams in a ref so they're available in the rendering effect
  const mermaidDiagramsRef = useRef<Array<{ id: string; content: string }>>([]);

  // Process markdown when content changes
  useEffect(() => {
    const { processed, mermaidDiagrams } = processMarkdown(content);
    mermaidDiagramsRef.current = mermaidDiagrams;
    setProcessedContent(processed);
  }, [content]);

  // Separate effect to render diagrams after DOM is updated
  useEffect(() => {
    const mermaidDiagrams = mermaidDiagramsRef.current;

    if (mermaidDiagrams.length === 0) {
      return;
    }

    // Function to render a single diagram
    const renderDiagram = (id: string, diagramContent: string): boolean => {
      const element = document.getElementById(id);
      if (!element) {
        return false; // Element not found yet
      }

      // Check if element already has SVG content (already rendered)
      const hasSvg = element.querySelector('svg');
      if (hasSvg) {
        return true; // Already rendered, skip
      }

      // Check if element still has loading state (not yet rendered)
      const hasLoadingState = element.querySelector('.text-gray-500');
      const isLoading =
        hasLoadingState || element.textContent?.includes('Loading diagram');

      // Clear the loading text
      element.innerHTML = '';

      // Create a unique render ID for mermaid
      const renderId = `${id}-render-${Math.random()
        .toString(36)
        .substr(2, 9)}`;

      // Sanitize the diagram content before rendering
      const sanitizedContent = sanitizeMermaidCode(diagramContent);

      mermaid
        .render(renderId, sanitizedContent)
        .then(({ svg }) => {
          const updatedElement = document.getElementById(id);
          if (updatedElement) {
            updatedElement.innerHTML = svg;
            updatedElement.className =
              'mermaid-diagram my-4 flex items-center justify-center bg-gray-50 rounded-lg p-4 border border-gray-200 overflow-auto';
          }
        })
        .catch(error => {
          console.error('Error rendering mermaid diagram:', error);
          const errorElement = document.getElementById(id);
          if (errorElement) {
            // Extract error details
            const errorMessage = error.message || 'Unknown error';

            // Format the error display with helpful hints
            const hasParentheses =
              diagramContent.includes('(') && diagramContent.includes(')');
            const commonFixes = hasParentheses
              ? '<div class="text-xs text-red-600 mt-2 bg-red-100 p-2 rounded border border-red-200"><strong>💡 Common Fix:</strong> Node labels with parentheses or special characters should be wrapped in quotes. Change <code class="bg-red-200 px-1 rounded">C[ReactDOM.render()]</code> to <code class="bg-red-200 px-1 rounded">C["ReactDOM.render()"]</code></div>'
              : '';

            errorElement.innerHTML = `
              <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex items-start gap-2 mb-3">
                  <svg class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <div class="flex-1">
                    <h4 class="font-semibold text-red-800 mb-1">Mermaid Diagram Syntax Error</h4>
                    <p class="text-red-700 text-sm mb-2 font-mono text-xs bg-red-100 px-2 py-1 rounded">${errorMessage}</p>
                    ${commonFixes}
                    <details class="mt-3">
                      <summary class="text-sm text-red-600 cursor-pointer hover:text-red-800 font-medium">
                        Show diagram code
                      </summary>
                      <pre class="mt-2 p-3 bg-red-100 rounded text-xs overflow-x-auto text-red-900 border border-red-200 font-mono"><code>${diagramContent
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;')
                        .replace(/"/g, '&quot;')}</code></pre>
                    </details>
                  </div>
                </div>
              </div>
            `;
            errorElement.className =
              'mermaid-diagram my-4 flex items-center justify-center bg-red-50 rounded-lg p-4 border border-red-200';
          }
        });

      return true; // Rendering started
    };

    // Function to render all diagrams with retry logic
    const renderDiagrams = (attempt = 0) => {
      const maxAttempts = 5;
      let allRendered = true;

      mermaidDiagrams.forEach(({ id, content: diagramContent }) => {
        const rendered = renderDiagram(id, diagramContent);
        if (!rendered) {
          allRendered = false;
        }
      });

      // If not all diagrams were rendered and we haven't exceeded max attempts, retry
      if (!allRendered && attempt < maxAttempts) {
        setTimeout(() => {
          renderDiagrams(attempt + 1);
        }, 100 * (attempt + 1));
      }
    };

    // Use requestAnimationFrame to ensure DOM is ready after React updates
    const timeoutId = setTimeout(() => {
      renderDiagrams();
    }, 50);

    // Also try after a longer delay as fallback
    const fallbackTimeoutId = setTimeout(() => {
      renderDiagrams();
    }, 300);

    return () => {
      clearTimeout(timeoutId);
      clearTimeout(fallbackTimeoutId);
    };
  }, [processedContent]);

  return (
    <div
      ref={containerRef}
      className="markdown-content prose max-w-none"
      dangerouslySetInnerHTML={{ __html: processedContent }}
    />
  );
};

export default MarkdownRenderer;
