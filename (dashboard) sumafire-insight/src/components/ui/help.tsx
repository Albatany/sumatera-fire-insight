"use client";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tooltip from "@radix-ui/react-tooltip";
import { FolderInput, X } from "lucide-react";
import { Button } from "./button";
export function Tip({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Tooltip.Provider delayDuration={200}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content className="tooltip" sideOffset={6}>
            {label}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
export function ImportHelp() {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <Button variant="outline" size="sm">
          <FolderInput size={15} />
          Connect data
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog">
          <Dialog.Title>Connect your research snapshot</Dialog.Title>
          <Dialog.Description>
            Import a copy. Original research files remain unchanged.
          </Dialog.Description>
          <ol>
            <li>
              Extract the original research ZIP outside this website folder.
            </li>
            <li>Install the Python dependencies in .venv.</li>
            <li>
              Run:
              <pre>
                npm run data:connect-research --
                &quot;/path/to/Paket_UTS_Klasifikasi_F1E325063&quot;
              </pre>
            </li>
            <li>
              Check the snapshot:<pre>npm run data:verify</pre>
            </li>
          </ol>
          <p>
            For new NASA CSVs, configure <code>config/dataset.json</code>, copy
            inputs to <code>incoming/raw</code>, then run{" "}
            <code>data:validate</code> and <code>data:build</code>.
          </p>
          <p className="notice">
            The page detects imported snapshots every 30 seconds. This is not a
            live NASA feed.
          </p>
          <Dialog.Close asChild>
            <Button
              className="dialog-close"
              variant="ghost"
              size="icon"
              aria-label="Close import instructions"
            >
              <X size={18} />
            </Button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
