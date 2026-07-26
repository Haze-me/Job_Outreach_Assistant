import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Copies text and reports success briefly, so a button can show "Copied".
 *
 * `navigator.clipboard` needs a secure context; the textarea fallback keeps
 * the feature working over plain http, which is how the dev server is served.
 */
export function useCopyToClipboard(resetAfter = 2000) {
  const [copied, setCopied] = useState(null);
  const timerRef = useRef(null);

  useEffect(() => () => clearTimeout(timerRef.current), []);

  const copy = useCallback(
    async (text) => {
      let ok = false;
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
          ok = true;
        } else {
          const area = document.createElement("textarea");
          area.value = text;
          area.setAttribute("readonly", "");
          area.style.position = "absolute";
          area.style.left = "-9999px";
          document.body.appendChild(area);
          area.select();
          ok = document.execCommand("copy");
          document.body.removeChild(area);
        }
      } catch {
        ok = false;
      }

      setCopied(ok ? text : null);
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setCopied(null), resetAfter);
      return ok;
    },
    [resetAfter],
  );

  return { copy, copied };
}
