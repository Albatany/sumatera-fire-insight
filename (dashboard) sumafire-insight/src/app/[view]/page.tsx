import { notFound } from "next/navigation";
import Dashboard from "@/components/dashboard";
import type { View } from "@/lib/types";
const views = [
  "explorer",
  "analytics",
  "clusters",
  "predictions",
  "transparency",
  "research",
];
export function generateStaticParams() {
  return views.map((view) => ({ view }));
}
export default async function Page({
  params,
}: {
  params: Promise<{ view: string }>;
}) {
  const { view } = await params;
  if (!views.includes(view)) notFound();
  return <Dashboard view={view as View} />;
}
