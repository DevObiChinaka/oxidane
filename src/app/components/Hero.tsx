'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useForexData, useMarketSessions } from '../hooks/useForexData';

export default function Hero() {
  const { rates, isLoading, lastUpdate } = useForexData();
  const sessions = useMarketSessions();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const getSessionStatus = () => {
    if (sessions.london.isOpen && sessions.newYork.isOpen) return { text: 'PEAK TRADING', color: 'bg-green-500' };
    if (sessions.london.isOpen) return { text: 'LONDON OPEN', color: 'bg-blue-500' };
    if (sessions.newYork.isOpen) return { text: 'NEW YORK OPEN', color: 'bg-green-500' };
    if (sessions.tokyo.isOpen) return { text: 'TOKYO OPEN', color: 'bg-purple-500' };
    if (sessions.sydney.isOpen) return { text: 'SYDNEY OPEN', color: 'bg-yellow-500' };
    return { text: 'MARKET CLOSED', color: 'bg-gray-500' };
  };

  const sessionStatus = getSessionStatus();

  return (
    <section className="relative min-h-screen overflow-hidden">
      {/* Professional Background */}
      <div className="absolute inset-0">
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#000ABE] via-[#032DA0] to-[#00B38F]"></div>
        
        {/* Financial Pattern Background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}></div>
        </div>

        {/* Subtle Chart Lines */}
        <div className="absolute inset-0 opacity-5">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path
              d="M0,50 Q25,30 50,40 T100,35"
              stroke="white"
              strokeWidth="0.5"
              fill="none"
              className="animate-pulse"
            />
            <path
              d="M0,60 Q25,40 50,50 T100,45"
              stroke="white"
              strokeWidth="0.3"
              fill="none"
              className="animate-pulse"
              style={{ animationDelay: '1s' }}
            />
          </svg>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="grid lg:grid-cols-2 gap-12 items-center min-h-screen">
          {/* Left Column - Main Content */}
          <div className="space-y-8 text-white">
            {/* Professional Badge */}
            <div className="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-md border border-[#00B39F]/30 rounded-full text-sm font-medium">
              <div className={`w-2 h-2 ${sessionStatus.color} rounded-full mr-2 animate-pulse`}></div>
              OxiWorld • Professional Since 2021
            </div>

            {/* Main Heading */}
            <div className="space-y-6">
              <h1 className="text-5xl lg:text-7xl font-bold leading-relaxed pb-6">
                Master Forex
                <span className="block bg-gradient-to-r from-[#00B39F] to-[#578E7] bg-clip-text text-transparent pb-3">
                  Trading
                </span>
              </h1>
              <p className="text-xl lg:text-2xl text-gray-300 leading-relaxed max-w-2xl">
                Professional-grade education, institutional strategies, and real market insights. 
                Join 5,000+ traders who've transformed their approach to forex markets.
              </p>
            </div>

            {/* Professional Statistics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 py-8">
              <div className="text-center">
                <div className="text-3xl font-bold text-[#00B39F]">$2.5B+</div>
                <div className="text-sm text-gray-400">Volume Traded</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[#00B38F]">78%</div>
                <div className="text-sm text-gray-400">Success Rate</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[#578E7]">5,247</div>
                <div className="text-sm text-gray-400">Students</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-[#42DAD9]">24/7</div>
                <div className="text-sm text-gray-400">Support</div>
              </div>
            </div>

            {/* Professional CTA */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Link 
                href="/courses" 
                className="bg-gradient-to-r from-[#00B38F] to-[#00B39F] text-white px-8 py-4 rounded-lg text-lg font-semibold hover:from-[#00A87D] hover:to-[#00A58D] transition-all duration-300 transform hover:scale-105 shadow-xl"
              >
                Start Professional Course
              </Link>
              <Link 
                href="/market-analysis" 
                className="border-2 border-[#00B39F]/50 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-[#00B39F]/10 backdrop-blur-md transition-all duration-300"
              >
                View Market Analysis
              </Link>
            </div>

            {/* Trust Indicators */}
            <div className="pt-8 space-y-4">
              <div className="flex flex-wrap items-center gap-8 text-sm text-gray-400">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-[#00B38F] rounded-full"></div>
                  <span>CFA Institute Certified</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-[#000ABE] rounded-full"></div>
                  <span>Regulated & Compliant</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-[#00B39F] rounded-full"></div>
                  <span>Institutional Grade</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Live Market Data */}
          <div className="space-y-6">
            {/* Live Market Feed */}
            <div className="bg-white/10 backdrop-blur-md border border-[#00B39F]/20 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white">Live Market Rates</h3>
                <div className="flex items-center space-x-2 text-sm text-gray-300">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span>Live • {mounted ? lastUpdate.toLocaleTimeString() : '--:--:--'}</span>
                </div>
              </div>
              
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-16 bg-white/5 rounded-lg"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {rates.slice(0, 4).map((rate, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors">
                      <div className="flex items-center space-x-4">
                        <div>
                          <div className="text-lg font-semibold text-white">{rate.symbol}</div>
                          <div className="text-xs text-gray-400">Spread: {rate.spread} pips</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-white">{rate.price}</div>
                        <div className={`text-sm font-medium flex items-center ${rate.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                          <span className="mr-1">{rate.isPositive ? '↗' : '↘'}</span>
                          {rate.change >= 0 ? '+' : ''}{rate.change} ({rate.changePercent >= 0 ? '+' : ''}{rate.changePercent}%)
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="mt-4 pt-4 border-t border-white/10">
                <p className="text-xs text-gray-400 text-center">
                  Real-time institutional feeds • Spreads from 0.1 pips • ECN execution
                </p>
              </div>
            </div>

            {/* Market Session Status */}
            <div className="bg-white/10 backdrop-blur-md border border-[#00B39F]/20 rounded-2xl p-6">
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
            <div className="bg-gradient-to-r from-[#000ABE]/20 to-[#00B38F]/20 backdrop-blur-md border border-[#00B39F]/30 rounded-2xl p-6">
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