"""lecture.json → 강의안.md (강의 시나리오 포함) + prompts.md"""
import sys
from lecture import load


def cell(v):
    return str(v or '').replace('|', '\\|').replace('\n', '<br>')


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '|'.join(['---'] * len(head)) + '|']
    out += ['| ' + ' | '.join(cell(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def bullets(items):
    return '\n'.join(f'- {x}' for x in items)


def build_md(d):
    c, L = d['course'], d['lessons']
    o = [f"# {c['title'].replace(chr(10), ' ')}", '']
    o += [f"> {c['kicker']}" + (f"　/　{c['audience']}" if c['audience'] else ''), '']
    if c['summary']:
        o += [c['summary'].replace('\n', ' '), '']
    o += ['## 과정 개요', '', table(['항목', '내용'], [
        ['과정명', c['title'].replace('\n', ' ')],
        ['대상', c['audience'] or '-'],
        ['구성', f"{len(L)}개 강의 · 총 {sum(l['minutes'] for l in L)}분"],
        ['강사', c['instructor'] or '-'],
    ]), '']
    if c['goals']:
        o += ['## 과정 목표', '', bullets(c['goals']), '']
    if c['preparation']:
        o += ['## 준비물', '', bullets(c['preparation']), '']
    o += ['## 강의 구성', '', table(['차시', '강의명', '수준', '시간', '핵심 내용'],
          [[l['num'], l['title'], l['level'], f"{l['minutes']}분", l['description']] for l in L]), '']
    for l in L:
        o += ['---', '', f"## {l['num']}강. {l['title']}", '']
        o += [f"**수준** {l['level']}　·　**시간** {l['minutes']}분　·　**슬라이드** {len(l['slides'])}장", '']
        if l['description']:
            o += [l['description'], '']
        if l['objectives']:
            o += ['### 학습 목표', '', bullets(l['objectives']), '']
        if l['materials']:
            o += ['### 준비물', '', bullets(l['materials']), '']
        if l['scenario']:
            o += ['### 강의 시나리오 (타임라인)', '', table(['시간', '단계', '진행 내용', '학습자 활동'],
                  [[s['time'], s['stage'], s['activity'], s['learner']] for s in l['scenario']]), '']
            o += ['### 단계별 진행 대본', '']
            for s in l['scenario']:
                o += [f"#### [{s['time']}] {s['stage']} — {s['activity']}", '']
                if s['script']:
                    o += ['**강사 멘트**', ''] + [f'> {ln}' if ln else '>' for ln in s['script'].split('\n')] + ['']
                if s['learner']:
                    o += [f"- **학습자 활동**: {s['learner']}"]
                if s['tip']:
                    o += [f"- **진행 팁**: {s['tip']}"]
                o += ['']
        if l['slides']:
            o += ['### 슬라이드 구성', '', table(['No', '제목', '핵심 내용'],
                  [[f'{i + 1:02d}', s['title'], ' / '.join(slide_points(s))] for i, s in enumerate(l['slides'])]), '']
        if l['prompts']:
            o += ['### 실습 프롬프트', '']
            for p in l['prompts']:
                o += [f"#### {p['name']}", '', '```', p['text'], '```', '']
        if l['assessment']:
            o += ['### 확인 및 평가', '', bullets(l['assessment']), '']
        if l['homework']:
            o += ['### 과제', '', l['homework'], '']
        if l['note']:
            o += ['### 강사용 노트', '', l['note'], '']
    return '\n'.join(o).rstrip() + '\n'


def slide_points(s):
    pts = list(s.get('bullets', []))
    for side in ('left', 'right'):
        if s.get(side):
            pts.append(s[side].get('title', ''))
    pts += [x.get('title', '') for x in s.get('steps', [])]
    if s.get('subtitle') and not pts:
        pts = [s['subtitle']]
    return [str(p) for p in pts if p][:4]


def build_prompts_md(d):
    o = [f"# {d['course']['prompt_page']['title']}", '']
    for l in d['lessons']:
        if not l['prompts']:
            continue
        o += [f"## {l['num']}　{l['title']}", '']
        for p in l['prompts']:
            o += [f"### {p['name']}", '', p['text'], '']
    return '\n'.join(o).rstrip() + '\n'


if __name__ == '__main__':
    d = load(sys.argv[1])
    open(sys.argv[2], 'w', encoding='utf-8').write(build_md(d))
