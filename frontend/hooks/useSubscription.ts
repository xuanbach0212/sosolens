'use client';

import { useState, useEffect, useCallback } from 'react';
import { createWalletClient, createPublicClient, custom, http, parseAbi } from 'viem';
import { baseSepolia } from 'viem/chains';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const CONTRACT_ADDRESS = (process.env.NEXT_PUBLIC_SUBSCRIPTION_CONTRACT_ADDRESS ?? '') as `0x${string}`;
const USDC_ADDRESS = (
  process.env.NEXT_PUBLIC_USDC_ADDRESS ?? '0x036CbD53842c5426634e7929541eC2318f3dCF7e'
) as `0x${string}`;
const PRICE = 5_000_000n; // 5 USDC (6 decimals)

const USDC_ABI = parseAbi([
  'function approve(address spender, uint256 amount) returns (bool)',
  'function allowance(address owner, address spender) view returns (uint256)',
]);

const SUBSCRIPTION_ABI = parseAbi(['function subscribe()']);

export type SubscribeStep = 'idle' | 'approving' | 'subscribing' | 'done' | 'error';

export interface SubscriptionState {
  isSubscribed: boolean;
  expiry: Date | null;
  isChecking: boolean;
  step: SubscribeStep;
  error: string | null;
  subscribe: () => Promise<void>;
  reset: () => void;
}

export function useSubscription(wallet: string | null): SubscriptionState {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [expiry, setExpiry] = useState<Date | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [step, setStep] = useState<SubscribeStep>('idle');
  const [error, setError] = useState<string | null>(null);

  const checkStatus = useCallback(async (addr: string) => {
    setIsChecking(true);
    try {
      const res = await fetch(`${API_BASE}/api/subscription/status?wallet=${addr}`);
      if (!res.ok) return;
      const data = await res.json();
      setIsSubscribed(data.subscribed ?? false);
      setExpiry(data.expiry ? new Date(data.expiry * 1000) : null);
    } catch {
      // network error — keep current state
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    if (!wallet) {
      setIsSubscribed(false);
      setExpiry(null);
      return;
    }
    checkStatus(wallet);
  }, [wallet, checkStatus]);

  const subscribe = useCallback(async () => {
    if (!wallet || !CONTRACT_ADDRESS || !window.ethereum) return;
    setError(null);

    try {
      const publicClient = createPublicClient({ chain: baseSepolia, transport: http() });
      const walletClient = createWalletClient({
        chain: baseSepolia,
        transport: custom(window.ethereum),
      });
      const account = wallet as `0x${string}`;

      // Check existing allowance — skip approve if already sufficient
      const allowance = await publicClient.readContract({
        address: USDC_ADDRESS,
        abi: USDC_ABI,
        functionName: 'allowance',
        args: [account, CONTRACT_ADDRESS],
      });

      if (allowance < PRICE) {
        setStep('approving');
        const approveTx = await walletClient.writeContract({
          address: USDC_ADDRESS,
          abi: USDC_ABI,
          functionName: 'approve',
          args: [CONTRACT_ADDRESS, PRICE],
          account,
        });
        await publicClient.waitForTransactionReceipt({ hash: approveTx });
      }

      setStep('subscribing');
      const subscribeTx = await walletClient.writeContract({
        address: CONTRACT_ADDRESS,
        abi: SUBSCRIPTION_ABI,
        functionName: 'subscribe',
        account,
      });
      await publicClient.waitForTransactionReceipt({ hash: subscribeTx });

      setStep('done');
      await checkStatus(wallet);
    } catch (err) {
      setStep('error');
      setError(err instanceof Error ? err.message : 'Transaction failed');
    }
  }, [wallet, checkStatus]);

  const reset = useCallback(() => {
    setStep('idle');
    setError(null);
  }, []);

  return { isSubscribed, expiry, isChecking, step, error, subscribe, reset };
}
