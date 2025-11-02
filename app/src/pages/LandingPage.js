import { useState } from 'react';
import { Link } from 'react-router-dom';
import Logo from '../assets/pramana-logo-black.png';

const features = [
  {
    title: 'Verify Text, Image, or URL',
    description: 'Send any claim, screenshot, or link and get an evidence-backed verdict in seconds.',
  },
  {
    title: 'Transparent Results',
    description: 'Every verdict includes citations, confidence scores, and reasoning you can audit.',
  },
  {
    title: 'Private by Default',
    description: 'Designed for privacy-first workflows — no training on your data, ever.',
  },
];

const LandingPage = () => {
  const [showAbout, setShowAbout] = useState(false);

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Subtle Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_60%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(100,100,255,0.06),transparent_70%)] pointer-events-none" />

      <div className="relative z-10 flex min-h-screen flex-col">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-5 md:px-12 border-b border-white/10">
          <Link 
            to="/" 
            className="flex items-center gap-3 transition-all duration-300 hover:opacity-80"
          >
            <div className="h-10 w-10 rounded-full bg-white flex items-center justify-center transition-transform duration-300 hover:scale-110">
              <img src={Logo} alt="Pramana Logo" className="h-7 w-7 object-contain" />
            </div>
            <div>
              <p className="text-lg font-semibold tracking-wide">Pramana</p>
              <p className="text-xs text-zinc-400">Verify Before You Believe</p>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/channi23/OrangeLens/releases/download/v4.0/Pramana-Version-4.apk"
              className="group relative overflow-hidden rounded-full border border-white/30 bg-transparent px-5 py-2 text-sm font-medium text-white transition-all duration-300 hover:border-white hover:bg-white/5"
            >
              <span className="relative z-10">Download App</span>
              <div className="absolute inset-0 bg-white/10 scale-0 group-hover:scale-100 transition-transform duration-300 rounded-full" />
            </a>
            <button
              type="button"
              onClick={() => setShowAbout((prev) => !prev)}
              className="group relative overflow-hidden rounded-full border border-white/30 bg-black px-5 py-2 text-sm font-medium text-white transition-all duration-300 hover:border-white hover:bg-white/5"
            >
              <span className="relative z-10">About</span>
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-16 px-6 pb-24 pt-16 text-center md:px-12">
          {/* Hero Section */}
          <section className="space-y-8">
            <div className="inline-block rounded-full border border-white/20 bg-white/5 px-4 py-2 backdrop-blur-sm transition-all duration-300 hover:border-white/40 hover:bg-white/10">
              <p className="text-xs uppercase tracking-[0.35em] text-zinc-300">
                AI-Powered Fact Verification
              </p>
            </div>

            <h1 className="font-display text-5xl font-bold leading-tight text-white sm:text-6xl md:text-7xl lg:text-8xl transition-all duration-300 hover:text-zinc-200">
              Verify before
              <br />
              you believe.
            </h1>

            <p className="mx-auto max-w-2xl text-lg leading-relaxed text-zinc-300 md:text-xl">
              Pramana delivers instant, trustworthy fact checks for your organisation.{' '}
              <span className="text-white font-medium">Automate verification</span>, protect your audience, and{' '}
              <span className="text-white font-medium">stay ahead of misinformation</span>.
            </p>

            <div className="flex flex-wrap justify-center gap-4 pt-4">
              <Link
                to="/console"
                className="group relative overflow-hidden rounded-full border-2 border-white bg-white px-8 py-3.5 text-sm font-bold text-black transition-all duration-300 hover:scale-105 hover:shadow-[0_8px_30px_rgba(255,255,255,0.4)] active:scale-95"
              >
                <span className="relative z-10">Launch Console</span>
                <div className="absolute inset-0 bg-zinc-100 scale-0 group-hover:scale-100 transition-transform duration-300 rounded-full" />
              </Link>

              <button
                type="button"
                onClick={() => setShowAbout(true)}
                className="group rounded-full border-2 border-white/40 bg-transparent px-8 py-3.5 text-sm font-bold text-white backdrop-blur-sm transition-all duration-300 hover:border-white hover:bg-white/10 hover:shadow-[0_8px_30px_rgba(255,255,255,0.2)] active:scale-95"
              >
                Learn More
              </button>
            </div>
          </section>

          {/* Feature Cards */}
          <section className="grid gap-6 md:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group relative overflow-hidden rounded-3xl border border-white/20 bg-gradient-to-br from-white/5 to-transparent p-6 text-left backdrop-blur-sm transition-all duration-500 hover:border-white/40 hover:bg-white/10 hover:shadow-[0_8px_30px_rgba(255,255,255,0.15)] hover:-translate-y-1"
              >
                
                <h3 className="text-xl font-bold text-white mb-3">
                  {feature.title}
                </h3>
                
                <p className="text-sm leading-relaxed text-zinc-400 group-hover:text-zinc-300 transition-colors duration-300">
                  {feature.description}
                </p>

                {/* Subtle corner accent */}
                <div className="absolute -right-8 -top-8 h-24 w-24 rounded-full bg-white/10 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              </div>
            ))}
          </section>

          {/* About Section */}
          {showAbout && (
            <section className="mx-auto max-w-3xl overflow-hidden rounded-3xl border border-white/30 bg-gradient-to-br from-white/10 to-white/5 p-8 text-left shadow-[0_0_40px_rgba(255,255,255,0.1)] backdrop-blur-xl animate-fadeInUp">
              <div className="relative">
                <div className="absolute -left-4 top-0 h-full w-1 bg-gradient-to-b from-white/50 via-white/20 to-transparent" />
                
                <h2 className="text-3xl font-bold text-white mb-4">
                  Why Pramana?
                </h2>
                
                <p className="text-base leading-relaxed text-zinc-300 mb-6">
                  Built for B2B teams that cannot afford misinformation. Pramana provides{' '}
                  <span className="text-white font-semibold">API-driven workflows</span>,{' '}
                  <span className="text-white font-semibold">enterprise-grade privacy</span>, and{' '}
                  <span className="text-white font-semibold">verifiable AI outputs</span>. Use it to vet marketing
                  campaigns, moderate user submissions, or automate due diligence.
                </p>
                
                <div className="flex flex-wrap gap-3 text-xs">
                  {['Vertex AI Gemini', 'Google Fact Check', 'BigQuery Analytics', 'Audit-ready Logs'].map(
                    (tag) => (
                      <span
                        key={tag}
                        className="rounded-full border border-white/30 bg-white/5 px-4 py-2 text-zinc-300 backdrop-blur-sm transition-all duration-300 hover:border-white/60 hover:bg-white/15 hover:text-white cursor-default"
                      >
                        {tag}
                      </span>
                    )
                  )}
                </div>
              </div>
            </section>
          )}
        </main>

        {/* Footer */}
        <footer className="px-6 py-6 text-center text-xs text-zinc-500 md:px-12 border-t border-white/10">
          <div className="mb-4 h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
          © Pramana 2025 · Powered by Google Cloud AI
        </footer>
      </div>

      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeInUp {
          animation: fadeInUp 0.4s ease-out;
        }
      `}</style>
    </div>
  );
};

export default LandingPage;
