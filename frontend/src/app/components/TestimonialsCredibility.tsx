'use client';

import { useState, useEffect } from 'react';

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Former Bank Employee",
    location: "Singapore",
    image: (
      <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-gray-100 to-slate-200 flex items-center justify-center overflow-hidden ring-4 ring-[#00B38F]/20 shadow-lg">
        <img 
          src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=160&h=160&fit=crop&crop=face&auto=format&q=90" 
          alt="Sarah Chen - Professional Trader"
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=160&h=160&fit=crop&crop=face&auto=format&q=90";
          }}
        />
      </div>
    ),
    story: "Started as a complete beginner with the free course. The risk management lessons saved me from huge losses. Now I trade part-time with consistent profits.",
    result: "12% monthly returns",
    timeframe: "After 8 months",
    beforeAfter: {
      before: "Lost $500 in first month",
      after: "Consistent profitable trader"
    }
  },
  {
    name: "Marcus Johnson", 
    role: "Software Engineer",
    location: "London, UK",
    image: (
      <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-gray-100 to-slate-200 flex items-center justify-center overflow-hidden ring-4 ring-[#00B39F]/20 shadow-lg">
        <img 
          src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&h=160&fit=crop&crop=face&auto=format&q=90" 
          alt="Marcus Johnson - Professional Trader"
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=160&h=160&fit=crop&crop=face&auto=format&q=90";
          }}
        />
      </div>
    ),
    story: "The mentorship program changed everything. Having a professional trader guide my development was invaluable. The psychology training was eye-opening.",
    result: "Funded $50k account",
    timeframe: "After 6 months", 
    beforeAfter: {
      before: "Emotional trader with losses",
      after: "Disciplined prop firm trader"
    }
  },
  {
    name: "Emma Rodriguez",
    role: "Medical Student", 
    location: "Madrid, Spain",
    image: (
      <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-[#00B38F]/20 to-[#00B39F]/20 flex items-center justify-center overflow-hidden ring-4 ring-[#00B38F]/20 shadow-lg">
        <img 
          src="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=160&h=160&fit=crop&crop=face&auto=format&q=90" 
          alt="Emma Rodriguez - Professional Trader"
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = "https://images.unsplash.com/photo-1559233375-61fc6ac57b28?w=160&h=160&fit=crop&crop=face&auto=format&q=90";
          }}
        />
      </div>
    ),
    story: "Perfect for my busy schedule. Free lessons are incredibly detailed. The telegram signals helped me understand market timing while learning.",
    result: "Profitable in 4 months",
    timeframe: "Part-time trading",
    beforeAfter: {
      before: "No trading knowledge",
      after: "Supplementing income"
    }
  }
];

const credentials = [
  {
    icon: (
      <svg className="w-8 h-8 text-[#00B39F]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.228a25.08 25.08 0 012.916.52 6.003 6.003 0 00-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0" />
      </svg>
    ),
    title: "Certified Trader",
    description: "CFA Institute certified with 5+ years in institutional trading"
  },
  {
    icon: (
      <svg className="w-8 h-8 text-[#00B38F]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ), 
    title: "Track Record",
    description: "Audited 24-month performance with 78% win rate"
  },
  {
    icon: (
      <svg className="w-8 h-8 text-[#000ABE]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" />
      </svg>
    ),
    title: "Educator",
    description: "Trained 5000+ students across 50+ countries"
  },
  {
    icon: (
      <svg className="w-8 h-8 text-[#00B39F]" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    title: "Risk First",
    description: "Zero account blow-ups in 3 years of teaching"
  }
];

const realResults = [
  { metric: "Students Taught", value: "5,247", period: "Since 2021" },
  { metric: "Countries Reached", value: "52", period: "Globally" },
  { metric: "Free Course Rating", value: "4.9/5", period: "2,100+ reviews" },
  { metric: "Student Success Rate", value: "78%", period: "Profitable after 6 months" }
];

export default function TestimonialsCredibility() {
  const [currentTestimonial, setCurrentTestimonial] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Real Results */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8">
            Real Students, Real Results
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {realResults.map((result, index) => (
              <div key={index} className="bg-gradient-to-br from-[#00B38F]/10 to-[#00B39F]/10 rounded-xl p-6 text-center">
                <div className="text-3xl font-bold text-[#00B38F]/80 mb-2">{result.value}</div>
                <div className="font-semibold text-gray-900 mb-1">{result.metric}</div>
                <div className="text-sm text-gray-600">{result.period}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Testimonial Carousel */}
        <div className="bg-gradient-to-br from-gray-50 to-[#00B38F]/10 rounded-3xl p-8 md:p-12 mb-16">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Student Success Stories</h3>
              <p className="text-gray-600">Real transformations from our education-first approach</p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-lg relative overflow-hidden">
              {/* Testimonial Content */}
              <div className="text-center space-y-6">
                <div className="mb-4">{testimonials[currentTestimonial].image}</div>
                
                <blockquote className="text-lg text-gray-700 leading-relaxed italic">
                  "{testimonials[currentTestimonial].story}"
                </blockquote>

                <div className="space-y-4">
                  <div className="flex justify-center space-x-8">
                    <div className="text-center">
                      <div className="text-sm text-gray-500">Before</div>
                      <div className="font-semibold text-red-600">
                        {testimonials[currentTestimonial].beforeAfter.before}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-500">After</div>
                      <div className="font-semibold text-green-600">
                        {testimonials[currentTestimonial].beforeAfter.after}
                      </div>
                    </div>
                  </div>

                  <div className="text-center">
                    <div className="text-2xl font-bold text-[#000ABE]">
                      {testimonials[currentTestimonial].result}
                    </div>
                    <div className="text-sm text-gray-600">
                      {testimonials[currentTestimonial].timeframe}
                    </div>
                  </div>

                  <div className="text-center">
                    <div className="font-semibold text-gray-900">
                      {testimonials[currentTestimonial].name}
                    </div>
                    <div className="text-sm text-gray-600">
                      {testimonials[currentTestimonial].role} • {testimonials[currentTestimonial].location}
                    </div>
                  </div>
                </div>
              </div>

              {/* Navigation Dots */}
              <div className="flex justify-center space-x-2 mt-8">
                {testimonials.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentTestimonial(index)}
                    className={`w-3 h-3 rounded-full transition-all ${
                      index === currentTestimonial ? 'bg-[#00B38F]' : 'bg-gray-300'
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Testimonial Preview Gallery */}
            <div className="mt-8 bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <h4 className="text-center text-white text-sm font-medium mb-4">
                All Client Success Stories
              </h4>
              <div className="flex justify-center items-center space-x-8">
                {testimonials.map((testimonial, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentTestimonial(index)}
                    className={`group relative transition-all duration-300 ${
                      index === currentTestimonial ? 'scale-110' : 'hover:scale-105 opacity-70'
                    }`}
                  >
                    <div className={`w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-[#00B38F]/20 to-[#00B39F]/20 flex items-center justify-center overflow-hidden transition-all duration-300 ${
                      index === currentTestimonial 
                        ? 'ring-4 ring-[#00B38F] shadow-lg shadow-[#00B38F]/30' 
                        : 'ring-2 ring-gray-400 group-hover:ring-[#00B38F]/50'
                    }`}>
                      <img 
                        src={testimonial.name === "Sarah Chen" 
                          ? "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=64&h=64&fit=crop&crop=face&auto=format&q=90"
                          : testimonial.name === "Marcus Johnson"
                          ? "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=64&h=64&fit=crop&crop=face&auto=format&q=90"
                          : "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=64&h=64&fit=crop&crop=face&auto=format&q=90"
                        }
                        alt={`${testimonial.name} - Professional Trader`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          if (testimonial.name === "Sarah Chen") {
                            e.currentTarget.src = "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=64&h=64&fit=crop&crop=face&auto=format&q=90";
                          } else if (testimonial.name === "Marcus Johnson") {
                            e.currentTarget.src = "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=64&h=64&fit=crop&crop=face&auto=format&q=90";
                          } else {
                            e.currentTarget.src = "https://images.unsplash.com/photo-1559233375-61fc6ac57b28?w=64&h=64&fit=crop&crop=face&auto=format&q=90";
                          }
                        }}
                      />
                    </div>
                    <div className="mt-2 text-center">
                      <p className={`text-xs font-medium transition-colors duration-300 ${
                        index === currentTestimonial ? 'text-[#00B38F]' : 'text-gray-400'
                      }`}>
                        {testimonial.name}
                      </p>
                      <p className={`text-xs transition-colors duration-300 ${
                        index === currentTestimonial ? 'text-[#00B39F]' : 'text-gray-500'
                      }`}>
                        {testimonial.result}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Instructor Credentials */}
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-8">
            <div>
              <h3 className="text-3xl font-bold text-gray-900 mb-4">
                Your Instructor: Professional Credentials
              </h3>
              <p className="text-lg text-gray-600 leading-relaxed">
                Learn from someone who's been there. Our lead instructor brings institutional 
                trading experience and a proven track record of student success.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {credentials.map((credential, index) => (
                <div key={index} className="bg-white rounded-xl p-6 shadow-lg border border-[#00B38F]/20">
                  <div className="mb-3">{credential.icon}</div>
                  <h4 className="font-bold text-gray-900 mb-2">{credential.title}</h4>
                  <p className="text-gray-600 text-sm">{credential.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            {/* Verified Track Record */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-8 border border-green-200">
              <h4 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                <svg className="w-6 h-6 text-green-600 mr-2" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Verified Trading Record
              </h4>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">Win Rate (24 months)</span>
                  <span className="font-bold text-green-600">78.3%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">Average Risk-Reward</span>
                  <span className="font-bold text-green-600">1:2.4</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">Maximum Drawdown</span>
                  <span className="font-bold text-green-600">8.2%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">Consistency Score</span>
                  <span className="font-bold text-green-600">92/100</span>
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-600">
                *Audited by third-party verification service
              </div>
            </div>

            {/* Education Philosophy */}
            <div className="bg-gradient-to-br from-[#000ABE]/10 to-[#00B39F]/10 rounded-2xl p-8">
              <h4 className="text-xl font-bold text-gray-900 mb-4">Our Teaching Philosophy</h4>
              <ul className="space-y-3">
                <li className="flex items-start space-x-3">
                  <div className="w-5 h-5 bg-gradient-to-r from-[#00B38F] to-[#00B39F] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-white text-xs">1</span>
                  </div>
                  <span className="text-gray-700">Education before profit - understand before you trade</span>
                </li>
                <li className="flex items-start space-x-3">
                  <div className="w-5 h-5 bg-gradient-to-r from-[#000ABE] to-[#00B38F] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-white text-xs">2</span>
                  </div>
                  <span className="text-gray-700">Risk management is the foundation of all profitable trading</span>
                </li>
                <li className="flex items-start space-x-3">
                  <div className="w-5 h-5 bg-gradient-to-r from-[#00B39F] to-[#000ABE] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-white text-xs">3</span>
                  </div>
                  <span className="text-gray-700">Psychology and discipline matter more than indicators</span>
                </li>
                <li className="flex items-start space-x-3">
                  <div className="w-5 h-5 bg-gradient-to-r from-[#00B38F] to-[#000ABE] rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-white text-xs">4</span>
                  </div>
                  <span className="text-gray-700">Real market experience through guided practice</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Trust Badges */}
        <div className="text-center mt-16">
          <p className="text-gray-600 mb-6">Trusted by students worldwide</p>
          <div className="flex flex-wrap justify-center items-center gap-8 opacity-60">
            <div className="text-gray-400 font-semibold flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.228a25.08 25.08 0 012.916.52 6.003 6.003 0 00-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0" />
              </svg>
              CFA Institute
            </div>
            <div className="text-gray-400 font-semibold flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
              TradingView Partner
            </div>
            <div className="text-gray-400 font-semibold flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
              Risk Management Certified
            </div>
            <div className="text-gray-400 font-semibold flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3s-4.5 4.03-4.5 9 2.015 9 4.5 9z" />
              </svg>
              Global Educator
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}