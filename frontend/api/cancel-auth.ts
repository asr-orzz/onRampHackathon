// Vercel Serverless Function for /api/cancel-auth
// Frontend calls this when user cancels authorization

import type { VercelRequest, VercelResponse } from '@vercel/node';

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
        const { token, error: cancelError } = req.body;

        if (!token) {
            return res.status(400).json({
                success: false,
                error: 'Missing required field: token',
            });
        }

        const kvUrl = process.env.KV_REST_API_URL;
        const kvToken = process.env.KV_REST_API_TOKEN;

        if (!kvUrl || !kvToken) {
            return res.status(500).json({
                success: false,
                error: 'KV store not configured',
            });
        }

        // Check if pending auth exists
        const checkResponse = await fetch(`${kvUrl}/get/pending_auth_${token}`, {
            headers: {
                Authorization: `Bearer ${kvToken}`,
            },
        });

        if (!checkResponse.ok) {
            return res.status(404).json({
                success: false,
                error: 'Authorization request not found',
            });
        }

        const checkResult = await checkResponse.json();
        if (!checkResult.result) {
            return res.status(404).json({
                success: false,
                error: 'Authorization request not found',
            });
        }

        // Store cancellation
        const cancelData = {
            error: cancelError || 'User cancelled authorization',
        };

        await fetch(`${kvUrl}/set/cancelled_${token}`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${kvToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cancelData),
        });

        // Set expiry (5 minutes)
        await fetch(`${kvUrl}/expire/cancelled_${token}/300`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${kvToken}`,
            },
        });

        // Delete pending auth
        await fetch(`${kvUrl}/del/pending_auth_${token}`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${kvToken}`,
            },
        });

        return res.status(200).json({ success: true });

    } catch (error: any) {
        console.error('Error in cancel-auth:', error);
        return res.status(500).json({
            success: false,
            error: error?.message || 'Internal server error',
        });
    }
}
