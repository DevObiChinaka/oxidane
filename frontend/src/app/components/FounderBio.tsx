'use client';

export default function FounderBio() {
  return (
    <section id="about" className="py-12 md:py-20 bg-gradient-to-br from-gray-50 to-slate-100 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-8 md:gap-12 items-center">
          {/* Left Column - Founder Image */}
          <div className="relative order-1 lg:order-1 overflow-hidden">
            <div className="relative z-10 px-2 sm:px-0">
              {/* Profile Image */}
              <div className="aspect-square rounded-2xl bg-gradient-to-br from-[#00B38F] to-[#00B39F] p-1 shadow-2xl overflow-hidden">
                <div className="w-full h-full rounded-2xl overflow-hidden bg-gray-900">
                  <img 
                    src="/images/founder.jpg" 
                    alt="OxiWorld Founder - Professional Forex Trader"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Crect fill='%23001529' width='400' height='400'/%3E%3Ctext x='50%25' y='50%25' font-size='60' fill='white' text-anchor='middle' dy='.3em' font-family='Arial'%3EOxiWorld%3C/text%3E%3C/svg%3E";
                    }}
                  />
                </div>
              </div>
              
              {/* Floating Achievement Cards */}
              <div className="absolute right-1 sm:-right-2 md:-right-4 top-4 md:top-8 bg-white rounded-lg md:rounded-xl p-2 sm:p-3 md:p-4 shadow-xl border border-gray-200 max-w-[100px] sm:max-w-[130px] md:max-w-[200px]">
                <div className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-[#00B38F]">1M+</div>
                <div className="text-[10px] sm:text-xs md:text-sm text-gray-600">Social Views</div>
              </div>
              
              <div className="absolute left-1 sm:-left-2 md:-left-4 bottom-4 md:bottom-8 bg-white rounded-lg md:rounded-xl p-2 sm:p-3 md:p-4 shadow-xl border border-gray-200 max-w-[100px] sm:max-w-[130px] md:max-w-[200px]">
                <div className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-[#000ABE]">500+</div>
                <div className="text-[10px] sm:text-xs md:text-sm text-gray-600">Students</div>
              </div>
            </div>
            
            {/* Background Decoration */}
            <div className="absolute inset-0 -z-10">
              <div className="absolute top-1/4 -left-8 md:-left-12 w-48 md:w-64 h-48 md:h-64 bg-[#00B38F]/20 rounded-full blur-3xl"></div>
              <div className="absolute bottom-1/4 -right-8 md:-right-12 w-48 md:w-64 h-48 md:h-64 bg-[#000ABE]/20 rounded-full blur-3xl"></div>
            </div>
          </div>

          {/* Right Column - Bio Content */}
          <div className="space-y-4 md:space-y-6 order-2 lg:order-2">
            <div className="inline-flex items-center px-4 py-2 bg-white rounded-full text-sm font-medium shadow-md border border-gray-200">
              <div className="w-2 h-2 bg-[#00B38F] rounded-full mr-2 animate-pulse"></div>
              <span className="text-gray-700">Meet Your Instructor</span>
            </div>

            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900">
              From Professional Trader to Educator
            </h2>

            <div className="space-y-3 md:space-y-4 text-base md:text-lg text-gray-700 leading-relaxed">
              <p>
                I've been trading forex for over 5 years, navigating both the highs of consistent profitability and the lows that taught me invaluable lessons. 
                My journey took me from institutional trading environments to becoming an independent trader, where I developed and refined the exact strategies 
                I now teach at OxiWorld Forex Academy.
              </p>

              <p>
                What started as sharing insights on social media grew into a community of over 1 million views and 500+ dedicated students across the globe. 
                I realized that while many "gurus" sell dreams, what traders actually need is honest, practical education about market structure, risk management, 
                and the psychological discipline required to succeed in this challenging field.
              </p>

              <p>
                Beyond trading, my background in software engineering and tech gives me a unique perspective on systematic approaches to the markets. 
                I built OxiWorld not just as a course platform, but as a complete ecosystem—combining structured education, live mentorship through Telegram, 
                and real trading signals so students can learn by seeing professional setups in action. As an official partner with Exness and Maven, 
                I'm committed to providing legitimate, transparent education in an industry full of noise.
              </p>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-3 gap-3 md:gap-4 pt-4 md:pt-6 border-t border-gray-300">
              <div className="text-center">
                <div className="text-xl md:text-2xl font-bold text-[#00B38F]">1M+</div>
                <div className="text-xs md:text-sm text-gray-600">Social Media Views</div>
              </div>
              <div className="text-center">
                <div className="text-xl md:text-2xl font-bold text-[#000ABE]">500+</div>
                <div className="text-xs md:text-sm text-gray-600">Students Trained</div>
              </div>
              <div className="text-center">
                <div className="text-xl md:text-2xl font-bold text-[#00B39F]">2</div>
                <div className="text-xs md:text-sm text-gray-600">Official Partnerships</div>
              </div>
            </div>

            {/* Partnership Badges */}
            <div className="flex flex-wrap items-center gap-3 md:gap-4 pt-3 md:pt-4">
              <div className="flex items-center space-x-2 text-xs md:text-sm text-gray-600">
                <svg className="w-5 h-5 text-[#00B38F]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">Exness Partner</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <svg className="w-5 h-5 text-[#00B38F]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">Maven Partner</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <svg className="w-5 h-5 text-[#00B38F]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium">5+ Years Trading Experience</span>
              </div>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-16 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-xl p-6">
          <div className="flex items-start space-x-3">
            <svg className="w-6 h-6 text-yellow-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <div>
              <h4 className="font-bold text-yellow-800 mb-2">Disclaimer: Trading Involves Risk</h4>
              <p className="text-yellow-700 text-sm leading-relaxed">
                Forex trading carries significant risk and is not suitable for all investors. Past performance is not indicative of future results. 
                The information provided through OxiWorld Forex Academy is for educational purposes only and should not be considered financial advice. 
                You should never trade with money you cannot afford to lose. All trading decisions are your own responsibility. 
                Please ensure you fully understand the risks involved and seek independent financial advice if necessary.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
