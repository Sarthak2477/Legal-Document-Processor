"use client";
import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";

const Navbar = ({ hideLaunchButton = false }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const navLinksRef = useRef(null);

  const handleMouseMove = (e) => {
    if (navLinksRef.current) {
      const rect = navLinksRef.current.getBoundingClientRect();
      setMousePosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    }
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-slate-900/80 backdrop-blur-lg shadow-lg border-b border-slate-800/50"
          : "bg-transparent"
      }`}
    >
      <div className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          {/* Logo / Brand Name */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <svg
                className="w-5 h-5 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V8zm8 0a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1V8zm0 4a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1v-2z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <a
              href="#"
              className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent hover:from-blue-400 hover:to-indigo-400 transition-all duration-300"
            >
              DocuMind
            </a>
          </div>

          {/* Desktop Navigation */}
          <div
            ref={navLinksRef}
            onMouseMove={handleMouseMove}
            className="hidden lg:flex relative bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-full px-6 py-3 shadow-lg overflow-hidden"
          >
            <div
              className="absolute inset-0 transition-all duration-300"
              style={{
                background: `radial-gradient(circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(59, 130, 246, 0.15), transparent 40%)`,
              }}
            ></div>
            <ul className="flex items-center space-x-8 relative z-10">
              <li>
                <a
                  href="#"
                  className="text-white transition-all duration-300 text-sm font-medium relative group"
                >
                  Home
                  <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-gradient-to-r from-blue-400 to-indigo-500"></span>
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-white transition-all duration-300 text-sm font-medium relative group"
                >
                  Features
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-400 to-indigo-500 group-hover:w-full transition-all duration-300"></span>
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-gray-300 hover:text-white transition-all duration-300 text-sm font-medium relative group"
                >
                  About
                  <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-blue-400 to-indigo-500 group-hover:w-full transition-all duration-300"></span>
                </a>
              </li>
            </ul>
          </div>

          {/* CTA Button */}
          {/* --- CHANGE IS HERE: Conditionally render the button --- */}
          {!hideLaunchButton && (
            <div className="hidden lg:flex bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-full p-1 shadow-lg">
              <Link href="/app?mode=upload">
                <button className="group relative bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold py-2 px-6 rounded-full transition-all duration-300 transform hover:scale-105">
                  Launch App
                </button>
              </Link>
            </div>
          )}

          {/* Mobile Menu Button */}
          <div className="lg:hidden">
            <button
              onClick={toggleMobileMenu}
              className="text-gray-300 hover:text-white focus:outline-none p-2 rounded-lg hover:bg-slate-800/50 transition-all duration-300"
            >
              <svg
                className={`w-6 h-6 transform transition-all duration-300 ${
                  isMobileMenuOpen ? "rotate-180" : "rotate-0"
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {isMobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 6h16M4 12h16m-7 6h7"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu Panel */}
        <div
          className={`absolute top-full left-0 w-full z-40 transition-all duration-500 ease-in-out lg:hidden ${
            isMobileMenuOpen
              ? "opacity-100 translate-y-0"
              : "opacity-0 -translate-y-4 pointer-events-none"
          }`}
        >
          <div className="bg-gradient-to-b from-slate-900/95 to-slate-900/80 backdrop-blur-lg rounded-b-2xl p-6 border-t border-slate-700/50 shadow-2xl">
            <ul className="flex flex-col space-y-3">
              <li>
                <a
                  href="#"
                  className="flex items-center justify-between text-white transition-all duration-300 py-3 px-4 rounded-lg hover:bg-slate-800/70"
                >
                  <span className="font-medium">Home</span>
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="flex items-center justify-between text-gray-300 hover:text-white transition-all duration-300 py-3 px-4 rounded-lg hover:bg-slate-800/70 group"
                >
                  <span className="font-medium">Features</span>
                  <svg
                    className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 8l4 4m0 0l-4 4m4-4H3"
                    />
                  </svg>
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="flex items-center justify-between text-gray-300 hover:text-white transition-all duration-300 py-3 px-4 rounded-lg hover:bg-slate-800/70 group"
                >
                  <span className="font-medium">About</span>
                  <svg
                    className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 8l4 4m0 0l-4 4m4-4H3"
                    />
                  </svg>
                </a>
              </li>
              {!hideLaunchButton && (
                <li className="pt-4 border-t border-slate-700/50">
                  <Link href="/app?mode=upload" passHref>
                    <button className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold py-3 px-6 rounded-full transition-all duration-300 transform hover:scale-105 shadow-lg">
                      Launch App
                    </button>
                  </Link>
                </li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
