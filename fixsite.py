#!/usr/bin/env python3
"""Ускорение и починка chish.ru прямо на хостинге: python3 fixsite.py ~/public_html
- локальный jQuery вместо Google, убраны Google Fonts, emoji, ссылки на несуществующие файлы WP;
- лёгкое фоновое видео, QR-код НОКО, рабочая отправка форм (send.php);
- пережатие больших фото (оригиналы -> ~/img-orig/)."""
import os, re, sys, glob, shutil, subprocess, urllib.request, urllib.parse
ROOT = os.path.abspath(os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/public_html"))
KIT = sys.argv[2] if len(sys.argv) > 2 else "https://raw.githubusercontent.com/pavelgnedkov/chish-preview/main/fixkit/"
ORIG = os.path.expanduser("~/img-orig")
os.chdir(ROOT)

def kit(name):
    if KIT.startswith("http"):
        return urllib.request.urlopen(KIT + name, timeout=120).read()
    return open(os.path.join(KIT, name), "rb").read()

def put(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "wb").write(data)

# 1. файлы из набора
JQ = "/wp-content/themes/chish-new/markup/libs/jquery-3.5.1.min.js"
FILES = {
    JQ: "jquery-3.5.1.min.js",
    "/wp-content/plugins/jquery-updater/js/jquery-3.3.1.min.js": "jquery-3.3.1.min.js",
    "/wp-content/plugins/jquery-updater/js/jquery-migrate-3.0.0.min.js": "jquery-migrate-3.0.0.min.js",
    "/wp-content/uploads/hero-bg-v2.mp4": "hero-bg-v2.mp4",
    "/wp-content/uploads/hero-poster-v2.jpg": "hero-poster-v2.jpg",
    "/wp-content/uploads/2026/03/Qr-kod-NOKO.png": "Qr-kod-NOKO.png",
    "/wp-content/themes/chish-new/markup/img/icons/border.svg": "border.svg",
    "/wp-content/themes/chish-new/markup/js/form-send.js": "form-send.js",
    "/send.php": "send.php",
}
for miss, src in {"/wp-content/uploads/2021/11/house1.svg": "house.svg", "/wp-content/uploads/2021/11/house2.svg": "house.svg",
                  "/wp-content/themes/chish-new/markup/img/icons/vk1.svg": "vk1.svg"}.items():
    if not os.path.isfile(miss.lstrip("/")):
        FILES[miss] = src
for dst, src in FILES.items():
    put(dst.lstrip("/"), kit(src))
print("файлы набора: ок")

# 2. правка HTML
def exists(url):
    p = urllib.parse.unquote(url.split("?")[0].split("#")[0]).lstrip("/")
    if not p:
        return True
    return os.path.isfile(p) or os.path.isfile(os.path.join(p, "index.html"))

REMOVE = [
    re.compile(r"<script[^>]*>\s*window\._wpemojiSettings.*?</script>\s*", re.S),
    re.compile(r"<style[^>]*>\s*img\.wp-smiley.*?</style>\s*", re.S),
    re.compile(r"<link[^>]*(?:dns-prefetch|preconnect)[^>]*>\s*"),
    re.compile(r"<link[^>]*fonts\.googleapis\.com[^>]*>\s*"),
    re.compile(r"<link[^>]*(?:api\.w\.org|EditURI|wlwmanifest|oembed)[^>]*>\s*"),
    re.compile(r"<script[^>]*email-decode\.min\.js[^>]*>\s*</script>\s*"),
]
TAG = re.compile(r"""<script[^>]*\bsrc=['"](/[^'"]+)['"][^>]*>\s*</script>\s*|<link[^>]*\bhref=['"](/[^'"]+\.css[^'"]*)['"][^>]*>\s*""")
GAL = re.compile(r"""(/wp-content/uploads/photo-gallery/imported_from_media_libray/)(?!thumb/)([^'"?\s>]+)""")
IMG = re.compile(r"""<img[^>]*\bsrc=['"](/(?!/)[^'"]+)['"][^>]*>""")
FORM_JS = '<script src="/wp-content/themes/chish-new/markup/js/form-send.js?v=1" defer></script>'
changed = 0
for f in glob.glob("**/*.html", recursive=True):
    t = open(f, encoding="utf-8", errors="replace").read()
    o = t
    t = re.sub(r"""((?:src|href|srcset)=['"])(?://|(?=wp-content/))(wp-content/)""", r"\1/\2", t)
    t = re.sub(r"https://ajax\.googleapis\.com/ajax/libs/jquery/3\.5\.1/jquery\.min\.js(\?ver=\d+)?", JQ, t)
    for r in REMOVE:
        t = r.sub("", t)
    t = TAG.sub(lambda m: m.group(0) if exists(m.group(1) or m.group(2)) or (m.group(1) or m.group(2)).startswith("//") else "", t)
    def gal(m):
        full = m.group(1) + m.group(2)
        thumb = m.group(1) + "thumb/" + m.group(2)
        return full if exists(full) or not exists(thumb) else thumb
    t = GAL.sub(gal, t)
    t = IMG.sub(lambda m: m.group(0) if exists(m.group(1)) else "", t)
    t = t.replace("/wp-content/uploads/hero-bg.mp4", "/wp-content/uploads/hero-bg-v2.mp4").replace(
        "/wp-content/uploads/hero-poster.jpg", "/wp-content/uploads/hero-poster-v2.jpg")
    if "wpcf7-form" in t and "form-send.js" not in t:
        t = t.replace("</body>", FORM_JS + "\n</body>", 1)
    if t != o:
        open(f, "w", encoding="utf-8").write(t)
        changed += 1
print("страниц исправлено:", changed)

# 3. пережатие фото
try:
    from PIL import Image
except ImportError:
    subprocess.call([sys.executable, "-m", "pip", "install", "--user", "-q", "pillow"])
    import site, importlib
    sys.path.append(site.getusersitepackages()); importlib.invalidate_caches()
    from PIL import Image
before = after = n = 0
for f in glob.glob("wp-content/uploads/**/*", recursive=True):
    ext = f.lower().rsplit(".", 1)[-1]
    if ext not in ("jpg", "jpeg", "png") or os.path.getsize(f) < 150_000:
        continue
    try:
        im = Image.open(f); im.load()
    except Exception:
        continue
    size0 = os.path.getsize(f)
    im.thumbnail((1920, 1920))
    tmp = f + ".tmp"
    if ext == "png":
        if im.mode == "P":
            im = im.convert("RGBA")
        im.save(tmp, "PNG", optimize=True)
    else:
        im.convert("RGB").save(tmp, "JPEG", quality=80, optimize=True, progressive=True)
    if os.path.getsize(tmp) < size0 * 0.9:
        keep = os.path.join(ORIG, f)
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        if not os.path.exists(keep):
            shutil.copy2(f, keep)
        os.replace(tmp, f)
        before += size0; after += os.path.getsize(f); n += 1
    else:
        os.remove(tmp)
print(f"фото пережато: {n}, было {before/1048576:.0f} МБ -> стало {after/1048576:.0f} МБ (оригиналы в {ORIG})")
if os.path.exists("wp-content/uploads/hero-bg.mp4"):
    os.remove("wp-content/uploads/hero-bg.mp4")
print("ГОТОВО")
