import json
import os
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(os.environ.get("MINDTUNE_ROOT", Path(__file__).resolve().parents[1])).resolve()
PROJECT_ROOT_FALLBACK = Path.home() / "Documents" / "Chatgpt" / "Biohacking"


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path.resolve()
    return paths[0].resolve()


CREDENTIALS_FILE = first_existing_path(
    ROOT / ".oura_credentials", PROJECT_ROOT_FALLBACK / ".oura_credentials"
)
TOKEN_FILE = first_existing_path(ROOT / ".oura_token", PROJECT_ROOT_FALLBACK / ".oura_token")
TOKEN_CANDIDATES = [
    ROOT / ".oura_token",
    Path(__file__).resolve().parent / ".oura_token",
    PROJECT_ROOT_FALLBACK / ".oura_token",
    Path.home() / "Library" / "Application Support" / "MindTune Lab" / ".oura_token",
    Path.home() / ".oura_token",
]
OAUTH_PORT = 8765
OAUTH_REDIRECT_URI = "http://localhost:8765/callback"
OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/v2/oauth/token"
OURA_DAILY_SLEEP_URL = "https://api.ouraring.com/v2/usercollection/daily_sleep"
OURA_DAILY_READINESS_URL = "https://api.ouraring.com/v2/usercollection/daily_readiness"
OURA_DAILY_ACTIVITY_URL = "https://api.ouraring.com/v2/usercollection/daily_activity"
OURA_DAILY_STRESS_URL = "https://api.ouraring.com/v2/usercollection/daily_stress"
OURA_SLEEP_URL = "https://api.ouraring.com/v2/usercollection/sleep"


def load_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        return {}
    try:
        return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_token() -> dict:
    for path in TOKEN_CANDIDATES:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["_token_file"] = str(path)
            return payload
        except Exception:
            continue
    return {}


def save_token(token: dict) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token, indent=2), encoding="utf-8")


def token_status() -> dict:
    token = load_token()
    return {
        "has_token": bool(token.get("access_token")),
        "token_file": token.get("_token_file") or str(TOKEN_FILE),
        "checked_paths": [str(path) for path in TOKEN_CANDIDATES],
    }


def _http_post(url: str, data: dict, headers: dict | None = None) -> tuple[bool, dict]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return False, json.loads(exc.read().decode("utf-8"))
        except Exception:
            return False, {"error": str(exc), "status": exc.code}
    except Exception as exc:
        return False, {"error": str(exc)}


def _http_get(url: str, token: str, params: dict | None = None) -> tuple[bool, dict]:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return False, json.loads(exc.read().decode("utf-8"))
        except Exception:
            return False, {"error": str(exc), "status": exc.code}
    except Exception as exc:
        return False, {"error": str(exc)}


def exchange_code_for_token(code: str, credentials: dict) -> dict:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": credentials.get("redirect_uri", OAUTH_REDIRECT_URI),
        "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"],
    }
    ok, result = _http_post(OURA_TOKEN_URL, data)
    if ok:
        result["obtained_at"] = time.time()
        return result
    return result


class _CallbackHandler(BaseHTTPRequestHandler):
    _token_result: dict | None = None
    _server_running: bool = False

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        query = urllib.parse.parse_qs(parsed.query)
        code = query.get("code", [None])[0]
        error = query.get("error", [None])[0]
        if error:
            _CallbackHandler._token_result = {
                "error": error,
                "error_description": query.get("error_description", [""])[0],
            }
        elif not code:
            _CallbackHandler._token_result = {"error": "no_code"}
        else:
            credentials = load_credentials()
            if not credentials:
                _CallbackHandler._token_result = {"error": "missing_credentials"}
            else:
                _CallbackHandler._token_result = exchange_code_for_token(code, credentials)
                if "access_token" in _CallbackHandler._token_result:
                    save_token(_CallbackHandler._token_result)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if "access_token" in (_CallbackHandler._token_result or {}):
            html = b"""<html><head><meta charset="utf-8"><title>Oura OK</title></head>
<body><h1>Autorizzazione Oura completata</h1>
<p>Tra 3 secondi torno a MindTune Lab.</p>
<script>setTimeout(function(){ window.location.href = "http://127.0.0.1:8792/"; }, 3000);</script>
</body></html>"""
            self.wfile.write(html)
        else:
            msg = json.dumps(_CallbackHandler._token_result)
            self.wfile.write(f"<h1>Errore autorizzazione Oura</h1><pre>{msg}</pre>".encode("utf-8"))

    def log_message(self, fmt, *args):
        pass


def get_auth_url() -> tuple[dict, str]:
    credentials = load_credentials()
    if not credentials or not credentials.get("client_id"):
        return {"ok": False, "error": "missing_credentials"}, ""
    scopes = "email personal daily"
    params = {
        "client_id": credentials["client_id"],
        "redirect_uri": credentials.get("redirect_uri", OAUTH_REDIRECT_URI),
        "response_type": "code",
        "scope": scopes,
    }
    return {"ok": True}, OURA_AUTH_URL + "?" + urllib.parse.urlencode(
        params, quote_via=urllib.parse.quote
    )


def ensure_callback_server() -> None:
    if _CallbackHandler._server_running:
        return
    _CallbackHandler._server_running = True
    _CallbackHandler._token_result = None
    server = HTTPServer(("127.0.0.1", OAUTH_PORT), _CallbackHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def _wait_and_shutdown():
        deadline = time.time() + 300
        while _CallbackHandler._token_result is None and time.time() < deadline:
            time.sleep(0.5)
        server.shutdown()
        _CallbackHandler._server_running = False

    Thread(target=_wait_and_shutdown, daemon=True).start()


def start_oauth_flow() -> dict:
    result, auth_url = get_auth_url()
    if not result.get("ok"):
        return result
    ensure_callback_server()
    webbrowser.open(auth_url, new=2)
    return {
        "ok": True,
        "message": "Autorizzazione Oura avviata nel browser. Completa l'accesso e torna all'app. Il widget si aggiorna entro 60 secondi.",
    }


def fetch_oura_daily(requested_day: str = "") -> dict:
    token_data = load_token()
    token = token_data.get("access_token")
    if not token:
        return {
            "ok": False,
            "needs_auth": True,
            "error": "Token Oura non trovato",
            **token_status(),
        }

    def seconds_to_h(value):
        return round(value / 3600.0, 2) if isinstance(value, (int, float)) else None

    def seconds_to_min(value):
        return round(value / 60.0, 1) if isinstance(value, (int, float)) else None

    def first_number(*values):
        for value in values:
            if isinstance(value, (int, float)):
                return value
        return None

    def compact_dict(data: dict) -> dict:
        return {k: v for k, v in (data or {}).items() if v not in (None, "", [], {})}

    def flatten(prefix: str, data: dict, out: dict) -> None:
        for key, value in (data or {}).items():
            name = f"{prefix}_{key}" if prefix else str(key)
            if isinstance(value, dict):
                flatten(name, value, out)
            elif isinstance(value, (str, int, float, bool)) or value is None:
                out[name] = value

    def make_payload(
        sleep_data: dict, readiness_data: dict, activity_data: dict, stress_data: dict, day: str
    ) -> dict:
        def activity_to_intensity(a: dict) -> str:
            if not a:
                return "none"
            if a.get("high_activity_time"):
                return "vigorous"
            if a.get("medium_activity_time"):
                return "moderate"
            if a.get("low_activity_time"):
                return "light"
            return "none"

        def stress_to_level(s: dict) -> int | None:
            if not s:
                return None
            summary = (s.get("day_summary") or "").lower()
            if summary == "restorative":
                return 2
            if summary == "stressful":
                return 6
            if summary == "normal":
                return 4
            return None

        raw_session = (
            sleep_data.get("_selected_sleep_session")
            if isinstance(sleep_data.get("_selected_sleep_session"), dict)
            else {}
        )
        sleep_total_s = first_number(
            sleep_data.get("total_sleep_duration"), raw_session.get("total_sleep_duration")
        )
        deep_s = first_number(
            sleep_data.get("deep_sleep_duration"), raw_session.get("deep_sleep_duration")
        )
        rem_s = first_number(
            sleep_data.get("rem_sleep_duration"), raw_session.get("rem_sleep_duration")
        )
        light_s = first_number(
            sleep_data.get("light_sleep_duration"), raw_session.get("light_sleep_duration")
        )
        awake_s = first_number(sleep_data.get("awake_time"), raw_session.get("awake_time"))
        time_in_bed_s = first_number(sleep_data.get("time_in_bed"), raw_session.get("time_in_bed"))
        latency_s = first_number(sleep_data.get("latency"), raw_session.get("latency"))
        contributors = {
            "sleep": sleep_data.get("contributors") or {},
            "readiness": readiness_data.get("contributors") or {},
            "activity": activity_data.get("contributors") or {},
        }
        metrics = {
            "day": day,
            "sleep_score": sleep_data.get("score"),
            "sleep_duration_s": sleep_total_s,
            "sleep_duration_h": seconds_to_h(sleep_total_s),
            "time_in_bed_s": time_in_bed_s,
            "time_in_bed_h": seconds_to_h(time_in_bed_s),
            "deep_s": deep_s,
            "deep_h": seconds_to_h(deep_s),
            "rem_s": rem_s,
            "rem_h": seconds_to_h(rem_s),
            "light_s": light_s,
            "light_h": seconds_to_h(light_s),
            "awake_s": awake_s,
            "awake_h": seconds_to_h(awake_s),
            "latency_s": latency_s,
            "latency_min": seconds_to_min(latency_s),
            "efficiency": first_number(sleep_data.get("efficiency"), raw_session.get("efficiency")),
            "restlessness": first_number(
                sleep_data.get("restlessness"), raw_session.get("restlessness")
            ),
            "bedtime_start": raw_session.get("bedtime_start") or sleep_data.get("bedtime_start"),
            "bedtime_end": raw_session.get("bedtime_end") or sleep_data.get("bedtime_end"),
            "sleep_average_hr": first_number(
                raw_session.get("average_heart_rate"),
                sleep_data.get("average_heart_rate"),
                sleep_data.get("hr_average"),
            ),
            "sleep_lowest_hr": first_number(
                raw_session.get("lowest_heart_rate"),
                sleep_data.get("lowest_heart_rate"),
                sleep_data.get("hr_lowest"),
            ),
            "sleep_average_hrv": first_number(
                raw_session.get("average_hrv"), sleep_data.get("average_hrv")
            ),
            "sleep_average_breath": first_number(
                raw_session.get("average_breath"), sleep_data.get("average_breath")
            ),
            "readiness_score": readiness_data.get("score"),
            "cognitive_energy": readiness_data.get("score"),
            "temperature_deviation": first_number(
                readiness_data.get("temperature_deviation"), readiness_data.get("temperature_delta")
            ),
            "temperature_trend_deviation": readiness_data.get("temperature_trend_deviation"),
            "activity_score": activity_data.get("score"),
            "steps": activity_data.get("steps"),
            "active_calories": activity_data.get("active_calories"),
            "total_calories": activity_data.get("total_calories"),
            "target_calories": activity_data.get("target_calories"),
            "equivalent_walking_distance": activity_data.get("equivalent_walking_distance"),
            "low_activity_min": seconds_to_min(activity_data.get("low_activity_time")),
            "medium_activity_min": seconds_to_min(activity_data.get("medium_activity_time")),
            "high_activity_min": seconds_to_min(activity_data.get("high_activity_time")),
            "inactive_min": seconds_to_min(activity_data.get("inactive_time")),
            "resting_min": seconds_to_min(activity_data.get("resting_time")),
            "non_wear_min": seconds_to_min(activity_data.get("non_wear_time")),
            "exercise_intensity": activity_to_intensity(activity_data),
            "stress_level": stress_to_level(stress_data),
            "stress_summary": stress_data.get("day_summary"),
        }
        flatten("stress", stress_data, metrics)
        flattened_raw = {}
        flatten("sleep", sleep_data, flattened_raw)
        flatten("readiness", readiness_data, flattened_raw)
        flatten("activity", activity_data, flattened_raw)
        flatten("stress", stress_data, flattened_raw)
        return {
            **compact_dict(metrics),
            "contributors": contributors,
            "all_metrics": compact_dict(flattened_raw),
            "raw_sleep": sleep_data,
            "raw_readiness": readiness_data,
            "raw_activity": activity_data,
            "raw_stress": stress_data,
        }

    today = time.strftime("%Y-%m-%d")
    start = time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400))
    sleep_ok, sleep_resp = _http_get(
        OURA_DAILY_SLEEP_URL, token, {"start_date": start, "end_date": today}
    )
    readiness_ok, readiness_resp = _http_get(
        OURA_DAILY_READINESS_URL, token, {"start_date": start, "end_date": today}
    )
    activity_ok, activity_resp = _http_get(
        OURA_DAILY_ACTIVITY_URL, token, {"start_date": start, "end_date": today}
    )
    stress_ok, stress_resp = _http_get(
        OURA_DAILY_STRESS_URL, token, {"start_date": start, "end_date": today}
    )
    sleep_session_ok, sleep_session_resp = _http_get(
        OURA_SLEEP_URL, token, {"start_date": start, "end_date": today}
    )
    api_status = {
        "daily_sleep": {
            "ok": sleep_ok,
            "error": sleep_resp.get("message") or sleep_resp.get("error"),
        },
        "daily_readiness": {
            "ok": readiness_ok,
            "error": readiness_resp.get("message") or readiness_resp.get("error"),
        },
        "daily_activity": {
            "ok": activity_ok,
            "error": activity_resp.get("message") or activity_resp.get("error"),
        },
        "daily_stress": {
            "ok": stress_ok,
            "error": stress_resp.get("message") or stress_resp.get("error"),
        },
        "sleep": {
            "ok": sleep_session_ok,
            "error": sleep_session_resp.get("message") or sleep_session_resp.get("error"),
        },
    }
    if (
        not sleep_ok
        and not readiness_ok
        and not activity_ok
        and not stress_ok
        and not sleep_session_ok
    ):
        return {
            "ok": False,
            "day": today,
            "error": "Oura API non disponibile",
            "api_status": api_status,
            **token_status(),
        }
    sleep_rows = {row.get("day"): row for row in (sleep_resp.get("data") or [])}
    readiness_rows = {row.get("day"): row for row in (readiness_resp.get("data") or [])}
    activity_rows = {row.get("day"): row for row in (activity_resp.get("data") or [])}
    stress_rows = {row.get("day"): row for row in (stress_resp.get("data") or [])}
    sleep_sessions = sorted(
        (sleep_session_resp.get("data") or []),
        key=lambda r: r.get("bedtime_end") or r.get("day") or "",
        reverse=True,
    )
    candidates = [
        time.strftime("%Y-%m-%d", time.localtime(time.time() - i * 86400)) for i in range(8)
    ]

    # Giorno principale: il più recente con sleep o readiness
    main_day = None
    for candidate in candidates:
        if sleep_rows.get(candidate) or readiness_rows.get(candidate):
            main_day = candidate
            break
    if not main_day:
        return {"ok": False, "day": today, "error": "dati Oura non trovati negli ultimi 7 giorni"}

    sleep_data = sleep_rows.get(main_day, {})
    readiness_data = readiness_rows.get(main_day, {})
    # Stress e attività dal più recente disponibile
    activity_data = {}
    stress_data = {}
    for candidate in candidates:
        if not activity_data and activity_rows.get(candidate):
            activity_data = activity_rows.get(candidate)
        if not stress_data and stress_rows.get(candidate):
            stress_data = stress_rows.get(candidate)
        if activity_data and stress_data:
            break

    # Trova la sessione di sonno piu lunga entro +/- 1 giorno dal main_day
    prev_day = time.strftime(
        "%Y-%m-%d", time.localtime(time.mktime(time.strptime(main_day, "%Y-%m-%d")) - 86400)
    )
    matching = [s for s in sleep_sessions if s.get("day", "") in (main_day, prev_day)]
    session = max(matching, key=lambda s: s.get("total_sleep_duration") or 0, default=None)
    if session:
        sleep_data = {
            **sleep_data,
            "total_sleep_duration": session.get("total_sleep_duration"),
            "deep_sleep_duration": session.get("deep_sleep_duration"),
            "rem_sleep_duration": session.get("rem_sleep_duration"),
            "light_sleep_duration": session.get("light_sleep_duration"),
            "awake_time": session.get("awake_time"),
            "time_in_bed": session.get("time_in_bed"),
            "latency": session.get("latency"),
            "efficiency": session.get("efficiency"),
            "restlessness": session.get("restlessness"),
            "_selected_sleep_session": session,
        }
    return {
        "ok": True,
        "day": main_day,
        "data": make_payload(sleep_data, readiness_data, activity_data, stress_data, main_day),
        "api_status": api_status,
        **token_status(),
    }
