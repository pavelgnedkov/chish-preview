#!/usr/bin/env python3
"""Боевая версия для chish.ru (Timeweb): адреса от корня, индексация открыта,
служебные пометки превью убраны, .htaccess с 301-переадресацией и https."""
import os, re, shutil, sys

SRC, DST = sys.argv[1], sys.argv[2]
shutil.copytree(SRC, DST)
TEXT = (".html", ".css", ".js", ".xml", ".txt", ".json")
MARKS = [re.compile(r'<span class="sv-(?:todo|draft|miss)">.*?</span>', re.S),
         re.compile(r'<p class="sv-banner">.*?</p>', re.S),
         re.compile(r'<meta[^>]*\bname="robots"[^>]*>|<meta[^>]*content="noindex[^"]*"[^>]*>')]
n = 0
for dp, _, fns in os.walk(DST):
    for f in fns:
        if not f.endswith(TEXT):
            continue
        p = os.path.join(dp, f)
        t = open(p, encoding="utf-8", errors="replace").read()
        o = t
        t = t.replace("/chish-preview/", "/").replace("/chish-preview#", "/#").replace("\\/chish-preview\\/", "\\/").replace('"/chish-preview"', '"/"')
        if f.endswith(".html"):
            for r in MARKS:
                t = r.sub("", t)
        if t != o:
            open(p, "w", encoding="utf-8").write(t)
            n += 1
for junk in ("report.txt", "sveden/status.json", ".nojekyll"):
    try:
        os.remove(os.path.join(DST, junk))
    except FileNotFoundError:
        pass
open(os.path.join(DST, "robots.txt"), "w").write("User-agent: *\nAllow: /\n")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OLD = {
    "svedeniya-o-shkole": "common", "osnovnye-svedeniya": "struct", "dokumenty": "document", "obrazovanie": "education",
    "obrazovatelnye-standarty": "eduStandarts", "rukovodstvo-pedagogicheskij-sostav": "managers",
    "materialno-tehnicheskoe-obespechenie-i-osnashhennost-obrazovatelnogo": "objects", "o-shkole/dostupnaya-sreda": "objects",
    "platnye-obrazovatelnye-uslugi": "paid_edu", "finansovo-hozyajstvennaya-deyatelnost": "budget",
    "vakantnye-mesta-dlya-priema-perevoda": "vacant", "stipendii-i-inye-vidy-materialnoj-podderzhki": "grants",
    "o-shkole/mezhdunarodnoe-sotrudnichestvo": "inter", "menyu": "catering",
}
rules = "\n".join(f"RewriteRule ^{re.escape(o)}/?$ /sveden/{s}/ [R=301,L]" for o, s in OLD.items())
open(os.path.join(DST, ".htaccess"), "w").write(
    "AddDefaultCharset UTF-8\nDirectoryIndex index.html\nErrorDocument 404 /404.html\n"
    "RewriteEngine On\n"
    "RewriteCond %{HTTPS} off\nRewriteRule ^(.*)$ https://chish.ru/$1 [R=301,L]\n"
    "RewriteCond %{HTTP_HOST} ^www\\.chish\\.ru$ [NC]\nRewriteRule ^(.*)$ https://chish.ru/$1 [R=301,L]\n"
    + rules + "\n")
print("prod files changed:", n)
