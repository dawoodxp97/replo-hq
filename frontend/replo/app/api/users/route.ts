import { NextResponse } from "next/server";
import { addUser, getUsers } from "@/lib/db";

export async function GET() {
  return NextResponse.json({ users: getUsers() });
}

export async function POST(request: Request) {
  try {
    const data = await request.json();
    const { name, email } = data || {};
    if (!name || !email) {
      return NextResponse.json({ error: "name and email are required" }, { status: 400 });
    }
    const created = addUser(name, email);
    return NextResponse.json({ user: created }, { status: 201 });
  } catch (e) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }
}