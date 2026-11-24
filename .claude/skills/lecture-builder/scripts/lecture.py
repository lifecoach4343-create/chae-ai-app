"""lecture.json 로더: 기본값을 채우고 번호·파일명을 계산한다 (모든 빌더가 공유)."""
import json, re


def _slug(s):
    s = re.sub(r'[\\/:*?"<>|]+', ' ', s).strip()
    return re.sub(r'\s+', ' ', s)


def load(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    c = d.setdefault('course', {})
    b = d.setdefault('brand', {})
    b.setdefault('name', '강의실'); b.setdefault('sub', '실습실'); b.setdefault('mark', '✳')
    c.setdefault('title', '강의 교안집')
    c.setdefault('kicker', b['name'].upper())
    c.setdefault('summary', '')
    c.setdefault('footer', '')
    c.setdefault('goals', []); c.setdefault('preparation', [])
    c.setdefault('audience', ''); c.setdefault('instructor', '')
    lessons = d['lessons']
    has_orient = bool(lessons and lessons[0].get('orientation'))
    for i, l in enumerate(lessons):
        l['id'] = i
        l.setdefault('num', f'{(i if has_orient else i + 1):02d}')
        l.setdefault('level', '시작 안내' if l.get('orientation') else '입문')
        l.setdefault('minutes', 90)
        l.setdefault('description', '')
        for k in ('objectives', 'materials', 'scenario', 'slides', 'prompts', 'assessment'):
            l.setdefault(k, [])
        l.setdefault('note', ''); l.setdefault('homework', '')
        for s in l['scenario']:
            for k in ('time', 'stage', 'activity', 'script', 'learner', 'tip'):
                s.setdefault(k, '')
        for s in l['slides']:
            s.setdefault('layout', 'bullets'); s.setdefault('title', ''); s.setdefault('notes', '')
        l['file'] = _slug(f"{l['num']}강 {l['title']}") + '.pptx'
    book = c.setdefault('book', {})
    book.setdefault('top', c['kicker'].split('/')[0].strip())
    book.setdefault('num', lessons[-1]['num'] if lessons else '01')
    book.setdefault('title', c['title'].split('\n')[0][:10])
    book.setdefault('bottom', 'LECTURE WORKBOOK')
    if 'facts' not in c:
        n_main = sum(1 for l in lessons if not l.get('orientation'))
        n_prompt = sum(len(l['prompts']) for l in lessons)
        n_slide = sum(len(l['slides']) for l in lessons)
        mins = sorted({l['minutes'] for l in lessons if not l.get('orientation')}) or [lessons[0]['minutes']]
        c['facts'] = [[f'{n_main:02d}', '실습 강의'],
                      [f'{mins[-1]}분', '강의당 시간'],
                      [f'{n_slide:02d}', '슬라이드'],
                      [f'{n_prompt:02d}', '실습 프롬프트'] if n_prompt else [f"{sum(len(l['scenario']) for l in lessons):02d}", '진행 단계']]
    pp = c.setdefault('prompt_page', {})
    pp.setdefault('title', '실습 프롬프트'); pp.setdefault('kicker', 'PRACTICE LIBRARY')
    pp.setdefault('desc', '프롬프트를 하나씩 복사해 실습에 활용하세요.')
    d.setdefault('slug', 'lecture')
    d['doc_name'] = _slug(c['title'].replace('\n', ' '))
    return d
