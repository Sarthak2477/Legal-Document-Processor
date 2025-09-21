"use client";
import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";

const IntroductionSection = () => {
  const [isVisible, setIsVisible] = useState(false);
  // State for parallax effect
  const [scrollPosition, setScrollPosition] = useState(0);

  // State and handlers for 3D card tilt effect
  const [card1Style, setCard1Style] = useState({});
  const [card2Style, setCard2Style] = useState({});

  const getCardStyle = useMemo(() => (cardStyle, delay) => ({
    ...cardStyle,
    transitionDelay: cardStyle.transition ? undefined : delay
  }), []);

  const handleMouseMove = (e, setStyle) => {
    const card = e.currentTarget;
    const { left, top, width, height } = card.getBoundingClientRect();
    const x = e.clientX - left - width / 2;
    const y = e.clientY - top - height / 2;
    const rotateX = (-y / height) * 10; // Tilt intensity
    const rotateY = (x / width) * 10;
    setStyle({
      transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`,
      transition: 'transform 0.1s ease-out'
    });
  };

  const handleMouseLeave = (setStyle) => {
    setStyle({
      transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
      transition: 'transform 0.6s ease-in-out'
    });
  };


  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 200);
    
    // Throttled parallax scroll listener
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          setScrollPosition(window.pageYOffset);
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      clearTimeout(timer);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <section className="relative py-24 bg-gradient-to-b text-white overflow-hidden" style={{ fontFamily: "'Poppins', sans-serif" }}>
      
      {/* Enhanced animated background elements with Parallax */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-80 h-80 bg-gradient-to-r from-blue-500/10 to-slate-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ transform: `translateY(${scrollPosition * 0.1}px)` }}></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-gradient-to-l from-slate-500/10 to-blue-600/10 rounded-full blur-3xl animate-pulse-slow delay-1000" style={{ transform: `translateY(${scrollPosition * 0.05}px)` }}></div>
      </div>

      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

      <div className="relative container mx-auto px-6 text-center z-10">
        
        <div className={`mb-20 transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          <div className="inline-flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-full px-4 py-2 mb-8 text-sm font-medium text-slate-300 backdrop-blur-sm">
            <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
            </svg>
            How It Works
          </div>
          <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-8">
            <span className="block bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              A Clearer Path Forward
            </span>
          </h2>
          <p className="text-xl md:text-2xl text-gray-400 max-w-4xl mx-auto leading-relaxed">
            Our process is simple. Securely upload your document, then interact with our AI to get the insights you need.
          </p>
        </div>

        {/* Enhanced Cards Container */}
        <div className="grid lg:grid-cols-2 gap-8 xl:gap-12 max-w-6xl mx-auto">
          
          {/* Card 1 with 3D Tilt */}
          <div 
            className={`group relative bg-gradient-to-br from-slate-800/40 to-gray-900/60 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-slate-700/50 transition-all duration-500 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`} 
            style={getCardStyle(card1Style, '400ms')}
            onMouseMove={(e) => handleMouseMove(e, setCard1Style)}
            onMouseLeave={() => handleMouseLeave(setCard1Style)}
          >
             <div className="relative z-10 flex flex-col h-full">
                <div className="mb-8 flex justify-center">
                    <div className="w-40 h-40 bg-gradient-to-br from-slate-700/50 to-gray-800/50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    </div>
                </div>
                <h3 className="text-3xl font-bold text-white mb-6 group-hover:text-blue-300 transition-colors duration-300">
                    Securely Process Documents
                </h3>
                <p className="text-gray-400 text-lg mb-8 leading-relaxed group-hover:text-gray-300 transition-colors duration-300 flex-grow">
                    Upload contracts and policies for AI-powered analysis with 
                    <span className="text-white font-semibold"> enterprise-grade security</span> and instant PII sanitization.
                </p>
                <Link href="/app?mode=upload" className="block mt-auto">
                    <button className="relative w-full bg-slate-700 hover:bg-slate-600 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-slate-600/25 overflow-hidden group/btn">
                    <span className="relative z-10 flex items-center justify-center gap-3">
                        <svg className="w-5 h-5 group-hover/btn:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        Upload & Analyze
                    </span>
                    <div className="absolute inset-0 bg-white/10 transform scale-x-0 group-hover/btn:scale-x-100 transition-transform origin-left duration-300"></div>
                    </button>
                </Link>
            </div>
          </div>

          {/* Card 2 with 3D Tilt */}
          <div 
            className={`group relative bg-gradient-to-br from-slate-800/40 to-gray-900/60 backdrop-blur-sm rounded-3xl p-10 shadow-2xl border border-slate-700/50 transition-all duration-500 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}`} 
            style={getCardStyle(card2Style, '600ms')}
            onMouseMove={(e) => handleMouseMove(e, setCard2Style)}
            onMouseLeave={() => handleMouseLeave(setCard2Style)}
          >
            <div className="relative z-10 flex flex-col h-full">
              <div className="mb-8 flex justify-center">
                <div className="w-40 h-40 bg-gradient-to-br from-slate-700/50 to-gray-800/50 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
                  </svg>
                </div>
              </div>
              <h3 className="text-3xl font-bold text-white mb-6 group-hover:text-blue-300 transition-colors duration-300">
                Chat & Get Instant Answers
              </h3>
              <p className="text-gray-400 text-lg mb-8 leading-relaxed group-hover:text-gray-300 transition-colors duration-300 flex-grow">
                Interact with your documents using our 
                <span className="text-white font-semibold"> intelligent AI chatbot</span>. 
                Receive clear, verifiable insights with 
                <span className="text-blue-400 font-semibold"> cited sources</span> instantly.
              </p>
              <Link href="/app?mode=chat" className="block mt-auto">
                <button className="relative w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-blue-500/25 overflow-hidden group/btn">
                  <span className="relative z-10 flex items-center justify-center gap-3">
                    <svg className="w-5 h-5 group-hover/btn:scale-110 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    Start Chatting
                  </span>
                  <div className="absolute inset-0 bg-white/20 transform scale-x-0 group-hover/btn:scale-x-100 transition-transform origin-left duration-300"></div>
                </button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.4; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.03); }
        }
        .animate-pulse-slow {
          animation: pulse-slow 5s ease-in-out infinite;
        }
        .bg-grid-pattern {
          background-image: radial-gradient(circle, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
          background-size: 40px 40px;
        }
      `}</style>
    </section>
  );
};

export default IntroductionSection;

