# -*- coding: utf-8 -*-
"""海克斯大乱斗快捷助手：搜索英雄 → 直达 ARAM Mayhem 官网页 + 本地摘要。"""
from __future__ import annotations

from flask import Flask, jsonify, redirect, render_template_string, request

from fetcher import get_champion_guide, search_champions

app = Flask(__name__)
SITE = "https://arammayhem.com/zh-cn"

PAGE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>海克斯大乱斗 · 快捷入口</title>
  <style>
    :root {
      --bg: #0b0e13;
      --panel: #151a22;
      --line: #2a3140;
      --text: #edf1f7;
      --muted: #9aa3b5;
      --accent: #d4a017;
      --ok: #3dd68c;
      --link: #7eb6ff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--text);
      background:
        radial-gradient(900px 420px at 50% -8%, #1c2638 0%, transparent 55%),
        var(--bg);
    }
    .wrap { max-width: 720px; margin: 0 auto; padding: 36px 16px 48px; }
    h1 { margin: 0 0 4px; font-size: 1.45rem; }
    .sub { color: var(--muted); margin-bottom: 18px; font-size: 0.92rem; line-height: 1.45; }
    .box {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
    }
    .row { display: flex; gap: 8px; flex-wrap: wrap; }
    input[type=search] {
      flex: 1; min-width: 200px;
      background: #0f131a; color: var(--text);
      border: 1px solid var(--line); border-radius: 10px;
      padding: 14px 14px; font-size: 1.05rem; outline: none;
    }
    input[type=search]:focus { border-color: var(--accent); }
    button, .btn {
      border: 0; border-radius: 10px; padding: 12px 16px;
      font-weight: 700; cursor: pointer; font-size: 0.95rem;
      text-decoration: none; display: inline-flex; align-items: center;
    }
    .primary { background: var(--accent); color: #16120a; }
    .ghost { background: #243044; color: var(--text); }
    .hints { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .hint {
      background: #1c2330; border: 1px solid var(--line); color: var(--muted);
      border-radius: 999px; padding: 7px 12px; cursor: pointer; font-size: 0.85rem;
    }
    .hint:hover { color: var(--text); border-color: var(--accent); }
    .links { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 6px; }
    .card {
      margin-top: 14px; background: var(--panel);
      border: 1px solid var(--line); border-radius: 14px; padding: 16px;
    }
    .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 6px; }
    .pill {
      border-radius: 999px; padding: 3px 10px; font-size: 0.78rem; font-weight: 700;
      background: #243044;
    }
    .pill.tier { background: #3a2d12; color: #f5c542; }
    .pill.wr { background: #123526; color: var(--ok); }
    .sec { margin-top: 12px; }
    .lab {
      font-size: 0.75rem; color: var(--muted); letter-spacing: 0.06em;
      margin-bottom: 6px; text-transform: uppercase;
    }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      background: #121722; border: 1px solid var(--line);
      border-radius: 10px; padding: 9px 11px; min-width: 110px;
    }
    .chip.top { border-color: #5b4a1e; }
    .chip .n { font-weight: 650; }
    .chip .w { color: var(--muted); font-size: 0.8rem; margin-top: 2px; }
    .tip { color: var(--muted); font-size: 0.82rem; margin-top: 16px; line-height: 1.5; }
    .err { color: #ff8f8f; padding: 10px 2px; }
    a { color: var(--link); }
    .mode {
      display: flex; gap: 8px; align-items: center; margin-bottom: 10px;
      color: var(--muted); font-size: 0.88rem;
    }
    .mode label { display: inline-flex; gap: 6px; align-items: center; cursor: pointer; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>海克斯大乱斗 · 快捷入口</h1>
    <div class="sub">输入英雄，回车直达 ARAM Mayhem 官网出装页；同时在下方给出海克斯/出装摘要。</div>

    <div class="box">
      <div class="mode">
        <label><input type="checkbox" id="autoOpen" checked /> 回车后自动打开官网</label>
      </div>
      <div class="row">
        <input id="q" type="search" placeholder="艾希 / 火男 / ashe / 寒冰…" autofocus />
        <button class="primary" id="go">查询并打开</button>
        <button class="ghost" id="onlyLocal">只看摘要</button>
      </div>
      <div class="hints" id="hints"></div>
      <div class="links">
        <a class="btn ghost" href="https://arammayhem.com/zh-cn/" target="_blank" rel="noreferrer">官网首页</a>
        <a class="btn ghost" href="https://arammayhem.com/zh-cn/augments/" target="_blank" rel="noreferrer">全部海克斯</a>
        <a class="btn ghost" href="https://arammayhem.com/zh-cn/build/" target="_blank" rel="noreferrer">英雄出装列表</a>
        <a class="btn ghost" href="https://arammayhem.com/zh-cn/combo/" target="_blank" rel="noreferrer">强势组合</a>
      </div>
    </div>

    <div id="out"></div>
    <div class="tip">
      用法：选完英雄后，在这个小页搜名字 → 回车。会打开官网对应英雄页，方便对照局内三选一。<br/>
      桌面快捷方式「海克斯大乱斗助手」启动本页；官网书签可继续用。
    </div>
  </div>
  <script>
    const q = document.getElementById('q');
    const out = document.getElementById('out');
    const hints = document.getElementById('hints');
    const autoOpen = document.getElementById('autoOpen');
    autoOpen.checked = localStorage.getItem('autoOpen') !== '0';
    autoOpen.onchange = () => localStorage.setItem('autoOpen', autoOpen.checked ? '1' : '0');

    function recentPush(name, slug) {
      let arr = [];
      try { arr = JSON.parse(localStorage.getItem('recent') || '[]'); } catch {}
      arr = [{name, slug}, ...arr.filter(x => x.slug !== slug)].slice(0, 8);
      localStorage.setItem('recent', JSON.stringify(arr));
      renderRecent();
    }
    function renderRecent() {
      let arr = [];
      try { arr = JSON.parse(localStorage.getItem('recent') || '[]'); } catch {}
      if (!arr.length) return;
      const bar = document.createElement('div');
      bar.className = 'hints';
      bar.style.marginTop = '8px';
      bar.innerHTML = '<span style="color:#9aa3b5;font-size:0.82rem;margin-right:4px">最近：</span>';
      arr.forEach(c => {
        const b = document.createElement('button');
        b.className = 'hint';
        b.textContent = c.name;
        b.onclick = () => { q.value = c.name; run(true); };
        bar.appendChild(b);
      });
      // replace previous recent bar if any
      const old = document.getElementById('recentBar');
      if (old) old.remove();
      bar.id = 'recentBar';
      hints.parentNode.insertBefore(bar, hints.nextSibling);
    }

    async function suggest() {
      const res = await fetch('/api/search?q=' + encodeURIComponent(q.value.trim()));
      const data = await res.json();
      hints.innerHTML = '';
      data.slice(0, 10).forEach(c => {
        const el = document.createElement('button');
        el.className = 'hint';
        el.textContent = c.name;
        el.onclick = () => { q.value = c.name; run(true); };
        hints.appendChild(el);
      });
    }

    function wr(v){ return v == null ? '' : ('胜率 ' + Number(v).toFixed(2) + '%'); }

    function render(g) {
      if (g.error) { out.innerHTML = `<div class="err">${g.error}</div>`; return; }
      recentPush(g.name || g.slug, g.slug);
      const augs = (g.recommended_augments || []).slice(0, 6).map((a,i) => `
        <div class="chip ${i<3?'top':''}">
          <div class="n">${i<3?'★ ':''}${a.name}</div>
          <div class="w">${wr(a.winrate) || '推荐'}</div>
        </div>`).join('');
      const items = (g.core_items || []).map(it => `<div class="chip"><div class="n">${it.name}</div></div>`).join('');
      const boots = (g.boots || []).slice(0,4).map(it => `<div class="chip"><div class="n">${it.name}</div></div>`).join('');
      out.innerHTML = `
        <div class="card">
          <div class="meta">
            <strong style="font-size:1.15rem">${g.name || g.slug}</strong>
            ${g.tier ? `<span class="pill tier">${g.tier} 级</span>` : ''}
            ${g.winrate != null ? `<span class="pill wr">${g.winrate}%</span>` : ''}
            ${g.patch ? `<span class="pill">${g.patch}</span>` : ''}
          </div>
          <div class="links" style="margin:10px 0 0">
            <a class="btn primary" href="${g.source}" target="_blank" rel="noreferrer">打开官网完整出装页</a>
            <a class="btn ghost" href="https://arammayhem.com/zh-cn/augments/" target="_blank" rel="noreferrer">查全部海克斯</a>
          </div>
          <div class="sec"><div class="lab">海克斯优先（前三）</div><div class="chips">${augs || '—'}</div></div>
          <div class="sec"><div class="lab">核心出装</div><div class="chips">${items || '—'}</div></div>
          <div class="sec"><div class="lab">鞋子</div><div class="chips">${boots || '—'}</div></div>
        </div>`;
    }

    async function run(openSite) {
      const query = q.value.trim();
      if (!query) return;
      out.innerHTML = '<div class="card">查找中…</div>';
      const res = await fetch('/api/search?q=' + encodeURIComponent(query));
      const data = await res.json();
      if (!data.length) {
        out.innerHTML = '<div class="err">没找到英雄，换个关键词。</div>';
        return;
      }
      const c = data[0];
      if (openSite) {
        window.open('https://arammayhem.com/zh-cn/build/' + c.slug + '/', '_blank');
      }
      const gRes = await fetch('/api/guide/' + encodeURIComponent(c.slug));
      render(await gRes.json());
    }

    q.addEventListener('input', () => { clearTimeout(window._t); window._t = setTimeout(suggest, 160); });
    q.addEventListener('keydown', e => {
      if (e.key === 'Enter') run(autoOpen.checked);
    });
    document.getElementById('go').onclick = () => run(true);
    document.getElementById('onlyLocal').onclick = () => run(false);
    suggest();
    renderRecent();
  </script>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(PAGE)


@app.get("/api/search")
def api_search():
    return jsonify(search_champions(request.args.get("q", ""), limit=15))


@app.get("/api/guide/<slug>")
def api_guide(slug: str):
    refresh = request.args.get("refresh") in ("1", "true", "yes")
    try:
        return jsonify(get_champion_guide(slug, refresh=refresh))
    except Exception as e:
        return jsonify({"error": f"拉取失败：{e}", "slug": slug}), 500


@app.get("/go")
def go():
    """Bookmark-friendly: /go?q=艾希  → redirect to ARAM Mayhem build page."""
    q = request.args.get("q", "").strip()
    hits = search_champions(q, limit=1)
    if not hits:
        return redirect(f"{SITE}/build/")
    return redirect(f"{SITE}/build/{hits[0]['slug']}/")


if __name__ == "__main__":
    import os

    search_champions("")  # warm index
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8765"))
    print(f"快捷入口: http://{host}:{port}/")
    print(f"直达跳转: http://{host}:{port}/go?q=艾希")
    app.run(host=host, port=port, debug=False)
