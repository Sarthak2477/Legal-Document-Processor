"use client";
import React, { useState, useEffect, useRef } from "react";

const featuresData = [
  {
    title: "Interactive Q&A with Verifiable Proof",
    description:
      "Go beyond static text. Ask detailed questions about specific clauses and get plain-language answers backed by direct quotes from your document.",
    video: "/Document.mp4",
    points: ["Plain-Language Answers", "Verifiable Citations", "Context-Aware AI"],
  },
  {
    title: "Automated Risk Analysis (Riskometer)",
    description:
      "Proactively understand your position. Our AI identifies potential risks, hidden obligations, and unfair clauses, giving you a clear view of what needs attention.",
   video: "/Document - Made with Clipchamp.mp4",
    points: [
      "Color-Coded Risk Levels",
      "Obligation Highlighting",
      "Unfair Clause Detection",
    ],
  },
  // {
    // title: "Automated Document Checklists",
    // description:
    //   "Never miss a step. Our AI identifies your document type and instantly generates a checklist of required supporting documents and actions.",
    // image:
    //   "https://placehold.co/600x400/0f172a/94a3b8?text=Checklist+UI",
    // points: [
    //   "Document Type Recognition",
    //   "Actionable Step-by-Step Lists",
    //   "Reduces Manual Error",
    // ],
  // },
];

const FeaturesShowcase = () => {
  const [visibleElements, setVisibleElements] = useState([]);
  const sectionRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisibleElements((prev) => [
              ...new Set([...prev, entry.target]),
            ]);
          }
        });
      },
      { threshold: 0.2 }
    );

    const elements = sectionRef.current
      ? Array.from(sectionRef.current.querySelectorAll(".feature-item"))
      : [];
    elements.forEach((el) => observer.observe(el));

    return () => {
      elements.forEach((el) => observer.unobserve(el));
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      className="relative py-28"
      style={{ fontFamily: "'Poppins', sans-serif" }}
    >
      {/* Background Enhancements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 -left-32 w-[32rem] h-[32rem] bg-gradient-to-r from-blue-500/10 to-slate-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-0 w-[28rem] h-[28rem] bg-gradient-to-l from-indigo-600/10 to-slate-600/10 rounded-full blur-3xl animate-pulse-slow delay-1000"></div>
      </div>
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.04]"></div>

      <div className="container mx-auto px-6 relative z-10">
        {/* Section Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-full px-4 py-2 mb-6 text-sm font-medium text-slate-300 backdrop-blur-sm">
            <svg
              className="w-4 h-4 text-blue-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v2a2 2 0 01-2 2H7a2 2 0 01-2-2V4zm0 6a2 2 0 012-2h6a2 2 0 012 2v6a2 2 0 01-2 2H7a2 2 0 01-2-2v-6zM16 4a2 2 0 00-2-2h-1a1 1 0 100 2h1a1 1 0 011 1v1a1 1 0 102 0V4zM16 10a1 1 0 011 1v1a1 1 0 102 0v-1a2 2 0 00-2-2h-1a1 1 0 100 2h1zM16 16a1 1 0 011 1v1a2 2 0 002-2v-1a1 1 0 10-2 0v1a1 1 0 01-1 1z"></path>
            </svg>
            Core Features
          </div>
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-4">
            How We Help You
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Unlock powerful contract intelligence with interactive tools, risk
            detection, and smart checklists.
          </p>
          <div className="w-20 h-1 bg-gradient-to-r from-blue-500 to-indigo-500 mx-auto mt-6 rounded-full"></div>
        </div>

        {/* Features List */}
        <div className="space-y-24">
          {featuresData.map((feature, index) => {
            const isVisible = visibleElements.some(
              (el) => el.dataset.index === String(index)
            );
            const isOdd = index % 2 !== 0;

            return (
<div
  key={index}
  data-index={index}
  className={`feature-item relative grid grid-cols-1 lg:grid-cols-2 gap-10 items-center transition-all duration-1000 max-w-8xl mx-auto px-6 py-10 rounded-2xl bg-slate-800/40 backdrop-blur-md border border-slate-700/50 shadow-xl ${
    isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
  }`}
>
  {/* Image/Video Column */}
  <div className={`relative group ${isOdd ? 'lg:order-2' : ''}`}>
    <div className="absolute -inset-4 bg-gradient-to-b from-black via-gray-900 to-black rounded-2xl blur-xl opacity-40 group-hover:opacity-70 transition-opacity duration-300"></div>
    {feature.video ? (
      <video 
        autoPlay 
        loop 
        muted 
        playsInline
        className="relative rounded-lg shadow-2xl w-full h-72 object-cover"
      >
        <source src={feature.video} type="video/mp4" />
      </video>
    ) : (
      <img 
        src={feature.image} 
        alt={feature.title} 
        className="relative rounded-lg shadow-2xl w-full h-72 object-cover"
        onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/600x400/0f172a/94a3b8?text=Image+Not+Found'; }}
      />
    )}
  </div>

  {/* Text Column */}
  <div className={`text-center lg:text-left ${isOdd ? 'lg:order-1' : ''}`}>
    <h3 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent mb-4">
      {feature.title}
    </h3>
    <p className="text-gray-400 text-base mb-6">{feature.description}</p>
    <ul className="space-y-2">
      {feature.points.map((point, pIndex) => (
        <li key={pIndex} className="flex items-center gap-3 text-slate-300 text-sm">
          <svg className="w-5 h-5 text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span>{point}</span>
        </li>
      ))}
    </ul>
  </div>
</div>

            );
          })}
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
        .animate-pulse-slow {
          animation: pulse-slow 4s ease-in-out infinite;
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.8; }
        }
        .bg-grid-pattern {
          background-image: radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1px);
          background-size: 40px 40px;
        }
      `}</style>
    </section>
  );
};

export default FeaturesShowcase;

