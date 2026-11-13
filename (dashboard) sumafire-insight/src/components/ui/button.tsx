import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
// Adapted from the shadcn/ui Button pattern (MIT); tokens are project-specific.
const styles = cva("button", {
  variants: {
    variant: { default: "primary", outline: "button-outline", ghost: "ghost" },
    size: { default: "", sm: "small", icon: "icon" },
  },
  defaultVariants: { variant: "default", size: "default" },
});
export function Button({
  asChild = false,
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof styles> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp className={cn(styles({ variant, size, className }))} {...props} />
  );
}
