export function BrandMark({ className = 'h-5 w-5' }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" fill="none" className={className} aria-hidden="true">
      <rect width="64" height="64" rx="18" fill="currentColor" />
      <path d="M32 14L46 20V31C46 40.5 39.8 49.1 32 51C24.2 49.1 18 40.5 18 31V20L32 14Z" fill="white" fillOpacity="0.96" />
      <path d="M25 32.5L29.5 37L39.5 27" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
