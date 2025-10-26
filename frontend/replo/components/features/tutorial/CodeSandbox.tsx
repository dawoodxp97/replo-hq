'use client';

import { useMemo } from 'react';
import {
  SandpackProvider,
  SandpackLayout,
  SandpackCodeEditor,
  SandpackPreview,
} from '@codesandbox/sandpack-react';

interface CodeSandboxProps {
  code: string;
  filePath: string;
}

const CodeSandbox = ({ code, filePath }: CodeSandboxProps) => {
  // Determine file extension
  const fileExtension = filePath.split('.').pop()?.toLowerCase() || 'js';
  
  // Determine template based on file extension
  const template = useMemo(() => {
    switch (fileExtension) {
      case 'ts':
      case 'tsx':
        return 'vanilla-ts';
      case 'jsx':
        return 'react';
      case 'py':
        return 'node'; // Python not supported, fallback to node
      default:
        return 'vanilla';
    }
  }, [fileExtension]);
  
  // Create files object
  const files = useMemo(() => {
    const fileName = filePath.split('/').pop() || 'example.js';
    
    // Basic files setup
    const baseFiles: Record<string, { code: string }> = {
      [fileName]: { code },
    };
    
    // Add necessary files based on template
    if (template === 'react') {
      baseFiles['/index.html'] = {
        code: `
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>React App</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
        `,
      };
      
      baseFiles['/index.js'] = {
        code: `
import React from 'react';
import ReactDOM from 'react-dom';
import App from './${fileName}';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);
        `,
      };
    }
    
    return baseFiles;
  }, [code, filePath, template]);

  return (
    <div className="h-full">
      <SandpackProvider template={template} files={files}>
        <SandpackLayout>
          <SandpackCodeEditor
            showLineNumbers={true}
            showInlineErrors={true}
            wrapContent={true}
            style={{ height: '50%' }}
          />
          <SandpackPreview style={{ height: '50%' }} />
        </SandpackLayout>
      </SandpackProvider>
    </div>
  );
};

export default CodeSandbox;