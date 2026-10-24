# -*- coding: utf-8 -*-
"""Fetch ARAM Mayhem HTML and strip ad/redirect scripts for local mirror."""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from fetcher import BASE, CACHE, _get

AD_HOST_BITS = (
    "effectivecpm",
    "doubleclick",
    "googlesyndication",
    "googleadservices",
    "adnxs",
    "adservice",
    "popads",
    "popcash",
    "propeller",
    "exoclick",
    "trafficjunky",
    "sfwood",
    "safewoo",
    "histats",
    "hotjar",
    "facebook.net",
    "scorecardresearch",
    "taboola",
    "outbrain",
    "mgid",
    "adskeeper",
    "clickadu",
    "hilltopads",
)


def _is_ad_url(url: str) -> bool:
    u = (url or "").lower()
    return any(b in u for b in AD_HOST_BITS)


def clean_mayhem_html(html: str, slug: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Drop scripts entirely (ads + client redirects live here)
    for tag in soup.find_all("script"):
        tag.decompose()

    # Drop noscript ad blobs
    for tag in soup.find_all("noscript"):
        tag.decompose()

    # Drop iframes / embeds that look like ads
    for tag in soup.find_all(["iframe", "embed", "object"]):
        src = tag.get("src") or tag.get("data-src") or ""
        if not src or _is_ad_url(src) or src.startswith("//"):
            tag.decompose()
            continue
        if "arammayhem.com" not in src and not src.startswith("/"):
            tag.decompose()

    # Remove inline handlers that can redirect
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith("on"):
                del tag.attrs[attr]

    # Absolute-ize CSS / images / fonts so the page still looks right
    for tag in soup.find_all(["link", "img", "source", "video", "audio", "use"]):
        for key in ("href", "src", "srcset", "data-src"):
            if not tag.has_attr(key):
                continue
            val = tag.get(key)
            if not val:
                continue
            if key == "srcset":
                parts = []
                for piece in val.split(","):
                    piece = piece.strip()
                    if not piece:
                        continue
                    bits = piece.split()
                    bits[0] = urljoin(BASE + "/", bits[0])
                    parts.append(" ".join(bits))
                tag[key] = ", ".join(parts)
            else:
                if _is_ad_url(val):
                    if tag.name == "link":
                        tag.decompose()
                    else:
                        tag[key] = ""
                    continue
                tag[key] = urljoin(BASE + "/", val)

    # Rewrite internal build links to our mirror; keep other mayhem links absolute
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if _is_ad_url(href):
            a["href"] = "#"
            continue
        full = urljoin(BASE + "/zh-cn/", href)
        path = urlparse(full).path or ""
        m = re.search(r"/zh-cn/build/([a-z0-9-]+)/?", path)
        if m:
            a["href"] = f"/mirror/{m.group(1)}"
            continue
        if href.startswith("/"):
            a["href"] = urljoin(BASE + "/", href)
            a["target"] = "_blank"
            a["rel"] = "noopener noreferrer"
        elif href.startswith("http") and "arammayhem.com" in href:
            a["target"] = "_blank"
            a["rel"] = "noopener noreferrer"

    # Inject top bar: back + note
    # Do NOT use <base> — it would rewrite href="/" / "/mirror/..." to arammayhem.com
    bar = BeautifulSoup(
        f"""
<div id="local-mirror-bar" style="
  position:sticky;top:0;z-index:99999;padding:10px 14px;
  background:#121722;color:#edf1f7;font:14px/1.4 sans-serif;
  border-bottom:1px solid #2a3140;display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
  <a href="/" style="color:#7eb6ff;text-decoration:none">← 返回中转助手</a>
  <span style="color:#9aa3b5">中转镜像 · 官网内容去广告，避免二次跳转</span>
  <a href="/view/{slug}" style="color:#9aa3b5;text-decoration:none;margin-left:auto">简洁预览</a>
</div>
""",
        "lxml",
    ).find("div")

    if soup.body:
        soup.body.insert(0, bar)

    if soup.html:
        soup.html["data-theme"] = "dark"
        classes = soup.html.get("class") or []
        if isinstance(classes, str):
            classes = classes.split()
        if "dark" not in classes:
            classes.append("dark")
        soup.html["class"] = classes

    if soup.head:
        # Remove any upstream <base> so local absolute paths stay on our host
        for old in soup.head.find_all("base"):
            old.decompose()
        scheme = soup.new_tag("meta")
        scheme.attrs["name"] = "color-scheme"
        scheme.attrs["content"] = "dark"
        soup.head.insert(0, scheme)
        dark_style = soup.new_tag("style")
        dark_style.attrs["id"] = "local-mirror-dark"
        dark_style.string = "html{color-scheme:dark}"
        soup.head.insert(0, dark_style)
        csp = soup.new_tag("meta")
        csp.attrs["http-equiv"] = "Content-Security-Policy"
        csp.attrs["content"] = (
            "default-src 'self' https://arammayhem.com https://*.arammayhem.com "
            "https://pub-2322c7068eed43b08bc0dddf6528d1e2.r2.dev data: blob:; "
            "script-src 'none'; "
            "style-src 'self' 'unsafe-inline' https://arammayhem.com https://*.arammayhem.com https://fonts.googleapis.com; "
            "font-src 'self' data: https://arammayhem.com https://*.arammayhem.com https://fonts.gstatic.com; "
            "img-src * data: blob:; "
            "frame-src 'none'; "
            "object-src 'none'"
        )
        soup.head.insert(0, csp)

    return str(soup)


def get_mirror_html(slug: str, refresh: bool = False) -> str:
    slug = slug.lower().strip()
    cache_name = f"build_{slug}.html"
    path = CACHE / cache_name
    if refresh and path.exists():
        path.unlink()
    html = _get(f"{BASE}/zh-cn/build/{slug}/", cache_name)
    return clean_mayhem_html(html, slug)
