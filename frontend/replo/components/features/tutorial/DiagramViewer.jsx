'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

export default function DiagramViewer({ diagram }) {
  const diagramRef = useRef(null);
  const mermaidInitialized = useRef(false);
  const [isRendering, setIsRendering] = useState(false);
  const [error, setError] = useState(null);

  // Function to sanitize/fix common Mermaid syntax issues
  const sanitizeMermaidCode = code => {
    let sanitized = code;

    // Fix node labels with special characters that need to be quoted
    // Pattern: nodeId[label] where label contains special chars like /, ., (), etc.
    // Handle both regular labels and shape syntax like [/text/], [text], (text), etc.
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

        // Check if this is a shape syntax (starts and ends with /, (, {, etc.)
        const isShapeSyntax =
          (label.startsWith('/') && label.endsWith('/')) ||
          (label.startsWith('(') && label.endsWith(')')) ||
          (label.startsWith('{') && label.endsWith('}')) ||
          (label.startsWith('[') && label.endsWith(']'));

        // For shape syntax like [/index.js/], we need to quote the entire label
        // For regular labels with special chars, quote them too
        const hasSpecialChars = /[\/.()]/.test(label);
        const needsQuoting = hasSpecialChars || /[A-Z]\.[A-Z]/.test(label);

        if (needsQuoting) {
          // Escape any existing quotes and backslashes in the label
          // Must escape backslashes first, then quotes
          const escapedLabel = label
            .replace(/\\/g, '\\\\') // Escape backslashes first
            .replace(/"/g, '\\"'); // Then escape quotes

          // If it's shape syntax, preserve it by quoting the whole thing
          // Otherwise, just quote the label
          return `${nodeId}["${escapedLabel}"]`;
        }

        return match;
      }
    );

    return sanitized;
  };

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

  useEffect(() => {
    if (!diagram || !diagramRef.current || !mermaidInitialized.current) {
      return;
    }

    // Convert escaped newlines to actual newlines
    let diagramContent = diagram.replace(/\\n/g, '\n').trim();

    // Sanitize the diagram content to fix common syntax issues
    diagramContent = sanitizeMermaidCode(diagramContent);

    if (!diagramContent) {
      return;
    }

    // Clear previous content and error state
    setIsRendering(true);
    setError(null);
    diagramRef.current.innerHTML =
      '<div class="text-gray-500">Loading diagram...</div>';

    // Create a unique ID for this diagram
    const id = `mermaid-diagram-${Date.now()}-${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    const renderId = `${id}-render`;

    // Render the diagram with sanitized content
    mermaid
      .render(renderId, diagramContent)
      .then(({ svg }) => {
        if (diagramRef.current) {
          diagramRef.current.innerHTML = svg;
          setIsRendering(false);
        }
      })
      .catch(error => {
        setError(error.message || 'Unknown error');
        setIsRendering(false);
        if (diagramRef.current) {
          diagramRef.current.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
              <p class="text-red-600 font-semibold mb-2">Error rendering diagram</p>
              <p class="text-red-700 text-sm">${
                error.message || 'Unknown error'
              }</p>
              <details class="mt-2">
                <summary class="text-sm text-red-600 cursor-pointer">Show diagram code</summary>
                <pre class="mt-2 p-2 bg-red-100 rounded text-xs overflow-x-auto"><code>${diagramContent
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')}</code></pre>
              </details>
            </div>
          `;
        }
      });
  }, [diagram]);

  if (!diagram) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-500">No diagram available for this module</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg p-4 border border-gray-200 overflow-auto">
      <div
        ref={diagramRef}
        className="mermaid-container flex items-center justify-center min-h-[300px]"
      ></div>
    </div>
  );
}
