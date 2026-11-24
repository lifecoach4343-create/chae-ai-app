# 레퍼런스 사이트 설계·디자인 명세

원본: https://wkdream8.dothome.co.kr/sb/ (생활 앱 제작 실습실 · 성북50+)
구성 파일: `index.html`(뼈대) · `style.css` · `course.js`(데이터) · `app.js`(해시 라우팅 SPA). 프레임워크·외부 라이브러리·웹폰트 CDN 없음.
`assets/site/style.css`는 원본 CSS를 **한 글자도 바꾸지 않고** 복사한 뒤, 맨 아래에 강의안 페이지용 규칙만 덧붙였다.

## 1. 디자인 토큰

| 토큰 | 값 | 쓰임 |
|---|---|---|
| `--ink` | `#161815` | 본문 글자, 굵은 구분선(2px), primary 버튼 배경 |
| `--blue` | `#2d4efa` | 포인트: 로고 박스, kicker, level, 화살표, hover, focus |
| `--paper` | `#fafaf7` | 페이지 배경 |
| `--line` | `#bfc1ba` | 얇은 구분선(1px), 카드 사이 세로선 |
| 보조 회색 | `#53564f` `#565a53` `#646861` `#61655d` | 설명문, small, footer |
| 패널 | `#eeefe9`(intro) `#eff1ed`(art 점무늬 배경) `#f0f1eb`(prompt) `#eff0eb`(th) | 면 구분 |
| hover | `#e9ecff` | 카드·intro hover 배경 |
| 점무늬 | `radial-gradient(#b4b9b1 1px, transparent 1px)` 10px 격자 | hero 오른쪽 일러스트 |
| 진한 파랑 | `#182994` | 책 등(book spine) 선 |

## 2. 글꼴

- 본문: `Inter, "Malgun Gothic", Arial, sans-serif` + `word-break: keep-all`
- 숫자 디스플레이: `Arial` 800~900 (`.num`, `.fact b`, `.book b`), 자간 -0.05 ~ -0.09em
- 모노(kicker·level·mono): `Consolas, monospace` 700 12px, 자간 .09em
- 제목: h1 `clamp(48px,5.7vw,86px)` 자간 -.085em 행간 1.12 / 상세 h1 `clamp(36px,4.3vw,64px)` / section h2 28px / card h3 `clamp(21px,2vw,29px)`
- 로고: 950 weight 23px 자간 -1.5px

## 3. 레이아웃·컴포넌트

- 컨테이너: `.bar, main, footer { max-width:1340px; margin:auto; padding-inline:5vw }`
- header: 높이 76px, 아래 1px ink 선. 로고(파란 36px 정사각형 안 흰 `✳`) · 오른쪽 nav(14px 700) · `PDF 저장 ↗` 테두리 버튼
- hero: `grid 1.4fr 1fr` — 왼쪽 kicker(앞에 28×2px 선) / h1 2줄 / 설명 17px · 오른쪽 `.art` 244px 점무늬 패널 + `-10°` 회전된 파란 책(`.book`, 계단식 box-shadow) + 모서리 `+`
- facts: 4칸 grid, 위아래 2px ink 선, 칸 사이 1px line. 큰 숫자(32px Arial) + 라벨(14px bold)
- section 제목: 아래 2px 선, 오른쪽 mono small(`COURSE INDEX / 00—03`)
- intro(오리엔테이션): 회색 띠, 큰 번호, level, 제목, 오른쪽 `→`
- cards: 3열 grid, 아래 2px 선, 칸 사이 1px line. 번호 48px · level(블루 mono) · h3 · 설명 · `↗`. hover시 `#e9ecff`
- 버튼: 투명 배경 + 1px ink 테두리, 10px 15px, 700. `.primary`는 ink 배경 흰 글자. 모서리 없음(radius 0), 그림자 없음
- footer: 위 1px line, 13px, 양끝 정렬
- 반응형 `max-width:760px`: header 63px, hero `1fr .55fr`, 책 scale .64, facts 세로 쌓기, cards 1열, 화살표 절대 위치
- print: header/footer/tools/pager 숨기고 `.printslides`(모든 슬라이드 이미지)만 한 장씩 출력
- fullscreen: `:fullscreen`에서 header/footer/detail-top 숨기고 슬라이드 이미지를 `100dvh-85px` 높이로

## 4. 페이지(해시 라우트)

| 라우트 | 내용 |
|---|---|
| `#home` (기본) | hero → facts → 강의 목록(intro + cards) |
| `#lesson/{id}/{page}` | ← 강의 목록 · h1 · 설명 · tools(원본 교안 ↓ / 외부 도구 ↗ / 실습 프롬프트 / 강사용 노트 / 전체 화면 / 도움말) · 슬라이드 PNG(1600×900) · pager(← 이전 / select / 다음 →, 마지막엔 다음 강의 →) |
| `#prompts` | kicker `PRACTICE LIBRARY` · h1 · 전체 원문 ↓ · 강의별 h2 + `.prompt` 박스(복사 버튼) |
| `#plan`, `#plan/{id}` | **(스킬 추가)** 강의안: MD/HWPX 다운로드 + 강의별 시나리오 표(레퍼런스의 미사용 `table/th/td/.tablewrap` 스타일 활용) |

## 5. 동작(JavaScript)

- `hashchange` → `render()` 로 main을 다시 그림, 문서 제목 갱신, 맨 위로 스크롤
- 키보드: `← →`/`Space` 이동, `Home/End`, `N` 강사용 노트(dialog), `F` 전체 화면, `P` 인쇄, `?` 도움말
- 프롬프트 복사: `navigator.clipboard` → 실패 시 textarea+execCommand → 그래도 실패 시 dialog로 원문 표시. 성공 시 하단 `#notice` 토스트 1.8초
- 슬라이드는 **PPTX를 렌더링한 이미지**를 그대로 보여주고, 원본 PPTX는 `materials/{id}.pptx`로 다운로드

## 6. 슬라이드(PPTX) 디자인 규칙 — 사이트와 같은 언어

16:9(13.333×7.5in), 배경 paper. 상단: 블루 정사각형 로고 + 브랜드명, 오른쪽 `NN강 / 03 — 12`(mono), 아래 ink 선. 하단: line 선 + 강의명 / kicker.
kicker는 블루 선 + mono 대문자. 제목은 굵게·자간 좁게. 목록은 `01` 블루 mono 번호 + 얇은 line 구분선. 강조 박스는 `#e9ecff` + 왼쪽 블루 바.
표지는 hero와 같은 구도(왼쪽 제목, 오른쪽 점무늬 패널 + 회전한 파란 책, 아래 facts 띠). 마무리는 ink 배경 반전.
