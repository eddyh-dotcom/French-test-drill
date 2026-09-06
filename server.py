#!/usr/bin/env python3
"""Local server for the French tense drill.

Serves the static app, persists progress.json, and (optionally) proxies
item generation to the Anthropic API when ANTHROPIC_API_KEY is set.
No dependencies beyond the standard library.
"""
import json
import os
import threading
import urllib.request
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
# 8642 is deliberately distinct from Ben's other local apps
# (pdf-search → 8123, library-browser → 4242)
PORT = int(os.environ.get("PORT", "8642"))

PAIR_BRIEFS = {
    "imp-cond": (
        "imparfait vs conditionnel présent. Mix cues: si+imparfait protasis forcing "
        "conditionnel in the main clause, future-in-the-past after past reporting verbs "
        "(il a dit que...), habitual-past markers (autrefois, chaque matin, quand j'étais "
        "jeune) forcing imparfait, and si-clauses where the blank IS the protasis (imparfait)."
    ),
    "pc-imp": (
        "passé composé vs imparfait. Mix cues: punctual/completed events (soudain, hier, "
        "puis, bounded durations like 'pendant dix ans') vs background states, descriptions, "
        "habits, and interrupted ongoing actions."
    ),
    "cond-fut": (
        "conditionnel présent vs futur simple. Mix cues: si+présent forcing futur, "
        "quand/dès que + futur, present vs past reporting verbs (il dit que / il a dit que), "
        "and si+imparfait forcing conditionnel."
    ),
    "subj": (
        "subjonctif présent vs indicatif. Mix real subjonctif triggers (il faut que, bien que, "
        "pour que, avant que, douter que, ne pas penser que) with indicative traps "
        "(affirmative penser que, il est certain que)."
    ),
}


def generate_items(api_key, pair):
    brief = PAIR_BRIEFS.get(pair, PAIR_BRIEFS["imp-cond"])
    prompt = (
        "Generate 5 French fill-in-the-blank drill items testing the tense contrast: "
        + brief
        + "\n\nRules:\n"
        "- Each item is one natural French sentence with exactly one blank written as ___ .\n"
        "- The contextual cue must force exactly one tense choice; avoid ambiguous items.\n"
        "- Prefer irregular verbs: être, avoir, aller, venir, faire, vouloir, pouvoir, "
        "devoir, savoir, voir, prendre.\n"
        "- If the blank follows an elided pronoun, write the elision into the sentence "
        "(e.g. \"j'___\").\n"
        "- 'why' is ONE short grammatical sentence naming the trigger.\n\n"
        "Return ONLY a JSON array, each element exactly:\n"
        '{"sentence": "... ___ ...", "infinitive": "venir", "answer": "viendrais", '
        '"alt": [], "tense": "conditionnel présent", "pair": "' + pair + '", '
        '"why": "..."}'
    )
    body = json.dumps({
        "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = "".join(block.get("text", "") for block in data.get("content", []))
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("no JSON array in model response")
    items = json.loads(text[start:end + 1])
    valid = []
    for it in items:
        if not isinstance(it, dict):
            continue
        if "___" not in it.get("sentence", "") or not it.get("answer"):
            continue
        it.setdefault("alt", [])
        it.setdefault("tense", "")
        it.setdefault("why", "")
        it["pair"] = pair
        valid.append(it)
    if not valid:
        raise ValueError("model returned no usable items")
    return valid


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def _send_json(self, obj, code=200):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json({"error": "bad json"}, 400)
            return

        if self.path == "/save":
            with open(os.path.join(ROOT, "progress.json"), "w") as f:
                json.dump(body, f, ensure_ascii=False, indent=1)
            self._send_json({"ok": True})
        elif self.path == "/generate":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                self._send_json({"error": "ANTHROPIC_API_KEY not set"}, 503)
                return
            try:
                self._send_json({"items": generate_items(api_key, body.get("pair", "imp-cond"))})
            except Exception as exc:
                self._send_json({"error": str(exc)}, 502)
        else:
            self._send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    ai = "on" if os.environ.get("ANTHROPIC_API_KEY") else "off (set ANTHROPIC_API_KEY to enable)"
    server = None
    for port in range(PORT, PORT + 10):
        try:
            server = HTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit(f"no free port in {PORT}-{PORT + 9}")
    if server.server_port != PORT:
        print(f"NOTE: port {PORT} was busy — another app may be running there.")
    url = f"http://localhost:{server.server_port}"
    print(f"French drill → {url}  [AI generation: {ai}]")
    print("Leave this window open while you drill; close it (or Ctrl-C) to stop.")
    if not os.environ.get("NO_BROWSER"):
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
