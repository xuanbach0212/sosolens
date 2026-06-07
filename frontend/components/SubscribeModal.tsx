'use client';

import { useEffect, useRef } from 'react';
import type { SubscribeStep } from '@/hooks/useSubscription';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  isSubscribed: boolean;
  step: SubscribeStep;
  error: string | null;
  expiry: Date | null;
  onSubscribe: () => void;
  onReset: () => void;
}

const BUTTON_LABEL: Record<SubscribeStep, string> = {
  idle: 'APPROVE + SUBSCRIBE  ·  5 USDC / 30 DAYS',
  approving: 'APPROVING USDC...',
  subscribing: 'SUBSCRIBING...',
  done: 'PREMIUM ACTIVE ✓',
  error: '[ RETRY ]',
};

export default function SubscribeModal({
  isOpen,
  onClose,
  isSubscribed,
  step,
  error,
  expiry,
  onSubscribe,
  onReset,
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (isOpen) dialogRef.current?.focus();
  }, [isOpen]);

  if (!isOpen) return null;

  const isActive = step === 'approving' || step === 'subscribing';

  const expiryStr = expiry
    ? expiry.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : null;

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
      onClick={onClose}
      onKeyDown={(e) => { if (e.key === 'Escape') onClose(); }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="subscribe-modal-title"
        tabIndex={-1}
        className="bg-terminal-panel border border-terminal-border w-[380px] font-mono text-xs outline-none"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border">
          <span id="subscribe-modal-title" className="font-bold tracking-widest text-terminal-green">SOSOLENS PREMIUM</span>
          <button
            onClick={onClose}
            className="text-terminal-muted hover:text-terminal-text cursor-pointer"
          >
            [ X ]
          </button>
        </div>

        {/* Details */}
        <div className="px-4 py-4 space-y-2">
          <div className="flex justify-between">
            <span className="text-terminal-muted">PRICE</span>
            <span className="text-terminal-text">5 USDC / 30 DAYS</span>
          </div>
          <div className="flex justify-between">
            <span className="text-terminal-muted">NETWORK</span>
            <span className="text-terminal-text">BASE SEPOLIA</span>
          </div>
          <div className="flex justify-between">
            <span className="text-terminal-muted">SIGNALS</span>
            <span className={isSubscribed ? 'text-terminal-green' : 'text-terminal-yellow'}>
              {isSubscribed ? 'REAL-TIME' : 'DELAYED 1H  (FREE)'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-terminal-muted">STREAM</span>
            <span className={isSubscribed ? 'text-terminal-green' : 'text-terminal-yellow'}>
              {isSubscribed ? 'SSE LIVE' : 'POLLING FALLBACK'}
            </span>
          </div>
          {expiryStr && (
            <div className="flex justify-between">
              <span className="text-terminal-muted">EXPIRES</span>
              <span className="text-terminal-green">{expiryStr}</span>
            </div>
          )}

          {error && (
            <div className="text-terminal-red text-[10px] break-all pt-1">
              ERR: {error.slice(0, 140)}
            </div>
          )}

          {/* Action */}
          <div className="pt-3">
            {isSubscribed ? (
              <div className="text-center text-terminal-green py-2 border border-terminal-green tracking-widest">
                PREMIUM ACTIVE ●
              </div>
            ) : (
              <button
                onClick={step === 'error' ? onReset : onSubscribe}
                disabled={isActive || step === 'done'}
                className={`w-full py-2 text-center border tracking-wide transition-colors cursor-pointer disabled:cursor-default ${
                  step === 'done'
                    ? 'border-terminal-green text-terminal-green'
                    : isActive
                    ? 'border-terminal-muted text-terminal-muted opacity-60'
                    : step === 'error'
                    ? 'border-terminal-red text-terminal-red hover:bg-terminal-red hover:text-terminal-bg'
                    : 'border-terminal-yellow text-terminal-yellow hover:bg-terminal-yellow hover:text-terminal-bg'
                }`}
              >
                {isActive && <span className="animate-pulse">▋ </span>}
                {BUTTON_LABEL[step]}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
