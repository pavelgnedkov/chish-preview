#!/usr/bin/env python3
"""Чистит собранный сайт перед публикацией на GitHub Pages.

Pages плохо переносит пустые файлы-«каталоги», имена с управляющими
символами, '?', '#', ':' и очень длинные пути. Такие файлы удаляем
и печатаем список, остальное не трогаем.
"""
import os, sys

root = sys.argv[1]
BAD = set('?#:*"<>|\\') | {chr(c) for c in range(32)}
removed = []
for dp, dns, fns in os.walk(root, topdown=False):
    for n in fns:
        p = os.path.join(dp, n)
        rel = os.path.relpath(p, root)
        if os.path.islink(p) or any(ch in BAD for ch in rel) or len(rel.encode()) > 400 or os.path.getsize(p) > 95 * 1024 * 1024:
            os.remove(p)
            removed.append(rel)
    for n in dns:
        p = os.path.join(dp, n)
        if os.path.islink(p):
            os.remove(p)
            removed.append(os.path.relpath(p, root) + "/ (link)")
        elif not os.listdir(p):
            os.rmdir(p)
for p, _, fns in os.walk(root):
    for n in fns:
        os.chmod(os.path.join(p, n), 0o644)
    os.chmod(p, 0o755)
print("removed:", len(removed))
for r in removed[:50]:
    print("  ", r)
