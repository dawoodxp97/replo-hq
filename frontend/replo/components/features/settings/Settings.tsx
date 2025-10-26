"use client";

import React, { useState } from "react";

export default function Settings() {
  const [theme, setTheme] = useState("light");
  const [notifications, setNotifications] = useState(true);

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="p-4 border rounded bg-white">
        <label className="block text-sm font-medium mb-2">Theme</label>
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          className="px-3 py-2 border rounded"
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </div>

      <div className="p-4 border rounded bg-white">
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={notifications}
            onChange={(e) => setNotifications(e.target.checked)}
          />
          Enable notifications
        </label>
      </div>

      <button className="px-4 py-2 bg-blue-600 text-white rounded">Save</button>
    </div>
  );
}