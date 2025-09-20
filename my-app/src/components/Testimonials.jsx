"use client";
import React, { useState, useEffect, useRef } from 'react';

// Sample testimonial data
const testimonials = [
    {
        quote: "DocuMind saved me hours of confusion. I finally understood my freelance contract and could negotiate with confidence. A must-have for any independent contractor!",
        name: "Sarah L.",
        role: "Freelance Designer",
        avatar: "https://randomuser.me/api/portraits/women/44.jpg" // Placeholder image
    },
    {
        quote: "As a small business owner, I deal with contracts daily. The Riskometer feature is a game-changer. It instantly flagged a risky clause that I had completely missed.",
        name: "David Chen",
        role: "Small Business Owner",
        avatar: "https://randomuser.me/api/portraits/men/32.jpg" // Placeholder image
    },
    {
        quote: "I used this for my apartment lease, and it was incredible. The Q&A with proof gave me total peace of mind. I'll never sign another document without running it through DocuMind first.",
        name: "Maria G.",
        role: "Renter & Student",
        avatar: "https://randomuser.me/api/portraits/women/68.jpg" // Placeholder image
    }
];

const Testimonials = () => {
    const [isVisible, setIsVisible] = useState(false);
    const sectionRef = useRef(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    setIsVisible(true);
                    observer.disconnect();
                }
            },
            { threshold: 0.2 }
        );

        if (sectionRef.current) {
            observer.observe(sectionRef.current);
        }

        return () => observer.disconnect();
    }, []);

    return (
        <section ref={sectionRef} className="relative bg-gradient-to-b from-slate-800 via-gray-900 to-black py-24" style={{ fontFamily: "'Poppins', sans-serif" }}>
            {/* Consistent themed background elements */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-l from-slate-500/10 to-blue-600/10 rounded-full blur-3xl animate-pulse-slow"></div>
            </div>

            <div className="container mx-auto px-6 relative z-10">
                {/* Section Header */}
                <div className={`text-center mb-16 transform transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                    <div className="inline-flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-full px-4 py-2 mb-6 text-sm font-medium text-slate-300 backdrop-blur-sm">
                        <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                        Real Stories, Real Confidence
                    </div>
                    <h2 className="text-5xl md:text-6xl font-bold text-white">Trusted by Professionals & Individuals</h2>
                </div>

                {/* Testimonials Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {testimonials.map((testimonial, index) => (
                        <div
                            key={index}
                            className={`bg-slate-800/40 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-lg transform transition-all duration-500 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
                            style={{ transitionDelay: `${index * 200}ms` }}
                        >
                            <div className="flex items-center mb-6">
                                <img src={testimonial.avatar} alt={testimonial.name} className="w-12 h-12 rounded-full mr-4 border-2 border-slate-600"/>
                                <div>
                                    <p className="font-bold text-white">{testimonial.name}</p>
                                    <p className="text-sm text-slate-400">{testimonial.role}</p>
                                </div>
                            </div>
                            <p className="text-gray-300 italic">"{testimonial.quote}"</p>
                            <div className="flex mt-6">
                                {[...Array(5)].map((_, i) => (
                                    <svg key={i} className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                    </svg>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
             <style>{`
                 @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
            `}</style>
        </section>
    );
};

export default Testimonials;
