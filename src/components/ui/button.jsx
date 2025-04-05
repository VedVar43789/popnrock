export function Button({ className, children, ...props }) {
    return (
      <button
        className={`bg-pink-600 hover:bg-pink-700 text-white font-bold py-2 px-4 rounded-xl ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
  