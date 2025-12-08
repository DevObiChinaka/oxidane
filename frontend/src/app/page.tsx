import Navigation from './components/Navigation';
import Hero from './components/Hero';
import EducationalValue from './components/EducationalValue';
import StrategyShowcase from './components/StrategyShowcase';
import Features from './components/Features';
import FounderBio from './components/FounderBio';
import TestimonialsCredibility from './components/TestimonialsCredibility';
import Footer from './components/Footer';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <Hero />
      <EducationalValue />
      <StrategyShowcase />
      <Features />
      <FounderBio />
      <TestimonialsCredibility />
      <Footer />
    </div>
  );
}
