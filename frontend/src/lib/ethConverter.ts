/**
 * Utility functions for converting ETH to INR and vice versa
 */

// Use relative URL if VITE_BACKEND_URL is not set (will use vite proxy)
// If VITE_BACKEND_URL is set, use it; otherwise use relative URL for proxy
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';

interface EthToInrRate {
  rate: number | null;
  currency: string;
  status: string;
  message?: string;
}

let cachedRate: number | null = null;
let cacheTimestamp: number = 0;
const CACHE_DURATION = 60000; // Cache for 1 minute

/**
 * Fetch ETH to INR conversion rate from backend
 */
export async function getEthToInrRate(): Promise<number | null> {
  // Return cached rate if still valid
  const now = Date.now();
  if (cachedRate && (now - cacheTimestamp) < CACHE_DURATION) {
    return cachedRate;
  }

  try {
    // Always use relative URL to leverage Vite proxy (avoids CORS issues)
    // The proxy will forward to the correct backend URL
    // Use CoinGecko public price API
    const COIN_GECKO_API_KEY = import.meta.env.VITE_COINGECKO_API_KEY;
    const coin_id = "ethereum";
    const to_currency = "inr";
    const url = `https://api.coingecko.com/api/v3/simple/price?ids=${coin_id}&vs_currencies=${to_currency}&x_cg_demo_api_key=${COIN_GECKO_API_KEY}`;
    console.log(`Fetching ETH rate from CoinGecko: ${url}`);
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch ETH rate from CoinGecko');
    }
    // The response shape: { ethereum: { inr: <rate> } }
    const dataRaw = await response.json();
    const data: EthToInrRate = {
      rate: (dataRaw && dataRaw.ethereum && typeof dataRaw.ethereum.inr === 'number') ? dataRaw.ethereum.inr : null,
      currency: "INR",
      status: (dataRaw && dataRaw.ethereum && typeof dataRaw.ethereum.inr === 'number') ? 'success' : 'error',
      message: (dataRaw && dataRaw.ethereum && typeof dataRaw.ethereum.inr === 'number') ? undefined : 'Invalid CoinGecko response'
    };
    
    if (data.status === 'success' && data.rate) {
      cachedRate = data.rate;
      cacheTimestamp = now;
      return data.rate;
    }
    
    return null;
  } catch (error) {
    console.error('Error fetching ETH to INR rate:', error);
    // Return cached rate even if expired, as fallback
    return cachedRate;
  }
}

/**
 * Convert ETH amount to INR
 */
export async function ethToInr(ethAmount: number | string): Promise<number | null> {
  const eth = typeof ethAmount === 'string' ? parseFloat(ethAmount) : ethAmount;
  if (isNaN(eth) || eth < 0) {
    return null;
  }

  const rate = await getEthToInrRate();
  if (!rate) {
    return null;
  }

  return eth * rate;
}

/**
 * Format INR amount for display
 */
export function formatInr(amount: number | null): string {
  if (amount === null || isNaN(amount)) {
    return '₹0.00';
  }
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format INR amount for display with compact notation for large amounts
 */
export function formatInrCompact(amount: number | null): string {
  if (amount === null || isNaN(amount)) {
    return '₹0.00';
  }
  
  if (amount >= 10000000) {
    // For amounts >= 1 crore, show in crores
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  } else if (amount >= 100000) {
    // For amounts >= 1 lakh, show in lakhs
    return `₹${(amount / 100000).toFixed(2)} L`;
  } else if (amount >= 1000) {
    // For amounts >= 1000, show in thousands
    return `₹${(amount / 1000).toFixed(2)} K`;
  }
  
  return formatInr(amount);
}
