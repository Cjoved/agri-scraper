"""
Cloudflare bypass using FlareSolverr (Docker).
Returns cookies and User-Agent for Playwright so the scraper can bypass Cloudflare.
Set FLARESOLVERR_URL in .env (e.g. http://localhost:8191).
"""
import os
import requests
from urllib.parse import urlparse

def get_flaresolverr_url():
    """Base URL of FlareSolverr (no trailing slash)."""
    url = (os.getenv("FLARESOLVERR_URL") or "http://localhost:8191").strip().rstrip("/")
    return url


def _flaresolverr_api_url():
    """Full FlareSolverr API endpoint (POST here; root / returns 405)."""
    base = get_flaresolverr_url().rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def _request_flaresolverr(base, payload, log, timeout=70):
    """POST to FlareSolverr; returns (data dict or None, error message or None)."""
    api_url = _flaresolverr_api_url()
    try:
        r = requests.post(api_url, json=payload, timeout=timeout, headers={"Content-Type": "application/json"})
        r.raise_for_status()
        return r.json(), None
    except requests.RequestException as e:
        return None, str(e)
    except ValueError as e:
        return None, f"Invalid JSON: {e}"


def get_cloudflare_cookies(url, log=None):
    """
    Call FlareSolverr to solve Cloudflare for the given URL.
    Uses a session so the browser keeps state and we get cookies after the challenge.
    Returns (cookies_list, user_agent).
    - cookies_list: list of dicts for Playwright context.add_cookies() (each has "url" set)
    - user_agent: str or None
    If FlareSolverr is unreachable or fails, returns ([], None).
    """
    if log is None:
        log = print

    base = get_flaresolverr_url()
    session_id = None

    # 1) Create session so browser persists and we capture cookies after Cloudflare
    create_payload = {"cmd": "sessions.create"}
    data, err = _request_flaresolverr(base, create_payload, log, timeout=90)
    if err:
        log(f"FlareSolverr sessions.create failed: {err}")
        # Fallback: request.get without session (one-off browser)
        data, err = _request_flaresolverr(base, {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
        }, log, timeout=70)
        if err:
            log(f"FlareSolverr request.get failed: {err}")
            return [], None
        session_id = None
    else:
        if data.get("status") != "ok":
            msg = data.get("message", "Unknown error")
            log(f"FlareSolverr sessions.create: {msg}")
            return [], None
        session_id = (data.get("solution") or {}).get("session")
        if not session_id:
            log("FlareSolverr: no session ID in response, trying request.get without session.")
            data, err = _request_flaresolverr(base, {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000,
            }, log, timeout=70)
            if err:
                return [], None
        else:
            # 2) request.get with session
            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000,
            }
            if session_id:
                payload["session"] = session_id
            data, err = _request_flaresolverr(base, payload, log, timeout=70)
            if err:
                log(f"FlareSolverr request.get failed: {err}")
                try:
                    requests.post(_flaresolverr_api_url(), json={"cmd": "sessions.destroy", "session": session_id}, timeout=5)
                except Exception:
                    pass
                return [], None

            # Destroy session after we got the solution
            try:
                requests.post(_flaresolverr_api_url(), json={"cmd": "sessions.destroy", "session": session_id}, timeout=5)
            except Exception:
                pass

    status = data.get("status")
    if status != "ok":
        msg = data.get("message", "Unknown error")
        log(f"FlareSolverr returned status '{status}': {msg}")
        return [], None

    solution = data.get("solution") or {}
    cookies_raw = solution.get("cookies")
    if cookies_raw is None:
        # Some versions might use different key
        cookies_raw = solution.get("cookie") or []
    if not isinstance(cookies_raw, list):
        cookies_raw = []

    user_agent = solution.get("userAgent") or solution.get("User-Agent") or None

    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or ""
    # Playwright add_cookies: each cookie MUST have either "url" OR ("domain" + "path").
    # Use a single origin URL so cookies apply to the site we're opening.
    cookie_base_url = f"{scheme}://{netloc}/" if netloc else ""

    cookies = []
    for c in cookies_raw:
        if not isinstance(c, dict):
            continue
        name = c.get("name")
        if name is None:
            continue
        value = c.get("value")
        # Playwright: provide only "url" (no domain/path) so it accepts the cookie
        if not cookie_base_url:
            continue
        cookie_entry = {
            "name": name,
            "value": str(value) if value is not None else "",
            "url": cookie_base_url,
        }
        cookies.append(cookie_entry)

    if cookies:
        log(f"FlareSolverr: got {len(cookies)} cookie(s) and user agent.")
    else:
        log("FlareSolverr: no cookies in response (solution keys: %s)." % list(solution.keys()))

    return cookies, user_agent
