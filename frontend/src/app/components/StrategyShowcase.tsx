'use client';

const strategies = [
  {
    name: 'SMC',
    icon: '📊',
    color: 'from-[#00B38F] to-[#00B39F]',
    description: 'Learn to identify institutional order blocks, liquidity zones, and market structure shifts that professional traders use to enter high-probability positions.'
  },
  {
    name: 'ALGO',
    icon: '🤖',
    color: 'from-[#000ABE] to-[#00B39F]',
    description: 'Master algorithmic price action patterns and automated structure recognition to spot trading opportunities like the institutions do.'
  },
  {
    name: 'Alchemist',
    icon: '⚗️',
    color: 'from-purple-500 to-pink-500',
    description: 'Transform market chaos into consistent profits using advanced price manipulation techniques and liquidity hunting strategies.'
  },
  {
    name: 'MSNR',
    icon: '🎯',
    color: 'from-orange-500 to-red-500',
    description: 'Discover how to spot market sweeps, liquidity raids, and reaction zones where smart money makes their moves.'
  },
  {
    name: 'CRT',
    icon: '💎',
    color: 'from-cyan-500 to-blue-500',
    description: 'Read price action like a book. Understand what each candle formation reveals about market psychology and trader positioning.'
  }
];

export default function StrategyShowcase() {
  return (
    <section id="strategies" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white rounded-full text-sm font-medium mb-4">
            Advanced Trading Strategies
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Master Professional Trading Strategies
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            We teach you the exact strategies professional traders use to consistently profit from the markets. 
            Learn multiple approaches and discover what works best for your style.
          </p>
        </div>

        {/* Strategy Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {strategies.map((strategy, index) => (
            <div 
              key={index}
              className="group relative bg-gradient-to-br from-gray-50 to-white rounded-2xl p-8 shadow-lg border border-gray-200 hover:shadow-2xl transition-all duration-300 hover:-translate-y-1"
            >
              {/* Gradient Top Border */}
              <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${strategy.color} rounded-t-2xl`}></div>
              
              {/* Icon */}
              <div className="text-5xl mb-4">{strategy.icon}</div>
              
              {/* Strategy Name */}
              <h3 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
                {strategy.name}
                <span className={`ml-2 text-xs font-medium px-2 py-1 rounded-full bg-gradient-to-r ${strategy.color} text-white`}>
                  PRO
                </span>
              </h3>
              
              {/* Description */}
              <p className="text-gray-600 leading-relaxed">
                {strategy.description}
              </p>

              {/* Hover Indicator */}
              <div className={`mt-6 flex items-center text-sm font-medium bg-gradient-to-r ${strategy.color} bg-clip-text text-transparent opacity-0 group-hover:opacity-100 transition-opacity`}>
                Learn this strategy
                <svg className="w-4 h-4 ml-2 text-[#00B38F]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
            </div>
          ))}
        </div>

        {/* Pro Tip Box */}
        <div className="bg-gradient-to-br from-[#00B38F]/10 to-[#00B39F]/10 rounded-2xl p-8 border-l-4 border-[#00B38F]">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-gradient-to-r from-[#00B38F] to-[#00B39F] rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
            </div>
            <div>
              <h4 className="text-xl font-bold text-gray-900 mb-2">Pro Tip: Find YOUR Strategy</h4>
              <p className="text-gray-700 leading-relaxed">
                At OxiWorld, you don't just learn these strategies—you learn how to <span className="font-semibold">professionally execute</span> them 
                and discover what works best for <span className="font-semibold">YOUR trading style and risk tolerance</span>. No two traders are the same, 
                and we help you find your edge in the market.
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <a 
            href="/pricing"
            className="inline-block bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white px-8 py-4 rounded-lg text-lg font-semibold hover:from-[#00A87D] hover:to-[#00A58D] transition-all duration-300 transform hover:scale-105 shadow-xl"
          >
            Start Learning These Strategies
          </a>
          <p className="text-sm text-gray-500 mt-4">Access all strategies with any premium plan</p>
        </div>
      </div>
    </section>
  );
}
