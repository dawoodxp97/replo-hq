import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="w-full border-b bg-white">
      <div className="mx-auto max-w-5xl flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg">Replo</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <Link className="text-gray-700 hover:text-black" href="/">Home</Link>
          <Link className="text-gray-700 hover:text-black" href="/dashboard">Dashboard</Link>
          <Link className="text-gray-700 hover:text-black" href="/login">Login</Link>
          <Link className="text-gray-700 hover:text-black" href="/register">Register</Link>
        </div>
      </div>
    </nav>
  );
}