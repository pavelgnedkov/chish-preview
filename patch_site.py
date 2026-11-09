#!/usr/bin/env python3
"""Точечные правки готовой сборки превью.

1. Подменяет страницы, у которых в архиве есть более новые живые снимки
   (после даты основной сборки), — актуальные версии раздела «Сведения».
2. Возвращает файлы, которые не скачались в основной сборке, но есть в архиве.
3. Раскодирует e-mail, спрятанные Cloudflare (data-cfemail), — чтобы адреса
   были видны без JavaScript и читались машинно (п. 23, 26 приказа № 1493).
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

SITE = sys.argv[1]
WB = build.WB

NEWER_PAGES = {
    "obrazovanie/index.html": ("20260831032102", "http://chish.ru/obrazovanie/"),
    "platnye-obrazovatelnye-uslugi/index.html": ("20260831023050", "http://chish.ru/platnye-obrazovatelnye-uslugi/"),
    "finansovo-hozyajstvennaya-deyatelnost/index.html": ("20260831100804", "http://chish.ru/finansovo-hozyajstvennaya-deyatelnost/"),
    "olimpiady/index.html": ("20260831060618", "http://chish.ru/olimpiady/"),
}
EXTRA_FILES = {
    "wp-content/uploads/2024/01/Turaeva2.jpg": ("20240729220022", "http://chish.ru/wp-content/uploads/2024/01/Turaeva2.jpg"),
}

for name, (ts, url) in NEWER_PAGES.items():
    try:
        b = build.get(f"{WB}/web/{ts}id_/{url}")
    except Exception as e:  # noqa: BLE001
        print("page fail", name, e)
        continue
    text, enc = build.decode(b)
    if build.STUB in text[:80000]:
        print("page is stub, skip", name)
        continue
    dest = os.path.join(SITE, name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(build.rewrite(text, True).encode(enc, "replace"))
    print("page updated", name, ts)

for name, (ts, url) in EXTRA_FILES.items():
    try:
        b = build.get(f"{WB}/web/{ts}id_/{url}")
        dest = os.path.join(SITE, name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(b)
        print("file restored", name, len(b))
    except Exception as e:  # noqa: BLE001
        print("file fail", name, e)


def cf_decode(h):
    key = int(h[:2], 16)
    return "".join(chr(int(h[i:i + 2], 16) ^ key) for i in range(2, len(h), 2))


A_RE = re.compile(r'href=(["\'])[^"\']*/cdn-cgi/l/email-protection#([0-9a-fA-F]+)\1')
SPAN_RE = re.compile(r'<(span|a)[^>]*data-cfemail=["\']([0-9a-fA-F]+)["\'][^>]*>.*?</\1>', re.S)
fixed_pages = fixed = 0
for dp, _, fns in os.walk(SITE):
    for n in fns:
        if not n.endswith(".html"):
            continue
        p = os.path.join(dp, n)
        html = open(p, encoding="utf-8", errors="replace").read()
        if "email-protection" not in html and "data-cfemail" not in html:
            continue
        new, c1 = A_RE.subn(lambda m: f"href={m.group(1)}mailto:{cf_decode(m.group(2))}{m.group(1)}", html)
        new, c2 = SPAN_RE.subn(lambda m: cf_decode(m.group(2)), new)
        if c1 or c2:
            open(p, "w", encoding="utf-8").write(new)
            fixed_pages += 1
            fixed += c1 + c2
print(f"cloudflare emails decoded: {fixed} on {fixed_pages} pages")
