'use client';

import { useState } from 'react';

/**
 * Réinitialise un formulaire de dialog à l'ouverture (et si resetKey change à ouvert).
 * Évite setState dans un effect (react-hooks/set-state-in-effect).
 */
export function useOpenReset(open: boolean, resetKey: string, onOpen: () => void): void {
  const source = open ? `open:${resetKey}` : 'closed';
  const [applied, setApplied] = useState(source);
  if (source !== applied) {
    setApplied(source);
    if (open) {
      onOpen();
    }
  }
}
