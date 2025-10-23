"use client";

import { Sandpack } from "@codesandbox/sandpack-react";
import { useEffect, useState } from "react";

export default function Home() {
  const [backendStatus, setBackendStatus] = useState("checking...");

  // Test the API connection
  useEffect(() => {
    fetch("http://localhost:8000/api/v1/health")
      .then((res) => res.json())
      .then((data) => {
        setBackendStatus(`Connected! Message: "${data.message}"`);
      })
      .catch((err) => {
        setBackendStatus("Failed to connect. Is the backend running?");
      });
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center p-24">
      <h1 className="text-4xl font-bold mb-8">
        AI-Powered Code Tutorial Generator
      </h1>

      <div className="mb-8">
        <p><strong>Backend Status:</strong> {backendStatus}</p>
      </div>

      <div className="w-full max-w-4xl">
        <h2 className="text-2xl mb-4">Interactive Sandbox Test:</h2>
        <Sandpack
          template="react"
          files={{
            "/App.js": `export default function App() {
  return <h1>Hello, Sandpack!</h1>
}`,
          }}
        />
      </div>
    </main>
  );
}