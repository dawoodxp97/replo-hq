"use client";

import { useRouter } from "next/navigation";


export default function DashboardPage() {
  const router = useRouter();

  const handleTutorialSelect = (tutorial: any) => {
    router.push(`/tutorial/${tutorial.id}`);
  };

  return <div>
    Dashboard
  </div>
}