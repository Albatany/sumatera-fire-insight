import { Database, AlertCircle } from "lucide-react";
import { ImportHelp } from "./ui/help";
export function Panel({
  title,
  sub,
  action,
  children,
  className = "",
}: {
  title: string;
  sub?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={"panel " + className}>
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {sub && <p>{sub}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function Empty({
  title = "Dataset not connected",
  text = "Import NASA FIRMS observations to explore the data.",
  compact = false,
}: {
  title?: string;
  text?: string;
  compact?: boolean;
}) {
  return (
    <div className={"empty " + (compact ? "compact" : "")}>
      <span className="empty-icon">
        <Database size={23} />
      </span>
      <h3>{title}</h3>
      <p>{text}</p>
      {!compact && <ImportHelp />}
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading" role="status" aria-label="Loading data">
      <span className="sr-only">Loading data</span>
      <div />
      <div />
      <div />
    </div>
  );
}
export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="error" role="alert">
      <AlertCircle size={20} />
      <div>
        <strong>Data request could not be completed</strong>
        <p>{message}</p>
      </div>
    </div>
  );
}
