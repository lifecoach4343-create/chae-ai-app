---
name: lecture-builder
description: 주제 하나로 강의 패키지 전체를 만든다 — 강의 시나리오가 포함된 강의안(Markdown + HWPX), 그 강의안 기반 PPT(PPTX 다운로드), 그리고 레퍼런스 사이트(wkdream8.dothome.co.kr/sb)와 같은 설계·UI·글꼴·색상의 강의 웹사이트(HTML·CSS·JavaScript만, 제작된 PPT를 그대로 슬라이드로 사용). 사용자가 "강의안 만들어줘", "강의 주제", "교안", "강의 사이트", "강의 PPT", "HWPX 강의안"처럼 강의 주제를 주거나 강의 자료/강의 웹사이트 제작을 요청할 때 사용.
---

# 강의 패키지 빌더 (강의안 → HWPX → PPTX → 강의 웹사이트)

사용자가 **주제**를 주면 아래 4가지를 한 번에 만든다.

| # | 산출물 | 형식 |
|---|---|---|
| 1 | 강의안 (강의 시나리오·강사 멘트·학습자 활동·시간표 포함) | `.md` + `.hwpx` |
| 2 | 강의별 발표 자료 (발표자 노트에 시나리오 대본) | `.pptx` |
| 3 | 강의 웹사이트 — 레퍼런스와 동일한 디자인, 제작된 PPT를 그대로 표시·다운로드 | `site/` (HTML·CSS·JS) + `.zip` |

핵심 원칙: **lecture.json 하나가 유일한 원본**이다. 내용은 JSON에만 쓰고, 나머지는 스크립트가 만든다. 그래서 강의안·PPT·사이트 내용이 항상 일치한다.

## 작업 순서

### 0단계 — 주제 확인
주제만 받았다면 아래를 합리적으로 정하고 시작한다(모호하면 한 번에 묶어 질문):
대상(연령·수준) · 강의 수(기본: 오리엔테이션 1 + 본강의 2~3) · 강의당 시간(기본 90분) · 실습 도구(external_link) · 브랜드/기관명(기본 "성북50+ / 실습실" 대신 사용자 기관명) · 과정 일차/월.

### 1단계 — 강의안 설계 → `lecture.json` 작성
`references/lecture-schema.md`를 읽고 작업 폴더(예: `output/<slug>/lecture.json`)에 작성한다. 품질 기준:

- **시나리오**: 강의마다 도입 → 전개(개념) → 실습 → 공유 → 정리 5단계 이상. `time` 구간이 빈틈없이 이어지고 합이 `minutes`와 같아야 한다.
- **script(강사 멘트)**: 강사가 그대로 읽을 수 있는 구어체 문장. 질문·확인 멘트 포함.
- **learner / tip**: 학습자가 실제로 하는 행동, 막히는 지점과 대처법.
- **slides**: 시나리오 순서를 따라 배치. 각 `notes`에 해당 구간 시간과 진행 멘트를 넣는다(사이트의 "강사용 노트"와 PPT 발표자 노트로 쓰임). 분량 기준은 스키마 표를 지킨다(넘치면 슬라이드를 나눈다).
- **prompts**: 실습이 있으면 복사해서 바로 쓸 수 있는 완결된 원문. 기본 → 응용 순.
- 첫 강의를 `orientation: true`로 두면 홈 화면이 레퍼런스처럼 "00 intro 띠 + 카드 3열"이 된다.

### 2단계 — 한 번에 빌드
```bash
python3 .claude/skills/lecture-builder/scripts/build.py output/<slug>/lecture.json -o output/<slug>
```
결과:
```
output/<slug>/
  강의안/<과정명> 강의안.md     ← 1. 강의안 (Markdown)
  강의안/<과정명> 강의안.hwpx   ← 1. 강의안 (한글)
  PPT/<NN강 강의명>.pptx        ← 2. 발표 자료
  site/                         ← 3. 강의 웹사이트 (index.html)
  <slug>-site.zip               ← 사이트 업로드용 압축
```
필요 도구: `python-pptx`, `lxml`, LibreOffice(`soffice` + Python `uno`), `pdftoppm`, 한글 글꼴(없으면 `apt-get install -y fonts-nanum`). `--skip-render`는 PNG 렌더링 생략.

개별 실행도 가능: `make_md.py`, `md_to_hwpx.py <md> <hwpx>`(사용자가 고친 MD를 다시 HWPX로), `make_pptx.py`, `render_slides.py <pptx> <폴더>`.

### 3단계 — 검수 (반드시)
1. 슬라이드 PNG를 몇 장 열어 글자 넘침·겹침 확인 → 넘치면 JSON 문구를 줄이거나 슬라이드를 나눠 재빌드.
2. Playwright로 `site/index.html`의 `#home`, `#lesson/1/1`, `#plan`, `#prompts`와 모바일 폭(390px)을 스크린샷해 확인하고, 콘솔 에러가 없는지 본다.
3. HWPX는 zip 첫 항목이 `mimetype`(무압축)이고 모든 XML이 well-formed인지 확인.

### 4단계 — 전달
강의안(MD·HWPX), PPTX, 사이트 zip을 사용자에게 보내고, 사이트는 폴더째 정적 호스팅(dothome 등 FTP 업로드, GitHub Pages)하면 된다고 안내한다. `file://`로 열어도 동작한다.

## 웹사이트 규칙 (레퍼런스 그대로)
상세 명세: `references/design-spec.md`. 요약:
- `assets/site/style.css`는 레퍼런스 원본 CSS 그대로 + 강의안 페이지용 규칙만 추가. **색상·글꼴·간격을 임의로 바꾸지 않는다.**
  토큰: `--ink #161815` `--blue #2d4efa` `--paper #fafaf7` `--line #bfc1ba` / 글꼴 `Inter, "Malgun Gothic", Arial` + `Consolas` + 숫자 `Arial 800`.
- 페이지: `#home`(hero·facts·강의 목록) · `#lesson/{id}/{n}`(슬라이드 뷰어) · `#prompts`(복사 박스) · `#plan`(강의안 시나리오 표, 스킬 추가).
- 슬라이드는 **제작된 PPTX를 렌더링한 PNG**를 그대로 쓰고, "원본 교안 ↓"는 그 PPTX 파일을 내려받는다.
- 단축키 ←/→/Space·Home/End·N·F·P·?, 전체 화면, 인쇄 시 모든 슬라이드 출력, 프롬프트 복사 토스트 — 모두 유지.
- 외부 라이브러리·프레임워크·빌드 도구 없이 HTML·CSS·JavaScript만 사용.

## 디자인을 바꿔야 할 때
사용자가 브랜드명·kicker·book 문구를 바꾸려면 JSON만 수정한다. 색상 자체를 바꾸라는 명시적 요청이 있을 때만 `style.css`의 `:root` 토큰과 `make_pptx.py` 상단 색 상수를 **함께** 바꿔 사이트와 PPT가 계속 일치하게 한다.
