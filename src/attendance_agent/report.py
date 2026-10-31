"""EPIC 6 (part 1) - self-contained HTML report (works offline, no libraries)."""
import html
import os
from typing import List

from .agent import DISCLAIMER
from .models import Suggestion, Window


def _fmt(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def _chart(windows: List[Window]) -> str:
    W, H, pad = 720, 220, 30
    if not windows:
        return ""
    n = len(windows)
    pts = []
    for i, w in enumerate(windows):
        x = pad + (W - 2 * pad) * (i / max(n - 1, 1))
        y = H - pad - (H - 2 * pad) * w.engagement
        pts.append((x, y, w))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#2563eb">'
                   f'<title>{_fmt(w.start)} engagement {w.engagement:.2f}</title></circle>'
                   for x, y, w in pts)
    labels = "".join(f'<text x="{x:.1f}" y="{H - 8}" font-size="10" text-anchor="middle">{_fmt(w.start)}</text>'
                     for x, _, w in pts[::max(n // 10, 1)])
    return (f'<svg viewBox="0 0 {W} {H}" width="100%">'
            f'<line x1="{pad}" y1="{H - pad}" x2="{W - pad}" y2="{H - pad}" stroke="#999"/>'
            f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{H - pad}" stroke="#999"/>'
            f'<text x="4" y="{pad + 4}" font-size="10">1.0</text><text x="4" y="{H - pad}" font-size="10">0</text>'
            f'<polyline points="{line}" fill="none" stroke="#2563eb" stroke-width="2"/>{dots}{labels}</svg>')


def write_report(path: str, title: str, summary: dict, attendance: List[dict],
                 windows: List[Window], suggestions: List[Suggestion]):
    rows = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r.values()) + "</tr>"
                   for r in attendance)
    head = "".join(f"<th>{html.escape(k)}</th>" for k in (attendance[0].keys() if attendance else []))
    sug = "".join(
        f'<div class="card {s.category}"><b>{_fmt(s.start)}-{_fmt(s.end)} - {s.category.title()}</b><br>'
        f'{html.escape(s.observation)}<br><i>{html.escape(s.suggestion)}</i> '
        f'<small>(confidence {s.confidence:.0%})</small></div>' for s in suggestions) or "<p>No suggestions.</p>"
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:860px;margin:30px auto;padding:0 16px;color:#111}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:6px 8px;font-size:14px}}
th{{background:#f3f4f6;text-align:left}}.card{{border-left:4px solid #2563eb;background:#f8fafc;padding:8px 12px;margin:8px 0}}
.positive{{border-color:#16a34a}}.pacing{{border-color:#d97706}}.attention{{border-color:#dc2626}}
.kpi span{{display:inline-block;background:#eef2ff;padding:8px 14px;margin:4px;border-radius:8px}}</style></head><body>
<h1>{html.escape(title)}</h1>
<div class="kpi"><span>Present: <b>{summary.get('participants_present', 0)}</b> / {summary.get('participants_detected', 0)}</span>
<span>Mean engagement: <b>{summary.get('mean_engagement', 0)}</b></span></div>
<h2>Engagement over time</h2>{_chart(windows)}
<h2>Attendance log</h2><table><tr>{head}</tr>{rows}</table>
<h2>Teaching suggestions</h2>{sug}
<p><small>{html.escape(DISCLAIMER)} All processing was local; no images or audio were stored.</small></p>
</body></html>"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
