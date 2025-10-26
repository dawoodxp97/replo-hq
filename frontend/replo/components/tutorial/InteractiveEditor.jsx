'use client';

import React from 'react';
import CodeSandbox from './CodeSandbox';

export default function InteractiveEditor({ code = "export default function App(){return (<div>Hello</div>)}", filePath = "App.jsx" }) {
  return (
    <div className="h-full">
      <CodeSandbox code={code} filePath={filePath} />
    </div>
  );
}