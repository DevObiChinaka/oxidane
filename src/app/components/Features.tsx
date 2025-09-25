'use client';

import Link from 'next/link';

const features = [
  {
    icon: (
      <svg className="w-16 h-16 text-[var(--brand-teal-green)]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0118 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: 'Complete Education',
    description: 'Comprehensive forex education from absolute basics to advanced institutional strategies.',
    features: [
      'Market fundamentals & economics',
      'Technical & fundamental analysis', 
      'Risk management frameworks',
      'Trading psychology mastery',
      'Live market practice',
      'Lifetime access & updates'
    ],
    link: '/courses',
    buttonText: 'Start Free Learning',
    price: 'Free Forever',
    highlight: 'Most Popular'
  },
  {
    icon: (
      <svg className="w-16 h-16 text-[var(--brand-cyan)]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
      </svg>
    ),
    title: 'Personal Mentorship',
    description: 'One-on-one guidance from profitable traders who have walked the journey.',
    features: [
      'Weekly 1-on-1 video calls',
      'Personal trading plan review',
      'Live trading sessions',
      'Direct message support',
      'Career development guidance',
      'Prop firm preparation'
    ],
    link: '/mentorship',
    buttonText: 'Apply for Mentorship',
    price: 'From $299/month',
    highlight: 'Limited Spots'
  },
  {
    icon: (
      <svg className="w-16 h-16 text-[var(--brand-electric)]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    title: 'Market Signals',
    description: 'High-probability trade setups with full analysis - learn while you earn.',
    features: [
      'Daily market analysis',
      'Entry/exit levels with reasoning',
      'Risk management guidance',
      'Educational explanations',
      'Performance tracking',
      'Strategy breakdowns'
    ],
    link: '/signals',
    buttonText: 'Join Signal Service',
    price: 'From $97/month',
    highlight: 'Learn & Earn'
  }
];

export default function Features() {
  return (
    <section className="py-24 bg-brand-page relative overflow-hidden">
      {/* Creative Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 -left-32 w-64 h-64 gradient-brand-electric rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-float"></div>
        <div className="absolute bottom-1/4 -right-32 w-80 h-80 gradient-brand-ocean rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-pulse"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 gradient-brand-glow rounded-full mix-blend-multiply filter blur-2xl opacity-10 animate-float" style={{ animationDelay: '3s' }}></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Creative Section Header */}
        <div className="text-center space-y-6 mb-20">
          <div className="inline-flex items-center px-6 py-3 card-brand rounded-full mb-4">
            <span className="text-[var(--brand-electric)] font-semibold">🚀 COMPLETE TRADING ECOSYSTEM</span>
          </div>
          <h2 className="text-5xl md:text-7xl font-bold text-white leading-tight">
            Your Professional Trading
            <span className="gradient-brand-text block mt-2">Education Journey</span>
          </h2>
          <p className="text-xl text-white/80 max-w-4xl mx-auto leading-relaxed">
            Everything you need to transform from beginner to professional forex trader - comprehensive education, expert mentorship, and real market insights
          </p>
          <div className="flex justify-center space-x-4 mt-8">
            <div className="flex items-center space-x-2 text-white/60">
              <div className="w-2 h-2 bg-[var(--brand-teal-green)] rounded-full"></div>
              <span>5,000+ Students Trained</span>
            </div>
            <div className="flex items-center space-x-2 text-white/60">
              <div className="w-2 h-2 bg-[var(--brand-electric)] rounded-full"></div>
              <span>78% Success Rate</span>
            </div>
            <div className="flex items-center space-x-2 text-white/60">
              <div className="w-2 h-2 bg-[var(--brand-cyan)] rounded-full"></div>
              <span>24/7 Support</span>
            </div>
          </div>
        </div>

        {/* Creative Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
          {features.map((feature, index) => (
            <div 
              key={index}
              className={`relative card-brand-glow p-8 hover-brand-lift animate-float group ${
                feature.highlight === 'Most Popular' ? 'shadow-brand-lg border-2 border-[var(--brand-electric)]' : 'shadow-brand'
              }`}
              style={{ animationDelay: `${index * 0.5}s` }}
            >
              {/* Creative Highlight Badge */}
              {feature.highlight && (
                <div className="absolute -top-6 left-1/2 transform -translate-x-1/2">
                  <div className="gradient-brand-glow px-6 py-2 rounded-full text-white font-bold text-sm animate-pulse-glow">
                    ⭐ {feature.highlight}
                  </div>
                </div>
              )}

              {/* Animated Icon Container */}
              <div className="flex justify-center mb-8">
                <div className="w-20 h-20 card-brand rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
              </div>

              {/* Content */}
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-2xl font-bold gradient-brand-text mb-3">{feature.title}</h3>
                  <div className="text-lg font-bold text-[var(--brand-electric)] mb-4 bg-white/5 px-4 py-2 rounded-full inline-block">
                    {feature.price}
                  </div>
                  <p className="text-white/80 leading-relaxed text-lg">{feature.description}</p>
                </div>

                {/* Creative Feature List */}
                <ul className="space-y-4">
                  {feature.features.map((item, featureIndex) => (
                    <li key={featureIndex} className="flex items-start space-x-4 group">
                      <div className="w-6 h-6 gradient-brand-glow rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <span className="text-white font-medium group-hover:text-[var(--brand-electric)] transition-colors">
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>

                {/* Creative CTA Button */}
                <div className="pt-6">
                  <Link 
                    href={feature.link}
                    className={`block w-full text-center py-4 px-8 rounded-xl font-bold text-lg transition-all duration-300 transform hover:scale-105 ${
                      feature.highlight === 'Most Popular'
                        ? 'gradient-brand-glow text-white hover:shadow-brand animate-pulse-glow' 
                        : 'border-2 border-[var(--brand-electric)] text-[var(--brand-electric)] hover:bg-[var(--brand-electric)] hover:text-white card-brand backdrop-blur-md'
                    }`}
                  >
                    <span className="flex items-center justify-center space-x-2">
                      <span>{feature.buttonText}</span>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </span>
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Creative Value Proposition */}
        <div className="text-center mt-20">
          <div className="card-brand-glow p-12 shadow-brand-lg max-w-6xl mx-auto animate-float" style={{ animationDelay: '2s' }}>
            <div className="gradient-brand-text text-3xl font-bold mb-6">
              🎯 Why Start with Professional Education?
            </div>
            <p className="text-white/90 mb-8 leading-relaxed text-lg max-w-4xl mx-auto">
              95% of traders lose money because they jump in without proper education. We believe in building 
              rock-solid foundations first. Our comprehensive system covers everything from psychology to advanced 
              institutional strategies before you risk a single dollar.
            </p>
            <div className="grid md:grid-cols-3 gap-8 mb-10">
              <div className="text-center">
                <div className="flex justify-center mb-2">
                  <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.847a4.5 4.5 0 003.09 3.09L15.75 12l-2.847.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                  </svg>
                </div>
                <div className="font-semibold text-gray-900">Understand First</div>
                <div className="text-sm text-gray-600">Learn market fundamentals before trading</div>
              </div>
              <div className="text-center">
                <div className="flex justify-center mb-2">
                  <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                </div>
                <div className="font-semibold text-gray-900">Protect Capital</div>
                <div className="text-sm text-gray-600">Master risk management from day one</div>
              </div>
              <div className="text-center">
                <div className="flex justify-center mb-2">
                  <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
                  </svg>
                </div>
                <div className="font-semibold text-gray-900">Build Confidence</div>
                <div className="text-sm text-gray-600">Practice with demo before going live</div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                href="/courses" 
                className="gradient-purple text-white px-8 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity"
              >
                Start Free Education
              </Link>
              <Link 
                href="/about" 
                className="border-2 border-purple-600 text-purple-600 px-8 py-3 rounded-lg font-semibold hover:bg-purple-600 hover:text-white transition-all duration-300"
              >
                Learn About Us
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}