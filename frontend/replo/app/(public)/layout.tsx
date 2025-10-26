import React from 'react';

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <header></header>
      <main>{children}</main>
      <footer></footer>
    </div>
  );
}