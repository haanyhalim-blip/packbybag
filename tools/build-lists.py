#!/usr/bin/env python3
"""Builds a page of its own for every ready-made list, every school, and an index of all lists.

Run from the repo root after changing any list in index.html:   python3 tools/build-lists.py
It reads the lists straight out of index.html (TRIPS, CAT, BAGS, BAGOF), writes lists/*.html and
refreshes sitemap.xml. Cloudflare serves lists/rowan.html at packbybag.com/lists/rowan.
"""
import html, json, os, re, datetime, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://packbybag.com"
src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

def js(var):
    return json.loads(re.search(r"var " + var + r" = (.*?);\n", src, re.S).group(1))

CAT, BAGS, BAGOF, TRIPS = js("CAT"), js("BAGS"), js("BAGOF"), js("TRIPS")
VER = re.search(r'<span class="ver">(v\d+)</span>', src).group(1)
e = lambda s: html.escape(str(s), quote=True)
slug = lambda x: re.sub(r"[^a-z0-9]+", "-", x.lower().replace("’", "").replace("'", "")).strip("-")
area_of = {n: a for a, names in CAT.items() for n in names}

def bag(t, n):
    """Same rule as the site: the list's own bag for an item, else the item's usual bag."""
    if n in (t.get("bags") or {}): return t["bags"][n]
    b = BAGOF.get(n) or BAGOF.get(area_of.get(n, ""), "hold")
    if t.get("force") and b == "hold": return t["force"]
    return b

CSS = """
:root{color-scheme:light;--bg:#eef3f4;--card:#fff;--line:#cfdde1;--ink:#182a31;--muted:#5c7079;--main:#1f5f73;--main-deep:#16475a;--wash:#dbeaef;--gold:#e6be55;--gold-deep:#c9971f;--gold-ink:#5c430a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Atkinson Hyperlegible",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:16px;line-height:1.5}
.wrap{max-width:760px;margin:0 auto;padding:0 16px 60px}
header{padding:22px 0 12px;border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.brand{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:1.45rem;color:var(--main);text-decoration:none}
.brand span{color:var(--ink)}
header .home{margin-left:auto;font-size:.9rem;color:var(--main-deep)}
.crumbs{font-size:.85rem;color:var(--muted);margin:14px 0 6px}
.crumbs a{color:var(--main-deep)}
h1{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:1.9rem;line-height:1.15;margin:4px 0 8px;color:var(--main-deep)}
.lead{margin:0 0 14px;color:var(--muted)}
.by{display:flex;align-items:center;gap:12px;margin:0 0 16px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--gold);background:linear-gradient(90deg,#fff6dc,#fffdf6)}
.av{flex:none;width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--gold),var(--gold-deep));color:#fff;font-size:1.45rem;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 2px #fff,0 0 0 3.5px var(--gold)}
.by small{display:block;font-size:.7rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#a67c14}
.by b{font-size:1.05rem;color:var(--gold-ink)}
.go{display:block;text-align:center;background:var(--main);color:#fff;text-decoration:none;font-weight:700;font-size:1.05rem;padding:14px 16px;border-radius:12px;margin:0 0 8px}
.go:hover{background:var(--main-deep)}
.acts{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;font-size:.9rem;margin:0 0 20px}
.acts a,.acts button{color:var(--main-deep);background:none;border:0;padding:0;font:inherit;text-decoration:underline;text-underline-offset:3px;cursor:pointer}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:6px 16px 12px;margin:0 0 14px}
h2{font-size:.8rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--main);margin:14px 0 6px}
h2 small{letter-spacing:0;text-transform:none;font-weight:400;color:var(--muted)}
ul.items{list-style:none;margin:0;padding:0}
ul.items li{display:flex;gap:10px;align-items:center;padding:7px 0;border-top:1px solid var(--line)}
ul.items li:first-child{border-top:0}
ul.items li::before{content:"";flex:none;width:18px;height:18px;border:2px solid var(--main);border-radius:5px}
ul.items li.opt{color:var(--muted)}
ul.items li.opt::before{border-style:dashed;border-color:var(--muted)}
ul.items li.opt em{font-style:normal;font-size:.8rem;margin-left:auto}
.lists{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin:8px 0 18px}
.lists a{display:block;background:var(--card);border:1.5px solid var(--line);border-radius:10px;padding:12px 13px;text-decoration:none;color:var(--ink)}
.lists a.gold{border-color:var(--gold);background:linear-gradient(180deg,#fffaf0,#fff 70%)}
.lists a b{display:block;color:var(--main-deep)}
.lists a small{display:block;font-size:.84rem;color:var(--muted);line-height:1.35;margin-top:3px}
.lists a span{display:block;font-size:.78rem;color:var(--main);font-weight:700;margin-top:5px}
footer{border-top:1px solid var(--line);margin-top:26px;padding-top:14px;font-size:.85rem;color:var(--muted)}
footer a{color:var(--main-deep)}
@media print{header .home,.go,.acts,footer,.crumbs{display:none}body{background:#fff}.card{border:0;padding:0}}
"""

def page(path, title, desc, body, crumbs):
    url = SITE + "/" + path
    cr = " › ".join('<a href="%s">%s</a>' % (e(h), e(t)) if h else e(t) for t, h in crumbs)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#1f5f73">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pack by Bag">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%231f5f73'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Atkinson+Hyperlegible:wght@400;700&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header><a class="brand" href="/">Pack<span>by</span>Bag</a><a class="home" href="/">← PackbyBag home</a></header>
<p class="crumbs">{cr}</p>
{body}
<footer>
<p><a href="/"><b>PackbyBag</b></a> – a packing list sorted by bag, so nothing gets left behind. Free, no account needed.
<a href="/">Start your own list</a> · <a href="/lists/">All ready-made lists</a></p>
<p>From Handy Little Tools – also try <a href="https://listbyaisle.com/">ListbyAisle</a> (a shopping list sorted by aisle), <a href="https://dobytoday.com/">DobyToday</a> (today’s jobs, sorted by when) and <a href="https://dueareset.com/">DueAReset</a> (a page of your own to change a habit). {VER}</p>
</footer>
</div>
<script>
document.addEventListener("click", function(ev){{ var b = ev.target.closest("[data-copy]"); if(!b) return; var u = b.getAttribute("data-copy");
  function done(){{ b.textContent = "Link copied ✓"; setTimeout(function(){{ b.textContent = "Copy link"; }}, 2200); }}
  if(navigator.clipboard) navigator.clipboard.writeText(u).then(done, function(){{ prompt("Copy this link:", u); }}); else prompt("Copy this link:", u); }});
</script>
</body>
</html>
"""

def card(t):
    gold = " gold" if t.get("by") else ""
    by = " · by " + e(t["by"]) if t.get("by") else ""
    return f'<a class="{gold.strip()}" href="/lists/{e(t["slug"])}"><b>{e(t["name"])}</b><small>{e(t["blurb"])}</small><span>{len(t["items"])} things{by}</span></a>'

schools = {}
for t in TRIPS:
    if t.get("named"): schools.setdefault(t.get("school") or t["name"], []).append(t)
school_slug = {s: slug(s) for s in schools}
taken = {t["slug"] for t in TRIPS}
for s, sl in school_slug.items(): assert sl not in taken, "school page would clash with a list page: " + sl

out = os.path.join(ROOT, "lists")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    if f.endswith(".html"): os.remove(os.path.join(out, f))   # only pages this script made
pages = []

for t in TRIPS:
    off = set(t.get("off") or [])
    groups = []
    for b in BAGS:
        its = [n for n in t["items"] if bag(t, n) == b[0]]
        if its: groups.append((b, its))
    body = [f'<h1>{e(t["name"])}</h1><p class="lead">{e(t["blurb"])}</p>']
    if t.get("by"):
        body.append(f'<div class="by"><span class="av" aria-hidden="true">★</span><span><small>A list by</small><b>{e(t["by"])}</b></span></div>')
    link = f'{SITE}/lists/{t["slug"]}'
    body.append(f'<a class="go" href="/#list={e(t["slug"])}">Use this list in PackbyBag →</a>')
    body.append(f'<p class="acts"><button type="button" data-copy="{e(link)}">Copy link</button><a href="https://wa.me/?text={e(urllib.parse.quote(t["name"] + " – " + link))}">Send on WhatsApp</a><a href="javascript:print()">Print</a></p>')
    body.append('<div class="card">')
    for b, its in groups:
        sub = f' <small>– {e(b[2])}</small>' if b[2] else ""
        lis = "".join(f'<li class="opt">{e(n)}<em>if needed</em></li>' if n in off else f"<li>{e(n)}</li>" for n in its)
        body.append(f'<h2>{e(b[1])}{sub}</h2><ul class="items">{lis}</ul>')
    body.append("</div>")
    crumbs = [("PackbyBag", "/"), ("Ready-made lists", "/lists/")]
    if t.get("named"):
        s = t.get("school") or t["name"]
        crumbs.append((s, "/lists/" + school_slug[s]))
        others = [x for x in schools[s] if x is not t]
        if others: body.append(f'<h2>More lists for {e(s)}</h2><div class="lists">' + "".join(card(x) for x in others) + "</div>")
    crumbs.append((t["name"], None))
    desc = f'{t["name"]} packing list: {t["blurb"]} {len(t["items"])} things, sorted by bag. Tick it off on your phone – free, no account.'
    open(os.path.join(out, t["slug"] + ".html"), "w", encoding="utf-8").write(
        page("lists/" + t["slug"], f'{t["name"]} – packing list | PackbyBag', desc, "\n".join(body), crumbs))
    pages.append("lists/" + t["slug"])

for s, ts in schools.items():
    sl = school_slug[s]
    link = f"{SITE}/lists/{sl}"
    area = next((t["area"] for t in ts if t.get("area")), "")
    where = f" in {area}" if area else ""
    body = (f'<h1>{e(s)} packing lists</h1><p class="lead">Ready-made packing lists for {e(s)}{e(where)}, sorted by bag. Open one, untick what you don\'t need, and tick things off as you pack.</p>'
            f'<p class="acts"><button type="button" data-copy="{e(link)}">Copy link to this page</button></p>'
            '<div class="lists">' + "".join(card(t) for t in ts) + "</div>")
    open(os.path.join(out, sl + ".html"), "w", encoding="utf-8").write(
        page("lists/" + sl, f"{s}{' (' + area + ')' if area else ''} packing lists | PackbyBag", f"Ready-made school packing lists for {s}{where}: " + ", ".join(t["name"] for t in ts) + ".", body,
             [("PackbyBag", "/"), ("Ready-made lists", "/lists/"), (s, None)]))
    pages.append("lists/" + sl)

general = [t for t in TRIPS if not t.get("named")]
body = ('<h1>Ready-made packing lists</h1><p class="lead">Start from one of these, untick what you don\'t need, and tick things off as you pack. Everything is sorted by bag.</p>'
        '<h2>Trips, holidays and school bags</h2><div class="lists">' + "".join(card(t) for t in general) + "</div>"
        + "".join(f'<h2>Schools in {e(a)}</h2><div class="lists">' + "".join(
            f'<a class="gold" href="/lists/{school_slug[s]}"><b>{e(s)}</b><span>{len(ts)} list{"s" if len(ts) != 1 else ""}</span></a>' for s, ts in sorted(schools.items()) if (next((t.get("area") for t in ts if t.get("area")), "") or "other areas") == a) + "</div>"
            for a in sorted({next((t.get("area") for t in ts if t.get("area")), "") or "other areas" for ts in schools.values()})))
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(
    page("lists/", "Ready-made packing lists | PackbyBag", "Free ready-made packing lists sorted by bag: holidays, work trips, events, school bags by age and lists for particular schools.", body,
         [("PackbyBag", "/"), ("Ready-made lists", None)]))
pages.insert(0, "lists/")

today = datetime.date.today().isoformat()
urls = [""] + pages
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url>\n    <loc>{SITE}/{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>\n" for u in urls) + "</urlset>\n")
print(f"Built {len(pages)} pages in lists/ and updated sitemap.xml")
