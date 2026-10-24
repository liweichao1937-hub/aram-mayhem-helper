# -*- coding: utf-8 -*-
"""海克斯大乱斗中转助手：搜外号 → 干净镜像详情（去广告、不二次跳转）。"""
from __future__ import annotations

from flask import Flask, Response, jsonify, redirect, render_template_string, request

from fetcher import get_champion_guide, search_champions
from mirror import get_mirror_html

app = Flask(__name__)
SITE = "https://arammayhem.com/zh-cn"

PAGE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>海克斯大乱斗 · 中转助手</title>
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
      --rank1: #f5c542;
      --rank2: #c9d1d9;
      --rank3: #c47a3a;
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
    .wrap { max-width: 780px; margin: 0 auto; padding: 28px 16px 48px; }
    h1 { margin: 0 0 4px; font-size: 1.4rem; }
    .sub { color: var(--muted); margin-bottom: 16px; font-size: 0.9rem; line-height: 1.45; }
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
      justify-content: center;
    }
    .primary { background: var(--accent); color: #16120a; }
    .ghost { background: #243044; color: var(--text); }
    .soft { background: transparent; color: var(--muted); border: 1px solid var(--line); }
    .hints { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
    .hint {
      background: #1c2330; border: 1px solid var(--line); color: var(--muted);
      border-radius: 999px; padding: 7px 12px; cursor: pointer; font-size: 0.85rem;
    }
    .hint:hover { color: var(--text); border-color: var(--accent); }
    .links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
    .card {
      margin-top: 14px; background: var(--panel);
      border: 1px solid var(--line); border-radius: 14px; padding: 18px;
    }
    .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .hero-name { font-size: 1.35rem; font-weight: 750; margin-right: 4px; }
    .pill {
      border-radius: 999px; padding: 3px 10px; font-size: 0.78rem; font-weight: 700;
      background: #243044;
    }
    .pill.tier { background: #3a2d12; color: #f5c542; }
    .pill.wr { background: #123526; color: var(--ok); }
    .fresh { color: var(--muted); font-size: 0.8rem; margin-top: 8px; }
    .sec { margin-top: 16px; }
    .lab {
      font-size: 0.75rem; color: var(--muted); letter-spacing: 0.06em;
      margin-bottom: 10px; text-transform: uppercase;
    }
    .picks { display: grid; gap: 10px; }
    .pick {
      display: grid; grid-template-columns: 42px 1fr auto; gap: 12px; align-items: center;
      background: #121722; border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px;
    }
    .pick.r1 { border-color: #6a5420; background: linear-gradient(90deg, #2a2210, #121722 55%); }
    .pick.r2 { border-color: #3d4654; }
    .pick.r3 { border-color: #5a3d28; }
    .rank {
      width: 42px; height: 42px; border-radius: 10px; display: grid; place-items: center;
      font-weight: 800; font-size: 1.15rem; background: #1c2330;
    }
    .pick.r1 .rank { color: var(--rank1); background: #3a2d12; }
    .pick.r2 .rank { color: var(--rank2); }
    .pick.r3 .rank { color: var(--rank3); background: #2a1c14; }
    .pick .n { font-weight: 700; font-size: 1.05rem; }
    .pick .w { color: var(--muted); font-size: 0.84rem; margin-top: 2px; }
    .pick .tag { color: var(--accent); font-size: 0.78rem; font-weight: 700; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      background: #121722; border: 1px solid var(--line);
      border-radius: 10px; padding: 9px 11px; display: flex; gap: 8px; align-items: center;
    }
    .chip .ord {
      width: 22px; height: 22px; border-radius: 6px; background: #243044;
      display: grid; place-items: center; font-size: 0.75rem; font-weight: 700; color: var(--muted);
    }
    .chip .n { font-weight: 650; }
    .tip { color: var(--muted); font-size: 0.82rem; margin-top: 16px; line-height: 1.5; }
    .err { color: #ff8f8f; padding: 10px 2px; }
    a { color: var(--link); }
    .mode {
      display: flex; gap: 8px; align-items: center; margin-bottom: 10px;
      color: var(--muted); font-size: 0.88rem;
    }
    .mode label { display: inline-flex; gap: 6px; align-items: center; cursor: pointer; }
    .toast {
      position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%);
      background: #243044; color: var(--text); border: 1px solid var(--line);
      padding: 10px 16px; border-radius: 999px; font-size: 0.9rem; display: none; z-index: 99;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>海克斯大乱斗 · 中转助手</h1>
    <div class="sub">用中文外号快速中转到干净的完整攻略页：版式接近官网，已去广告、不二次跳转。</div>

    <div class="box">
      <div class="mode">
        <label><input type="checkbox" id="autoOpen" checked /> 回车后新窗口打开镜像</label>
      </div>
      <div class="row">
        <input id="q" type="search" placeholder="火男 / 男枪 / 小鱼人 / 艾希…" autofocus />
        <button class="primary" id="go">打开镜像</button>
      </div>
      <div class="hints" id="hints"></div>
    </div>

    <div id="out"></div>
    <div class="tip">定位：优秀中转工具。主路径是完整镜像；下方摘要只作预览。</div>
  </div>
  <div class="toast" id="toast">已复制开局清单</div>
  <script>
    const q = document.getElementById('q');
    const out = document.getElementById('out');
    const hints = document.getElementById('hints');
    const autoOpen = document.getElementById('autoOpen');
    const toast = document.getElementById('toast');
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

    function wr(v){ return v == null ? '推荐' : ('胜率 ' + Number(v).toFixed(1) + '%'); }
    function fmtTime(ts) {
      if (!ts) return '';
      const d = new Date(Number(ts) * 1000);
      if (Number.isNaN(d.getTime())) return '';
      const pad = n => String(n).padStart(2, '0');
      return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate())
        + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    }
    function showToast(msg) {
      toast.textContent = msg;
      toast.style.display = 'block';
      clearTimeout(window._toastT);
      window._toastT = setTimeout(() => toast.style.display = 'none', 1600);
    }

    function buildChecklist(g) {
      const name = g.name || g.slug;
      const augs = (g.recommended_augments || []).slice(0, 3);
      const items = (g.core_items || []).slice(0, 5);
      const boots = (g.boots || []).slice(0, 2);
      const lines = [
        name + (g.tier ? ` · ${g.tier}级` : '') + (g.winrate != null ? ` · ${g.winrate}%` : ''),
        '海克斯：' + (augs.map((a,i) => `${i+1}.${a.name}`).join(' > ') || '暂无'),
        '出装：' + (items.map(it => it.name).join(' → ') || '暂无'),
        '鞋子：' + (boots.map(it => it.name).join(' / ') || '暂无'),
      ];
      if (g.patch) lines.push('版本 ' + g.patch);
      return lines.join('\n');
    }

    function render(g) {
      if (g.error) { out.innerHTML = `<div class="err">${g.error}</div>`; return; }
      recentPush(g.name || g.slug, g.slug);
      const top = (g.recommended_augments || []).slice(0, 3);
      const more = (g.recommended_augments || []).slice(3, 6);
      const picks = top.map((a, i) => `
        <div class="pick r${i+1}">
          <div class="rank">${i+1}</div>
          <div>
            <div class="n">${a.name}</div>
            <div class="w">${wr(a.winrate)}</div>
          </div>
          <div class="tag">${i===0?'优先':'备选'}</div>
        </div>`).join('');
      const moreChips = more.map(a => `
        <div class="chip"><div class="n">${a.name}</div></div>`).join('');
      const items = (g.core_items || []).map((it, i) => `
        <div class="chip"><div class="ord">${i+1}</div><div class="n">${it.name}</div></div>`).join('');
      const boots = (g.boots || []).slice(0, 4).map(it => `
        <div class="chip"><div class="n">${it.name}</div></div>`).join('');
      const fresh = [g.patch ? ('版本 ' + g.patch) : '', fmtTime(g.cached_at) ? ('更新 ' + fmtTime(g.cached_at)) : '']
        .filter(Boolean).join(' · ');
      out.innerHTML = `
        <div class="card" id="desk">
          <div class="meta">
            <span class="hero-name">${g.name || g.slug}</span>
            ${g.tier ? `<span class="pill tier">${g.tier} 级</span>` : ''}
            ${g.winrate != null ? `<span class="pill wr">胜率 ${g.winrate}%</span>` : ''}
          </div>
          ${fresh ? `<div class="fresh">${fresh}</div>` : ''}

          <div class="links" style="margin-top:12px">
            <a class="btn primary" href="/mirror/${g.slug}" target="_blank" rel="noopener">打开完整镜像</a>
            <a class="btn ghost" href="/view/${g.slug}" target="_blank" rel="noopener">简洁预览</a>
            <button class="btn soft" id="copyBtn">复制清单</button>
          </div>

          <div class="sec">
            <div class="lab">预览 · 海克斯优先</div>
            <div class="picks">${picks || '<div class="tip">暂无海克斯数据</div>'}</div>
          </div>

          ${moreChips ? `<div class="sec"><div class="lab">后续可考虑</div><div class="chips">${moreChips}</div></div>` : ''}

          <div class="sec">
            <div class="lab">预览 · 核心出装</div>
            <div class="chips">${items || '—'}</div>
          </div>
          <div class="sec">
            <div class="lab">预览 · 鞋子</div>
            <div class="chips">${boots || '—'}</div>
          </div>
        </div>`;
      document.getElementById('copyBtn').onclick = async () => {
        const text = buildChecklist(g);
        try {
          await navigator.clipboard.writeText(text);
          showToast('已复制清单');
        } catch {
          prompt('复制下面内容：', text);
        }
      };
    }

    async function run(openDetail) {
      const query = q.value.trim();
      if (!query) return;
      out.innerHTML = '<div class="card">查找中…</div>';
      const res = await fetch('/api/search?q=' + encodeURIComponent(query));
      const data = await res.json();
      if (!data.length) {
        out.innerHTML = '<div class="err">没找到英雄，换个外号或正式名再试。</div>';
        return;
      }
      const c = data[0];
      if (openDetail) {
        window.open('/mirror/' + encodeURIComponent(c.slug), '_blank', 'noopener');
      }
      const gRes = await fetch('/api/guide/' + encodeURIComponent(c.slug));
      render(await gRes.json());
    }

    q.addEventListener('input', () => { clearTimeout(window._t); window._t = setTimeout(suggest, 160); });
    q.addEventListener('keydown', e => {
      if (e.key === 'Enter') run(autoOpen.checked);
    });
    document.getElementById('go').onclick = () => run(true);
    suggest();
    renderRecent();
  </script>
</body>
</html>
"""

VIEW_PAGE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ name }} · 简洁预览</title>
  <style>
    :root {
      --bg:#0b0e13; --panel:#151a22; --line:#2a3140; --text:#edf1f7;
      --muted:#9aa3b5; --accent:#d4a017; --ok:#3dd68c;
    }
    *{box-sizing:border-box}
    body{
      margin:0; min-height:100vh; color:var(--text);
      font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
      background:radial-gradient(900px 420px at 50% -8%, #1c2638 0%, transparent 55%), var(--bg);
    }
    .wrap{max-width:760px;margin:0 auto;padding:28px 16px 48px}
    a{color:#7eb6ff;text-decoration:none}
    .back{color:var(--muted);font-size:.9rem}
    h1{margin:12px 0 6px;font-size:1.45rem}
    .meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px}
    .fresh{color:var(--muted);font-size:.82rem;margin-bottom:14px}
    .pill{border-radius:999px;padding:3px 10px;font-size:.78rem;font-weight:700;background:#243044}
    .pill.tier{background:#3a2d12;color:#f5c542}
    .pill.wr{background:#123526;color:var(--ok)}
    .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
    .lab{font-size:.75rem;color:var(--muted);letter-spacing:.06em;margin-bottom:8px;text-transform:uppercase}
    .aug{border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:8px;background:#121722;display:grid;grid-template-columns:36px 1fr;gap:10px}
    .aug.top{border-color:#5b4a1e}
    .aug .rk{width:36px;height:36px;border-radius:8px;background:#243044;display:grid;place-items:center;font-weight:800}
    .aug.top .rk{background:#3a2d12;color:#f5c542}
    .aug .n{font-weight:700}
    .aug .w{color:var(--muted);font-size:.85rem;margin-top:2px}
    .aug .d{color:#c8d0de;font-size:.9rem;margin-top:6px;line-height:1.45;grid-column:2}
    .chips{display:flex;flex-wrap:wrap;gap:8px}
    .chip{background:#121722;border:1px solid var(--line);border-radius:10px;padding:9px 11px}
    .tip{color:var(--muted);font-size:.82rem;margin-top:16px;line-height:1.5}
    .links{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 4px}
    .btn{border:0;border-radius:10px;padding:10px 14px;font-weight:700;background:#243044;color:var(--text)}
  </style>
</head>
<body>
  <div class="wrap">
    <a class="back" href="/">← 返回中转助手</a>
    <h1>{{ name }}{% if title %} · {{ title }}{% endif %}</h1>
    <div class="meta">
      {% if tier %}<span class="pill tier">{{ tier }} 级</span>{% endif %}
      {% if winrate is not none %}<span class="pill wr">胜率 {{ winrate }}%</span>{% endif %}
      {% if patch %}<span class="pill">版本 {{ patch }}</span>{% endif %}
    </div>
    {% if cached_at %}<div class="fresh">数据更新时间：{{ cached_at }}</div>{% endif %}

    <div class="card">
      <div class="lab">海克斯（前三优先）</div>
      {% for a in augments %}
      <div class="aug {% if loop.index0 < 3 %}top{% endif %}">
        <div class="rk">{{ loop.index }}</div>
        <div>
          <div class="n">{{ a.name }}</div>
          <div class="w">{% if a.winrate is not none %}胜率 {{ '%.1f'|format(a.winrate) }}%{% else %}推荐{% endif %}</div>
          {% if a.desc %}<div class="d">{{ a.desc }}</div>{% endif %}
        </div>
      </div>
      {% else %}
      <div class="tip">暂无海克斯数据</div>
      {% endfor %}
    </div>

    <div class="card">
      <div class="lab">核心出装</div>
      <div class="chips">
        {% for it in items %}<div class="chip">{{ loop.index }}. {{ it.name }}</div>{% else %}<span class="tip">暂无</span>{% endfor %}
      </div>
    </div>

    <div class="card">
      <div class="lab">鞋子</div>
      <div class="chips">
        {% for it in boots %}<div class="chip">{{ it.name }}</div>{% else %}<span class="tip">暂无</span>{% endfor %}
      </div>
    </div>

    <div class="links">
      <a class="btn" href="/mirror/{{ slug }}" target="_blank" rel="noopener">打开完整镜像（主路径）</a>
    </div>
    <div class="tip">本页是简洁预览；完整内容请走镜像中转页。</div>
  </div>
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


@app.get("/view/<slug>")
def view_champion(slug: str):
    from datetime import datetime

    refresh = request.args.get("refresh") in ("1", "true", "yes")
    try:
        g = get_champion_guide(slug, refresh=refresh)
    except Exception as e:
        return f"加载失败：{e}", 500
    cached_at = ""
    ts = g.get("cached_at")
    if ts:
        cached_at = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    return render_template_string(
        VIEW_PAGE,
        slug=slug,
        name=g.get("name") or g.get("display") or slug,
        title=g.get("title") or "",
        tier=g.get("tier"),
        winrate=g.get("winrate"),
        patch=g.get("patch"),
        cached_at=cached_at,
        augments=(g.get("recommended_augments") or [])[:12],
        items=g.get("core_items") or [],
        boots=g.get("boots") or [],
    )


@app.get("/mirror/<slug>")
def mirror_champion(slug: str):
    """官网样式镜像：保留版式与内容，剥离广告脚本。"""
    refresh = request.args.get("refresh") in ("1", "true", "yes")
    try:
        html = get_mirror_html(slug, refresh=refresh)
    except Exception:
        return redirect(f"/view/{slug}")
    return Response(html, mimetype="text/html; charset=utf-8")


@app.get("/go")
def go():
    """Bookmark-friendly: /go?q=火男 → 完整镜像（主路径）。"""
    q = request.args.get("q", "").strip()
    hits = search_champions(q, limit=1)
    if not hits:
        return redirect("/")
    return redirect(f"/mirror/{hits[0]['slug']}")


if __name__ == "__main__":
    import os

    search_champions("")  # warm index
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8765"))
    print(f"中转助手: http://{host}:{port}/")
    print(f"镜像直达: http://{host}:{port}/go?q=火男")
    app.run(host=host, port=port, debug=False)
