'use client';

import Link from 'next/link';

const services = [
  {
    icon: (
      <svg className="w-12 h-12 text-[#00B39F]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    title: 'Professional Forex Signals',
    description: 'High-probability trade setups with detailed analysis delivered daily via Telegram.',
    features: [
      'Daily market analysis & signals',
      'Entry/exit levels with reasoning',
      'Risk management guidance',
      'Real-time trade updates',
      'Performance tracking',
      'Strategy explanations'
    ]
  },
  {
    icon: (
      <svg className="w-12 h-12 text-[#000ABE]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
      </svg>
    ),
    title: 'Community Mentorship',
    description: 'Join our trading community with expert guidance and peer support.',
    features: [
      'Group mentorship sessions',
      'Trade review & feedback',
      'Live trading rooms',
      'Community support network',
      'Weekly market analysis',
      'Trading psychology workshops'
    ]
  },
  {
    icon: (
      <svg className="w-12 h-12 text-[#00B38F]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0118 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: 'Trading Education',
    description: 'Comprehensive forex education resources to build your trading foundation.',
    features: [
      'Market fundamentals & economics',
      'Technical & fundamental analysis',
      'Risk management frameworks',
      'Trading psychology mastery',
      'Live market examples',
      'Strategy development guides'
    ]
  }
];

export default function Features() {
  return (
    <section id="services" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 bg-[#00B38F] text-white rounded-full text-sm font-medium mb-4">
            Professional Trading Services
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight mb-4">
            What We Offer
            <span className="text-[#00B38F] block mt-2">Professional Traders</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed mb-8">
            Everything you need to succeed in forex trading - premium signals, expert community mentorship, and comprehensive educational resources
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-[#00B38F] rounded-full"></div>
              <span>5,000+ Active Traders</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-[#000ABE] rounded-full"></div>
              <span>78% Success Rate</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-[#00B39F] rounded-full"></div>
              <span>24/7 Support</span>
            </div>
          </div>
        </div>

        {/* Services Grid */}
        <div className="grid md:grid-cols-3 gap-8">
          {services.map((service, index) => (
            <div 
              key={index}
              className="relative bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow duration-300 border border-gray-200"
            >
              {/* Icon Container */}
              <div className="flex justify-center mb-6">
                <div className="w-16 h-16 bg-gray-50 rounded-lg flex items-center justify-center">
                  {service.icon}
                </div>
              </div>

              {/* Content */}
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-gray-900 mb-4">{service.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{service.description}</p>
                </div>

                {/* Feature List */}
                <ul className="space-y-3">
                  {service.features.map((item, featureIndex) => (
                    <li key={featureIndex} className="flex items-start space-x-3">
                      <div className="w-5 h-5 bg-[#00B38F] rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <span className="text-gray-700 font-medium">
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* Pricing Plans CTA */}
        <div className="text-center mt-20">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-4xl mx-auto">
            <div className="text-3xl font-bold text-gray-900 mb-6">
              Ready to Start Trading Professionally?
            </div>
            <p className="text-gray-600 mb-8 leading-relaxed text-lg">
              Join thousands of successful traders who trust OxiWorld for premium signals, expert mentorship, and comprehensive trading education. Choose the plan that fits your trading goals.
            </p>
            <div className="grid md:grid-cols-3 gap-8 mb-8">
              <div className="text-center">
                <div className="flex justify-center mb-3">
                  <svg className="w-8 h-8 text-[#00B39F]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                  </svg>
                </div>
                <div className="font-semibold text-gray-900 mb-2">Premium Signals</div>
                <div className="text-sm text-gray-600">High-probability setups daily</div>
              </div>
              <div className="text-center">
                <div className="flex justify-center mb-3">
                  <svg className="w-8 h-8 text-[#000ABE]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                  </svg>
                </div>
                <div className="font-semibold text-gray-900 mb-2">Expert Community</div>
                <div className="text-sm text-gray-600">Learn from professional traders</div>
              </div>
              <div className="text-center">
                <div className="flex justify-center mb-3">
                  <svg className="w-8 h-8 text-[#00B38F]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0118 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                  </svg>
                </div>
                <div className="font-semibold text-gray-900 mb-2">Comprehensive Education</div>
                <div className="text-sm text-gray-600">Complete trading curriculum</div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                href="/pricing" 
                className="bg-[#00B38F] text-white px-8 py-4 rounded-lg font-semibold hover:bg-[#00A87D] transition-colors text-lg"
              >
                View Pricing Plans
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}