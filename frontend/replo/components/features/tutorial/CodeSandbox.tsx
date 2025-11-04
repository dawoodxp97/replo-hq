'use client';

import { useMemo, useEffect, useRef } from 'react';
import {
  SandpackProvider,
  SandpackLayout,
  SandpackCodeEditor,
  SandpackPreview,
  useSandpack,
} from '@codesandbox/sandpack-react';

interface CodeSandboxProps {
  code: string;
  filePath: string;
}

// Inner component that syncs external code changes with Sandpack
const SandpackContent = ({
  code,
  filePath,
  initialFiles,
  template,
}: {
  code: string;
  filePath: string;
  initialFiles: Record<string, { code: string }>;
  template: string;
}) => {
  const { sandpack } = useSandpack();
  const lastCodeRef = useRef<string>(code);
  const lastFilePathRef = useRef<string>(filePath);
  const isInitialMount = useRef<boolean>(true);

  // Update files when external code or filePath changes
  useEffect(() => {
    // Skip the first render since files are already set via props
    if (isInitialMount.current) {
      isInitialMount.current = false;
      lastCodeRef.current = code;
      lastFilePathRef.current = filePath;
      return;
    }

    // Only update if code or filePath changed from outside (not from internal edits)
    if (code !== lastCodeRef.current || filePath !== lastFilePathRef.current) {
      lastCodeRef.current = code;
      lastFilePathRef.current = filePath;

      // Determine which file to update based on template and filePath
      const fileName = filePath.split('/').pop() || 'example.js';
      const isIndexFile = fileName.toLowerCase().includes('index');
      const importsApp =
        code.includes('import App') ||
        code.includes("from './App'") ||
        code.includes('from "./App"');

      if (template === 'react') {
        if ((importsApp || code.includes('ReactDOM.render')) && isIndexFile) {
          let indexCode = code;
          if (code.includes('ReactDOM.render')) {
            indexCode = indexCode.replace(
              /import ReactDOM from ['"]react-dom['"];?/g,
              "import ReactDOM from 'react-dom/client';"
            );

            const renderMatch = indexCode.match(
              /ReactDOM\.render\s*\(\s*([\s\S]*?),\s*document\.getElementById\(['"]root['"]\)\s*\)/
            );
            if (renderMatch) {
              const componentToRender = renderMatch[1].trim();
              indexCode = indexCode.replace(
                /ReactDOM\.render\s*\(\s*[\s\S]*?,\s*document\.getElementById\(['"]root['"]\)\s*\)/,
                `const root = ReactDOM.createRoot(document.getElementById('root'));\nroot.render(${componentToRender});`
              );
            }
          }
          sandpack.updateFile('/index.jsx', indexCode);
        } else {
          sandpack.updateFile('/App.jsx', code);
        }
      } else {
        sandpack.updateFile(`/${fileName}`, code);
      }
    }
  }, [code, filePath, template, sandpack]);

  return (
    <SandpackLayout>
      <SandpackCodeEditor
        showLineNumbers={true}
        showInlineErrors={true}
        wrapContent={true}
        style={{ height: '50%' }}
      />
      <SandpackPreview
        style={{ height: '50%' }}
        showRefreshButton={true}
        showOpenInCodeSandbox={false}
      />
    </SandpackLayout>
  );
};

const CodeSandbox = ({ code, filePath }: CodeSandboxProps) => {
  // Determine file extension
  const fileExtension = filePath.split('.').pop()?.toLowerCase() || 'js';

  // Detect if code contains React/JSX
  const isReactCode = useMemo(() => {
    return (
      code.includes('import React') ||
      code.includes('from "react"') ||
      code.includes("from 'react'") ||
      code.includes('ReactDOM') ||
      code.includes('React.StrictMode') ||
      (code.includes('<') &&
        code.includes('>') &&
        (code.includes('</') || code.includes('/>')))
    );
  }, [code]);

  // Determine template based on file extension and code content
  const template = useMemo(() => {
    // If code contains React, use react template
    if (isReactCode) {
      return 'react';
    }

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
  }, [fileExtension, isReactCode]);

  // Create files object
  const files = useMemo(() => {
    const fileName = filePath.split('/').pop() || 'example.js';
    const isIndexFile = fileName.toLowerCase().includes('index');
    const importsApp =
      code.includes('import App') ||
      code.includes("from './App'") ||
      code.includes('from "./App"');

    // Basic files setup
    const baseFiles: Record<string, { code: string }> = {};

    // For react template
    if (template === 'react') {
      // If code imports App or is an index file with ReactDOM.render
      if ((importsApp || code.includes('ReactDOM.render')) && isIndexFile) {
        // Convert ReactDOM.render to React 18 createRoot API and use .jsx extension
        let indexCode = code;
        if (code.includes('ReactDOM.render')) {
          // Replace import
          indexCode = indexCode.replace(
            /import ReactDOM from ['"]react-dom['"];?/g,
            "import ReactDOM from 'react-dom/client';"
          );

          // Replace ReactDOM.render with createRoot - handle common patterns
          if (indexCode.includes('ReactDOM.render')) {
            // Find the ReactDOM.render call and the component being rendered
            const renderMatch = indexCode.match(
              /ReactDOM\.render\s*\(\s*([\s\S]*?),\s*document\.getElementById\(['"]root['"]\)\s*\)/
            );
            if (renderMatch) {
              const componentToRender = renderMatch[1].trim();
              indexCode = indexCode.replace(
                /ReactDOM\.render\s*\(\s*[\s\S]*?,\s*document\.getElementById\(['"]root['"]\)\s*\)/,
                `const root = ReactDOM.createRoot(document.getElementById('root'));\nroot.render(${componentToRender});`
              );
            }
          }
        }

        // Use .jsx extension for JSX syntax
        baseFiles['/index.jsx'] = { code: indexCode };

        // Create stub files for common imports
        if (
          indexCode.includes("from './index.css'") ||
          indexCode.includes('from "./index.css"')
        ) {
          baseFiles['/index.css'] = { code: '/* Add your styles here */' };
        }

        if (
          indexCode.includes("from './reportWebVitals'") ||
          indexCode.includes('from "./reportWebVitals"')
        ) {
          baseFiles['/reportWebVitals.js'] = {
            code: `const reportWebVitals = (onPerfEntry) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    });
  }
};

export default reportWebVitals;`,
          };
        }

        // Create a basic App component if it's being imported but doesn't exist in the code
        if (
          importsApp &&
          !code.includes('export default function App') &&
          !code.includes('const App =') &&
          !code.includes('function App(')
        ) {
          baseFiles['/App.jsx'] = {
            code: `export default function App() {
  return (
    <div>
      <h1>Hello World</h1>
      <p>Edit App.jsx to see changes.</p>
    </div>
  );
}`,
          };
        }
      } else {
        // For component files, use /App.jsx (Sandpack's default)
        baseFiles['/App.jsx'] = { code };
      }
    } else {
      // For other templates, use the original fileName
      baseFiles[`/${fileName}`] = { code };
    }

    return baseFiles;
  }, [code, filePath, template]);

  // Create a stable key based on filePath and template to force re-initialization only when these change
  const sandpackKey = useMemo(
    () => `${template}-${filePath}`,
    [template, filePath]
  );

  return (
    <div className="h-full">
      <SandpackProvider
        key={sandpackKey}
        template={template}
        files={files}
        options={{
          recompileMode: 'immediate', // Recompile immediately on changes
          recompileDelay: 0, // No delay
        }}
      >
        <SandpackContent
          code={code}
          filePath={filePath}
          initialFiles={files}
          template={template}
        />
      </SandpackProvider>
    </div>
  );
};

export default CodeSandbox;
