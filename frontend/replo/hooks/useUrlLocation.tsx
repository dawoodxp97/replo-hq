"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type HistoryMode = "push" | "replace";

interface HistoryOptions {
  mode?: HistoryMode;
  state?: unknown;
}

type SearchParamValue = string | number | boolean;

type SearchParamsObject = Record<string, string | string[]>;

interface UseUrlLocationReturn {
  // Environment
  isReady: boolean;

  // Window location parity (read-only values)
  href: string;
  protocol: string;
  host: string;
  hostname: string;
  port: string;
  pathname: string;
  search: string;
  hash: string;

  // Raw objects for advanced use
  location: Location | null; // SSR-safe
  url: URL | null; // SSR-safe

  // Search parameter management
  paramsObject: SearchParamsObject;
  getParam: (name: string) => string | null;
  setParam: (name: string, value: SearchParamValue, options?: HistoryOptions) => void;
  deleteParam: (name: string, options?: HistoryOptions) => void;
  setParams: (
    params: Record<string, SearchParamValue | null | undefined>,
    options?: HistoryOptions
  ) => void;
  paramsToString: () => string;

  // URL modification capabilities
  setHref: (href: string, options?: HistoryOptions) => void; // updates via history
  replaceHref: (href: string, state?: unknown) => void; // no history entry
  pushState: (state: unknown, href?: string) => void;
  replaceState: (state: unknown, href?: string) => void;

  // Component setters (push by default)
  setProtocol: (protocol: string, options?: HistoryOptions) => void;
  setHost: (host: string, options?: HistoryOptions) => void;
  setHostname: (hostname: string, options?: HistoryOptions) => void;
  setPort: (port: string, options?: HistoryOptions) => void;
  setPathname: (pathname: string, options?: HistoryOptions) => void;
  setSearch: (search: string, options?: HistoryOptions) => void;
  setHash: (hash: string, options?: HistoryOptions) => void;

  // Event listeners
  addListener: (listener: (url: URL) => void) => () => void; // returns cleanup

  // Utility
  refresh: () => void;
}

const useUrlLocation = (): UseUrlLocationReturn => {
  const isReady = typeof window !== "undefined";
  const [url, setUrl] = useState<URL | null>(() => (isReady ? new URL(window.location.href) : null));

  // Maintain reference to listeners to notify on changes
  const listenersRef = useRef<Set<(url: URL) => void>>(new Set());

  const notifyListeners = useCallback(
    (nextUrl: URL) => {
      // Call in a microtask to avoid re-entrancy problems
      queueMicrotask(() => {
        listenersRef.current.forEach((fn) => {
          try {
            fn(nextUrl);
          } catch (_) {
            // Swallow listener errors to avoid breaking the hook
          }
        });
      });
    },
    []
  );

  const refresh = useCallback(() => {
    if (!isReady) return;
    const next = new URL(window.location.href);
    setUrl(next);
    notifyListeners(next);
  }, [isReady, notifyListeners]);

  useEffect(() => {
    if (!isReady) return;
    const onPopState = () => refresh();
    const onHashChange = () => refresh();
    window.addEventListener("popstate", onPopState);
    window.addEventListener("hashchange", onHashChange);
    return () => {
      window.removeEventListener("popstate", onPopState);
      window.removeEventListener("hashchange", onHashChange);
    };
  }, [isReady, refresh]);

  // Helper to apply URL changes with history management
  const applyUrlUpdate = useCallback(
    (updater: (u: URL) => void, options?: HistoryOptions) => {
      if (!isReady) return;
      const current = new URL(window.location.href);
      updater(current);
      const mode: HistoryMode = options?.mode === "replace" ? "replace" : "push";
      const state = options?.state ?? window.history.state;
      if (mode === "replace") {
        window.history.replaceState(state, "", current.toString());
      } else {
        window.history.pushState(state, "", current.toString());
      }
      setUrl(current);
      notifyListeners(current);
    },
    [isReady, notifyListeners]
  );

  // Values (derived)
  const href = url?.href ?? "";
  const protocol = url?.protocol ?? "";
  const host = url?.host ?? "";
  const hostname = url?.hostname ?? "";
  const port = url?.port ?? "";
  const pathname = url?.pathname ?? "";
  const search = url?.search ?? "";
  const hash = url?.hash ?? "";

  // Memoized params object (handles duplicate keys -> array)
  const paramsObject: SearchParamsObject = useMemo(() => {
    if (!url) return {};
    const obj: SearchParamsObject = {};
    url.searchParams.forEach((value, key) => {
      if (obj[key] === undefined) {
        obj[key] = value;
      } else if (Array.isArray(obj[key])) {
        (obj[key] as string[]).push(value);
      } else {
        obj[key] = [obj[key] as string, value];
      }
    });
    return obj;
  }, [url?.search]);

  // Search param helpers
  const getParam = useCallback(
    (name: string) => {
      return url ? url.searchParams.get(name) : null;
    },
    [url]
  );

  const setParam = useCallback(
    (name: string, value: SearchParamValue, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        u.searchParams.set(name, String(value));
      }, options);
    },
    [applyUrlUpdate]
  );

  const deleteParam = useCallback(
    (name: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        u.searchParams.delete(name);
      }, options);
    },
    [applyUrlUpdate]
  );

  const setParams = useCallback(
    (
      params: Record<string, SearchParamValue | null | undefined>,
      options?: HistoryOptions
    ) => {
      applyUrlUpdate((u) => {
        Object.entries(params).forEach(([key, val]) => {
          if (val === null || val === undefined) {
            u.searchParams.delete(key);
          } else {
            u.searchParams.set(key, String(val));
          }
        });
      }, options);
    },
    [applyUrlUpdate]
  );

  const paramsToString = useCallback(() => (url ? url.searchParams.toString() : ""), [url]);

  // URL modification
  const setHref = useCallback(
    (nextHref: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        const next = new URL(nextHref, u.toString());
        u.href = next.href;
      }, options);
    },
    [applyUrlUpdate]
  );

  const replaceHref = useCallback(
    (nextHref: string, state?: unknown) => {
      if (!isReady) return;
      const current = new URL(nextHref, window.location.href);
      window.history.replaceState(state ?? window.history.state, "", current.toString());
      setUrl(current);
      notifyListeners(current);
    },
    [isReady, notifyListeners]
  );

  const pushState = useCallback(
    (state: unknown, hrefOverride?: string) => {
      if (!isReady) return;
      const target = hrefOverride ? new URL(hrefOverride, window.location.href) : new URL(window.location.href);
      window.history.pushState(state, "", target.toString());
      setUrl(target);
      notifyListeners(target);
    },
    [isReady, notifyListeners]
  );

  const replaceState = useCallback(
    (state: unknown, hrefOverride?: string) => {
      if (!isReady) return;
      const target = hrefOverride ? new URL(hrefOverride, window.location.href) : new URL(window.location.href);
      window.history.replaceState(state, "", target.toString());
      setUrl(target);
      notifyListeners(target);
    },
    [isReady, notifyListeners]
  );

  // Component setters
  const setProtocol = useCallback(
    (next: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        const normalized = next.endsWith(":") ? next : `${next}:`;
        u.protocol = normalized;
      }, options);
    },
    [applyUrlUpdate]
  );

  const setHost = useCallback(
    (next: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        u.host = next;
      }, options);
    },
    [applyUrlUpdate]
  );

  const setHostname = useCallback(
    (next: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        u.hostname = next;
      }, options);
    },
    [applyUrlUpdate]
  );

  const setPort = useCallback(
    (next: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        u.port = next;
      }, options);
    },
    [applyUrlUpdate]
  );

  const setPathname = useCallback(
    (next: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        u.pathname = next.startsWith("/") ? next : `/${next}`;
      }, options);
    },
    [applyUrlUpdate]
  );

  const setSearch = useCallback(
    (next: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        const normalized = next ? (next.startsWith("?") ? next : `?${next}`) : "";
        u.search = normalized;
      }, options);
    },
    [applyUrlUpdate]
  );

  const setHash = useCallback(
    (next: string, options?: HistoryOptions) => {
      applyUrlUpdate((u) => {
        const normalized = next ? (next.startsWith("#") ? next : `#${next}`) : "";
        u.hash = normalized;
      }, options);
    },
    [applyUrlUpdate]
  );

  // External listener registration
  const addListener = useCallback((listener: (url: URL) => void) => {
    listenersRef.current.add(listener);
    return () => listenersRef.current.delete(listener);
  }, []);

  // Ensure values maintain referential equality via memoization
  const memoizedReturn = useMemo<UseUrlLocationReturn>(() => {
    return {
      isReady,
      href,
      protocol,
      host,
      hostname,
      port,
      pathname,
      search,
      hash,
      location: isReady ? window.location : null,
      url,
      paramsObject,
      getParam,
      setParam,
      deleteParam,
      setParams,
      paramsToString,
      setHref,
      replaceHref,
      pushState,
      replaceState,
      setProtocol,
      setHost,
      setHostname,
      setPort,
      setPathname,
      setSearch,
      setHash,
      addListener,
      refresh,
    };
  }, [
    isReady,
    href,
    protocol,
    host,
    hostname,
    port,
    pathname,
    search,
    hash,
    url,
    paramsObject,
    getParam,
    setParam,
    deleteParam,
    setParams,
    paramsToString,
    setHref,
    replaceHref,
    pushState,
    replaceState,
    setProtocol,
    setHost,
    setHostname,
    setPort,
    setPathname,
    setSearch,
    setHash,
    addListener,
    refresh,
  ]);

  return memoizedReturn;
};

export default useUrlLocation;