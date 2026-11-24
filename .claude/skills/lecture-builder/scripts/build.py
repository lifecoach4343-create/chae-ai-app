#!/usr/bin/env python3
"""한 번에 빌드: lecture.json → 강의안(MD·HWPX) → PPTX → 슬라이드 PNG → 강의 웹사이트

사용: python3 build.py lecture.json -o output/<slug>
결과:
  <out>/강의안/<제목> 강의안.md, .hwpx
  <out>/PPT/<NN강 제목>.pptx
  <out>/site/ (index.html 열면 바로 동작, 정적 호스팅에 폴더째 업로드)
  <out>/<slug>-site.zip
"""
import argparse, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lecture import load
from make_md import build_md, build_prompts_md
from md_to_hwpx import write_hwpx
from make_pptx import build_lesson
from render_slides import render
from make_site import build_site


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('json')
    ap.add_argument('-o', '--out', default='output')
    ap.add_argument('--skip-render', action='store_true', help='PNG 렌더링 생략(이미 있을 때)')
    a = ap.parse_args()
    d = load(a.json)
    out = os.path.abspath(a.out)
    plan_dir, ppt_dir, work = os.path.join(out, '강의안'), os.path.join(out, 'PPT'), os.path.join(out, '.build')
    for p in (plan_dir, ppt_dir, work):
        os.makedirs(p, exist_ok=True)

    md = build_md(d)
    md_path = os.path.join(plan_dir, d['doc_name'] + ' 강의안.md')
    open(md_path, 'w', encoding='utf-8').write(md)
    hwpx_path = os.path.join(plan_dir, d['doc_name'] + ' 강의안.hwpx')
    write_hwpx(md, hwpx_path, d['doc_name'] + ' 강의안')
    prompts_md = os.path.join(work, 'prompts.md')
    open(prompts_md, 'w', encoding='utf-8').write(build_prompts_md(d))
    print('✓ 강의안 MD/HWPX')

    for l in d['lessons']:
        p = os.path.join(work, f"{l['id']}.pptx")
        build_lesson(d, l, p)
        shutil.copy(p, os.path.join(ppt_dir, l['file']))
        if not a.skip_render:
            n = render(p, os.path.join(work, 'png', str(l['id'])))
            print(f"✓ PPT {l['file']} · {n}장 렌더링")

    site = os.path.join(out, 'site')
    build_site(d, site, work, os.path.join(work, 'png'), md_path, hwpx_path, prompts_md)
    z = shutil.make_archive(os.path.join(out, d['slug'] + '-site'), 'zip', site)
    print('✓ 웹사이트', site)
    print('✓ ZIP', z)


if __name__ == '__main__':
    main()
