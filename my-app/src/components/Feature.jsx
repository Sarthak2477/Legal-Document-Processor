"use client";
import React, { useState, useEffect, useRef } from 'react';

const features = [
    {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
        title: 'Q&A with Proof',
        description: 'Ask detailed questions and get plain-language answers backed by direct quotes from your document.',
        highlight: 'Instant Answers',
        stat: '99.7% accuracy'
    },
    {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
        ),
        title: 'Riskometer',
        description: 'Proactively identify potential risks, hidden obligations, and unfair clauses before you sign.',
        highlight: 'Risk Detection',
        stat: '47 risk types'
    },
    {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
            </svg>
        ),
        title: 'Automated Checklists',
        description: 'Instantly generate a list of supporting documents required for your specific contract type.',
        highlight: 'Smart Lists',
        stat: '12 doc types'
    },
    {
        icon: (
             <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-blue-400 group-hover:text-blue-300 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                 <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
        ),
        title: 'Secure & Private',
        description: 'Your documents are processed with privacy first. All personal information is automatically removed.',
        highlight: 'Bank-Level Security',
        stat: 'SOC 2 certified'
    },
];

const FeaturesPage = () => {
    const [visibleIndexes, setVisibleIndexes] = useState([]);
    const sectionRef = useRef(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const index = parseInt(entry.target.dataset.index);
                        setVisibleIndexes(prev => [...new Set([...prev, index])]);
                    }
                });
            },
            { threshold: 0.3 }
        );

        const featureElements = sectionRef.current ? Array.from(sectionRef.current.querySelectorAll('[data-index]')) : [];
        featureElements.forEach((el) => observer.observe(el));

        return () => {
            featureElements.forEach((el) => observer.unobserve(el));
        };
    }, []);

    return (
        <div className="relative overflow-hidden" style={{ fontFamily: "'Poppins', sans-serif" }}>
            
            {/* Consistent themed background elements */}
            <div className="absolute inset-0">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-blue-500/10 to-slate-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-l from-slate-500/10 to-blue-600/10 rounded-full blur-3xl animate-pulse-slow delay-1000"></div>
            </div>
            
            {/* Grid pattern overlay */}
            <div className="absolute inset-0 bg-grid-pattern opacity-3"></div>

            <section ref={sectionRef} className="py-24 relative z-10">
                <div className="container mx-auto px-6">
                    
                    {/* Enhanced Section Header */}
                    <div className="text-center mb-20">
                        <div className="inline-flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-full px-4 py-2 mb-6 text-sm font-medium text-slate-300 backdrop-blur-sm">
                            <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                            </svg>
                            Comprehensive Legal Tools
                        </div>
                        
                        <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-8 leading-tight">
                            <span className="bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                                Your All-in-One
                            </span>
                            <br />
                            <span className="bg-gradient-to-r from-slate-300 to-slate-400 bg-clip-text text-transparent">
                                Legal Solution
                            </span>
                        </h2>
                        
                        <p className="text-gray-400 text-xl md:text-2xl max-w-4xl mx-auto leading-relaxed">
                            Empower your legal decisions with <span className="text-white font-semibold">AI-powered analysis</span>, 
                            risk assessment, and automated workflows. Transform complex contracts into 
                            <span className="text-blue-400 font-semibold"> clear, actionable insights</span>.
                        </p>
                    </div>

                    {/* Enhanced Features Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
                        {features.map((feature, index) => (
                           <div 
                                key={index} 
                                data-index={index} 
                                className={`group relative bg-gradient-to-br from-slate-800/40 to-gray-900/60 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 hover:border-blue-500/50 transition-all duration-500 hover:transform hover:-translate-y-2 cursor-pointer ${
                                    visibleIndexes.includes(index) 
                                        ? 'opacity-100 translate-y-0' 
                                        : 'opacity-0 translate-y-8'
                                }`}
                                style={{
                                    transitionDelay: `${index * 150}ms`,
                                }}
                           >
                               <div className="relative z-10">
                                    <div className="mb-6 relative">
                                        <div className="w-16 h-16 bg-gradient-to-br from-slate-700/50 to-gray-800/50 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 mb-4">
                                            {feature.icon}
                                        </div>
                                        <span className="inline-block bg-blue-500/10 border border-blue-400/20 text-blue-300 text-xs font-medium px-2 py-1 rounded-md">
                                            {feature.highlight}
                                        </span>
                                    </div>
                                    <h3 className="text-2xl font-bold mb-4 text-white group-hover:text-blue-300 transition-colors duration-300">
                                        {feature.title}
                                    </h3>
                                    <p className="text-gray-400 text-base leading-relaxed mb-6 group-hover:text-gray-300 transition-colors duration-300">
                                        {feature.description}
                                    </p>
                                    <div className="flex items-center justify-between">
                                        <span className="text-blue-400 font-semibold text-sm">
                                            {feature.stat}
                                        </span>
                                        <svg 
                                            className="w-5 h-5 text-blue-400 transform group-hover:translate-x-1 transition-transform duration-300" 
                                            fill="none" 
                                            stroke="currentColor" 
                                            viewBox="0 0 24 24"
                                        >
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                                        </svg>
                                    </div>
                                </div>
                           </div>
                        ))}
                    </div>
                </div>
            </section>

            <style>{`
                @keyframes pulse-slow {
                    0%, 100% { opacity: 0.4; }
                    50% { opacity: 0.8; }
                }
                
                .animate-pulse-slow {
                    animation: pulse-slow 4s ease-in-out infinite;
                }
                
                .bg-grid-pattern {
                    background-image: radial-gradient(circle, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
                    background-size: 50px 50px;
                }
                 @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
            `}</style>
        </div>
    );
};

export default FeaturesPage;

