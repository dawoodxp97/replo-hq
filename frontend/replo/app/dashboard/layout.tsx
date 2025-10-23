import Navbar from "@/components/Navbar";

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <section>
      <Navbar />
      <div className="mx-auto max-w-5xl p-6">
        {children}
      </div>
    </section>
  );
}