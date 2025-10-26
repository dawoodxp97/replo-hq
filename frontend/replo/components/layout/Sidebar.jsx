"use client";

import Link from "next/link";
import { useGlobalStore } from "@/store/useGlobalStore";

export default function Sidebar() {
  const { isSidebarOpen } = useGlobalStore();

  if (!isSidebarOpen) return null;

  return (
    <aside className="w-64 bg-gray-100 border-r p-4 h-full">
      <nav className="space-y-2 text-sm">
        <Link className="block hover:underline" href="/dashboard">Dashboard</Link>
        <Link className="block hover:underline" href="/library">Library</Link>
        <Link className="block hover:underline" href="/progress">Progress</Link>
        <Link className="block hover:underline" href="/authoring">Authoring</Link>
        <Link className="block hover:underline" href="/settings">Settings</Link>
      </nav>
    </aside>
  );
}