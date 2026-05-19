'use client';

interface Props {
  address: string | null;
  isSubscribed: boolean;
  isConnecting: boolean;
  hasMetaMask: boolean;
  expiry: Date | null;
  onConnect: () => void;
  onUpgrade: () => void;
}

function truncate(addr: string) {
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export default function WalletBar({
  address,
  isSubscribed,
  isConnecting,
  hasMetaMask,
  expiry,
  onConnect,
  onUpgrade,
}: Props) {
  if (!hasMetaMask) {
    return <span className="text-terminal-muted text-[10px]">NO WALLET</span>;
  }

  if (!address) {
    return (
      <button
        onClick={onConnect}
        disabled={isConnecting}
        className="text-[10px] text-terminal-yellow border border-terminal-yellow px-2 py-0.5 hover:bg-terminal-yellow hover:text-terminal-bg transition-colors cursor-pointer disabled:opacity-50"
      >
        {isConnecting ? 'CONNECTING...' : '[ CONNECT WALLET ]'}
      </button>
    );
  }

  if (isSubscribed) {
    const expiryStr = expiry
      ? expiry.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
      : null;
    return (
      <span className="text-[10px] flex items-center gap-2">
        <span className="text-terminal-green font-bold">PREMIUM ●</span>
        <span className="text-terminal-muted">·</span>
        <span className="text-terminal-text">{truncate(address)}</span>
        {expiryStr && (
          <>
            <span className="text-terminal-muted">·</span>
            <span className="text-terminal-muted">EXP {expiryStr}</span>
          </>
        )}
      </span>
    );
  }

  return (
    <span className="text-[10px] flex items-center gap-2">
      <span className="text-terminal-yellow">FREE TIER · ⚠ DELAYED 1H</span>
      <span className="text-terminal-muted">·</span>
      <span className="text-terminal-muted">{truncate(address)}</span>
      <span className="text-terminal-muted">·</span>
      <button
        onClick={onUpgrade}
        className="text-terminal-green border border-terminal-green px-2 py-0.5 hover:bg-terminal-green hover:text-terminal-bg transition-colors cursor-pointer"
      >
        [ UPGRADE ]
      </button>
    </span>
  );
}
