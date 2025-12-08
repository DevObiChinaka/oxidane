'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useMarketSessions } from '../hooks/useForexData';

export default function Hero() {
  const sessions = useMarketSessions();
  const [mounted, setMounted] = useState(false);
  const [selectedPair, setSelectedPair] = useState('EURUSD');

  useEffect(() => {
    setMounted(true);
  }, []);

  const getSessionStatus = () => {
    if (sessions.london.isOpen && sessions.newYork.isOpen) return { text: 'PEAK TRADING', color: 'bg-green-500' };
    if (sessions.london.isOpen) return { text: 'LONDON OPEN', color: 'bg-[#000ABE]' };
    if (sessions.newYork.isOpen) return { text: 'NEW YORK OPEN', color: 'bg-green-500' };
    if (sessions.tokyo.isOpen) return { text: 'TOKYO OPEN', color: 'bg-[#00B39F]' };
    if (sessions.sydney.isOpen) return { text: 'SYDNEY OPEN', color: 'bg-[#00B38F]' };
    return { text: 'MARKET CLOSED', color: 'bg-gray-500' };
  };

  const sessionStatus = getSessionStatus();

  return (
    <section id="hero" className="relative min-h-screen overflow-hidden">
      {/* Professional Background */}
      <div className="absolute inset-0">
        {/* Enhanced Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#000856] via-[#002A5C] to-[#004A42]"></div>
        
        {/* Financial Pattern Background */}
        <div className="absolute inset-0 opacity-8">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}></div>
        </div>

        {/* Subtle Chart Lines */}
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path
              d="M0,50 Q25,30 50,40 T100,35"
              stroke="#00B38F"
              strokeWidth="0.8"
              fill="none"
              className="animate-pulse"
            />
            <path
              d="M0,60 Q25,40 50,50 T100,45"
              stroke="#00B39F"
              strokeWidth="0.6"
              fill="none"
              className="animate-pulse"
              style={{ animationDelay: '1s' }}
            />
          </svg>
        </div>

        {/* Subtle Glow Effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 md:w-96 md:h-96 bg-[#00B38F]/5 rounded-full blur-3xl"></div>
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 md:w-96 md:h-96 bg-[#000ABE]/5 rounded-full blur-3xl"></div>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 md:pt-20 pb-8 md:pb-16 w-full">
        <div className="grid lg:grid-cols-2 gap-8 md:gap-12 items-center min-h-screen w-full">
          {/* Left Column - Main Content */}
          <div className="space-y-6 md:space-y-8 text-white">
            {/* Professional Badge */}
            <div className="inline-flex items-center px-4 sm:px-5 py-2 sm:py-2.5 bg-white/15 backdrop-blur-xl border border-white/20 rounded-full text-sm sm:text-base font-medium shadow-xl">
              <div className={`w-2 h-2 ${sessionStatus.color} rounded-full mr-2 animate-pulse`}></div>
              OxiWorld • Professional Since 2021
            </div>

            {/* Main Heading */}
            <div className="space-y-4 md:space-y-6">
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold leading-tight pb-4 md:pb-6">
                Master Forex Trading
                <span className="block bg-gradient-to-r from-[#00B38F] to-[#00B39F] bg-clip-text text-transparent pb-2 md:pb-3 mt-2">
                  with OxiWorld Forex Academy
                </span>
              </h1>
              <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-300 leading-relaxed">
                Learn proven trading strategies from a professional forex trader. Join thousands of students mastering SMC, ALGO, and advanced techniques to become consistently profitable traders.
              </p>
            </div>

            {/* Professional Statistics */}
            <div className="grid grid-cols-2 gap-4 sm:gap-6 py-6 md:py-8">
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-3 sm:p-4 border border-white/10 text-center hover:bg-white/10 transition-all">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-[#00B39F]">$2.5B+</div>
                <div className="text-xs sm:text-sm text-gray-300 mt-1">Volume Traded</div>
              </div>
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-3 sm:p-4 border border-white/10 text-center hover:bg-white/10 transition-all">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-[#00B38F]">78%</div>
                <div className="text-xs sm:text-sm text-gray-300 mt-1">Success Rate</div>
              </div>
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-3 sm:p-4 border border-white/10 text-center hover:bg-white/10 transition-all">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-white">500+</div>
                <div className="text-xs sm:text-sm text-gray-300 mt-1">Students</div>
              </div>
              <div className="bg-white/5 backdrop-blur-sm rounded-xl p-3 sm:p-4 border border-white/10 text-center hover:bg-white/10 transition-all">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-[#00B38F]">24/7</div>
                <div className="text-xs sm:text-sm text-gray-300 mt-1">Support</div>
              </div>
            </div>

            {/* Professional CTA */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Link 
                href="/auth?mode=signup" 
                className="bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white px-8 py-4 sm:py-5 rounded-xl text-base sm:text-lg md:text-xl font-bold hover:from-[#00A87D] hover:to-[#00A58D] transition-all duration-300 transform hover:scale-105 shadow-2xl shadow-[#00B38F]/50 text-center"
              >
                Start Trading Today
              </Link>
            </div>

            {/* Trust Indicators */}
            <div className="pt-6 md:pt-8 space-y-4">
              <div className="flex flex-wrap items-center gap-4 sm:gap-6 md:gap-8 text-xs sm:text-sm text-gray-400">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-[#00B38F] rounded-full"></div>
                  <span>1M+ Social Media Views</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-[#000ABE] rounded-full"></div>
                  <span>Exness & Maven Partner</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 sm:w-4 sm:h-4 bg-[#00B39F] rounded-full"></div>
                  <span>Real Trading Results</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Live Market Data */}
          <div className="space-y-6 w-full max-w-full overflow-hidden">
            {/* TradingView Widget with Vertical Pair Selection */}
            <div className="bg-white/8 backdrop-blur-2xl border border-white/15 rounded-2xl p-4 sm:p-5 md:p-6 shadow-2xl">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 sm:mb-6 gap-3 sm:gap-0">
                <div>
                  <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-1">Live Market Rates</h3>
                  <p className="text-xs sm:text-sm text-gray-400 hidden lg:block">Real-time institutional pricing across major pairs</p>
                </div>
                <div className="flex items-center space-x-2 text-xs sm:text-sm text-gray-200 bg-white/10 px-4 py-2 rounded-full backdrop-blur-md border border-white/20 shadow-lg">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50"></div>
                  <span className="font-semibold">Live • TradingView</span>
                </div>
              </div>
              
              <div className="flex flex-col lg:grid lg:grid-cols-4 gap-4 lg:gap-5">
                {/* Pair List */}
                <div className="lg:col-span-1 grid grid-cols-3 lg:grid-cols-1 gap-2 lg:gap-2.5">
                  {[
                    { symbol: 'EURUSD', name: 'EUR/USD', category: 'Major', flag: '🇪🇺/🇺🇸' },
                    { symbol: 'GBPUSD', name: 'GBP/USD', category: 'Major', flag: '🇬🇧/🇺🇸' },
                    { symbol: 'USDJPY', name: 'USD/JPY', category: 'Major', flag: '🇺🇸/🇯🇵' },
                    { symbol: 'USDCAD', name: 'USD/CAD', category: 'Major', flag: '🇺🇸/🇨🇦' },
                    { symbol: 'AUDUSD', name: 'AUD/USD', category: 'Major', flag: '🇦🇺/🇺🇸' },
                    { symbol: 'NZDUSD', name: 'NZD/USD', category: 'Major', flag: '🇳🇿/🇺🇸' }
                  ].map((pair) => (
                    <button
                      key={pair.symbol}
                      onClick={() => setSelectedPair(pair.symbol)}
                      className={`group relative w-full text-center lg:text-left px-3 py-2.5 lg:py-3 rounded-xl transition-all duration-300 ${
                        selectedPair === pair.symbol
                          ? 'bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white shadow-xl shadow-[#00B38F]/30 ring-2 ring-white/30 scale-105 lg:scale-100'
                          : 'bg-white/5 text-gray-300 hover:bg-white/10 border border-white/10 hover:border-white/20 hover:scale-105'
                      }`}
                    >
                      <div className="flex items-center justify-center lg:justify-start gap-2">
                        <span className="text-sm lg:text-base hidden lg:inline">{pair.flag}</span>
                        <div>
                          <div className="font-bold text-xs sm:text-sm lg:text-sm">{pair.name}</div>
                          {selectedPair === pair.symbol && (
                            <div className="text-[10px] opacity-90 mt-0.5 hidden lg:block font-normal">Live Chart</div>
                          )}
                          {selectedPair !== pair.symbol && (
                            <div className="text-[9px] opacity-70 mt-0.5 hidden lg:block">{pair.category}</div>
                          )}
                        </div>
                      </div>
                      {selectedPair === pair.symbol && (
                        <div className="absolute inset-0 bg-gradient-to-r from-[#00B38F]/20 to-[#00B39F]/20 rounded-xl blur-xl -z-10"></div>
                      )}
                    </button>
                  ))}
                </div>

                {/* Selected Pair Widget */}
                <div className="lg:col-span-3">
                  <div className="relative bg-gradient-to-br from-white/10 to-white/5 rounded-2xl overflow-hidden border-2 border-white/20 shadow-2xl">
                    {/* Chart Header */}
                    <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/40 to-transparent p-3 lg:p-4 z-10">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-white font-bold text-sm lg:text-base">
                            {[{ symbol: 'EURUSD', name: 'EUR/USD' }, { symbol: 'GBPUSD', name: 'GBP/USD' }, { symbol: 'USDJPY', name: 'USD/JPY' }, { symbol: 'USDCAD', name: 'USD/CAD' }, { symbol: 'AUDUSD', name: 'AUD/USD' }, { symbol: 'NZDUSD', name: 'NZD/USD' }].find(p => p.symbol === selectedPair)?.name}
                          </span>
                        </div>
                        <span className="text-xs text-gray-300 bg-black/30 px-3 py-1 rounded-full backdrop-blur-sm">1D Chart</span>
                      </div>
                    </div>
                    
                    <iframe 
                      key={selectedPair}
                      src={`https://www.tradingview-widget.com/embed-widget/mini-symbol-overview/?locale=en#%7B%22symbol%22%3A%22FX:${selectedPair}%22%2C%22width%22%3A%22100%25%22%2C%22height%22%3A%22320%22%2C%22dateRange%22%3A%221D%22%2C%22colorTheme%22%3A%22dark%22%2C%22trendLineColor%22%3A%22rgba(0%2C%20179%2C%20143%2C%201)%22%2C%22underLineColor%22%3A%22rgba(0%2C%20179%2C%20159%2C%200.3)%22%2C%22isTransparent%22%3Atrue%2C%22autosize%22%3Afalse%2C%22largeChartUrl%22%3A%22%22%2C%22utm_source%22%3A%22oxidane.com%22%2C%22utm_medium%22%3A%22widget%22%2C%22utm_campaign%22%3A%22mini-symbol-overview%22%7D`}
                      className="w-full h-[250px] sm:h-[280px] lg:h-[320px] border-0"
                      style={{ background: 'transparent' }}
                      title={`${selectedPair} Chart`}
                    ></iframe>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 lg:mt-6 pt-4 lg:pt-5 border-t border-white/10">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                  <p className="text-xs text-gray-300 bg-white/5 px-4 py-2 rounded-lg backdrop-blur-sm border border-white/10">
                    <span className="font-semibold text-white">TradingView</span> • Real-time institutional pricing
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Updated every second</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Market Session Status */}
            <div className="bg-white/8 backdrop-blur-2xl border border-white/15 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-bold text-white">Market Status</h4>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 ${sessionStatus.color} rounded-full animate-pulse`}></div>
                  <span className="text-white font-medium text-sm">{sessionStatus.text}</span>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">London</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 ${sessions.london.isOpen ? 'bg-green-400 animate-pulse' : 'bg-gray-400'} rounded-full`}></div>
                    <span className={`font-medium text-sm ${sessions.london.isOpen ? 'text-green-400' : 'text-gray-400'}`}>
                      {sessions.london.isOpen ? 'OPEN' : 'CLOSED'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">New York</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 ${sessions.newYork.isOpen ? 'bg-green-400 animate-pulse' : 'bg-gray-400'} rounded-full`}></div>
                    <span className={`font-medium text-sm ${sessions.newYork.isOpen ? 'text-green-400' : 'text-gray-400'}`}>
                      {sessions.newYork.isOpen ? 'OPEN' : 'CLOSED'}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Tokyo</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 ${sessions.tokyo.isOpen ? 'bg-green-400 animate-pulse' : 'bg-gray-400'} rounded-full`}></div>
                    <span className={`font-medium text-sm ${sessions.tokyo.isOpen ? 'text-green-400' : 'text-gray-400'}`}>
                      {sessions.tokyo.isOpen ? 'OPEN' : 'CLOSED'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Trading Opportunity Alert */}
            <div className="bg-gradient-to-r from-[#00B38F]/10 to-[#00B39F]/10 backdrop-blur-2xl border border-white/15 rounded-2xl p-6 shadow-2xl">
              <h4 className="text-lg font-bold text-white mb-3 flex items-center">
                <span className="text-yellow-400 mr-2">⚡</span>
                Trading Opportunity
              </h4>
              <div className="space-y-2">
                <div className="text-white font-medium">EUR/USD Breakout Setup</div>
                <div className="text-sm text-gray-300">
                  Price testing key resistance at 1.0890. Strong momentum building.
                </div>
                <div className="flex items-center space-x-4 text-xs text-gray-400">
                  <span>Risk: 1.5%</span>
                  <span>R:R 1:3</span>
                  <span>Confidence: High</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}