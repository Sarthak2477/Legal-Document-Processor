// app/page.js (or your LandingPage file)

"use client";
import Navbar from '@/components/Navbar';
import HeroSection from '@/components/Hero-section';
import FeaturesSection from '@/components/Feature';
import IntroductionSection from '@/components/IntroductionSection';
import FeaturesShowcase from '@/components/FeaturesShowcase';
import Footer from '@/components/Footer';
import Beams from '@/components/Beams';

const LandingPage = () => {
  return (
    <div className="relative min-h-screen font-sans">
      
      {/* Beams Background */}
      <div className="absolute inset-0 -z-10">
        <Beams lightColor="blue" rotation="20"  scale="0.2" beamHeight="30" />
      </div>

      {/* Page Content */}
      <Navbar />
      <main>
        {/* The "Home" link will scroll here */}
        <section id="home">
          <HeroSection />
        </section>

        {/* The "Features" link will scroll here */}
        <section id="features">
          <FeaturesSection />
          <FeaturesShowcase />
        </section>

        {/* The "About" link will scroll here */}
        <section id="about">
          <IntroductionSection />
        </section>
        
        {/* <Testimonials /> */}
      </main>
      <Footer /> 
    </div>
  );
};

export default LandingPage;