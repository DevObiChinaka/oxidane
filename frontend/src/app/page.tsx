import Navigation from './components/Navigation';
import Hero from './components/Hero';
import EducationalValue from './components/EducationalValue';
import Features from './components/Features';
import FounderBio from './components/FounderBio';
import TestimonialsCredibility from './components/TestimonialsCredibility';
import Footer from './components/Footer';
import WhatsAppSupport from './components/WhatsAppSupport';

export default function Home() {
  return (
    <div className="min-h-screen bg-white overflow-x-hidden">
      <Navigation />
      {/* Spacer for fixed navbar - matches navbar height (h-20 = 80px) */}
      <div className="h-20"></div>
      <Hero />
      <EducationalValue />
      <Features />
      <FounderBio />
      <TestimonialsCredibility />
      <Footer />
      <WhatsAppSupport />
    </div>
  );
}
