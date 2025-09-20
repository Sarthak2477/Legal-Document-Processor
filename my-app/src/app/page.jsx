// 1. Correct import paths using the standard Next.js '@/' alias
import Navbar from '@/components/Navbar';
import HeroSection from '@/components/Hero-section';
import FeaturesSection from '@/components/Feature';
import IntroductionSection from '@/components/IntroductionSection';
import FeaturesShowcase from '@/components/FeaturesShowcase'; // Assuming you have this component
import Footer from '@/components/Footer';

// 2. Renamed component to be more descriptive (best practice)
const LandingPage = () => {
    return (
        <div className="bg-black" style={{ fontFamily: "'Inter', sans-serif" }}>
            <Navbar />
            <main>
                <HeroSection />
                <FeaturesSection />
                <FeaturesShowcase />
                <IntroductionSection />
                {/* <Testimonials />  */}
            </main>
            <Footer />
        </div>
    );
};

export default LandingPage;
