interface ProgressBarProps {
  value: number;
  max?: number;
  className?: string;
  color?: "accent" | "danger" | "warning";
}

export default function ProgressBar({
  value,
  max = 100,
  className = "",
  color = "accent",
}: ProgressBarProps) {
  const percent = Math.min(Math.max((value / max) * 100, 0), 100);

  const colorStyles = {
    accent: "bg-accent",
    danger: "bg-danger",
    warning: "bg-warning",
  };

  return (
    <div className={`w-full h-2 bg-border rounded-full overflow-hidden ${className}`}>
      <div
        className={`h-full rounded-full transition-all duration-300 ${colorStyles[color]}`}
        style={{ width: `${percent}%` }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      />
    </div>
  );
}
