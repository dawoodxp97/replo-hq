export type User = {
  id: string;
  name: string;
  email: string;
};

// Simple in-memory store for demo purposes
const users: User[] = [
  { id: "1", name: "Alice", email: "alice@example.com" },
  { id: "2", name: "Bob", email: "bob@example.com" },
];

export function getUsers(): User[] {
  return users;
}

export function addUser(name: string, email: string): User {
  const id = String(users.length + 1);
  const user = { id, name, email };
  users.push(user);
  return user;
}