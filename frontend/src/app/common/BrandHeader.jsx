import brandLogo from '../../assets/images/equilateral_logo.png';

export function BrandHeader() {
  const taglineParts = ['Queueless Transaction', 'Quick Trial', 'Queue Transformation'];

  return (
    <header className=" bg-[transparent]">
      <div className="w-full px-4 py-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 flex-1 items-center justify-start">
            <div className="relative h-12 w-auto origin-left transition-all duration-300 hover:scale-110 sm:h-16 md:h-20">
              <img
                src={brandLogo}
                alt="The Equilateral Logo"
                className="h-full w-auto object-cover object-left"
              />
            </div>
          </div>

          <div className="flex-none px-1 text-center">
            <a href="/" className="group relative">
              <h1 className="cursor-pointer select-none text-[clamp(1.5rem,5vw,3rem)] font-extrabold leading-none tracking-tighter text-brand-red transition-all duration-500 group-hover:scale-110 group-hover:drop-shadow-sm">
                QuT
              </h1>
            </a>

            <div className="mt-0.5 hidden items-center gap-2 opacity-80 transition-opacity duration-300 hover:opacity-100 sm:flex">
              {taglineParts.map((part, index) => (
                <span key={part} className="contents">
                  {index > 0 ? <span className="text-[0.6rem] text-brand-red">·</span> : null}
                  <p className="whitespace-nowrap text-[clamp(0.5rem,1.2vw,0.7rem)] font-bold text-gray-800">
                    {part}
                  </p>
                </span>
              ))}
            </div>
          </div>

          <div className="flex min-w-0 flex-1 items-center justify-end">
            <div className="relative h-12 w-auto origin-right transition-all duration-300 hover:scale-110 sm:h-16 md:h-20">
              <img
                src={brandLogo}
                alt="Brand Logo"
                className="h-full w-auto object-cover object-right"
                onError={(event) => {
                  event.currentTarget.style.display = 'none';
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
