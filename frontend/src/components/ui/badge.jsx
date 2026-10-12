import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "border-border bg-card text-foreground",
        high: "border-transparent bg-[#fee2e2] text-[#dc2626]",
        medium: "border-transparent bg-[#fef3c7] text-[#b45309]",
        low: "border-transparent bg-[#d1fae5] text-[#059669]",
        green: "border-transparent bg-[#d1fae5] text-[#059669]",
        red: "border-transparent bg-[#fee2e2] text-[#dc2626]",
        amber: "border-transparent bg-[#fef3c7] text-[#b45309]",
        gray: "border-transparent bg-[#eef0f2] text-[#5b6672]",
        payer: "border-transparent bg-secondary text-[#6b5b4b]",
      },
    },
    defaultVariants: { variant: "default" },
  },
)

function Badge({ className, variant, ...props }) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
