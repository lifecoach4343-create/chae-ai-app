"""Markdown → HWPX (한글 OWPML) 변환기. 외부 라이브러리 없이 표준 zip + XML로 작성.

지원: # ~ ####, 문단, **굵게**, `코드`, - 글머리, 1. 번호, > 인용, 표(|), ``` 코드블록, --- (쪽 나눔)
사용: python3 md_to_hwpx.py 강의안.md 강의안.hwpx ["문서 제목"]
"""
import re, sys, zipfile
from xml.sax.saxutils import escape

NS = ('xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
      'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
      'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" '
      'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
      'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
      'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
      'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" '
      'xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" '
      'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
      'xmlns:dc="http://purl.org/dc/elements/1.1/" '
      'xmlns:opf="http://www.idpf.org/2007/opf/" '
      'xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" '
      'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" '
      'xmlns:epub="http://www.idpf.org/2007/ops" '
      'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"')

INK, BLUE, GRAY = '#161815', '#2D4EFA', '#53564F'
TEXT_W = 42520  # A4(59528) - 좌우 여백 8504*2
LANGS = ['HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER']

# 글자 모양: (id, 크기 pt*100, 색, 굵게, 글꼴 id[0=맑은 고딕,1=Consolas])
CHARS = {
    'body': (0, 1050, INK, False, 0), 'bold': (1, 1050, INK, True, 0),
    'title': (2, 2400, INK, True, 0), 'h1': (3, 1700, INK, True, 0),
    'h2': (4, 1350, BLUE, True, 0), 'h3': (5, 1150, INK, True, 0),
    'kicker': (6, 950, BLUE, True, 1), 'th': (7, 950, INK, True, 0),
    'td': (8, 950, INK, False, 0), 'tdb': (9, 950, INK, True, 0),
    'quote': (10, 1050, GRAY, False, 0), 'quoteb': (11, 1050, GRAY, True, 0),
    'code': (12, 950, INK, False, 1), 'h4': (13, 1100, BLUE, True, 0),
}
# 문단 모양: (id, 정렬, 왼쪽, 들여쓰기, 위, 아래, 줄간격%, 테두리채우기 id)
PARAS = {
    'body': (0, 'JUSTIFY', 0, 0, 0, 400, 165, 1), 'title': (1, 'LEFT', 0, 0, 0, 600, 140, 1),
    'h1': (2, 'LEFT', 0, 0, 1600, 500, 140, 1), 'h2': (3, 'LEFT', 0, 0, 1000, 300, 140, 1),
    'li': (4, 'JUSTIFY', 1800, -1000, 0, 200, 160, 1), 'cell': (5, 'LEFT', 0, 0, 0, 0, 140, 1),
    'quote': (6, 'JUSTIFY', 1400, 0, 0, 100, 160, 5), 'code': (7, 'LEFT', 600, 0, 0, 0, 150, 6),
    'kicker': (8, 'LEFT', 0, 0, 0, 200, 140, 1), 'h3': (9, 'LEFT', 0, 0, 700, 200, 140, 1),
}


def _border(i, line='NONE', fill=None, left=None):
    def side(n, t):
        return f'<hh:{n} type="{t}" width="0.12 mm" color="#BFC1BA"/>'
    lf = left or line
    x = (f'<hh:borderFill id="{i}" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">'
         '<hh:slash type="NONE" Crooked="0" isCounter="0"/><hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
         + (f'<hh:leftBorder type="{lf}" width="{"0.7 mm" if left else "0.12 mm"}" color="{BLUE if left else "#BFC1BA"}"/>')
         + side('rightBorder', line) + side('topBorder', line) + side('bottomBorder', line)
         + '<hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')
    if fill:
        x += f'<hc:fillBrush><hc:winBrush faceColor="{fill}" hatchColor="#999999" alpha="0"/></hc:fillBrush>'
    return x + '</hh:borderFill>'


def header_xml():
    fonts = ''.join(
        f'<hh:fontface lang="{lg}" fontCnt="2">'
        '<hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0"><hh:typeInfo familyType="FCAT_GOTHIC" weight="6" proportion="4" contrast="0" strokeVariation="1" armStyle="1" letterform="1" midline="1" xHeight="1"/></hh:font>'
        '<hh:font id="1" face="Consolas" type="TTF" isEmbedded="0"><hh:typeInfo familyType="FCAT_GOTHIC" weight="5" proportion="9" contrast="0" strokeVariation="1" armStyle="1" letterform="1" midline="1" xHeight="1"/></hh:font>'
        '</hh:fontface>' for lg in LANGS)
    borders = (_border(1) + _border(2) + _border(3, 'SOLID') + _border(4, 'SOLID', '#EFF0EB')
               + _border(5, 'NONE', None, 'SOLID') + _border(6, 'NONE', '#F0F1EB'))
    def all7(tag, v):
        return f'<hh:{tag} ' + ' '.join(f'{k.lower()}="{v}"' for k in LANGS) + '/>'
    chars = ''
    for cid, h, col, bold, font in sorted(CHARS.values()):
        chars += (f'<hh:charPr id="{cid}" height="{h}" textColor="{col}" shadeColor="none" useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">'
                  + all7('fontRef', font) + all7('ratio', 100) + all7('spacing', -3 if h >= 1350 else 0)
                  + all7('relSz', 100) + all7('offset', 0) + ('<hh:bold/>' if bold else '')
                  + '<hh:underline type="NONE" shape="SOLID" color="#000000"/><hh:strikeout shape="NONE" color="#000000"/>'
                  '<hh:outline type="NONE"/><hh:shadow type="NONE" color="#B2B2B2" offsetX="10" offsetY="10"/></hh:charPr>')
    paras = ''
    for pid, al, left, ind, prev, nxt, ls, bf in sorted(PARAS.values()):
        paras += (f'<hh:paraPr id="{pid}" tabPrIDRef="0" condense="0" fontLineHeight="0" snapToGrid="1" suppressLineNumbers="0" checked="0">'
                  f'<hh:align horizontal="{al}" vertical="BASELINE"/><hh:heading type="NONE" idRef="0" level="0"/>'
                  '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="KEEP_WORD" widowOrphan="0" keepWithNext="0" keepLines="0" pageBreakBefore="0" lineWrap="BREAK"/>'
                  '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
                  f'<hh:margin><hc:intent value="{ind}" unit="HWPUNIT"/><hc:left value="{left}" unit="HWPUNIT"/><hc:right value="0" unit="HWPUNIT"/>'
                  f'<hc:prev value="{prev}" unit="HWPUNIT"/><hc:next value="{nxt}" unit="HWPUNIT"/></hh:margin>'
                  f'<hh:lineSpacing type="PERCENT" value="{ls}" unit="HWPUNIT"/>'
                  f'<hh:border borderFillIDRef="{bf}" offsetLeft="{400 if bf in (5, 6) else 0}" offsetRight="{400 if bf == 6 else 0}" offsetTop="{200 if bf == 6 else 0}" offsetBottom="{200 if bf == 6 else 0}" connect="1" ignoreMargin="0"/></hh:paraPr>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
            f'<hh:head {NS} version="1.4" secCnt="1">'
            '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>'
            f'<hh:refList><hh:fontfaces itemCnt="7">{fonts}</hh:fontfaces>'
            f'<hh:borderFills itemCnt="6">{borders}</hh:borderFills>'
            f'<hh:charProperties itemCnt="{len(CHARS)}">{chars}</hh:charProperties>'
            '<hh:tabProperties itemCnt="1"><hh:tabPr id="0" autoTabLeft="0" autoTabRight="0"/></hh:tabProperties>'
            f'<hh:paraProperties itemCnt="{len(PARAS)}">{paras}</hh:paraProperties>'
            '<hh:styles itemCnt="1"><hh:style id="0" type="PARA" name="바탕글" engName="Normal" paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" langID="1042" lockForm="0"/></hh:styles>'
            '</hh:refList><hh:compatibleDocument targetProgram="HWP201X"><hh:layoutCompatibility/></hh:compatibleDocument>'
            '<hh:docOption><hh:linkinfo path="" pageInherit="0" footnoteInherit="0"/></hh:docOption>'
            '<hh:trackchageConfig flags="56"/></hh:head>')


SEC_PR = ('<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">'
          '<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/><hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>'
          '<hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>'
          '<hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>'
          '<hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY"><hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/></hp:pagePr>'
          '<hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr>'
          '<hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr>'
          '<hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill>'
          '<hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill>'
          '<hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill>'
          '</hp:secPr><hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl>')


class Writer:
    def __init__(self):
        self.out, self.pid, self.first, self.tid = [], 0, True, 1000

    def _id(self):
        self.pid += 1
        return self.pid

    def runs(self, text, base='body', boldk='bold'):
        """**굵게**, `코드` 인라인 처리 → hp:run 목록"""
        res = []
        for part in re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', text):
            if not part:
                continue
            k = base
            if part.startswith('**') and part.endswith('**'):
                part, k = part[2:-2], boldk
            elif part.startswith('`') and part.endswith('`'):
                part, k = part[1:-1], 'code'
            res.append(f'<hp:run charPrIDRef="{CHARS[k][0]}"><hp:t>{escape(part)}</hp:t></hp:run>')
        return ''.join(res) or f'<hp:run charPrIDRef="{CHARS[base][0]}"/>'

    def para(self, inner, pk='body', page_break=False, inner_only=False):
        lead = ''
        if self.first and not inner_only:
            lead, self.first = f'<hp:run charPrIDRef="0">{SEC_PR}</hp:run>', False
        x = (f'<hp:p id="{self._id()}" paraPrIDRef="{PARAS[pk][0]}" styleIDRef="0" pageBreak="{1 if page_break else 0}" columnBreak="0" merged="0">'
             f'{lead}{inner}</hp:p>')
        if inner_only:
            return x
        self.out.append(x)

    def table(self, rows):
        ncol = max(len(r) for r in rows)
        # 내용 길이에 비례한 열 너비
        lens = [max(4, min(40, max(len(r[i]) if i < len(r) else 0 for r in rows))) for i in range(ncol)]
        ws = [int(TEXT_W * v / sum(lens)) for v in lens]
        ws[-1] = TEXT_W - sum(ws[:-1])
        trs = []
        for ri, r in enumerate(rows):
            tcs = []
            for ci in range(ncol):
                txt = r[ci] if ci < len(r) else ''
                head = ri == 0
                ps = ''.join(self.para(self.runs(line, 'th' if head else 'td', 'th' if head else 'tdb'), 'cell', inner_only=True)
                             for line in (txt.split('<br>') or ['']))
                tcs.append(f'<hp:tc name="" header="{1 if head else 0}" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{4 if head else 3}">'
                           f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{ps}</hp:subList>'
                           f'<hp:cellAddr colAddr="{ci}" rowAddr="{ri}"/><hp:cellSpan colSpan="1" rowSpan="1"/>'
                           f'<hp:cellSz width="{ws[ci]}" height="1600"/><hp:cellMargin left="510" right="510" top="200" bottom="200"/></hp:tc>')
            trs.append('<hp:tr>' + ''.join(tcs) + '</hp:tr>')
        self.tid += 1
        tbl = (f'<hp:tbl id="{self.tid}" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{len(rows)}" colCnt="{ncol}" cellSpacing="0" borderFillIDRef="3" noAdjust="0">'
               f'<hp:sz width="{TEXT_W}" widthRelTo="ABSOLUTE" height="{1600 * len(rows)}" heightRelTo="ABSOLUTE" protect="0"/>'
               '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
               '<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:inMargin left="510" right="510" top="141" bottom="141"/>'
               + ''.join(trs) + '</hp:tbl>')
        self.para(f'<hp:run charPrIDRef="0">{tbl}<hp:t/></hp:run>', 'cell')
        self.para(f'<hp:run charPrIDRef="0"/>', 'body')


def convert(md, title):
    w = Writer()
    lines = md.split('\n')
    i, title_done, pending_break = 0, False, False
    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not s:
            i += 1; continue
        if s.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            i += 1
            for c in code or ['']:
                w.para(f'<hp:run charPrIDRef="{CHARS["code"][0]}"><hp:t>{escape(c)}</hp:t></hp:run>', 'code')
            w.para('<hp:run charPrIDRef="0"/>', 'body')
            continue
        if s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                r = lines[i].strip().strip('|')
                cells = [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', r)]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                w.table(rows)
            continue
        if re.fullmatch(r'-{3,}|\*{3,}', s):
            pending_break = True; i += 1; continue
        m = re.match(r'(#{1,4})\s+(.*)', s)
        if m:
            lv, txt = len(m.group(1)), m.group(2)
            if lv == 1 and not title_done:
                w.para(w.runs(txt, 'title', 'title'), 'title'); title_done = True
            else:
                key = {1: 'h1', 2: 'h1', 3: 'h2', 4: 'h3'}[lv]
                ck = {1: 'h1', 2: 'h1', 3: 'h2', 4: 'h4'}[lv]
                w.para(w.runs(txt, ck, ck), key, page_break=pending_break)
            pending_break = False
            i += 1; continue
        if s.startswith('>'):
            txt = s.lstrip('>').strip()
            if i == 1 or (title_done and w.pid <= 2):
                w.para(w.runs(txt, 'kicker', 'kicker'), 'kicker')
            else:
                w.para(w.runs(txt, 'quote', 'quoteb'), 'quote')
            i += 1; continue
        m = re.match(r'[-*]\s+(.*)', s)
        if m:
            w.para(f'<hp:run charPrIDRef="{CHARS["h2"][0]}"><hp:t>•  </hp:t></hp:run>' + w.runs(m.group(1)), 'li')
            i += 1; continue
        m = re.match(r'(\d+)[.)]\s+(.*)', s)
        if m:
            w.para(f'<hp:run charPrIDRef="{CHARS["h2"][0]}"><hp:t>{m.group(1)}.  </hp:t></hp:run>' + w.runs(m.group(2)), 'li')
            i += 1; continue
        buf = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'(#|>|[-*]\s|\d+[.)]\s|\||```)', lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        w.para(w.runs(' '.join(buf)), 'body')
    if w.first:
        w.para('<hp:run charPrIDRef="0"/>', 'body')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
            f'<hs:sec {NS}>' + ''.join(w.out) + '</hs:sec>')


def write_hwpx(md_text, out, title='강의안'):
    sec = convert(md_text, title)
    preview = re.sub(r'[#>*`|]', '', md_text)[:1000]
    files = {
        'version.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="1" buildNumber="0" os="1" xmlVersion="1.4" application="Hancom Office Hangul" appVersion="12, 0, 0, 0"/>',
        'META-INF/container.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"><ocf:rootfiles><ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/><ocf:rootfile full-path="Preview/PrvText.txt" media-type="text/plain"/></ocf:rootfiles></ocf:container>',
        'META-INF/manifest.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><odf:manifest xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>',
        'Contents/content.hpf': ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                                 f'<opf:package {NS} version="" unique-identifier="" id=""><opf:metadata><opf:title>{escape(title)}</opf:title><opf:language>ko</opf:language>'
                                 '<opf:meta name="creator" content="text">lecture-builder</opf:meta></opf:metadata>'
                                 '<opf:manifest><opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
                                 '<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>'
                                 '<opf:item id="settings" href="settings.xml" media-type="application/xml"/></opf:manifest>'
                                 '<opf:spine><opf:itemref idref="header" linear="yes"/><opf:itemref idref="section0" linear="yes"/></opf:spine></opf:package>'),
        'Contents/header.xml': header_xml(),
        'Contents/section0.xml': sec,
        'settings.xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><ha:HWPApplicationSetting xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"><ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/></ha:HWPApplicationSetting>',
        'Preview/PrvText.txt': preview,
    }
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr(zipfile.ZipInfo('mimetype'), 'application/hwp+zip', compress_type=zipfile.ZIP_STORED)
        for name, data in files.items():
            z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    write_hwpx(open(src, encoding='utf-8').read(), dst, sys.argv[3] if len(sys.argv) > 3 else '강의안')
    print('HWPX →', dst)
