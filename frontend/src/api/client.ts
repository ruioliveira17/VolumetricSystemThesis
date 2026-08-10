// --------------------------------------------------------------------- //
// |                     Central authenticated API client               | //
// --------------------------------------------------------------------- //
//
// Every authenticated request must go through apiFetch(). It does three
// things the scattered fetch() calls could not do:
//
//   1. injects the current access token, read at send time;
//   2. on a 401, refreshes the token and retries the request once;
//   3. shares a single in-flight refresh between all concurrent callers.
//
// Point 3 matters because /refresh rotates the refresh token: two parallel
// refreshes would store two different token pairs, one overwriting the other.
// It also keeps the 100 ms /volume/status poller from firing a refresh per
// tick while the token is expired.

const API_URL: string = import.meta.env.VITE_API_URL;

type AuthFailureHandler = () => void;

// Called when the session cannot be recovered (no refresh token, or the
// refresh token itself was rejected). The App registers logout() here.
let onAuthFailure: AuthFailureHandler | null = null;

let authFailureHandled = false;

// The refresh currently travelling, if any. Shared by every caller.
let refreshInFlight: Promise<boolean> | null = null;

function handleAuthFailure(): void {
    if (authFailureHandled) {
        return;
    }

    authFailureHandled = true;

    clearTokens();
    onAuthFailure?.();
}

export function setOnAuthFailure(handler: AuthFailureHandler | null): void {
    onAuthFailure = handler;
}

export function getAccessToken(): string | null {
    return localStorage.getItem("access_token");
}

export function storeTokens(accessToken: string, refreshToken?: string): void {
    localStorage.setItem("access_token", accessToken);

    if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
    }

    authFailureHandled = false;
}

export function clearTokens(): void {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

/**
 * Exchanges the refresh token for a new token pair.
 *
 * Returns true if a new access token was stored. Returns false on a rejected
 * or missing refresh token and on network errors: the caller decides whether
 * that means "log out" (apiFetch does) or "try again later" (the proactive
 * scheduler does).
 *
 * Concurrent calls share the same request.
 */
export function refreshTokens(): Promise<boolean> {
    if (refreshInFlight) {
        return refreshInFlight;
    }

    refreshInFlight = (async (): Promise<boolean> => {
        try {
            const refreshToken = localStorage.getItem("refresh_token");

            if (!refreshToken) {
                return false;
            }

            const response = await fetch(`${API_URL}/refreshAccessToken`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();

            if (!data.access_token) {
                return false;
            }

            storeTokens(data.access_token);
            return true;

        } catch (error) {
            // Network error: the tokens are probably still valid, so do not
            // throw them away. The next 401 will try again.
            console.warn("Token refresh failed:", error);
            return false;

        }
    })();

    refreshInFlight.finally(() => {
        refreshInFlight = null;
    });

    return refreshInFlight;
}

function sendWithToken(
    path: string,
    init: RequestInit,
    token: string | null
): Promise<Response> {
    const headers = new Headers(init.headers);

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    return fetch(`${API_URL}${path}`, { ...init, headers });
}

/**
 * Authenticated fetch. Use it for every endpoint behind get_current_user.
 *
 * `path` is the part after the API base URL, including the leading slash:
 *     apiFetch("/weight")
 *     apiFetch("/saveMeasurements", { method: "POST", body: JSON.stringify(x) })
 *
 * The returned Response is the caller's to inspect, exactly like fetch().
 * A 401 is only returned when the session is genuinely gone; by then
 * onAuthFailure has already been called.
 */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
    const tokenSent = getAccessToken();

    const response = await sendWithToken(path, init, tokenSent);

    if (response.status !== 401) {
        return response;
    }

    // Another request may have refreshed the token while this one was in
    // flight. In that case there is nothing to refresh: just retry.
    const currentToken = getAccessToken();
    const alreadyRefreshed = currentToken !== null && currentToken !== tokenSent;

    const refreshed = alreadyRefreshed || await refreshTokens();

    if (!refreshed) {
        handleAuthFailure();
        return response;
    }

    const retried = await sendWithToken(path, init, getAccessToken());

    // A 401 on the retry means the fresh token was rejected too: the session
    // is unrecoverable, stop here instead of looping.
    if (retried.status === 401) {
        handleAuthFailure();
    }

    return retried;
}

/**
 * apiFetch + JSON decoding, for the common case. Throws on a non-2xx
 * response so callers can rely on the returned value.
 */
export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await apiFetch(path, init);

    if (!response.ok) {
        throw new Error(`${init.method ?? "GET"} ${path} failed with ${response.status}`);
    }

    return await response.json() as T;
}
