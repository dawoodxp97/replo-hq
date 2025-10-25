export default function HomeLayout({ children }: { children: React.ReactNode }) {
  return (
    <section className="min-h-screen bg-white">
      {children}
    </section>
  );
}