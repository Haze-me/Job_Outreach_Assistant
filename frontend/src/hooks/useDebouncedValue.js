import { useEffect, useState } from "react";

/**
 * Delays a value until it stops changing.
 *
 * Used for search boxes: without it every keystroke fires a request, and the
 * responses can arrive out of order so the list briefly shows results for a
 * prefix of what was typed.
 */
export function useDebouncedValue(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
