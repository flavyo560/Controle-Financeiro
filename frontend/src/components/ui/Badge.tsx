type BadgeVariant = "default" | "success" | "danger" | "warning" | "muted" | "info";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-accent/10 text-accent",
  success: "bg-accent/10 text-accent",
  danger: "bg-danger/10 text-danger",
  warning: "bg-warning/10 text-warning",
  muted: "bg-muted/10 text-muted",
  info: "bg-blue-500/10 text-blue-400",
};

export default function Badge({ children, variant = "default", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
