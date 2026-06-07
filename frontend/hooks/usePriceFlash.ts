'use client';

import { useEffect, useRef, useState } from 'react';

// Strip "$", commas, whitespace; normalize U+2212 minus → "-".
// Unit suffixes (K/M/B/T) are intentionally ignored — direction is correct
// across same-unit ticks; the rare unit boundary ($999B→$1T) is acceptable noise.
function parseNum(v: string | number): number {
  if (typeof v === 'number') return v;
  const cleaned = v.replace(/[$,\s]/g, '').replace('−', '-');
  return parseFloat(cleaned);
}

export type FlashClass = '' | 'flash-up' | 'flash-down';

export function usePriceFlash(value: string | number | null | undefined): FlashClass {
  const prev = useRef<string | number | null | undefined>(value);
  const [cls, setCls] = useState<FlashClass>('');

  useEffect(() => {
    if (value == null || prev.current == null) {
      prev.current = value;
      return;
    }
    if (value === prev.current) return;

    const a = parseNum(prev.current);
    const b = parseNum(value);
    prev.current = value;

    if (!Number.isFinite(a) || !Number.isFinite(b) || a === b) return;

    setCls(b > a ? 'flash-up' : 'flash-down');
    const t = setTimeout(() => setCls(''), 700);
    return () => clearTimeout(t);
  }, [value]);

  return cls;
}
