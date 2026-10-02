#!/usr/bin/env python3
"""Deliberately vulnerable service for an isolated, authorized home lab only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import argparse
import html
import os
import subprocess

PAGE = """<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Relay 08 // Diagnostics</title><link rel='stylesheet' href='/style.css'></head><body><header><b>R//08</b><span>REMOTE SIGNAL RELAY</span><i>DEGRADED</i></header><main><section><p class='eyebrow'>NODE DIAGNOSTICS</p><h1>Can you hear<br>the signal?</h1><p class='lede'>Relay 08 has lost contact with the control room. Test an address to trace the fault.</p><form action='/diagnose' method='get'><label for='host'>TARGET ADDRESS</label><div><input id='host' name='host' value='127.0.0.1' autocomplete='off'><button>RUN TEST</button></div></form><p class='hint'>Expected input: an IPv4 address</p></section><aside><div class='scope'></div><dl><dt>NODE</dt><dd>RLY-08</dd><dt>OPERATOR</dt><dd>operator</dd><dt>HTTP</dt><dd>8080</dd></dl></aside></main><!-- Maintenance note: diagnostics are run by the shell. Credentials backup: /home/operator/relay/ssh-code.txt --><footer>RELAY SOFTWARE 0.8.3 // INTERNAL NETWORK ONLY</footer></body></html>"""

CSS = """:root{--black:#10140f;--cream:#ece9dc;--green:#c8ff39;--orange:#ff6448}*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--black);font-family:Arial,sans-serif}header{display:flex;align-items:center;gap:24px;padding:18px 5vw;border-bottom:1px solid}header b{background:var(--black);color:var(--green);padding:8px}header span{font-size:.7rem;font-weight:900;letter-spacing:.16em}header i{margin-left:auto;color:#c23d29;font:800 .7rem monospace}main{min-height:82vh;display:grid;grid-template-columns:1.4fr .6fr;padding:9vw;gap:8vw}h1{font-size:clamp(4rem,9vw,8rem);line-height:.82;letter-spacing:-.08em;margin:.18em 0}.eyebrow,label{font:800 .72rem monospace;letter-spacing:.16em}.lede{font-size:1.2rem;max-width:620px;color:#596056}form{margin-top:50px;max-width:670px}form div{display:flex;margin-top:9px}input{min-width:0;flex:1;padding:17px;border:2px solid;background:white;font:1rem monospace}button{border:0;background:var(--black);color:var(--green);padding:0 24px;font-weight:900}.hint{font:700 .7rem monospace;color:#73796f}.scope{width:100%;aspect-ratio:1;border:1px solid;border-radius:50%;background:repeating-radial-gradient(circle,transparent 0 20%,#10140f22 21%),conic-gradient(transparent 70%,#c8ff3988);animation:spin 5s linear infinite}@keyframes spin{to{transform:rotate(1turn)}}dl{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid;margin-top:35px}dt,dd{padding:12px 0;border-bottom:1px solid;margin:0;font:700 .7rem monospace}dd{text-align:right}footer{padding:23px 5vw;background:var(--black);color:#929a8e;font:700 .65rem monospace;letter-spacing:.12em}.result{white-space:pre-wrap;background:#172017;color:#c8ff39;padding:25px;font:14px/1.6 monospace;overflow:auto}.back{color:inherit;font-weight:bold}@media(max-width:700px){main{grid-template-columns:1fr;padding:70px 24px}aside{max-width:260px}form div{display:block}button{width:100%;padding:17px}}"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_page(PAGE)
        elif parsed.path == "/style.css":
            self.send_bytes(CSS.encode(), "text/css; charset=utf-8")
        elif parsed.path == "/diagnose":
            target = parse_qs(parsed.query).get("host", ["127.0.0.1"])[0]
            # INTENTIONALLY VULNERABLE: lesson target for an isolated lab.
            try:
                result = subprocess.run(
                    f"ping -c 1 -W 1 {target}", shell=True, capture_output=True,
                    text=True, timeout=4, env={"PATH": "/usr/bin:/bin"}
                )
                output = (result.stdout + result.stderr)[:12000]
            except subprocess.TimeoutExpired:
                output = "Diagnostic timed out."
            body = PAGE.replace("</section>", f"<div class='result'>{html.escape(output)}</div><p><a class='back' href='/'>← New test</a></p></section>")
            self.send_page(body)
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        print(f"[relay] {self.address_string()} - {fmt % args}")

    def send_page(self, body):
        self.send_bytes(body.encode(), "text/html; charset=utf-8")

    def send_bytes(self, data, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Lab-Warning", "Intentionally vulnerable; isolated networks only")
        self.end_headers(); self.wfile.write(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intentionally vulnerable Relay 08 lab")
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    # Linux lab guard; the getattr fallback also lets maintainers smoke-test on Windows.
    if getattr(os, "geteuid", lambda: -1)() == 0:
        raise SystemExit("Refusing to run as root. Start this service as the operator user.")
    print(f"Relay 08 listening on http://{args.bind}:{args.port} (LAB USE ONLY)")
    ThreadingHTTPServer((args.bind, args.port), Handler).serve_forever()
