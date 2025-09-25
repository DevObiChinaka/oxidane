'use client';

import { useState } from 'react';

const educationalContent = [
  {
    category: "Market Analysis",
    icon: (
      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    content: {
      title: "Understanding Currency Pairs",
      description: "Learn how major, minor, and exotic pairs behave in different market conditions.",
      keyPoints: [
        "Major pairs represent 80% of forex volume",
        "EUR/USD is the most traded pair globally",
        "Cross pairs don't include USD",
        "Exotic pairs have higher spreads"
      ],
      tip: "Start with major pairs as they have tighter spreads and more predictable movements."
    }
  },
  {
    category: "Risk Management",
    icon: (
      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
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
    icon: (
      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
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
    icon: (
      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
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
    time: "New York Session",
    period: "08:00 - 17:00 EST",
    activity: "High",
    pairs: "USD pairs most active",
    color: "bg-green-500"
  },
  {
    time: "London Session", 
    period: "03:00 - 12:00 EST",
    activity: "Highest",
    pairs: "EUR, GBP pairs peak",
    color: "bg-blue-500"
  },
  {
    time: "Asian Session",
    period: "19:00 - 04:00 EST", 
    activity: "Moderate",
    pairs: "JPY, AUD pairs active",
    color: "bg-purple-500"
  }
];

export default function EducationalValue() {
  const [activeTab, setActiveTab] = useState(0);
  const [accountSize, setAccountSize] = useState<number>(1000);
  const [riskPercentage, setRiskPercentage] = useState<number>(2);

  // Calculate risk amount
  const calculateRisk = () => {
    if (!accountSize || !riskPercentage) return 0;
    return (accountSize * riskPercentage) / 100;
  };

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center space-y-6 mb-16">
          <div className="inline-flex items-center px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
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
                      ? 'gradient-purple text-white shadow-lg' 
                      : 'bg-white text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.category}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-purple-100">
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
                        <div className="w-5 h-5 gradient-purple rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <span className="text-gray-700">{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <svg className="w-6 h-6 text-purple-600 mt-1" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
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
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-purple-100">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <svg className="w-6 h-6 text-purple-600 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
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
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-purple-100">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <svg className="w-6 h-6 text-purple-600 mr-2" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900"
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-gray-900"
                    />
                  </div>
                </div>
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4">
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
            <div className="bg-gradient-to-br from-purple-600 to-blue-600 text-white rounded-2xl p-8 shadow-lg">
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
              <button className="w-full bg-white text-purple-600 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
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