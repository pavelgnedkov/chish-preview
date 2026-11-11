#!/usr/bin/env python3
"""Выкладка chish.ru на Timeweb: качает превью по списку файлов, делает боевую версию
(make_prod.py) и кладёт в public_html (старое содержимое -> public_html.bak-<время>)."""
import os, sys, time, shutil, urllib.request, urllib.parse, subprocess, concurrent.futures as cf
RAW = "https://raw.githubusercontent.com/pavelgnedkov/chish-preview/main/"
BASE = "https://pavelgnedkov.github.io/chish-preview/"
H = os.path.expanduser("~")
dst = sys.argv[1] if len(sys.argv) > 1 else next(
    (p for p in (f"{H}/chish.ru/public_html", f"{H}/public_html") if os.path.isdir(p)), None)
if not dst:
    sys.exit("Не нашёл папку сайта. Запусти: python3 deploy.py /путь/к/public_html")
work = f"{H}/chish-deploy"; src = f"{work}/src"; out = f"{work}/prod"
shutil.rmtree(work, ignore_errors=True); os.makedirs(src)
get = lambda u: urllib.request.urlopen(u, timeout=120).read()
open(f"{work}/make_prod.py", "wb").write(get(RAW + "make_prod.py"))
files = get(RAW + "filelist.txt").decode().split("\n")
files = [f for f in files if f]
def dl(rel):
    p = os.path.join(src, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    for i in range(4):
        try:
            open(p, "wb").write(get(BASE + urllib.parse.quote(rel))); return None
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    return f"{rel}: {err}"
with cf.ThreadPoolExecutor(8) as ex:
    errs = [e for e in ex.map(dl, files) if e]
print(f"скачано {len(files)-len(errs)}/{len(files)}")
if errs:
    print("\n".join(errs[:20])); sys.exit("Есть ошибки скачивания — сайт НЕ тронут, запусти ещё раз.")
subprocess.check_call([sys.executable, f"{work}/make_prod.py", src, out])
bak = f"{dst}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
os.path.isdir(dst) and os.rename(dst, bak); shutil.move(out, dst); shutil.rmtree(work, ignore_errors=True)
print(f"ГОТОВО: сайт в {dst}, старое содержимое в {bak}")
