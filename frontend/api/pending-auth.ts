// Vercel Serverless Function for /api/pending-auth
// Frontend polls this to check for pending authorization requests

import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'GET') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    try {
        const kvUrl = process.env.KV_REST_API_URL;
        const kvToken = process.env.KV_REST_API_TOKEN;

        if (!kvUrl || !kvToken) {
            return res.status(500).json({
                success: false,
                error: 'KV store not configured',
            });
        }

        // Scan for pending auth keys
        const scanResponse = await fetch(`${kvUrl}/keys/pending_auth_*`, {
            headers: {
                Authorization: `Bearer ${kvToken}`,
            },
        });

        if (!scanResponse.ok) {
            return res.status(200).json({ token: null });
        }

        const scanResult = await scanResponse.json();
        const keys = scanResult.result || [];

        if (keys.length === 0) {
            return res.status(200).json({ token: null });
        }

        // Get first pending auth
        const firstKey = keys[0];
        const token = firstKey.replace('pending_auth_', '');

        return res.status(200).json({ token });

    } catch (error: any) {
        console.error('Error in pending-auth:', error);
        return res.status(500).json({
            success: false,
            error: error?.message || 'Internal server error',
        });
    }
}
