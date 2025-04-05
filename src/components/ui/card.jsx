export function Card({ className = "", children }) {
    return (
      <div className={`bg-white rounded-xl p-4 shadow-lg ${className}`}>
        {children}
      </div>
    );
  }
  
  export function CardContent({ className = "", children }) {
    return <div className={className}>{children}</div>;
  }
  