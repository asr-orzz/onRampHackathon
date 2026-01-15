// Vercel Serverless Function for /api/register-token
// This endpoint is called by the backend agent to request user authorization

import type { VercelRequest, VercelResponse } from '@vercel/node';

// In production, we use a database (e.g., Redis, Supabase) for shared state
// For now, we'll use a KV store approach - you'll need to configure Vercel KV or similar

// This endpoint creates a pending authorization request
// The frontend will poll /api/pending-auth and complete the flow
export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  try {
    // Generate unique token
    const token = crypto.randomUUID();
    
    // Store pending auth in KV store (Vercel KV, Redis, etc.)
    // For demonstration, we'll use Vercel KV
    // You need to set up VERCEL_KV_URL and VERCEL_KV_TOKEN environment variables
    
    const kvUrl = process.env.KV_REST_API_URL;
    const kvToken = process.env.KV_REST_API_TOKEN;
    
    if (!kvUrl || !kvToken) {
      // Fallback: Return immediately with polling approach
      // The frontend will poll and the user will complete auth manually
      const pendingAuth = {
        token,
        status: 'pending',
        createdAt: Date.now(),
      };
      
      // Store in KV
      const storeResponse = await fetch(`${kvUrl}/set/pending_auth_${token}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${kvToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(pendingAuth),
      });
      
      if (!storeResponse.ok) {
        console.error('Failed to store pending auth in KV');
      }
      
      // Set expiry (5 minutes)
      await fetch(`${kvUrl}/expire/pending_auth_${token}/300`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${kvToken}`,
        },
      });
    }

    // For a synchronous flow (backend waits for user), we need long polling
    // Wait for up to 5 minutes for user to authorize
    const maxWaitTime = 5 * 60 * 1000; // 5 minutes
    const pollInterval = 1000; // 1 second
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
      // Check if auth was completed
      if (kvUrl && kvToken) {
        const getResponse = await fetch(`${kvUrl}/get/session_${token}`, {
          headers: {
            Authorization: `Bearer ${kvToken}`,
          },
        });
        
        if (getResponse.ok) {
          const result = await getResponse.json();
          if (result.result) {
            // Session was created, return success
            return res.status(200).json({
              success: true,
              token,
            });
          }
        }
        
        // Check if auth was cancelled
        const cancelResponse = await fetch(`${kvUrl}/get/cancelled_${token}`, {
          headers: {
            Authorization: `Bearer ${kvToken}`,
          },
        });
        
        if (cancelResponse.ok) {
          const cancelResult = await cancelResponse.json();
          if (cancelResult.result) {
            return res.status(403).json({
              success: false,
              error: cancelResult.result.error || 'User cancelled authorization',
            });
          }
        }
      }
      
      // Wait before polling again
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    // Timeout
    return res.status(408).json({
      success: false,
      error: 'Authorization timeout - user did not respond in time',
    });

  } catch (error: any) {
    console.error('Error in register-token:', error);
    return res.status(500).json({
      success: false,
      error: error?.message || 'Internal server error',
    });
  }
}
