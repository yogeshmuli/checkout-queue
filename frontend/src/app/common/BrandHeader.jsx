import brandLogo from '../../assets/images/equilateral_logo.png';

export function BrandHeader() {
  const words = ['Queueless Trial', 'Quick Trial', 'Quality Trial'];

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

            <div className="mt-0.5 hidden items-center gap-1 opacity-80 transition-opacity duration-300 hover:opacity-100 sm:flex sm:gap-2">
              {words.map((word, i) => {
                const wordParts = word.split(' ');

                return (
                  <span key={word} className="contents">
                    {i > 0 ? <span className="text-[0.6rem] text-brand-red">|</span> : null}
                    <p className="whitespace-nowrap text-[clamp(0.5rem,1.2vw,0.7rem)] font-bold uppercase tracking-[0.15em] text-gray-800">
                      {wordParts.map((part, partIndex) => {
                        const isTrial = part.toUpperCase() === 'TRIAL';
                        const isFirstWord = partIndex === 0;

                        let q = '';
                        let u = '';
                        let middlePart = '';
                        let t = '';
                        let endPart = '';

                        if (isTrial) {
                          t = part.substring(0, 1);
                          endPart = part.substring(1);
                        } else if (isFirstWord) {
                          q = part.substring(0, 1);
                          u = part.substring(1, 2);
                          middlePart = part.substring(2);
                        }

                        return (
                          <span key={`${word}-${partIndex}`}>
                            {partIndex > 0 ? <span> </span> : null}
                            <span className="text-brand-red">{q}</span>
                            <span className="text-brand-red">{u}</span>
                            {middlePart}
                            <span className="text-brand-red">{t}</span>
                            {endPart}
                          </span>
                        );
                      })}
                    </p>
                  </span>
                );
              })}
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
