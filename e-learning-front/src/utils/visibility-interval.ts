/**
 * setInterval qui ne tick que lorsque l'onglet est visible.
 * Évite de pomper batterie/réseau quand `document.hidden`.
 * Le callback est exécuté immédiatement au démarrage (et au retour visible).
 */
export function setVisibilityInterval(
  callback: () => void,
  intervalMs: number
): () => void {
  let timer: ReturnType<typeof setInterval> | null = null;

  const clear = () => {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  };

  const start = () => {
    if (timer !== null) return;
    timer = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) return;
      callback();
    }, intervalMs);
  };

  const onVisibilityChange = () => {
    if (document.hidden) {
      clear();
    } else {
      callback();
      start();
    }
  };

  if (typeof document !== 'undefined' && !document.hidden) {
    callback();
    start();
  }

  document.addEventListener('visibilitychange', onVisibilityChange);

  return () => {
    clear();
    document.removeEventListener('visibilitychange', onVisibilityChange);
  };
}
