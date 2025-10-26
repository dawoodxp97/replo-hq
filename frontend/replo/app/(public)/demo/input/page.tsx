"use client";

import React, { useState } from "react";
import ReploInput from "@/components/ui/input/Input";

export default function InputDemoPage() {
  const [text, setText] = useState("");
  const [search, setSearch] = useState("");
  const [password, setPassword] = useState("");
  const [number, setNumber] = useState<number | null>(null);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold">Replo Input Demo</h1>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm">Text</label>
          <ReploInput
            kind="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Basic text input"
            allowClear
            responsive
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm">Text with Prefix/Suffix</label>
          <ReploInput
            kind="text"
            placeholder="username"
            prefix={<span>@</span>}
            suffix={<span>.com</span>}
            responsive
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <label className="text-sm">TextArea</label>
          <ReploInput
            kind="textarea"
            placeholder="Write something..."
            rows={4}
            autoSize={{ minRows: 3, maxRows: 8 }}
            showCount
            responsive
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm">Search</label>
          <ReploInput
            kind="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search demos"
            enterButton
            allowClear
            responsive
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm">Password</label>
          <ReploInput
            kind="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            visibilityToggle
            responsive
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm">Number</label>
          <ReploInput
            kind="number"
            value={number ?? undefined}
            onChange={(v) => setNumber(v)}
            placeholder="0-100"
            min={0}
            max={100}
            step={1}
            responsive
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm">Status Error</label>
          <ReploInput kind="text" placeholder="Error" status="error" responsive />
        </div>

        <div className="space-y-2">
          <label className="text-sm">With Addons</label>
          <ReploInput
            kind="search"
            placeholder="domain"
            addonBefore={<span>https://</span>}
            addonAfter={<span>.org</span>}
            responsive
          />
        </div>
      </section>
    </div>
  );
}