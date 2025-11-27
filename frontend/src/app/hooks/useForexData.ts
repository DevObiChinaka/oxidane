import { useState, useEffect } from 'react';

export interface ForexRate {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  isPositive: boolean;
  bid: number;
  ask: number;
  spread: number;
  timestamp: number;
}

// Free forex data from exchangerate-api.com or fixer.io alternative
// For demo purposes, we'll use a more realistic simulation
const MAJOR_PAIRS = [
  { symbol: 'EUR/USD', name: 'Euro vs US Dollar', baseRate: 1.0856 },
  { symbol: 'GBP/USD', name: 'British Pound vs US Dollar', baseRate: 1.2743 },
  { symbol: 'USD/JPY', name: 'US Dollar vs Japanese Yen', baseRate: 149.42 },
  { symbol: 'USD/CHF', name: 'US Dollar vs Swiss Franc', baseRate: 0.8756 },
  { symbol: 'AUD/USD', name: 'Australian Dollar vs US Dollar', baseRate: 0.6523 },
  { symbol: 'USD/CAD', name: 'US Dollar vs Canadian Dollar', baseRate: 1.3687 },
];

export function useForexData() {
  const [rates, setRates] = useState<ForexRate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date('2024-01-01')); // Fixed initial date
  const [mounted, setMounted] = useState(false);

  const generateRealisticPrice = (baseRate: number, volatility: number = 0.002) => {
    // Generate price movement based on normal distribution
    const random1 = Math.random();
    const random2 = Math.random();
    
    // Box-Muller transformation for normal distribution
    const normal = Math.sqrt(-2 * Math.log(random1)) * Math.cos(2 * Math.PI * random2);
    
    // Apply volatility and trending
    const change = normal * volatility * baseRate;
    return baseRate + change;
  };

  const calculateSpread = (symbol: string, price: number) => {
    // Realistic spreads for major pairs (in pips)
    const spreads: { [key: string]: number } = {
      'EUR/USD': 0.1,
      'GBP/USD': 0.2,
      'USD/JPY': 0.1,
      'USD/CHF': 0.2,
      'AUD/USD': 0.3,
      'USD/CAD': 0.3,
    };
    
    const spreadPips = spreads[symbol] || 0.2;
    const pipValue = symbol.includes('JPY') ? 0.01 : 0.0001;
    const spreadValue = spreadPips * pipValue;
    
    return {
      bid: price - spreadValue / 2,
      ask: price + spreadValue / 2,
      spread: spreadValue
    };
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    let interval: NodeJS.Timeout;

    const updateRates = () => {
      setRates(prevRates => {
        const newRates = MAJOR_PAIRS.map((pair, index) => {
          const previousRate = prevRates[index];
          const newPrice = generateRealisticPrice(pair.baseRate);
          const previousPrice = previousRate?.price || pair.baseRate;
          
          const change = newPrice - previousPrice;
          const changePercent = (change / previousPrice) * 100;
          const { bid, ask, spread } = calculateSpread(pair.symbol, newPrice);
          
          return {
            symbol: pair.symbol,
            name: pair.name,
            price: parseFloat(newPrice.toFixed(pair.symbol.includes('JPY') ? 2 : 4)),
            change: parseFloat(change.toFixed(pair.symbol.includes('JPY') ? 2 : 4)),
            changePercent: parseFloat(changePercent.toFixed(2)),
            isPositive: change >= 0,
            bid: parseFloat(bid.toFixed(pair.symbol.includes('JPY') ? 2 : 4)),
            ask: parseFloat(ask.toFixed(pair.symbol.includes('JPY') ? 2 : 4)),
            spread: parseFloat((spread * 10000).toFixed(1)), // in pips
            timestamp: Date.now()
          };
        });
        
        return newRates;
      });
      
      setLastUpdate(new Date());
    };

    // Initial load
    updateRates();
    setIsLoading(false);

    // Update every 3 seconds (realistic for retail forex)
    const interval = setInterval(updateRates, 3000);

    return () => {
      clearInterval(interval);
    };
  }, [mounted]);

  return {
    rates,
    isLoading,
    lastUpdate
  };
}

// Alternative: Real API integration (when you get API key)
export async function fetchRealForexData(apiKey?: string) {
  if (!apiKey) {
    throw new Error('API key required for real forex data');
  }

  try {
    // Example with Fixer.io or similar service
    const response = await fetch(
      `https://api.fixer.io/latest?access_key=${apiKey}&symbols=USD,EUR,GBP,JPY,CHF,AUD,CAD`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch forex data');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching real forex data:', error);
    throw error;
  }
}

// Market session checker
export function useMarketSessions() {
  const [sessions, setSessions] = useState({
    london: { isOpen: false, openTime: '', closeTime: '' },
    newYork: { isOpen: false, openTime: '', closeTime: '' },
    tokyo: { isOpen: false, openTime: '', closeTime: '' },
    sydney: { isOpen: false, openTime: '', closeTime: '' },
  });

  useEffect(() => {
    const checkSessions = () => {
      const now = new Date();
      const utcHours = now.getUTCHours();
      const utcMinutes = now.getUTCMinutes();
      const totalMinutes = utcHours * 60 + utcMinutes;

      // Convert to minutes for easier comparison
      const londonOpen = 8 * 60; // 08:00 UTC
      const londonClose = 17 * 60; // 17:00 UTC
      const newYorkOpen = 13 * 60; // 13:00 UTC
      const newYorkClose = 22 * 60; // 22:00 UTC
      const tokyoOpen = 23 * 60; // 23:00 UTC (previous day)
      const tokyoClose = 8 * 60; // 08:00 UTC
      const sydneyOpen = 21 * 60; // 21:00 UTC (previous day)
      const sydneyClose = 6 * 60; // 06:00 UTC

      setSessions({
        london: {
          isOpen: totalMinutes >= londonOpen && totalMinutes < londonClose,
          openTime: '08:00 UTC',
          closeTime: '17:00 UTC'
        },
        newYork: {
          isOpen: totalMinutes >= newYorkOpen && totalMinutes < newYorkClose,
          openTime: '13:00 UTC',
          closeTime: '22:00 UTC'
        },
        tokyo: {
          isOpen: totalMinutes >= tokyoOpen || totalMinutes < tokyoClose,
          openTime: '23:00 UTC',
          closeTime: '08:00 UTC'
        },
        sydney: {
          isOpen: totalMinutes >= sydneyOpen || totalMinutes < sydneyClose,
          openTime: '21:00 UTC',
          closeTime: '06:00 UTC'
        }
      });
    };

    checkSessions();
    const interval = setInterval(checkSessions, 60000); // Check every minute

    return () => clearInterval(interval);
  }, []);

  return sessions;
}