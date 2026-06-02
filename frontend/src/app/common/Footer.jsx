const footerLinks = [
  { name: 'Terms', href: '#' },
  { name: 'Privacy', href: '#' },
  { name: 'Contact', href: '#' },
  { name: "FAQ's", href: '#' },
];

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-8 border-t border-white/20 bg-gradient-to-br from-red-500 to-red-700 text-white shadow-2xl">
      <div className="container mx-auto px-6 py-4">
        <div className="flex flex-col items-center justify-between gap-3 md:flex-row md:gap-0">
          <div className="order-2 flex flex-col text-center md:order-1 md:flex-row md:items-center md:gap-4 md:text-left">
            <h3 className="text-lg font-black tracking-tight text-white">the Equilateral</h3>
            <p className="hidden text-xs font-medium text-white/80 md:block">|</p>
            <p className="text-xs font-medium text-white/80">&copy; {currentYear} All rights reserved.</p>
          </div>

          <nav className="order-1 flex flex-wrap justify-center gap-x-6 gap-y-1 md:order-2 md:justify-end" aria-label="Footer navigation">
            {footerLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="group relative whitespace-nowrap text-sm font-medium text-white/90 transition-colors duration-300 hover:text-white"
              >
                {link.name}
                <span className="absolute -bottom-0.5 left-0 h-0.5 w-0 rounded-full bg-white opacity-0 transition-all duration-300 ease-out group-hover:w-full group-hover:opacity-100" />
              </a>
            ))}
          </nav>
        </div>
      </div>
    </footer>
  );
}
