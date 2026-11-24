"""lecture.json → 강의별 PPTX (사이트 디자인 언어: paper/ink/blue, 굵은 라인, 모노 키커, 블루 북 모티프)

레이아웃: cover · agenda · section · bullets · two · steps · practice · quote · closing
각 슬라이드의 notes는 발표자 노트(강의 시나리오 대본)로 들어간다.
"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_PATTERN
from pptx.oxml.ns import qn
from lecture import load

INK, BLUE, PAPER, LINE = RGBColor(0x16, 0x18, 0x15), RGBColor(0x2D, 0x4E, 0xFA), RGBColor(0xFA, 0xFA, 0xF7), RGBColor(0xBF, 0xC1, 0xBA)
GRAY, PANEL, DOTBG, DOT, NAVY = RGBColor(0x53, 0x56, 0x4F), RGBColor(0xEE, 0xEF, 0xE9), RGBColor(0xEF, 0xF1, 0xED), RGBColor(0xB4, 0xB9, 0xB1), RGBColor(0x18, 0x29, 0x94)
PROMPT, WHITE, HOVER = RGBColor(0xF0, 0xF1, 0xEB), RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xE9, 0xEC, 0xFF)
KO, NUMF, MONO = 'Malgun Gothic', 'Arial', 'Consolas'
W, H = 13.333, 7.5
MX = 0.75  # 좌우 여백(in)


def font(run, name=KO, size=18, bold=False, color=INK, spacing=None):
    f = run.font
    f.size, f.bold, f.color.rgb = Pt(size), bold, color
    f.name = name
    rPr = run._r.get_or_add_rPr()
    for tag in ('a:ea', 'a:cs'):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set('typeface', KO if name == NUMF else name)
    if spacing is not None:
        rPr.set('spc', str(int(spacing * 100)))


def text(slide, x, y, w, h, s, size=18, name=KO, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None, line=1.15):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, 0)
    for i, ln in enumerate(str(s).split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.line_spacing = align, line
        r = p.add_run(); r.text = ln
        font(r, name, size, bold, color, spacing)
    return tb


def rect(slide, x, y, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb, s.line.width = line, Pt(lw)
    _flat(s)
    return s


def _flat(s):
    """테마 스타일(p:style)의 그림자 제거 → 사이트처럼 평면 디자인"""
    st = s._element.find(qn('p:style'))
    if st is not None:
        s._element.remove(st)


def hline(slide, y, x=MX, w=W - 2 * MX, color=INK, weight=1.0):
    return rect(slide, x, y, w, Pt(weight).inches, fill=color)


def kicker(slide, x, y, s, color=BLUE, size=11):
    rect(slide, x, y + 0.09, 0.38, Pt(2).inches, fill=color)
    text(slide, x + 0.5, y, 8, 0.3, s.upper() if s.isascii() else s, size, MONO, True, color, spacing=1.2)


def chrome(slide, d, l, idx, total, dark=False):
    """상단 브랜드 바 + 하단 라인 (사이트 header/footer와 동일 문법)"""
    b = d['brand']
    ink = WHITE if dark else INK
    m = rect(slide, MX, 0.32, 0.36, 0.36, fill=BLUE)
    tf = m.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = p.add_run(); r.text = b['mark'] + '\ufe0e'; font(r, 'Segoe UI Symbol', 17, True, WHITE)
    text(slide, MX + 0.48, 0.33, 5, 0.34, b['name'], 15, KO, True, ink, anchor=MSO_ANCHOR.MIDDLE, spacing=-0.8)
    text(slide, W - MX - 4, 0.36, 4, 0.3, f"{l['num']}강　/　{idx:02d} — {total:02d}", 10, MONO, True, GRAY if not dark else LINE, PP_ALIGN.RIGHT, MSO_ANCHOR.MIDDLE, spacing=1)
    hline(slide, 0.92, color=ink, weight=0.75)
    hline(slide, H - 0.62, color=LINE if not dark else GRAY, weight=0.75)
    text(slide, MX, H - 0.5, 8, 0.25, f"{l['title']}", 9.5, KO, False, GRAY if not dark else LINE)
    text(slide, W - MX - 4, H - 0.5, 4, 0.25, d['course']['kicker'], 9, MONO, True, GRAY if not dark else LINE, PP_ALIGN.RIGHT, spacing=1)


def heading(slide, s, default_kicker):
    kicker(slide, MX, 1.25, s.get('kicker') or default_kicker)
    t = s['title']
    size = 36 if len(t) <= 22 else 30 if len(t) <= 32 else 26
    text(slide, MX, 1.6, W - 2 * MX, 0.9, t, size, KO, True, INK, spacing=-1.5, line=1.05)
    if s.get('subtitle'):
        text(slide, MX, 2.42, W - 2 * MX, 0.45, s['subtitle'], 16, KO, False, GRAY)
    return 3.05 if s.get('subtitle') else 2.75


def book(slide, x, y, num, top, title, bottom, scale=1.0):
    """사이트 hero의 '.book' 모티프: 블루 표지 + 계단형 오프셋 그림자, -10° 회전"""
    bw, bh = 1.75 * scale, 2.25 * scale
    for k, col in ((4, INK), (3, PANEL), (2, INK), (1, PANEL)):
        sh = rect(slide, x + 0.035 * k * scale * 2, y + 0.035 * k * scale * 2, bw, bh, fill=col, line=INK if col == INK else None, lw=1)
        sh.rotation = -10
    bk = rect(slide, x, y, bw, bh, fill=BLUE, line=INK, lw=1.5)
    bk.rotation = -10
    tf = bk.text_frame; tf.word_wrap = True
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = Inches(0.3 * scale), Inches(0.12 * scale), Inches(0.18 * scale), Inches(0.12 * scale)
    tf.vertical_anchor = MSO_ANCHOR.TOP
    rows = [(top, MONO, 7.5, True), (num, NUMF, 66, True), (title, KO, 11, True), (bottom, MONO, 7, True)]
    for i, (s, f, sz, bd) in enumerate(rows):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 0.95 if f == NUMF else 1.1
        r = p.add_run(); r.text = s; font(r, f, sz * scale, bd, WHITE, -4 if f == NUMF else 0.6)
    return bk


def dotted(slide, x, y, w, h):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.patterned(); s.fill.pattern = MSO_PATTERN.PERCENT_10
    s.fill.fore_color.rgb, s.fill.back_color.rgb = DOT, DOTBG
    s.line.fill.background(); _flat(s)
    text(slide, x + 0.15, y + 0.08, 0.4, 0.3, '+', 18, MONO, False, GRAY)
    text(slide, x + w - 0.4, y + h - 0.42, 0.3, 0.3, '+', 18, MONO, False, GRAY)


# ── 레이아웃 ─────────────────────────────────────────

def lay_cover(sl, d, l, s, i, n):
    chrome(sl, d, l, i, n)
    kicker(sl, MX, 1.55, s.get('kicker') or f"LESSON {l['num']}　/　{l['level']}")
    t = s.get('title') or l['title']
    size = 54 if len(t) <= 14 else 44 if len(t) <= 22 else 36
    text(sl, MX, 1.95, 7.2, 2.6, t, size, KO, True, INK, spacing=-3.5, line=1.05)
    text(sl, MX, 4.45, 7.0, 1.0, s.get('subtitle') or l['description'], 17, KO, False, GRAY, line=1.45)
    dotted(sl, 8.45, 1.45, 4.13, 3.55)
    book(sl, 9.55, 2.0, l['num'], d['course']['book']['top'], l['title'][:12], d['course']['book']['bottom'])
    facts = s.get('facts') or [[l['num'], '강의 차시'], [f"{l['minutes']}분", '강의 시간'], [f"{n:02d}", '슬라이드'], [l['level'], '수준']]
    y = 5.45
    hline(sl, y, weight=2); hline(sl, y + 0.98, weight=2)
    cw = (W - 2 * MX) / len(facts)
    for k, (a, b) in enumerate(facts):
        x = MX + k * cw
        if k:
            rect(sl, x, y + 0.12, Pt(0.75).inches, 0.75, fill=LINE)
        text(sl, x + 0.3, y + 0.2, 2.0, 0.6, a, 28, NUMF, True, INK, anchor=MSO_ANCHOR.MIDDLE, spacing=-1.5)
        text(sl, x + 0.3 + min(2.0, 0.24 * len(a) + 0.35), y + 0.2, 1.6, 0.6, b, 12, KO, True, INK, anchor=MSO_ANCHOR.MIDDLE)


def lay_agenda(sl, d, l, s, i, n):
    chrome(sl, d, l, i, n)
    y0 = heading(sl, s, 'AGENDA')
    items = s.get('bullets', [])
    cols = 2 if len(items) > 4 else 1
    rows = -(-len(items) // cols)
    hline(sl, y0, weight=2)
    rh = min(0.95, (H - 0.9 - y0) / max(rows, 1))
    cw = (W - 2 * MX) / cols
    for k, it in enumerate(items):
        c, r = divmod(k, rows)
        x, y = MX + c * cw, y0 + r * rh
        text(sl, x + 0.1, y + 0.12, 1.0, rh - 0.2, f'{k + 1:02d}', 30, NUMF, True, BLUE, anchor=MSO_ANCHOR.MIDDLE, spacing=-2)
        text(sl, x + 1.15, y + 0.12, cw - 1.4, rh - 0.2, it, 20 if cols == 1 else 18, KO, True, INK, anchor=MSO_ANCHOR.MIDDLE)
        hline(sl, y + rh, x=x, w=cw - (0.2 if c < cols - 1 else 0), color=LINE, weight=0.75)


def lay_section(sl, d, l, s, i, n):
    rect(sl, 0, 0, W, H, fill=PANEL)
    chrome(sl, d, l, i, n)
    kicker(sl, MX, 2.0, s.get('kicker') or 'SECTION')
    text(sl, MX, 2.35, 4.0, 2.4, s.get('num') or f'{i:02d}', 150, NUMF, True, BLUE, spacing=-10, line=0.9)
    text(sl, 5.0, 2.75, W - 5.0 - MX, 1.6, s['title'], 44, KO, True, INK, anchor=MSO_ANCHOR.MIDDLE, spacing=-2.5, line=1.05)
    if s.get('subtitle'):
        text(sl, 5.0, 4.4, W - 5.0 - MX, 1.0, s['subtitle'], 18, KO, False, GRAY, line=1.45)
    hline(sl, 5.6, weight=2)


def lay_bullets(sl, d, l, s, i, n):
    chrome(sl, d, l, i, n)
    y0 = heading(sl, s, f"LESSON {l['num']}")
    items = s.get('bullets', [])
    hi = s.get('highlight')
    avail = H - 0.85 - y0 - (0.95 if hi else 0)
    rh = min(0.82, avail / max(len(items), 1))
    longest = max([len(x) for x in items] or [0])
    size = 21 if rh >= 0.7 and longest <= 48 else 18 if longest <= 70 else 16
    hline(sl, y0, weight=2)
    for k, it in enumerate(items):
        y = y0 + k * rh
        text(sl, MX + 0.05, y, 0.8, rh, f'{k + 1:02d}', 13, MONO, True, BLUE, anchor=MSO_ANCHOR.MIDDLE, spacing=1)
        text(sl, MX + 0.85, y, W - 2 * MX - 0.9, rh, it, size, KO, False, INK, anchor=MSO_ANCHOR.MIDDLE, line=1.2)
        hline(sl, y + rh, color=LINE, weight=0.75)
    if hi:
        y = y0 + len(items) * rh + 0.25
        b = rect(sl, MX, y, W - 2 * MX, 0.7, fill=HOVER)
        rect(sl, MX, y, 0.08, 0.7, fill=BLUE)
        text(sl, MX + 0.35, y, W - 2 * MX - 0.5, 0.7, hi, 17, KO, True, INK, anchor=MSO_ANCHOR.MIDDLE)


def _col(sl, x, y, w, h, block, accent=False):
    hline(sl, y, x=x, w=w, color=BLUE if accent else INK, weight=2.5)
    text(sl, x, y + 0.2, w, 0.55, block.get('title', ''), 22, KO, True, BLUE if accent else INK, spacing=-1)
    yy = y + 0.9
    its = block.get('bullets', [])
    rh = min(0.62, (h - 0.95) / max(len(its), 1))
    for it in its:
        text(sl, x, yy, 0.3, rh, '—', 16, MONO, True, BLUE, anchor=MSO_ANCHOR.MIDDLE)
        text(sl, x + 0.4, yy, w - 0.4, rh, it, 16.5, KO, False, INK, anchor=MSO_ANCHOR.MIDDLE, line=1.2)
        yy += rh


def lay_two(sl, d, l, s, i, n):
    chrome(sl, d, l, i, n)
    y0 = heading(sl, s, 'COMPARE') + 0.1
    cw = (W - 2 * MX - 0.6) / 2
    h = H - 0.9 - y0
    _col(sl, MX, y0, cw, h, s.get('left', {}))
    rect(sl, MX + cw + 0.3, y0 + 0.2, Pt(0.75).inches, h - 0.3, fill=LINE)
    _col(sl, MX + cw + 0.6, y0, cw, h, s.get('right', {}), accent=True)


def lay_steps(sl, d, l, s, i, n):
    chrome(sl, d, l, i, n)
    y0 = heading(sl, s, 'STEP BY STEP') + 0.05
    st = s.get('steps', [])
    k = max(len(st), 1)
    cw = (W - 2 * MX) / k
    h = H - 0.95 - y0
    hline(sl, y0, weight=2); hline(sl, y0 + h, weight=2)
    for j, x in enumerate(st):
        xx = MX + j * cw
        if j:
            rect(sl, xx, y0, Pt(0.75).inches, h, fill=LINE)
        text(sl, xx + 0.28, y0 + 0.3, 1.5, 0.8, f'{j + 1:02d}', 44, NUMF, True, INK, spacing=-3)
        text(sl, xx + cw - 1.6, y0 + 0.42, 1.35, 0.3, x.get('tag', 'STEP'), 10, MONO, True, BLUE, PP_ALIGN.RIGHT)
        text(sl, xx + 0.28, y0 + 1.35, cw - 0.5, 0.9, x.get('title', ''), 21 if k <= 3 else 18, KO, True, INK, spacing=-1, line=1.1)
        text(sl, xx + 0.28, y0 + 2.25, cw - 0.5, h - 2.4, x.get('text', ''), 15 if k <= 3 else 13.5, KO, False, GRAY, line=1.45)


def lay_practice(sl, d, l, s, i, n):
    chrome(sl, d, l, i, n)
    y0 = heading(sl, s, 'PRACTICE')
    body = s.get('code') or '\n'.join(s.get('bullets', []))
    h = H - 0.95 - y0
    rect(sl, MX, y0, W - 2 * MX, h, fill=PROMPT)
    text(sl, MX + 0.35, y0 + 0.22, 4, 0.3, s.get('label', 'PROMPT'), 11, MONO, True, BLUE, spacing=1.2)
    tag = rect(sl, W - MX - 1.55, y0 + 0.18, 1.3, 0.4, fill=INK)
    tf = tag.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = s.get('button', '복사'); font(r, KO, 12, True, WHITE)
    ln = len(body)
    size = 18 if ln < 220 else 15.5 if ln < 420 else 13
    text(sl, MX + 0.35, y0 + 0.75, W - 2 * MX - 0.7, h - 0.95, body, size, KO, False, INK, line=1.5)


def lay_quote(sl, d, l, s, i, n):
    chrome(sl, d, l, i, n)
    kicker(sl, MX, 1.4, s.get('kicker') or 'KEY MESSAGE')
    text(sl, MX - 0.05, 1.7, 1.2, 1.2, '“', 110, NUMF, True, BLUE, line=0.8)
    q = s['title']
    text(sl, MX + 1.1, 2.15, W - 2 * MX - 1.2, 2.6, q, 40 if len(q) <= 40 else 32, KO, True, INK, anchor=MSO_ANCHOR.MIDDLE, spacing=-2, line=1.2)
    if s.get('subtitle'):
        hline(sl, 5.15, x=MX + 1.1, w=2.0, color=INK, weight=2)
        text(sl, MX + 1.1, 5.35, W - 2 * MX - 1.2, 0.9, s['subtitle'], 17, KO, False, GRAY, line=1.45)


def lay_closing(sl, d, l, s, i, n):
    rect(sl, 0, 0, W, H, fill=INK)
    chrome(sl, d, l, i, n, dark=True)
    kicker(sl, MX, 1.5, s.get('kicker') or 'WRAP UP', color=RGBColor(0x8F, 0xA1, 0xFF))
    text(sl, MX, 1.9, 7.4, 1.8, s.get('title') or '정리 및 질의응답', 46, KO, True, WHITE, spacing=-3, line=1.05)
    y = 3.75
    for k, it in enumerate(s.get('bullets', [])[:5]):
        text(sl, MX, y, 0.7, 0.5, f'{k + 1:02d}', 12, MONO, True, RGBColor(0x8F, 0xA1, 0xFF), anchor=MSO_ANCHOR.MIDDLE)
        text(sl, MX + 0.7, y, 6.8, 0.5, it, 17, KO, False, WHITE, anchor=MSO_ANCHOR.MIDDLE)
        y += 0.56
    book(sl, 9.6, 2.2, l['num'], d['course']['book']['top'], s.get('book_title', 'Q & A'), 'THANK YOU', scale=1.0)


LAYOUTS = {'cover': lay_cover, 'agenda': lay_agenda, 'section': lay_section, 'bullets': lay_bullets, 'two': lay_two,
           'steps': lay_steps, 'practice': lay_practice, 'quote': lay_quote, 'closing': lay_closing}


def build_lesson(d, l, out):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    blank = prs.slide_layouts[6]
    n = len(l['slides'])
    for i, s in enumerate(l['slides'], 1):
        sl = prs.slides.add_slide(blank)
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb = PAPER
        LAYOUTS.get(s['layout'], lay_bullets)(sl, d, l, s, i, n)
        if s.get('notes'):
            sl.notes_slide.notes_text_frame.text = s['notes']
    prs.core_properties.title = l['title']
    prs.core_properties.author = d['brand']['name']
    prs.save(out)


if __name__ == '__main__':
    import os
    d = load(sys.argv[1]); od = sys.argv[2]; os.makedirs(od, exist_ok=True)
    for l in d['lessons']:
        build_lesson(d, l, os.path.join(od, f"{l['id']}.pptx"))
