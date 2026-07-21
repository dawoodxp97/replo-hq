'use client';

import React from 'react';
import CodeSandbox from '@/components/features/tutorial/CodeSandbox';

interface InteractiveEditorProps {
  code?: string;
  filePath?: string;
}

export default function InteractiveEditor({
  code = 'export default function App(){return (<div>Hello</div>)}',
  filePath = 'App.jsx',
}: InteractiveEditorProps) {
  return (
    <div className="h-full">
      <CodeSandbox code={code} filePath={filePath} />
    </div>
  );
}
