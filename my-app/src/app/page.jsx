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
    <div className="relative min-h-screen" style={{ fontFamily: "'Inter', sans-serif" }}>
      
      {/* Beams Background */}
      <div className="absolute inset-0 -z-10">
        <Beams lightColor="blue" rotation="20"  scale="0.2" beamHeight="30" />
      </div>

      {/* Page Content */}
      <Navbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <FeaturesShowcase />
        <IntroductionSection />  
       {/* <Testimonials /> */}
      </main>
       <Footer /> 
    </div>
  );
};

export default LandingPage;
