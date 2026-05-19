'use client';

import { useState, useEffect, useCallback } from 'react';

export interface WalletState {
  address: string | null;
  isConnecting: boolean;
  hasMetaMask: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
}

export function useWallet(): WalletState {
  const [address, setAddress] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [hasMetaMask, setHasMetaMask] = useState(false);

  useEffect(() => {
    setHasMetaMask(!!window.ethereum);
    if (!window.ethereum) return;

    const handleAccountsChanged = (accounts: string[]) => {
      setAddress(accounts[0] ?? null);
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);

    // Check if already authorized (no prompt)
    window.ethereum
      .request({ method: 'eth_accounts' })
      .then((accounts: string[]) => {
        setAddress(accounts[0] ?? null);
      })
      .catch(() => {});

    return () => {
      window.ethereum?.removeListener('accountsChanged', handleAccountsChanged);
    };
  }, []);

  const connect = useCallback(async () => {
    if (!window.ethereum) return;
    setIsConnecting(true);
    try {
      const accounts: string[] = await window.ethereum.request({
        method: 'eth_requestAccounts',
      });
      setAddress(accounts[0] ?? null);
    } catch {
      // user rejected
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    setAddress(null);
  }, []);

  return { address, isConnecting, hasMetaMask, connect, disconnect };
}
