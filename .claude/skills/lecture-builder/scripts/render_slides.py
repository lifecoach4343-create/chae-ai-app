"""PPTX → 1600×900 PNG (LibreOffice → PDF → pdftoppm). 사이트는 이 PNG를 '원본 슬라이드'로 그대로 보여준다.

한글 글꼴: 'Malgun Gothic'이 없으면 NanumGothic → Noto Sans CJK KR → WenQuanYi 순으로 대체 (fontconfig 별칭).
"""
import os, glob, shutil, subprocess, sys, tempfile

FONTCONF = """<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>
<include ignore_missing="yes">/etc/fonts/fonts.conf</include>
%s
</fontconfig>"""
MAP = {'Malgun Gothic': ['NanumGothic', 'Noto Sans CJK KR', 'WenQuanYi Zen Hei'],
       '맑은 고딕': ['NanumGothic', 'Noto Sans CJK KR', 'WenQuanYi Zen Hei'],
       'Consolas': ['NanumGothicCoding', 'DejaVu Sans Mono'],
       'Arial': ['Liberation Sans', 'NanumGothic'],
       'Segoe UI Symbol': ['DejaVu Sans']}


def fontconfig(tmp):
    rules = ''
    for src, dst in MAP.items():
        rules += (f'<match target="pattern"><test qual="any" name="family"><string>{src}</string></test>'
                  + ''.join(f'<edit name="family" mode="prepend" binding="strong"><string>{x}</string></edit>' for x in reversed(dst))
                  + '</match>\n')
    p = os.path.join(tmp, 'fonts.conf')
    open(p, 'w').write(FONTCONF % rules)
    return p


def render(pptx, out_dir, width=1600):
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, FONTCONFIG_FILE=fontconfig(tmp), HOME=tmp)
        pdf = os.path.join(tmp, os.path.splitext(os.path.basename(pptx))[0] + '.pdf')
        try:  # UNO로 열어 한글-영문 자동 간격(ParaIsCharacterDistance)을 끄고 PDF로 내보낸다
            subprocess.run([sys.executable, os.path.abspath(__file__), '--uno', pptx, pdf, tmp], check=True, env=env, timeout=300)
        except Exception:
            subprocess.run(['soffice', '--headless', '--norestore', f'-env:UserInstallation=file://{tmp}/lo',
                            '--convert-to', 'pdf', '--outdir', tmp, pptx], check=True, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
        subprocess.run(['pdftoppm', '-png', '-scale-to-x', str(width), '-scale-to-y', str(width * 9 // 16), pdf,
                        os.path.join(tmp, 's')], check=True)
        files = sorted(glob.glob(os.path.join(tmp, 's-*.png')), key=lambda f: int(f.rsplit('-', 1)[1][:-4]))
        for i, f in enumerate(files, 1):
            shutil.move(f, os.path.join(out_dir, f'{i}.png'))
        if pdf and os.path.exists(pdf):
            shutil.copy(pdf, os.path.join(out_dir, 'slides.pdf'))
    return len(files)


def uno_export(pptx, pdf, tmp):
    import time, uno
    from com.sun.star.beans import PropertyValue
    pipe = 'lb' + str(os.getpid())
    proc = subprocess.Popen(['soffice', '--headless', '--invisible', '--norestore', '--nologo',
                             f'-env:UserInstallation=file://{tmp}/lo', f'--accept=pipe,name={pipe};urp;'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        res = uno.getComponentContext().ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', uno.getComponentContext())
        for _ in range(120):
            try:
                ctx = res.resolve(f'uno:pipe,name={pipe};urp;StarOffice.ComponentContext'); break
            except Exception:
                time.sleep(0.5)
        desk = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
        def pv(n, v):
            p = PropertyValue(); p.Name, p.Value = n, v; return p
        doc = desk.loadComponentFromURL(uno.systemPathToFileUrl(os.path.abspath(pptx)), '_blank', 0, (pv('Hidden', True),))
        def fix(shape):
            if shape.supportsService('com.sun.star.drawing.GroupShape'):
                for k in range(shape.getCount()):
                    fix(shape.getByIndex(k))
                return
            if not hasattr(shape, 'getText'):
                return
            try:
                en = shape.getText().createEnumeration()
                while en.hasMoreElements():
                    en.nextElement().setPropertyValue('ParaIsCharacterDistance', False)
            except Exception:
                pass
        pages = doc.getDrawPages()
        for i in range(pages.getCount()):
            pg = pages.getByIndex(i)
            for k in range(pg.getCount()):
                fix(pg.getByIndex(k))
        doc.storeToURL(uno.systemPathToFileUrl(pdf), (pv('FilterName', 'impress_pdf_Export'),))
        doc.close(True)
        try:
            desk.terminate()
        except Exception:
            pass
    finally:
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == '--uno':
    uno_export(*sys.argv[2:5])
elif __name__ == '__main__':
    print(render(sys.argv[1], sys.argv[2]), 'slides')
