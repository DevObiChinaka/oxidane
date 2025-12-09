interface MobileMenuButtonProps {
  showNavbar: boolean;
  onMenuOpen: () => void;
}

export default function MobileMenuButton({ showNavbar, onMenuOpen }: MobileMenuButtonProps) {
  return (
    <>
      {/* Mobile Menu Button - Smart scroll behavior */}
      {/* Mobile Menu Button - Smart scroll behavior */}
      <div className={`lg:hidden fixed top-0 left-0 right-0 z-30 bg-white border-b border-gray-200 px-4 py-3 shadow-sm transition-transform duration-300 ${
        showNavbar ? 'translate-y-0' : '-translate-y-full'
      }`}>
        <button
          onClick={onMenuOpen}
          className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
          <span className="text-sm font-medium">Menu</span>
        </button>
      </div>
      {/* Spacer for fixed navbar on mobile */}
      {/* Spacer for fixed navbar on mobile */}
      {/* Spacer for fixed navbar on mobile */}
      <div className="lg:hidden h-[52px]"></div>
    </>
  );
}
