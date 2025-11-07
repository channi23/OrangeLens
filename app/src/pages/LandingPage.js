import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Logo from '../assets/pramana-logo-black.png';
import AboutPage from './AboutPage';

const LandingPage = () => {
  const aboutRef = useRef(null);
  const howToUseRef = useRef(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showFounderDetails, setShowFounderDetails] = useState(false);

  const scrollToHowToUse = () => {
    howToUseRef.current?.scrollIntoView({ behavior: 'smooth' });
    setIsMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-indigo-50 via-purple-50 to-purple-100 text-gray-900 flex flex-col overflow-hidden">
      <header className="flex items-center justify-between px-4 md:px-10 py-6 fixed top-0 left-0 w-full bg-white/60 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="flex items-center gap-3 flex-shrink-0">
          <img src={Logo} alt="Pramana Logo" className="h-8 w-8 flex-shrink-0" />
          <h1 className="font-semibold text-lg tracking-wide truncate">Pramana</h1>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-base">
          <a href="https://github.com/channi23/OrangeLens" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]">GitHub</a>
          <Link to="/about" className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]">About</Link>
          <a href="https://github.com/channi23/OrangeLens/releases/download/v4.0/Pramana-Version-4.apk" className="rounded-full px-5 py-2 text-base font-medium border border-indigo-300 hover:border-indigo-500 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] hover:bg-gradient-to-r hover:from-indigo-600 hover:to-purple-600 hover:text-white">
            Download App
          </a>
        </nav>
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="block md:hidden text-gray-600 hover:text-gray-900 focus:outline-none"
          aria-label="Toggle menu"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
            {isMenuOpen ? (
              <path d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path d="M3 12h18M3 6h18M3 18h18" />
            )}
          </svg>
        </button>
      </header>
      {isMenuOpen && (
        <nav className="flex flex-col items-center gap-4 bg-white/90 py-4 fixed top-16 left-0 w-full z-40 border-b border-gray-200 md:hidden text-base px-4">
          <a href="https://github.com/channi23/OrangeLens" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 w-full text-center bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]">GitHub</a>
          <Link to="/about" className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 w-full text-center bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]">About</Link>
          <a href="https://github.com/channi23/OrangeLens/releases/download/v4.0/Pramana-Version-4.apk" className="rounded-full px-5 py-2 text-base font-medium border border-indigo-300 hover:border-indigo-500 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] hover:bg-gradient-to-r hover:from-indigo-600 hover:to-purple-600 hover:text-white w-full text-center">
            Download App
          </a>
        </nav>
      )}

      <main className="flex-grow">
        <section className="relative flex flex-col items-center justify-center min-h-screen text-center px-8 py-20 overflow-hidden bg-gradient-to-b from-white via-indigo-50 via-purple-50 to-purple-100">
          {/* ultra-soft radial wash to remove any banding */}
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(160,140,255,0.25)_0%,_rgba(255,255,255,1)_85%)] blur-2xl" />

          {/* subtle grid for texture */}
          <div className="pointer-events-none absolute inset-0 bg-[url('data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'120\\' height=\\'120\\' viewBox=\\'0 0 120 120\\'><g fill=\\'none\\' stroke=\\'rgba(60,60,120,0.07)\\' stroke-width=\\'1\\'><path d=\\'M0 60 H120\\'/><path d=\\'M60 0 V120\\'/></g></svg>')] bg-repeat opacity-40" />

          {/* left abstract blend */}
          <div className="pointer-events-none absolute -left-24 top-24 w-[38rem] h-[38rem] rounded-full blur-2xl opacity-85"
               style={{ background: 'radial-gradient(closest-side, rgba(147,112,219,0.35), rgba(147,112,219,0.18), transparent 75%)' }} />

          {/* right abstract blend */}
          <div className="pointer-events-none absolute -right-24 bottom-16 w-[40rem] h-[40rem] rounded-full blur-2xl opacity-85"
               style={{ background: 'radial-gradient(closest-side, rgba(99,102,241,0.32), rgba(99,102,241,0.15), transparent 75%)' }} />

          {/* top-left soft accent */}
          <div className="pointer-events-none absolute top-10 left-1/4 w-[20rem] h-[20rem] rounded-full blur-xl opacity-70"
               style={{ background: 'radial-gradient(circle at center, rgba(179,157,255,0.25), rgba(255,255,255,0.1) 70%)' }} />
          
          {/* bottom-right soft accent */}
          <div className="pointer-events-none absolute bottom-8 right-1/4 w-[22rem] h-[22rem] rounded-full blur-xl opacity-70"
               style={{ background: 'radial-gradient(circle at center, rgba(160,140,255,0.3), rgba(255,255,255,0.1) 70%)' }} />

          {/* gentle arcs for premium feel */}
          <svg className="pointer-events-none absolute left-6 md:left-16 top-24 opacity-30" width="280" height="280" viewBox="0 0 280 280" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 140c0-71.8 58.2-130 130-130" stroke="url(#lg1)" strokeWidth="1.2" strokeLinecap="round"/>
            <path d="M30 140c0-60.3 49.7-110 110-110" stroke="url(#lg2)" strokeWidth="1" strokeLinecap="round"/>
            <defs>
              <linearGradient id="lg1" x1="10" y1="10" x2="140" y2="140" gradientUnits="userSpaceOnUse">
                <stop stopColor="rgba(99,102,241,0.35)"/>
                <stop offset="1" stopColor="rgba(147,112,219,0.15)"/>
              </linearGradient>
              <linearGradient id="lg2" x1="30" y1="30" x2="140" y2="140" gradientUnits="userSpaceOnUse">
                <stop stopColor="rgba(99,102,241,0.25)"/>
                <stop offset="1" stopColor="rgba(147,112,219,0.10)"/>
              </linearGradient>
            </defs>
          </svg>

          <svg className="pointer-events-none absolute right-6 md:right-16 bottom-24 opacity-30" width="300" height="300" viewBox="0 0 300 300" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M290 150c0 77-63 140-140 140" stroke="url(#rg1)" strokeWidth="1.2" strokeLinecap="round"/>
            <path d="M270 150c0 66-54 120-120 120" stroke="url(#rg2)" strokeWidth="1" strokeLinecap="round"/>
            <defs>
              <linearGradient id="rg1" x1="290" y1="150" x2="150" y2="290" gradientUnits="userSpaceOnUse">
                <stop stopColor="rgba(147,112,219,0.30)"/>
                <stop offset="1" stopColor="rgba(99,102,241,0.12)"/>
              </linearGradient>
              <linearGradient id="rg2" x1="270" y1="150" x2="150" y2="270" gradientUnits="userSpaceOnUse">
                <stop stopColor="rgba(147,112,219,0.22)"/>
                <stop offset="1" stopColor="rgba(99,102,241,0.10)"/>
              </linearGradient>
            </defs>
          </svg>
          {/* fluid organic abstract shapes */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden">
            {/* softly curved diagonal waves */}
            <svg className="absolute top-0 left-0 w-full h-full opacity-35" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320" preserveAspectRatio="none">
              <path fill="url(#lavenderFlow)" d="M0,160 C320,280 1120,40 1440,160 L1440,320 L0,320 Z"></path>
              <defs>
                <linearGradient id="lavenderFlow" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="rgba(160,140,255,0.18)" />
                  <stop offset="50%" stopColor="rgba(200,185,255,0.10)" />
                  <stop offset="100%" stopColor="rgba(255,255,255,0.08)" />
                </linearGradient>
              </defs>
            </svg>

            {/* small diffused droplets for organic fluidity */}
            <div className="absolute top-[20%] left-[10%] w-32 h-32 rounded-full blur-2xl opacity-55"
                 style={{ background: 'radial-gradient(circle at center, rgba(147,112,219,0.45), rgba(255,255,255,0.1))' }} />
            <div className="absolute bottom-[25%] right-[15%] w-40 h-40 rounded-full blur-2xl opacity-50"
                 style={{ background: 'radial-gradient(circle at center, rgba(99,102,241,0.4), rgba(255,255,255,0.12))' }} />
            <div className="absolute top-[50%] left-[45%] w-24 h-24 rounded-full blur-2xl opacity-30"
                 style={{ background: 'radial-gradient(circle at center, rgba(130,110,255,0.25), rgba(255,255,255,0.08))' }} />

            {/* faint dotted gradient layer for texture depth */}
            <div className="absolute inset-0 bg-[radial-gradient(circle,_rgba(160,140,255,0.18)_1px,transparent_1px)] bg-[size:22px_22px] opacity-35 mix-blend-overlay"></div>
          </div>
          <p className="text-base font-medium text-indigo-600 mb-5 z-10">The Fastest AI Verification Assistant</p>
          <h1 className="text-6xl md:text-8xl font-extrabold text-gray-900 mb-6 leading-tight z-10">Verify Before You Believe</h1>
          <p className="text-xl md:text-2xl text-gray-700 max-w-2xl mb-10 z-10">
            AI-powered misinformation detection for text, images, and links, now with multilingual accuracy.
          </p>
          <div className="flex flex-col sm:flex-row items-center gap-4 z-10">
            <a href="/console" className="bg-black text-white px-10 py-5 rounded-full text-lg font-semibold transition-all duration-300 hover:translate-y-[-1px] hover:shadow-lg hover:opacity-95 active:translate-y-[0px]">Launch Console</a>
            <button onClick={scrollToHowToUse} className="border border-gray-900 text-gray-800 px-8 py-5 rounded-full text-lg font-semibold transition-all duration-300 hover:bg-gradient-to-r hover:from-indigo-600 hover:to-purple-600 hover:text-white hover:shadow-lg hover:translate-y-[-1px] active:translate-y-[0px]">
              How to Use
            </button>
          </div>
          <p className="mt-8 text-base text-indigo-600 z-10">Join the war to combat misinformation, verify truth with Pramana</p>
        </section>

        <section ref={howToUseRef} className="relative flex flex-col md:flex-row items-center justify-between gap-16 px-16 py-36 bg-[radial-gradient(ellipse_at_top,_rgba(160,140,255,0.10)_0%,_rgba(255,255,255,1)_60%)]">

          <div className="w-full md:w-1/2 relative z-10 rounded-3xl overflow-hidden shadow-lg border border-gray-100">
            <iframe
              className="w-full h-72 md:h-96 rounded-3xl"
              src="https://www.youtube.com/embed/FsdYLMad8p4"
              title="How to Use Pramana"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>

          <div className="w-full md:w-1/2 text-left relative z-10">
            <h2 className="text-5xl font-extrabold bg-gradient-to-r from-indigo-700 to-purple-500 bg-clip-text text-transparent mb-6">How to Use Pramana</h2>
            <p className="text-gray-700 mb-5 text-xl leading-relaxed">
              Upload or share any <span className="font-semibold text-gray-900">text, image, video, or link</span> directly from your device or social media app.
            </p>
            <p className="text-gray-700 mb-5 text-xl leading-relaxed">
              Pramana verifies authenticity, detects manipulations, and cites trusted sources, all in seconds.
            </p>
            <p className="text-gray-700 text-xl leading-relaxed">
              You can also verify directly from <span className="font-semibold text-gray-900">WhatsApp, X (Twitter), or Instagram</span> using one-tap sharing.
            </p>
          </div>
        </section>

        <section ref={aboutRef} className="relative px-10 py-40 bg-gradient-to-b from-white via-indigo-50 to-purple-50 text-center">
          <h2 className="text-5xl font-extrabold mb-8 bg-gradient-to-r from-purple-700 to-indigo-600 bg-clip-text text-transparent z-10 relative">Why Pramana?</h2>
          <p className="text-gray-700 max-w-3xl mx-auto text-xl leading-relaxed z-10 relative">
            Designed for both individuals and B2B teams, Pramana empowers everyone to verify truth instantly, from daily news readers to enterprise data analysts. It ensures reliable fact-checking, authenticity validation, and AI-based insights within seconds.
          </p>
        </section>
      </main>
      <footer className="relative w-full mt-0 bg-gradient-to-b from-white via-indigo-50 to-purple-50">
        {/* ultra-soft footer wash to avoid any hard line at the bottom */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_rgba(164,148,255,0.12)_0%,_rgba(255,255,255,1)_70%)] blur-2xl" />
        <div className="max-w-screen-xl mx-auto px-6 py-12 flex items-center justify-center">
          <div className="relative bg-gradient-to-r from-[#f3e8ff] via-[#faf6ff] to-[#f6f3ff] backdrop-blur-sm rounded-full px-7 py-3 shadow-sm text-gray-700 border border-white/60">
            © 2025 Pramana · Developed by OrangexAI
            <span className="ml-3 text-xs text-gray-400 font-mono select-none">HV</span>
          </div>
        </div>
      </footer>
      <style>
        {`
          @keyframes fade-up {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
          }
          .animate-fade-up { animation: fade-up 0.6s ease-out forwards; }
        `}
      </style>
    </div>
  );
};

export default LandingPage;
