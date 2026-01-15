// Vercel Serverless Function for /api/agent/pay (routes to /agent/pay)
// Backend agent calls this to execute payment with session token

import type { VercelRequest, VercelResponse } from '@vercel/node';
import { ethers } from 'ethers';

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
        const { receiver, amount, sessionToken } = req.body;

        if (!receiver || amount === undefined || !sessionToken) {
            return res.status(400).json({
                success: false,
                error: 'Missing required fields: receiver, amount, sessionToken',
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

        // Get session
        const sessionResponse = await fetch(`${kvUrl}/get/session_${sessionToken}`, {
            headers: {
                Authorization: `Bearer ${kvToken}`,
            },
        });

        if (!sessionResponse.ok) {
            return res.status(403).json({
                success: false,
                error: 'Invalid or expired session token',
            });
        }

        const sessionResult = await sessionResponse.json();
        const session = sessionResult.result;

        if (!session) {
            return res.status(403).json({
                success: false,
                error: 'Invalid or expired session token',
            });
        }

        // Check expiry
        if (Date.now() >= session.expiresAt) {
            // Clean up expired session
            await fetch(`${kvUrl}/del/session_${sessionToken}`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${kvToken}`,
                },
            });

            return res.status(403).json({
                success: false,
                error: 'Session token has expired',
            });
        }

        // Validate receiver address
        if (!ethers.utils.isAddress(receiver)) {
            return res.status(400).json({
                success: false,
                error: 'Invalid receiver address',
            });
        }

        // Validate amount
        if (amount <= 0) {
            return res.status(400).json({
                success: false,
                error: 'Amount must be greater than 0',
            });
        }

        // Execute payment
        const sepoliaRpcUrl = 'https://sepolia.infura.io/v3/a1cf6b93c95b4e079a21fa4fca874411';

        const provider = new ethers.providers.JsonRpcProvider(sepoliaRpcUrl);
        const wallet = new ethers.Wallet(session.privateKey, provider);

        // Get gas price
        const gasPrice = await provider.getGasPrice();

        // Create and send transaction
        const tx = {
            to: receiver,
            value: ethers.utils.parseEther(amount.toString()),
            gasLimit: 21000,
            gasPrice: gasPrice,
        };

        console.log('Executing payment:', { to: receiver, amount });

        const txResponse = await wallet.sendTransaction(tx);
        const txHash = txResponse.hash;

        console.log('Transaction hash:', txHash);

        return res.status(200).json({
            success: true,
            tx_hash: txHash,
        });

    } catch (error: any) {
        console.error('Payment error:', error);
        return res.status(500).json({
            success: false,
            error: error?.message || 'Payment failed',
        });
    }
}
