// lecture-builder · 레퍼런스(wkdream8.dothome.co.kr/sb) app.js 구조를 그대로 따르되 course.js 데이터로 구동
const C = course, L = C.lessons, M = C.meta;
const main = document.querySelector('main'), dialog = document.querySelector('dialog');
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const br = v => esc(v).replace(/\n/g, '<br>');
const no = n => String(n).padStart(2, '0');
const hasPrompts = C.promptGroups.some(g => g.items.length);
const ext = M.external ? '<a class="button" href="' + esc(M.external.url) + '" target="_blank" rel="noopener">' + esc(M.external.label) + '</a>' : '';

function promptBox(p) { return '<section class="prompt"><div class="prompt-head"><b>' + esc(p.name) + '</b><button data-copy="' + p.idx + '">복사</button></div><pre>' + esc(C.prompts[p.idx]) + '</pre></section>' }

function home() {
  const intro = L.filter(l => l.orientation), rest = L.filter(l => !l.orientation);
  return '<div class="hero"><div><div class="kicker">' + esc(M.kicker) + '</div><h1>' + br(M.title) + '</h1><p>' + br(M.summary) + '</p></div>'
    + '<div class="art" aria-hidden="true"><span class="corner">+</span><div class="book"><small>' + esc(M.book.top) + '</small><b>' + esc(M.book.num) + '</b><strong>' + esc(M.book.title) + '</strong><small>' + esc(M.book.bottom) + '</small></div><span class="corner last">+</span></div></div>'
    + '<div class="facts">' + M.facts.map(v => '<div class="fact"><b>' + esc(v[0]) + '</b><span>' + esc(v[1]) + '</span></div>').join('') + '</div>'
    + '<div class="section"><h2>강의 목록</h2><small class="mono">COURSE INDEX　/　' + esc(L[0].num) + '—' + esc(L[L.length - 1].num) + '</small></div>'
    + intro.map(l => '<a class="intro" href="#lesson/' + l.id + '/1"><span class="num">' + esc(l.num) + '</span><div><span class="level">' + esc(l.levelEn || 'ORIENTATION') + '</span><h3>' + esc(l.title) + '</h3></div><span class="arrow">→</span></a>').join('')
    + (rest.length ? '<div class="cards">' + rest.map(l => '<a class="card" href="#lesson/' + l.id + '/1"><div class="card-top"><span class="num">' + esc(l.num) + '</span><span class="level">' + esc(l.level) + '　/　' + esc(l.minutes) + '분</span></div><h3>' + esc(l.title) + '</h3><p>' + esc(l.description) + '</p><span class="arrow">↗</span></a>').join('') + '</div>' : '');
}

function plan() {
  return '<div class="catalog plan"><div class="kicker">LECTURE PLAN</div><h1>강의안</h1><p class="desc">' + esc(M.planDesc) + '</p>'
    + '<div class="tools"><a class="button" href="materials/lecture.md" download="' + esc(M.files.md) + '">강의안 MD ↓</a><a class="button" href="materials/lecture.hwpx" download="' + esc(M.files.hwpx) + '">강의안 HWPX ↓</a>' + ext + '</div>'
    + L.map(l => '<h2 id="plan-' + l.id + '">' + esc(l.num) + '　' + esc(l.title) + '</h2>'
      + '<div class="meta"><span><b>수준</b> ' + esc(l.level) + '</span><span><b>시간</b> ' + esc(l.minutes) + '분</span><span><b>슬라이드</b> ' + l.slides.length + '장</span><a href="#lesson/' + l.id + '/1">슬라이드 보기 →</a></div>'
      + (l.objectives.length ? '<ul class="goals">' + l.objectives.map(o => '<li>' + esc(o) + '</li>').join('') + '</ul>' : '')
      + '<div class="tablewrap"><table><thead><tr><th>시간</th><th>단계</th><th>진행 내용</th><th>강사 멘트 · 학습자 활동</th></tr></thead><tbody>'
      + l.scenario.map(s => '<tr><td class="time">' + esc(s.time) + '</td><td class="stage">' + esc(s.stage) + '</td><td>' + esc(s.activity) + (s.tip ? '<small>TIP · ' + esc(s.tip) + '</small>' : '') + '</td><td><span class="script">' + esc(s.script) + '</span>' + (s.learner ? '<small>학습자 · ' + esc(s.learner) + '</small>' : '') + '</td></tr>').join('')
      + '</tbody></table></div>').join('') + '</div>';
}

let state = null;
function render() {
  if (dialog.open) dialog.close();
  const parts = location.hash.slice(1).split('/'); state = null; let anchor = null;
  if (parts[0] === 'lesson' && /^\d+$/.test(parts[1]) && L[+parts[1]]) {
    const id = Number(parts[1]), l = L[id], slides = l.slides, p = Math.max(1, Math.min(slides.length, parseInt(parts[2]) || 1)); state = {id, p, count: slides.length};
    const label = (s, i) => s.title || ('슬라이드 ' + (i + 1));
    const sheet = (s, i) => '<figure class="original-slide"><img src="slides/' + id + '/' + (i + 1) + '.png" alt="' + esc((i + 1) + '쪽 · ' + label(s, i)) + '" width="1600" height="900"></figure>';
    const last = id < L.length - 1;
    main.innerHTML = '<div class="detail"><div class="detail-top"><a href="#home">← 강의 목록</a><h1>' + esc(l.title) + '</h1><p class="desc">' + esc(l.description) + '</p><div class="tools"><a class="button" href="materials/' + id + '.pptx" download="' + esc(l.file) + '">원본 교안 ↓</a>' + ext + '<a class="button" href="#plan/' + id + '">강의 시나리오</a>' + (hasPrompts ? '<a class="button" href="#prompts">' + esc(M.promptTitle) + '</a>' : '') + '<button data-act="note">강사용 노트</button><button data-act="full">전체 화면</button><button data-act="help">도움말</button></div></div>'
      + '<div class="screen-slide">' + sheet(slides[p - 1], p - 1) + '</div>'
      + '<div class="pager"><button data-act="prev" ' + (p === 1 ? 'disabled' : '') + '>← 이전</button><select aria-label="슬라이드 선택">' + slides.map((s, i) => '<option value="' + (i + 1) + '" ' + (i + 1 === p ? 'selected' : '') + '>' + no(i + 1) + ' · ' + esc(label(s, i)) + '</option>').join('') + '</select>'
      + (p < slides.length ? '<button class="primary" data-act="next">다음 →</button>' : '<a class="button primary" href="' + (last ? '#lesson/' + (id + 1) + '/1' : '#home') + '">' + (last ? '다음 강의 →' : '강의 목록 →') + '</a>') + '</div>'
      + '<div class="printslides">' + slides.map(sheet).join('') + '</div></div>';
  } else if (parts[0] === 'prompts' && hasPrompts) {
    main.innerHTML = '<div class="catalog"><div class="kicker">' + esc(M.promptKicker) + '</div><h1>' + esc(M.promptTitle) + '</h1><p class="desc">' + esc(M.promptDesc) + '</p><div class="tools"><a class="button" href="materials/prompts.md" download="' + esc(M.files.prompts) + '">전체 원문 ↓</a>' + ext + '</div>'
      + C.promptGroups.filter(g => g.items.length).map(g => '<h2>' + esc(g.title) + '</h2>' + g.items.map(promptBox).join('')).join('') + '</div>';
  } else if (parts[0] === 'plan') {
    main.innerHTML = plan(); if (/^\d+$/.test(parts[1] || '')) anchor = 'plan-' + parts[1];
  } else { main.innerHTML = home() }
  document.title = (state ? L[state.id].title : parts[0] === 'prompts' ? M.promptTitle : parts[0] === 'plan' ? '강의안' : M.siteTitle) + ' · ' + M.brand;
  const a = anchor && document.getElementById(anchor); if (a) a.scrollIntoView(); else window.scrollTo(0, 0);
}
function go(p) { if (state && p >= 1 && p <= state.count) location.hash = 'lesson/' + state.id + '/' + p }
function modal(title, msg) { document.querySelector('#dialogTitle').textContent = title; document.querySelector('#dialogText').textContent = msg; dialog.showModal() }
async function action(a) {
  if (!state) return;
  if (a === 'prev') go(state.p - 1);
  if (a === 'next') go(state.p + 1);
  if (a === 'note') { const l = L[state.id], s = l.slides[state.p - 1]; modal('강사용 노트', [l.note, s.notes ? '[' + no(state.p) + ' · ' + (s.title || '') + ']\n' + s.notes : ''].filter(Boolean).join('\n\n')) }
  if (a === 'help') modal('발표 단축키', '← → 또는 Space　슬라이드 이동\nHome / End　처음 / 마지막\nN　강사용 노트　　F　전체 화면\nP　PDF 저장　　?　도움말');
  if (a === 'full') { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen() } catch { modal('전체 화면', '브라우저 메뉴에서 전체 화면을 선택하세요.') } }
}
document.addEventListener('click', async e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.dataset.act) action(b.dataset.act);
  if (b.dataset.copy !== undefined) {
    const value = C.prompts[+b.dataset.copy];
    try { await navigator.clipboard.writeText(value) } catch { const t = document.createElement('textarea'); t.value = value; document.body.append(t); t.select(); const ok = document.execCommand('copy'); t.remove(); if (!ok) { modal('직접 복사', value); return } }
    document.querySelector('#notice').textContent = '프롬프트를 복사했습니다'; setTimeout(() => document.querySelector('#notice').textContent = '', 1800);
  }
});
document.addEventListener('change', e => { if (e.target.matches('.pager select')) go(+e.target.value) });
document.addEventListener('keydown', e => {
  if (!state || dialog.open || e.ctrlKey || e.metaKey || e.altKey || e.target.matches('select,input,textarea') || (e.key === ' ' && e.target.matches('button,a'))) return;
  const a = {ArrowLeft: 'prev', ArrowRight: 'next', ' ': 'next', n: 'note', f: 'full', '?': 'help'}[e.key];
  if (a) { e.preventDefault(); action(a) } else if (['Home', 'End', 'p'].includes(e.key)) { e.preventDefault(); if (e.key === 'p') print(); else go(e.key === 'Home' ? 1 : state.count) }
});
window.addEventListener('hashchange', render); render();
