#!/usr/bin/env python3
"""Patch a TL JSON schema (core.telegram.org/schema/json format, used by Telegram Web K) with blue_tag.tl."""
import json, re, sys, pathlib
here = pathlib.Path(__file__).parent
def signed(h):
    v = int(h, 16); return str(v - (1 << 32) if v > 0x7fffffff else v)
def parse(line, is_method):
    head, rest = line.rstrip(';').split(' ', 1)
    name, cid = head.split('#')
    args, typ = rest.rsplit(' = ', 1)
    params = [{'name': n, 'type': t} for n, t in (a.split(':', 1) for a in args.split())]
    e = {'id': signed(cid), ('method' if is_method else 'predicate'): name, 'params': params, 'type': typ}
    return e
entries = []; is_method = False
for l in (here / 'blue_tag.tl').read_text().splitlines():
    l = l.strip()
    if l == '---functions---': is_method = True; continue
    if '#' in l and not l.startswith('//'): entries.append((is_method, parse(l, is_method)))
path = pathlib.Path(sys.argv[1]); text = path.read_text()
api_at = text.index('"API"')
def find_obj(text, key, name, start):
    m = re.compile(r'\{"id":"-?\d+","%s":"%s",' % (key, re.escape(name))).search(text, start)
    if not m: return None
    depth = 0
    for i in range(m.start(), len(text)):
        depth += {'{': 1, '}': -1}.get(text[i], 0)
        if depth == 0: return m.start(), i + 1
def list_end(text, key, start):
    i = text.index('"%s":[' % key, start) + len(key) + 4; depth = 1
    while depth:
        c = text[i]; depth += {'[': 1, ']': -1}.get(c, 0); i += 1
    return i - 1
for is_method, e in entries:
    key, nk = ('methods', 'method') if is_method else ('constructors', 'predicate')
    js = json.dumps(e, ensure_ascii=False, separators=(',', ':'))
    span = find_obj(text, nk, e[nk], api_at)
    if span: text = text[:span[0]] + js + text[span[1]:]
    else:
        end = list_end(text, key, api_at); text = text[:end] + ',' + js + text[end:]
json.loads(text)
path.write_text(text)
print('patched', path, len(entries))
