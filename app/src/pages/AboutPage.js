import React, { useState } from "react";
import { Link } from "react-router-dom";
import logo from '../assets/pramana-logo-black.png';

const AboutPage = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-indigo-50 via-purple-50 to-purple-100 text-gray-900 flex flex-col overflow-hidden">
      {/* Header (exact style as LandingPage) */}
      <header className="flex items-center justify-between px-4 md:px-10 py-6 fixed top-0 left-0 w-full bg-white/60 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="flex items-center gap-3 flex-shrink-0">
          <Link to="/" className="flex items-center gap-3">
            <img src={logo} alt="Pramana Logo" className="h-8 w-8 flex-shrink-0" />
            <h1 className="font-semibold text-lg tracking-wide truncate text-gray-900">Pramana</h1>
          </Link>
          <Link
            to="/"
            className="flex items-center text-indigo-600 hover:text-purple-600 text-sm font-medium mt-2 ml-10 md:ml-12 transition-all duration-300"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-5 h-5 mr-1">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </Link>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6 text-base">
          <a
            href="https://github.com/channi23/OrangeLens"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]"
          >
            GitHub
          </a>
          <Link
            to="/console"
            className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]"
          >
            Launch Console
          </Link>
          <Link
            to="/about"
            className="text-indigo-600 font-semibold border-b-2 border-indigo-600 pb-1"
          >
            About
          </Link>
          <a
            href="https://github.com/channi23/OrangeLens/releases/download/v4.0/Pramana-Version-4.apk"
            className="rounded-full px-5 py-2 text-base font-medium border border-indigo-300 hover:border-indigo-500 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] hover:bg-gradient-to-r hover:from-indigo-600 hover:to-purple-600 hover:text-white"
          >
            Download App
          </a>
        </nav>

        {/* Mobile burger */}
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

      {/* Mobile dropdown */}
      {isMenuOpen && (
        <nav className="flex flex-col items-center gap-4 bg-white/90 py-4 fixed top-16 left-0 w-full z-40 border-b border-gray-200 md:hidden text-base px-4">
          <a
            href="https://github.com/channi23/OrangeLens"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 w-full text-center bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]"
          >
            GitHub
          </a>
          <Link
            to="/console"
            className="text-gray-600 hover:text-indigo-600 transition-colors duration-300 w-full text-center bg-[linear-gradient(currentColor,currentColor)] bg-[length:0%_2px] bg-left-bottom bg-no-repeat transition-[background-size,color] duration-300 hover:bg-[length:100%_2px]"
          >
            Launch Console
          </Link>
          <Link
            to="/about"
            className="text-indigo-600 font-semibold w-full text-center"
          >
            About
          </Link>
          <a
            href="https://github.com/channi23/OrangeLens/releases/download/v4.0/Pramana-Version-4.apk"
            className="rounded-full px-5 py-2 text-base font-medium border border-indigo-300 hover:border-indigo-500 hover:shadow-lg transition-all duration-300 hover:scale-[1.02] hover:bg-gradient-to-r hover:from-indigo-600 hover:to-purple-600 hover:text-white w-full text-center"
          >
            Download App
          </a>
        </nav>
      )}

      <main className="flex-grow pt-24">
        {/* Subtle abstract radial blend (same design language as LandingPage) */}
        <section className="relative text-center py-24 px-6 overflow-hidden bg-[linear-gradient(180deg,_rgba(250,250,255,1)_0%,_rgba(240,235,255,0.9)_50%,_rgba(245,240,255,1)_100%)]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(190,170,255,0.1)_0%,_rgba(255,255,255,1)_80%)] blur-[120px] pointer-events-none"></div>
          <p className="text-base font-medium text-indigo-600 mb-4 z-10 relative">Truth. At speed and at scale.</p>
          <h1 className="text-5xl md:text-6xl font-extrabold text-gray-900 mb-4 leading-tight z-10 relative">
            About Pramana
          </h1>
          <p className="text-lg md:text-xl text-gray-700 max-w-2xl mx-auto z-10 relative">
            Empowering truth through AI — built for individuals and enterprises to combat misinformation with precision and trust.
          </p>
        </section>

        {/* Mission card (soft, no boxy edges; blended backdrop) */}
        <section className="relative max-w-5xl mx-auto px-6 py-16 text-center rounded-3xl shadow-xl border border-gray-100 bg-white/70 backdrop-blur-xl">
          <div className="absolute -z-10 inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(180,160,255,0.25)_0%,_rgba(255,255,255,1)_75%)] blur-2xl"></div>
          <h2 className="text-3xl font-bold text-indigo-700 mb-6">Our Mission</h2>
          <p className="text-gray-700 text-lg leading-relaxed">
            Pramana bridges technology and truth—combining AI, deep learning, and linguistic analysis to verify text, images, videos, and links. Designed for both enterprises and individuals, it empowers fact-checkers, media houses, and everyday users to identify authenticity with clarity and speed.
          </p>
        </section>

        {/* Founders */}
        <section className="relative max-w-6xl mx-auto px-6 py-20">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_rgba(160,140,255,0.16)_0%,_rgba(255,255,255,1)_70%)] blur-2xl -z-10"></div>
          <h2 className="text-3xl font-bold text-center text-indigo-700 mb-12">Meet the Founders</h2>

          <div className="grid md:grid-cols-2 gap-12">
            <div className="bg-white/60 backdrop-blur-lg p-8 rounded-3xl shadow-lg border border-gray-100 hover:shadow-2xl transition-all duration-300">
              <h3 className="text-2xl font-semibold text-indigo-700">Sri Hari Haran Sharma</h3>
              <p className="text-gray-600 mt-2 font-medium">Founder &amp; Tech Innovator</p>
              <p className="mt-4 text-gray-700 leading-relaxed">
                Leading Pramana’s AI-driven truth verification with a vision for innovation.
              </p>
              <div className="mt-4 space-x-4">
                <a href="https://www.linkedin.com/in/sri-hariharan-sharma-aa1478286" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">LinkedIn</a>
                <a href="https://x.com/Hariharangurum1" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">X</a>
              </div>
            </div>

            <div className="bg-white/60 backdrop-blur-lg p-8 rounded-3xl shadow-lg border border-gray-100 hover:shadow-2xl transition-all duration-300">
              <h3 className="text-2xl font-semibold text-indigo-700">Vamshi Thirumal Reddy</h3>
              <p className="text-gray-600 mt-2 font-medium">Co-Founder &amp; Architect</p>
              <p className="mt-4 text-gray-700 leading-relaxed">
                Bringing analytical precision and architectural expertise to verification.
              </p>
              <div className="mt-4 space-x-4">
                <a href="https://www.linkedin.com/in/vamshi-thirumal-reddy?utm_source=share&amp;utm_campaign=share_via&amp;utm_content=profile&amp;utm_medium=android_app" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">LinkedIn</a>
                <a href="https://x.com/vamshi_6969?t=XJ3DTEzW0xyKbZ61BRk7pA&amp;s=09" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">X</a>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Blended footer with pill (same language as LandingPage), not floating */}
      <footer className="relative mt-10">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-50 to-purple-100 pointer-events-none" />
        <div className="relative py-16 flex items-center justify-center">
          <div className="px-6 py-3 rounded-full shadow-md border border-indigo-200/60 bg-gradient-to-r from-indigo-50 to-purple-50 backdrop-blur-md">
            <span className="text-sm text-gray-700">
              © 2025 Pramana · Developed by <span className="font-semibold text-indigo-600">OrangeXAI</span>
            </span>
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes fade-up {
          0% { opacity: 0; transform: translateY(20px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-up { animation: fade-up 0.6s ease-out forwards; }
        .delay-100 { animation-delay: 0.2s; }
      `}</style>
    </div>
  );
};

export default AboutPage;