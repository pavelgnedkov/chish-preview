#!/usr/bin/env python3
"""Собирает статическую копию chish.ru из web.archive.org для GitHub Pages.

Берёт последний снимок каждой страницы/файла до SNAP, заменяет заглушки
регистратора ранними живыми снимками, переписывает ссылки под PREFIX,
ставит noindex. Результат — папка site/ и report.txt.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

SNAP = "20260711143427"
PREFIX = os.environ.get("PREFIX", "/chish-preview")
OUT = "site"
WB = "https://web.archive.org"
STUB = "домена истек"
MAX_FILE = 95 * 1024 * 1024
SKIP = re.compile(r"^/(wp-json|xmlrpc|wp-login|wp-admin|wp-cron|\.well-known)|/feed/?$|/embed/?$|/wp-json/", re.I)
TEXT_MIME = re.compile(r"text/html|text/css|javascript|xml|json", re.I)


def get(url, timeout=120, tries=5):
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "chish-preview-builder"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            code = getattr(e, "code", None)
            if code == 404:
                break
            time.sleep(3 * (a + 1))
    raise last


def cdx(params):
    q = urllib.parse.urlencode(params, safe="*:")
    data = get(f"{WB}/cdx/search/cdx?{q}", timeout=300, tries=8)
    rows = json.loads(data or b"[]")
    return rows[1:] if rows else []


def local_name(path, mime):
    p = urllib.parse.unquote(path)
    if p.endswith("/"):
        p += "index.html"
    elif "html" in mime and not re.search(r"\.[A-Za-z0-9]{2,5}$", p.rsplit("/", 1)[-1]):
        p += "/index.html"
    p = p.lstrip("/")
    return os.path.normpath(p) if p else "index.html"


ABS = re.compile(r"(?:https?:)?(?:\\?/\\?/)(?:www\.)?chish\.ru(?::80)?", re.I)
ROOT_ATTR = re.compile(r"""(\b(?:href|src|action|data-src|data-href|poster|content)\s*=\s*["'])/(?!/)""", re.I)
ROOT_CSS = re.compile(r"""(url\(\s*["']?)/(?!/)""", re.I)


def rewrite(text, is_html):
    # сначала ссылки от корня, потом абсолютные — чтобы не задвоить префикс
    text = ROOT_ATTR.sub(lambda m: m.group(1) + PREFIX + "/", text)
    text = ROOT_CSS.sub(lambda m: m.group(1) + PREFIX + "/", text)
    text = ABS.sub(lambda m: PREFIX.replace("/", "\\/") if "\\" in m.group(0) else PREFIX, text)
    if is_html:
        text = re.sub(r"<meta[^>]+name=[\"']robots[\"'][^>]*>", "", text, flags=re.I)
        text = re.sub(r"<link[^>]+rel=[\"']canonical[\"'][^>]*>", "", text, flags=re.I)
        text, n = re.subn(r"(<head[^>]*>)", r'\1<meta name="robots" content="noindex, nofollow, noarchive">', text, count=1, flags=re.I)
        if not n:
            text = '<meta name="robots" content="noindex, nofollow, noarchive">' + text
    return text


def decode(b):
    for enc in ("utf-8", "cp1251"):
        try:
            return b.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return b.decode("utf-8", "replace"), "utf-8"


def earlier_live(orig):
    caps = cdx({"url": orig, "to": SNAP, "filter": "statuscode:200", "fl": "timestamp,original", "output": "json"})
    for ts, o in reversed(caps[-40:]):
        try:
            b = get(f"{WB}/web/{ts}id_/{o}")
        except Exception:  # noqa: BLE001
            continue
        if STUB not in decode(b)[0][:80000]:
            return b, ts
    return None, None


def main():
    rows = []
    for host in ("chish.ru/*", "www.chish.ru/*"):
        try:
            rows += cdx({"url": host, "to": SNAP, "filter": "statuscode:200", "fl": "timestamp,original,mimetype", "output": "json"})
        except Exception as e:  # noqa: BLE001
            print("cdx fail", host, e, file=sys.stderr)
    best = {}
    for ts, orig, mime in rows:
        try:
            u = urllib.parse.urlsplit(orig)
        except ValueError:
            continue
        if u.query or SKIP.search(u.path or "/"):
            continue
        name = local_name(u.path or "/", mime)
        if name not in best or ts > best[name][0]:
            best[name] = (ts, orig, mime)
    print("to download:", len(best), flush=True)

    stats = {"ok": 0, "fail": [], "stub_fixed": [], "stub_left": [], "big": []}

    def work(item):
        name, (ts, orig, mime) = item
        try:
            b = get(f"{WB}/web/{ts}id_/{orig}")
        except Exception as e:  # noqa: BLE001
            stats["fail"].append(f"{name} ({e})")
            return
        if len(b) > MAX_FILE:
            stats["big"].append(name)
            return
        is_html = "html" in mime or name.endswith(".html")
        if TEXT_MIME.search(mime) or name.endswith((".html", ".css", ".js")):
            text, enc = decode(b)
            if is_html and STUB in text[:80000]:
                nb, nts = earlier_live(orig)
                if nb is None:
                    stats["stub_left"].append(name)
                else:
                    text, enc = decode(nb)
                    stats["stub_fixed"].append(f"{name} <- {nts}")
            b = rewrite(text, is_html).encode(enc, "replace")
        dest = os.path.join(OUT, name)
        try:
            os.makedirs(os.path.dirname(dest) or OUT, exist_ok=True)
            if os.path.isdir(dest):
                dest = os.path.join(dest, "index.html")
            with open(dest, "wb") as f:
                f.write(b)
            stats["ok"] += 1
        except OSError as e:
            stats["fail"].append(f"{name} (write: {e})")

    items = sorted(best.items(), key=lambda kv: (0 if "html" in kv[1][2] else 1, kv[0]))
    done = 0
    with ThreadPoolExecutor(6) as ex:
        for _ in ex.map(work, items):
            done += 1
            if done % 100 == 0:
                print(f"{done}/{len(items)} ok={stats['ok']} fail={len(stats['fail'])}", flush=True)

    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nDisallow: /\n")
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    if not os.path.exists(os.path.join(OUT, "index.html")):
        with open(os.path.join(OUT, "index.html"), "w") as f:
            f.write("<meta name=robots content=noindex><p>Главная не скачалась</p>")

    rep = [f"snapshot<= {SNAP}", f"candidates {len(best)}", f"saved {stats['ok']}",
           f"failed {len(stats['fail'])}", f"stubs fixed {len(stats['stub_fixed'])}",
           f"stubs left {len(stats['stub_left'])}", f"skipped >95MB {len(stats['big'])}", ""]
    for k in ("stub_fixed", "stub_left", "big", "fail"):
        rep.append(f"== {k}")
        rep += stats[k]
    with open(os.path.join(OUT, "report.txt"), "w") as f:
        f.write("\n".join(rep))
    print("\n".join(rep[:8]))


if __name__ == "__main__":
    main()
