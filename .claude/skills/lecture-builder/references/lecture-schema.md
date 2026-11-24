# lecture.json 스키마

모든 산출물(강의안 MD·HWPX, PPTX, 웹사이트)은 이 JSON 하나에서 만들어진다. 전체 예시는 `examples/sample-lecture.json`에 있다.

```jsonc
{
  "slug": "ai-daily-life",                 // 출력 zip 이름(영문)
  "brand": { "name": "성북50+", "sub": "실습실", "mark": "✳" },
  "course": {
    "title": "생성형 AI\n생활 활용 교안집",  // hero h1 (\n = 줄바꿈, 2줄 권장)
    "kicker": "SEONGBUK 50+　/　DAY 03",     // 영문 대문자 + 전각 공백 구분
    "summary": "첫 줄\n둘째 줄",              // hero 설명 2줄
    "book": { "top": "SEONGBUK 50+ LAB", "num": "03", "title": "AI 생활 활용", "bottom": "CHATGPT WORKBOOK" },
    "footer": "11월 과정　/　3일차",
    "audience": "대상", "instructor": "강사",
    "goals": ["과정 목표"], "preparation": ["준비물"],
    "facts": [["02","실습 강의"], ["90분","강의당 시간"], ["14","슬라이드"], ["05","실습 프롬프트"]], // 생략 시 자동 계산
    "external_link": { "label": "ChatGPT ↗", "url": "https://chatgpt.com/" },  // 실습 도구 (선택)
    "prompt_page": { "title": "실습 프롬프트", "kicker": "PRACTICE LIBRARY", "desc": "..." },
    "plan_desc": "강의안 페이지 설명 (선택)"
  },
  "lessons": [
    {
      "orientation": true,                 // 첫 강의만: 홈에서 회색 intro 띠로 표시, 번호 00
      "title": "강의명", "level": "입문", "level_en": "ORIENTATION", "minutes": 90,
      "description": "카드에 들어갈 한 문장 설명",
      "objectives": ["학습 목표"], "materials": ["준비물"],
      "scenario": [                        // ★ 강의 시나리오: 시간 합계 = minutes
        { "time": "00:00–10:00", "stage": "도입", "activity": "진행 내용",
          "script": "강사 멘트(실제로 말할 문장, \n 가능)", "learner": "학습자 활동", "tip": "진행 팁" }
      ],
      "slides": [ /* 아래 레이아웃 */ ],
      "note": "강사용 노트(강의 전체)",
      "prompts": [ { "name": "기본 프롬프트", "text": "복사할 원문" } ],
      "assessment": ["확인 질문"], "homework": "과제"
    }
  ]
}
```

## 슬라이드 레이아웃

모든 슬라이드: `layout`, `title`, 선택 `kicker`, `subtitle`, `notes`(발표자 노트 = 해당 구간 시나리오 대본, `[00:00–10:00 도입]`처럼 시간 표기 권장).

| layout | 추가 필드 | 쓰임 / 분량 기준 |
|---|---|---|
| `cover` | `facts`(선택) | 강의 첫 장. 제목 ≤ 14자 권장 |
| `agenda` | `bullets` (≤ 8) | 순서·목차 |
| `section` | `num`, `subtitle` | 단원 전환 |
| `bullets` | `bullets` (3~6, 각 ≤ 48자), `highlight` | 핵심 설명 |
| `two` | `left`·`right` = `{title, bullets(≤5)}` | 비교(전/후, 나쁜/좋은 예) |
| `steps` | `steps` = `[{tag, title, text}]` (3~4) | 절차·구성요소 |
| `practice` | `code` (≤ 400자), `label`, `button` | 실습 프롬프트/명령 |
| `quote` | `subtitle` | 핵심 메시지 한 문장 (≤ 40자) |
| `closing` | `bullets` (≤ 5), `book_title` | 마무리·Q&A (어두운 반전) |

권장 흐름(90분): cover → agenda/two(도입) → section → bullets/steps(개념) → practice ×1~3 → quote → closing. 강의당 7~14장.
