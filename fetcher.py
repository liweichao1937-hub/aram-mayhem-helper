# -*- coding: utf-8 -*-
"""Fetch & parse ARAM Mayhem (海克斯大乱斗) champion pages."""
from __future__ import annotations

import json
import re
import ssl
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from aliases import ALIASES, alias_slug

BASE = "https://arammayhem.com"
CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
SSL_CTX = ssl._create_unverified_context()


def _get(url: str, cache_name: str | None = None, max_age_sec: int = 6 * 3600) -> str:
    path = CACHE / cache_name if cache_name else None
    if path and path.exists() and (time.time() - path.stat().st_mtime) < max_age_sec:
        return path.read_text(encoding="utf-8")
    data = None
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"}
        )
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        # Fallback: curl.exe often works when Python SSL chain is broken on Windows
        r = subprocess.run(
            [
                "curl.exe",
                "-sL",
                "--connect-timeout",
                "20",
                "--max-time",
                "45",
                "-A",
                UA,
                url,
            ],
            capture_output=True,
            check=False,
        )
        data = r.stdout.decode("utf-8", errors="ignore")
        if r.returncode != 0 or not data:
            raise RuntimeError(f"download failed: {url}")
    if path:
        path.write_text(data, encoding="utf-8")
    return data


def load_champion_index() -> list[dict[str, str]]:
    """slug + CN/EN names from Data Dragon + builds page."""
    cache_json = CACHE / "champion_index.json"
    if cache_json.exists() and (time.time() - cache_json.stat().st_mtime) < 24 * 3600:
        return json.loads(cache_json.read_text(encoding="utf-8"))

    versions = json.loads(
        _get(
            "https://ddragon.leagueoflegends.com/api/versions.json",
            "ddragon_versions.json",
            max_age_sec=24 * 3600,
        )
    )
    ver = versions[0]
    raw = json.loads(
        _get(
            f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/zh_CN/champion.json",
            f"ddragon_champions_zh_{ver}.json",
            max_age_sec=24 * 3600,
        )
    )["data"]

    builds_html = _get(f"{BASE}/zh-cn/build/", "builds.html", max_age_sec=12 * 3600)
    slugs = sorted(set(re.findall(r"/zh-cn/build/([a-z0-9]+)/?", builds_html)))

    # Map ddragon id lower -> names. Slugs on site are lowercased ids mostly (aurelionsol, etc.)
    by_id = {}
    for cid, info in raw.items():
        key = cid.lower()
        by_id[key] = {
            "id": cid,
            "slug": key,
            "name": info["name"],
            "title": info["title"],
            "key": info["key"],
        }

    # Fix known slug mismatches if any
    aliases = {
        "monkeyking": "wukong",
        "wukong": "monkeyking",
    }
    index = []
    for slug in slugs:
        info = by_id.get(slug) or by_id.get(aliases.get(slug, ""))
        if info:
            row = dict(info)
            row["slug"] = slug
            index.append(row)
        else:
            index.append(
                {
                    "id": slug,
                    "slug": slug,
                    "name": slug,
                    "title": "",
                    "key": "",
                }
            )

    cache_json.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


def search_champions(q: str, limit: int = 12) -> list[dict[str, str]]:
    q = (q or "").strip()
    index = load_champion_index()
    by_slug = {c["slug"]: c for c in index}
    if not q:
        return index[:limit]

    hits: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(c: dict[str, str] | None) -> None:
        if not c or c["slug"] in seen:
            return
        seen.add(c["slug"])
        hits.append(c)

    # 1) 外号精确 / 子串
    slug = alias_slug(q)
    if slug:
        add(by_slug.get(slug))

    # 2) 外号表里所有包含关键词的项
    ql = q.lower()
    for alias, s in ALIASES.items():
        if q in alias or alias in q or ql in alias.lower():
            add(by_slug.get(s))

    # 3) 正式名 / 称号 / 英文 id
    for c in index:
        blob = f"{c['slug']} {c['id']} {c['name']} {c.get('title', '')}".lower()
        if ql in blob or q in c["name"] or q in c.get("title", ""):
            add(c)

    return hits[:limit]


def parse_champion_page(html: str, slug: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    desc = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        desc = meta.get("content") or ""

    tier = None
    winrate = None
    patch = None
    m = re.search(r"([SABCD]\+?)\s*级?强度[，, ]*胜率\s*([\d.]+)%", desc)
    if m:
        tier, winrate = m.group(1), float(m.group(2))
    else:
        m2 = re.search(r"胜率\s*([\d.]+)%", desc)
        if m2:
            winrate = float(m2.group(1))
        t2 = re.search(r"\b([SABCD]\+?)\s*级", desc)
        if t2:
            tier = t2.group(1)
    pm = re.search(r"(\d{2}\.\d{2})\s*版本", desc)
    if pm:
        patch = pm.group(1)

    h1 = soup.find("h1")
    display_name = None
    if h1:
        display_name = re.sub(r"\s+", " ", h1.get_text(" ", strip=True))

    # Collect ordered unique entries by href type
    seen_aug: set[str] = set()
    seen_item: set[str] = set()
    augments: list[dict[str, Any]] = []
    core_items: list[dict[str, str]] = []
    boots: list[dict[str, str]] = []
    alt_builds: list[list[dict[str, str]]] = []

    boot_slugs = {
        "berserkers_greaves",
        "mercurys_treads",
        "plated_steelcaps",
        "boots_of_swiftness",
        "ionian_boots_of_lucidity",
        "sorcerers_shoes",
        "boots",
        "slightly_magical_footwear",
    }

    current_alt: list[dict[str, str]] | None = None

    for a in soup.find_all("a", href=True):
        href = a["href"]
        img = a.find("img", alt=True)
        name = (img["alt"].strip() if img else a.get_text(" ", strip=True)).strip()
        if not name:
            continue

        if re.search(r"/augments/[a-z0-9-]+/?$", href):
            slug_a = href.rstrip("/").split("/")[-1]
            if slug_a in ("augments", ""):
                continue
            wr = None
            desc_a = ""
            text = a.get_text(" ", strip=True)
            wm = re.search(r"胜率:\s*([\d.]+)%\s*(.*)$", text)
            if wm:
                wr = float(wm.group(1))
                desc_a = (wm.group(2) or "").strip()
            if wr is None:
                wm = re.search(r"([\d.]+)%", text)
                if wm:
                    wr = float(wm.group(1))
            clean_name = name
            if "胜率" in clean_name:
                clean_name = clean_name.split("胜率")[0].strip()
            if clean_name in ("强化符文", "全部强化符文", "Augments"):
                continue
            row = {
                "slug": slug_a,
                "name": clean_name,
                "winrate": wr,
                "desc": desc_a,
                "url": BASE + href if href.startswith("/") else href,
            }
            if slug_a not in seen_aug:
                seen_aug.add(slug_a)
                augments.append(row)
            else:
                for item in augments:
                    if item["slug"] == slug_a:
                        if item.get("winrate") is None and wr is not None:
                            item["winrate"] = wr
                        if not item.get("desc") and desc_a:
                            item["desc"] = desc_a
                        break

        elif re.search(r"/items/[a-z0-9_]+/?$", href):
            item_slug = href.rstrip("/").split("/")[-1]
            if item_slug in ("items", ""):
                continue
            row = {
                "slug": item_slug,
                "name": name,
                "url": BASE + href if href.startswith("/") else href,
            }
            if item_slug in boot_slugs:
                if item_slug not in {b["slug"] for b in boots}:
                    boots.append(row)
                continue
            if item_slug not in seen_item and len(core_items) < 6:
                seen_item.add(item_slug)
                core_items.append(row)
                continue
            if item_slug not in seen_item:
                seen_item.add(item_slug)
                if current_alt is None:
                    current_alt = []
                    alt_builds.append(current_alt)
                current_alt.append(row)
            else:
                current_alt = None

    return {
        "slug": slug,
        "display": display_name,
        "description": desc,
        "tier": tier,
        "winrate": winrate,
        "patch": patch,
        "recommended_augments": augments[:12],
        "core_items": core_items,
        "boots": boots,
        "source": f"{BASE}/zh-cn/build/{slug}/",
    }


def get_champion_guide(slug: str, refresh: bool = False) -> dict[str, Any]:
    slug = slug.lower().strip()
    cache_name = f"build_{slug}.html"
    path = CACHE / cache_name
    if refresh and path.exists():
        path.unlink()
    html = _get(f"{BASE}/zh-cn/build/{slug}/", cache_name)
    guide = parse_champion_page(html, slug)
    # attach names from index
    for c in load_champion_index():
        if c["slug"] == slug:
            guide["name"] = c["name"]
            guide["title"] = c["title"]
            guide["id"] = c["id"]
            break
    if path.exists():
        guide["cached_at"] = int(path.stat().st_mtime)
    else:
        guide["cached_at"] = int(time.time())
    out = CACHE / f"guide_{slug}.json"
    out.write_text(json.dumps(guide, ensure_ascii=False, indent=2), encoding="utf-8")
    return guide


if __name__ == "__main__":
    import sys

    q = sys.argv[1] if len(sys.argv) > 1 else "艾希"
    hits = search_champions(q)
    print("hits:", [(h["name"], h["slug"]) for h in hits[:5]])
    if hits:
        g = get_champion_guide(hits[0]["slug"], refresh=True)
        print(json.dumps(g, ensure_ascii=False, indent=2))
