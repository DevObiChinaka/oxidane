'use client';

import { useState } from 'react';

const educationalContent = [
  {
    category: "Currency Pairs",
    icon: (isActive: boolean) => (
      <svg className={`w-6 h-6 ${isActive ? 'text-white' : 'text-[#00B38F]'}`} fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 7.5V6C15 5.45 14.55 5 14 5H10C9.45 5 9 5.45 9 6V7.5L3 7V9L9 8.5V11.5L3 11V13L9 12.5V15C9 15.55 9.45 16 10 16H14C14.55 16 15 15.55 15 16V12.5L21 13V11L15 11.5V8.5L21 9Z" />
      </svg>
    ),
    content: {
      title: "Understanding Currency Pairs",
      description: "Learn how major, minor, and exotic pairs behave in different market conditions.",
      keyPoints: [
        "Major pairs have highest liquidity (EUR/USD, GBP/USD, USD/JPY)",
        "Minor pairs don't include USD but are still actively traded",
        "Exotic pairs include emerging market currencies",
        "Correlation between pairs affects portfolio risk"
      ],
      tip: "Start with major pairs as they have tighter spreads and more predictable movements."
    }
  },
  {
    category: "Risk Management",
    icon: (isActive: boolean) => (
      <svg className={`w-6 h-6 ${isActive ? 'text-white' : 'text-[#000ABE]'}`} fill="currentColor" viewBox="0 0 24 24">
        <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,7C13.4,7 14.8,8.6 14.8,10.1V11.1C15.4,11.4 16,12 16,12.8V17.7C16,18.4 15.4,19 14.7,19H9.2C8.6,19 8,18.4 8,17.7V12.8C8,12 8.4,11.4 9,11.1V10.1C9,8.6 10.6,7 12,7M12,8.2C11.2,8.2 10.2,8.7 10.2,10.1V11.1H13.8V10.1C13.8,8.7 12.8,8.2 12,8.2Z" />
      </svg>
    ),
    content: {
      title: "The 2% Rule",
      description: "Never risk more than 2% of your account on a single trade - this is fundamental.",
      keyPoints: [
        "Calculate position size before entering",
        "Use stop losses on every trade",
        "Risk-reward ratio should be 1:2 minimum",
        "Diversify across different pairs"
      ],
      tip: "If you have $1000, never risk more than $20 on one trade. This keeps you alive long-term."
    }
  },
  {
    category: "Technical Analysis",
    icon: (isActive: boolean) => (
      <svg className={`w-6 h-6 ${isActive ? 'text-white' : 'text-[#00B39F]'}`} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    content: {
      title: "Support and Resistance",
      description: "Price levels where buying or selling pressure historically increases.",
      keyPoints: [
        "Support acts as a floor for price",
        "Resistance acts as a ceiling",
        "Broken support becomes resistance",
        "Multiple touches make levels stronger"
      ],
      tip: "Look for confluence with moving averages, trendlines, and Fibonacci levels."
    }
  },
  {
    category: "Psychology",
    icon: (isActive: boolean) => (
      <svg className={`w-6 h-6 ${isActive ? 'text-white' : 'text-[#00B38F]'}`} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    content: {
      title: "Controlling Emotions",
      description: "Trading psychology accounts for 80% of trading success - master your mind first.",
      keyPoints: [
        "Fear leads to missed opportunities",
        "Greed causes over-leveraging",
        "Hope prevents cutting losses",
        "Discipline creates consistency"
      ],
      tip: "Keep a trading journal to track your emotional state with each trade."
    }
  }
];

const marketInsights = [
  {
    time: "Asian Session",
    period: "19:00 - 04:00 EST",
    activity: "Moderate",
    pairs: "JPY, AUD pairs active",
    color: "bg-blue-500"
  },
  {
    time: "London Session", 
    period: "03:00 - 12:00 EST",
    activity: "Highest",
    pairs: "EUR, GBP pairs peak",
    color: "bg-green-500"
  },
  {
    time: "New York Session",
    period: "08:00 - 17:00 EST",
    activity: "High",
    pairs: "USD pairs most active",
    color: "bg-purple-500"
  }
];

export default function EducationalValue() {
  const [activeTab, setActiveTab] = useState(0);
  const [accountSize, setAccountSize] = useState(1000);
  const [riskPercentage, setRiskPercentage] = useState(2);

  const calculateRisk = () => {
    if (!accountSize || !riskPercentage) return 0;
    return (accountSize * riskPercentage) / 100;
  };

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center space-y-6 mb-16">
          <div className="inline-flex items-center px-4 py-2 bg-teal-100 text-teal-700 rounded-full text-sm font-medium">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0118 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            Free Education First
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900">
            Learn Before You Earn
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            We believe in education-first approach. Here's a taste of what you'll learn in our comprehensive courses - completely free.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Educational Tabs */}
          <div className="space-y-6">
            <h3 className="text-2xl font-bold text-gray-900">Core Trading Concepts</h3>
            
            {/* Tab Navigation */}
            <div className="flex flex-wrap gap-2">
              {educationalContent.map((item, index) => (
                <button
                  key={index}
                  onClick={() => setActiveTab(index)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                    activeTab === index 
                      ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white shadow-lg' 
                      : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                  }`}
                >
                  {item.icon(activeTab === index)}
                  <span>{item.category}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <div className="space-y-6">
                <div>
                  <h4 className="text-xl font-bold text-gray-900 mb-2">
                    {educationalContent[activeTab].content.title}
                  </h4>
                  <p className="text-gray-600 leading-relaxed">
                    {educationalContent[activeTab].content.description}
                  </p>
                </div>

                <div>
                  <h5 className="font-semibold text-gray-900 mb-3">Key Points:</h5>
                  <ul className="space-y-2">
                    {educationalContent[activeTab].content.keyPoints.map((point, index) => (
                      <li key={index} className="flex items-start space-x-3">
                        <div className="w-5 h-5 bg-gradient-to-r from-teal-500 to-cyan-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <span className="text-gray-700">{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-gradient-to-r from-gray-50 to-slate-100 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <svg className="w-6 h-6 text-teal-500 mt-1" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m4.5 0a12.052 12.052 0 00-4.5 0M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h6 className="font-semibold text-gray-900 mb-1">Pro Tip:</h6>
                      <p className="text-gray-700 text-sm">
                        {educationalContent[activeTab].content.tip}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Market Sessions & Tools */}
          <div className="space-y-6">
            {/* Trading Sessions */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <svg className="w-6 h-6 text-cyan-500 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3s-4.5 4.03-4.5 9 2.015 9 4.5 9z" />
                </svg>
                Global Trading Sessions
              </h3>
              <div className="space-y-4">
                {marketInsights.map((session, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className={`w-4 h-4 ${session.color} rounded-full`}></div>
                      <div>
                        <div className="font-semibold text-gray-900">{session.time}</div>
                        <div className="text-sm text-gray-600">{session.period}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-gray-900">{session.activity} Activity</div>
                      <div className="text-sm text-gray-600">{session.pairs}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Calculator */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <svg className="w-6 h-6 text-[#00B38F] mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 15.75V18a.75.75 0 01-.75.75h-6a.75.75 0 01-.75-.75V9a.75.75 0 01.75-.75h4.5a.75.75 0 00.75-.75V6a.75.75 0 01.75-.75h2.25a.75.75 0 01.75.75v3.75a.75.75 0 01-.75.75H15V9.75a.75.75 0 00-.75-.75H9.75a.75.75 0 00-.75.75v8.25c0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75V15a.75.75 0 01.75-.75z" />
                </svg>
                Risk Calculator
              </h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account Size ($)
                    </label>
                    <input 
                      type="number" 
                      value={accountSize}
                      onChange={(e) => setAccountSize(Number(e.target.value))}
                      placeholder="1000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00B38F] text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Risk (%)
                    </label>
                    <input 
                      type="number" 
                      value={riskPercentage}
                      onChange={(e) => setRiskPercentage(Number(e.target.value))}
                      placeholder="2"
                      min="0"
                      max="100"
                      step="0.1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00B39F] text-gray-900"
                    />
                  </div>
                </div>
                <div className="bg-gradient-to-r from-[#00B38F]/10 to-[#00B39F]/10 rounded-lg p-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      ${calculateRisk().toFixed(2)}
                    </div>
                    <div className="text-sm text-gray-600">Maximum Risk Per Trade</div>
                  </div>
                  {riskPercentage > 5 && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <span className="text-sm text-yellow-800">
                          Warning: Risk above 5% is considered aggressive
                        </span>
                      </div>
                    </div>
                  )}
                  {riskPercentage <= 2 && (
                    <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                        </svg>
                        <span className="text-sm text-green-800">
                          Excellent: Conservative risk management
                        </span>
                      </div>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Professional traders typically risk 1-2% per trade
                </p>
              </div>
            </div>

            {/* Free Resources */}
            <div className="bg-gradient-to-br from-[#000ABE] to-[#00B39F] text-white rounded-2xl p-8 shadow-lg">
              <h3 className="text-xl font-bold mb-4 flex items-center">
                <svg className="w-6 h-6 text-white mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 11.25v8.25a1.5 1.5 0 01-1.5 1.5H5.25a1.5 1.5 0 01-1.5-1.5v-8.25M12 4.875A2.625 2.625 0 109.375 7.5H12m0-2.625V7.5m0-2.625A2.625 2.625 0 1114.625 7.5H12m0 0V21m-8.625-9.75h18c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125h-18c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                </svg>
                Get More Free Resources
              </h3>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>20+ Video Lessons</span>
                </li>
                <li className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Trading Plan Template</span>
                </li>
                <li className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Risk Management Guide</span>
                </li>
                <li className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Market Analysis Tools</span>
                </li>
              </ul>
              <button className="w-full bg-white text-[#000ABE] py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                Access Free Course
              </button>
            </div>
          </div>
        </div>

        {/* Warning Notice */}
        <div className="mt-16 bg-yellow-50 border border-yellow-200 rounded-2xl p-6">
          <div className="flex items-start space-x-3">
            <svg className="w-6 h-6 text-yellow-600 mt-1" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <div>
              <h4 className="font-bold text-yellow-800 mb-2">Risk Warning</h4>
              <p className="text-yellow-700 text-sm leading-relaxed">
                Trading foreign exchange involves substantial risk of loss and is not suitable for all investors. 
                Past performance is not indicative of future results. We strongly recommend starting with a demo account 
                and never trading money you cannot afford to lose. Our educational content is for informational purposes 
                and should not be considered financial advice.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}