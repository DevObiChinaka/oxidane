interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'white' | 'dark';
}

export default function Logo({ className = '', size = 'md', variant = 'default' }: LogoProps) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12', 
    lg: 'w-16 h-16'
  };

  const iconSizes = {
    sm: 'w-5 h-5',
    md: 'w-8 h-8',
    lg: 'w-10 h-10'
  };

  const backgroundClasses = {
    default: 'bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-700',
    white: 'bg-white border border-gray-200',
    dark: 'bg-gray-900'
  };

  const iconColors = {
    default: 'text-white',
    white: 'text-blue-600',
    dark: 'text-white'
  };

  return (
    <div className={`${sizeClasses[size]} ${backgroundClasses[variant]} rounded-xl flex items-center justify-center shadow-lg ${className}`}>
      <svg className={`${iconSizes[size]} ${iconColors[variant]}`} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Professional Forex Trading Logo */}
        <path d="M8 20L16 12L24 20L32 8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M28 8H32V12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
        <circle cx="16" cy="12" r="2" fill="currentColor"/>
        <circle cx="24" cy="20" r="2" fill="currentColor"/>
        <circle cx="32" cy="8" r="2" fill="currentColor"/>
        {/* Currency symbols integrated */}
        <text x="4" y="32" fontSize="8" fill="currentColor" fontWeight="bold">$</text>
        <text x="18" y="32" fontSize="8" fill="currentColor" fontWeight="bold">€</text>
        <text x="32" y="32" fontSize="8" fill="currentColor" fontWeight="bold">¥</text>
        {/* Company initial */}
        <text x="20" y="26" fontSize="6" fill="currentColor" fontWeight="bold" textAnchor="middle">OX</text>
      </svg>
    </div>
  );
}