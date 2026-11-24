"""레퍼런스 사이트 구조 그대로 강의 웹사이트 생성 (HTML·CSS·JavaScript만 사용).

site/
  index.html · style.css · app.js · course.js(데이터)
  slides/{강의id}/{n}.png        ← 제작된 PPTX를 렌더링한 원본 슬라이드
  materials/{강의id}.pptx        ← 제작된 PPTX 그대로
  materials/lecture.md · lecture.hwpx · prompts.md
"""
import json, os, shutil
from xml.sax.saxutils import escape

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'site')


def course_data(d):
    c, L = d['course'], d['lessons']
    prompts, groups = [], []
    for l in L:
        items = []
        for p in l['prompts']:
            items.append({'name': p['name'], 'idx': len(prompts)})
            prompts.append(p['text'])
        groups.append({'title': f"{l['num']}　{l['title']}", 'items': items})
    pp = c['prompt_page']
    meta = {
        'brand': d['brand']['name'], 'siteTitle': c['title'].replace('\n', ' '), 'title': c['title'],
        'kicker': c['kicker'], 'summary': c['summary'], 'book': c['book'], 'facts': c['facts'],
        'external': c.get('external_link'), 'promptTitle': pp['title'], 'promptKicker': pp['kicker'], 'promptDesc': pp['desc'],
        'planDesc': c.get('plan_desc', '강의별 진행 시간표와 강사 멘트, 학습자 활동을 정리한 강의 시나리오입니다.'),
        'files': {'md': d['doc_name'] + ' 강의안.md', 'hwpx': d['doc_name'] + ' 강의안.hwpx', 'prompts': pp['title'] + '.md'},
    }
    lessons = [{
        'id': l['id'], 'num': l['num'], 'title': l['title'], 'level': l['level'], 'levelEn': l.get('level_en'),
        'minutes': l['minutes'], 'description': l['description'], 'orientation': bool(l.get('orientation')),
        'objectives': l['objectives'], 'note': l['note'], 'file': l['file'],
        'scenario': [{k: s[k] for k in ('time', 'stage', 'activity', 'script', 'learner', 'tip')} for s in l['scenario']],
        'slides': [{'title': s['title'], 'notes': s['notes']} for s in l['slides']],
    } for l in L]
    return {'meta': meta, 'lessons': lessons, 'prompts': prompts, 'promptGroups': groups}


def build_site(d, out, pptx_dir, png_dir, md_path, hwpx_path, prompts_md):
    os.makedirs(os.path.join(out, 'materials'), exist_ok=True)
    data = course_data(d)
    has_prompts = any(g['items'] for g in data['promptGroups'])
    nav = '<a href="#home">강의 목록</a><a href="#plan">강의안</a>' + (f'<a href="#prompts">{escape(data["meta"]["promptTitle"].replace("실습 ", ""))}</a>' if has_prompts else '')
    html = open(os.path.join(ASSETS, 'index.html'), encoding='utf-8').read()
    for k, v in {'SITE_TITLE': data['meta']['siteTitle'], 'BRAND': d['brand']['name'], 'BRAND_SUB': d['brand']['sub'],
                 'MARK': d['brand']['mark'], 'FOOTER': d['course']['footer'], 'NAV': nav}.items():
        html = html.replace('{{%s}}' % k, v if k == 'NAV' else escape(v))
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
    for f in ('style.css', 'app.js'):
        shutil.copy(os.path.join(ASSETS, f), os.path.join(out, f))
    with open(os.path.join(out, 'course.js'), 'w', encoding='utf-8') as f:
        f.write('const course = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    for l in d['lessons']:
        i = l['id']
        shutil.copy(os.path.join(pptx_dir, f'{i}.pptx'), os.path.join(out, 'materials', f'{i}.pptx'))
        dst = os.path.join(out, 'slides', str(i))
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(png_dir, str(i)), dst, ignore=shutil.ignore_patterns('*.pdf'))
    shutil.copy(md_path, os.path.join(out, 'materials', 'lecture.md'))
    shutil.copy(hwpx_path, os.path.join(out, 'materials', 'lecture.hwpx'))
    shutil.copy(prompts_md, os.path.join(out, 'materials', 'prompts.md'))
