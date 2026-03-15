interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
}

export default function Card({ children, className = "", title }: CardProps) {
  return (
    <div className={`bg-surface border border-border rounded-xl p-4 ${className}`}>
      {title && (
        <h3 className="text-foreground font-medium mb-3">{title}</h3>
      )}
      {children}
    </div>
  );
}
