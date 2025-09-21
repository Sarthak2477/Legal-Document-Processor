"use client";
import React, { useState, useEffect } from "react";

const HeroPage = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Consistent animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-blue-500/10 to-slate-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-l from-slate-500/10 to-blue-600/10 rounded-full blur-3xl animate-pulse-slow delay-1000"></div>
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

      {/* Hero Section */}
      <main className="relative container mx-auto px-6 py-16 md:py-24 text-white z-10">
        <div className="flex justify-center">
          {/* Centered Content Column */}
          <div
            className={`text-center max-w-4xl transform transition-all duration-1000 ${
              isVisible
                ? "translate-y-0 opacity-100"
                : "translate-y-10 opacity-0"
            }`}
          >
            {/* Badge/Announcement */}
            <div className="inline-flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-full px-4 py-2 mb-6 text-sm font-medium text-slate-300 backdrop-blur-sm">
              <svg
                className="w-4 h-4 text-blue-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                  clipRule="evenodd"
                />
              </svg>
              AI-Powered Legal Analysis
            </div>

            {/* Main Headline */}
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-[0.9] mb-8 tracking-tight">
              <span className="block bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent mb-2">
                Contracts 
              </span>
              <span className="block bg-gradient-to-r from-slate-300 to-slate-400 bg-clip-text text-transparent">
                Understood.
              </span>
            </h1>

            {/* Description */}
            <p className="text-gray-400 text-xl md:text-2xl mb-10 max-w-2xl mx-auto leading-relaxed">
              <span className="text-white font-semibold">Unlock</span> the power
              of your legal documents with AI-powered analysis.
            </p>

            {/* CTA buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <button className="group relative bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-blue-500/25 overflow-hidden">
                <span className="relative z-10 flex items-center justify-center gap-3">
                  <svg
                    className="w-5 h-5 group-hover:rotate-12 transition-transform duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                  Start Free Analysis
                </span>
                <div className="absolute inset-0 bg-white/20 transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300"></div>
              </button>

              <button className="group bg-transparent border-2 border-slate-600 hover:border-slate-400 text-slate-400 hover:text-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 backdrop-blur-sm hover:bg-slate-800/20">
                <span className="flex items-center justify-center gap-3">
                  <svg
                    className="w-5 h-5 group-hover:scale-110 transition-transform duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.01M15 10h1.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Watch Demo
                </span>
              </button>
            </div>
          </div>
        </div>
      </main>

      <style>{`
        @keyframes scan {
          0% { transform: translateY(0); opacity: 0.6; }
          100% { transform: translateY(384px); opacity: 0; }
        }
        .animate-scan {
          animation: scan 4s ease-out infinite;
        }
        /* Highlight styles updated for a light background */
        .highlight-amber {
          background-color: rgba(251, 191, 36, 0.3);
        }
        .highlight-red {
          background-color: rgba(239, 68, 68, 0.2);
          font-weight: 600;
          color: #b91c1c;
        }
        .highlight-green {
          background-color: rgba(34, 197, 94, 0.2);
        }
        
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.8; }
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 4s ease-in-out infinite;
        }
        
        .bg-grid-pattern {
          background-image: radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
          background-size: 50px 50px;
        }
      `}</style>
    </div>
  );
};

export default HeroPage;