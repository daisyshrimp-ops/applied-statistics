"""Сборка интерактивного сайта: python tools/build_site.py."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, '-m', 'marimo', 'export', 'html-wasm',
                'lab01.py', '-o', 'site', '--mode', 'run'], cwd=root, check=True)

# HTML outputs in marimo do not execute arbitrary scripts. Install this small
# enhancement in the exported shell; the statistical notebook stays reactive.
READING_PROGRESS_JS = r'''
(() => {
  'use strict';
  if (window.__team10ReadingProgress) return;
  window.__team10ReadingProgress = true;
  const clamp = n => Math.min(1, Math.max(0, n));
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let frame = 0, current = 0, target = 0, previousTime = 0;
  let dirty = true, lastTab = '', resizeTarget = null;
  const findScroller = anchor => {
    for (let e = anchor.parentElement; e; e = e.parentElement) {
      if (/(auto|scroll)/.test(getComputedStyle(e).overflowY) && e.scrollHeight > e.clientHeight + 1) return e;
    }
    return document.scrollingElement || document.documentElement;
  };
  function measure() {
    const tab = document.querySelector('body:has(.theme-extra-active)') ? 'extra' :
      document.querySelector('body:has(.theme-sprint2-active)') ? 'sprint2' : 'top';
    const start = document.getElementById(tab);
    const indicator = document.querySelector('.read-glass');
    if (!start || !indicator || !start.getClientRects().length) return;
    const scroller = findScroller(start);
    const isDocument = scroller === document.scrollingElement || scroller === document.documentElement;
    const viewportTop = isDocument ? 0 : scroller.getBoundingClientRect().top + scroller.clientTop;
    const height = isDocument ? window.innerHeight : scroller.clientHeight;
    const top = scroller.scrollTop;
    const startY = start.getBoundingClientRect().top - viewportTop + top;
    const footer = document.querySelector('.site-footer');
    const endY = footer && footer.getClientRects().length
      ? footer.getBoundingClientRect().bottom - viewportTop + top : scroller.scrollHeight;
    const distance = endY - height - startY;
    target = distance > 1 ? clamp((top - startY) / distance) : 0;
    if (tab !== lastTab) { current = target; lastTab = tab; }
    const content = start.closest('.marimo-cell')?.parentElement || scroller;
    if (content !== resizeTarget) {
      resizeObserver.disconnect();
      resizeObserver.observe(content);
      if (content !== scroller) resizeObserver.observe(scroller);
      resizeTarget = content;
    }
  }
  function paint(time) {
    frame = 0;
    if (dirty) { dirty = false; measure(); }
    const elapsed = previousTime ? Math.min(64, time - previousTime) : 16;
    previousTime = time;
    // Small time-based smoothing, never a delayed jump near the end of the page.
    current = reducedMotion.matches ? target : current + (target - current) * (1 - Math.exp(-elapsed / 75));
    if (Math.abs(current - target) < 0.0001) current = target;
    const indicator = document.querySelector('.read-glass');
    if (indicator) {
      indicator.querySelectorAll('.read-wine').forEach(rect => {
        const bottom = Number(rect.getAttribute('data-fill-bottom') || 32);
        rect.setAttribute('y', (bottom - 28 * current).toFixed(4));
        rect.setAttribute('height', (28 * current).toFixed(4));
      });
      const percent = Math.round(current * 100);
      const caption = indicator.querySelector('.read-percent');
      if (caption && caption.textContent !== `${percent}%`) caption.textContent = `${percent}%`;
      if (indicator.getAttribute('aria-valuenow') !== String(percent)) indicator.setAttribute('aria-valuenow', String(percent));
    }
    if (current !== target) frame = requestAnimationFrame(paint);
    else previousTime = 0;
  }
  function schedule() {
    dirty = true;
    if (!frame) frame = requestAnimationFrame(paint);
  }
  const resizeObserver = new ResizeObserver(schedule);
  const mutationObserver = new MutationObserver(records => {
    // Ignore our percentage label; never create an observer/animation feedback loop.
    if (records.some(r => !(r.target instanceof Element && r.target.closest('.read-glass')))) schedule();
  });
  function init() {
    mutationObserver.observe(document.body, {childList: true, subtree: true});
    // Capturing sees both document scrolling and marimo's inner scroll viewport.
    document.addEventListener('scroll', schedule, {passive: true, capture: true});
    document.addEventListener('toggle', schedule, true);
    document.addEventListener('load', schedule, true);
    window.addEventListener('resize', schedule, {passive: true});
    window.addEventListener('hashchange', schedule);
    window.addEventListener('pageshow', schedule);
    reducedMotion.addEventListener('change', schedule);
    schedule();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once: true});
  else init();
})();
'''
REPORT_TRANSITIONS_JS = r'''
(() => {
  'use strict';
  if (window.__team10ReportTransitions) return;
  window.__team10ReportTransitions = true;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const views = {'Спринт 1': ['white', 'top'], 'Спринт 2': ['sprint2', 'sprint2'], 'Доп. КТиД': ['extra', 'extra']};
  let replay = false, switching = false, lastMode = '', enterTimer = 0;
  const mode = () => document.querySelector('.theme-extra-active') ? 'extra' :
    document.querySelector('.theme-sprint2-active') ? 'sprint2' :
    document.querySelector('.theme-white-active') ? 'white' : '';
  const visible = id => !!document.getElementById(id)?.getClientRects().length;
  function waitForReport(expected, anchor, activate) {
    return new Promise(resolve => {
      let settle = 0, timeout = 0, done = false;
      const finish = () => {
        if (done) return;
        done = true; clearTimeout(settle); clearTimeout(timeout); observer.disconnect(); resolve();
      };
      const check = records => {
        if (records?.length && records.every(r => r.target instanceof Element && r.target.closest('.read-glass'))) return;
        clearTimeout(settle);
        if (mode() === expected && visible(anchor)) settle = setTimeout(finish, 100);
      };
      const observer = new MutationObserver(check);
      observer.observe(document.body, {subtree: true, childList: true});
      timeout = setTimeout(finish, 1400);
      activate(); check();
    });
  }
  document.addEventListener('click', event => {
    if (replay || switching || reduced.matches || !document.startViewTransition) return;
    // marimo renders its buttons inside a shadow root: use the composed event path.
    const button = event.composedPath().find(node => node instanceof Element && node.getAttribute('role') === 'tab');
    if (!button || button.getAttribute('aria-selected') === 'true') return;
    const view = views[button.textContent.trim()];
    if (!view) return;
    event.preventDefault(); event.stopImmediatePropagation();
    const activate = () => {
      replay = true;
      try { button.click(); } finally { replay = false; }
    };
    switching = true;
    document.body.classList.remove('report-enter');
    try {
      const transition = document.startViewTransition(() => waitForReport(view[0], view[1], activate));
      transition.finished.catch(() => {}).finally(() => { switching = false; lastMode = mode(); });
    } catch (_) {
      switching = false; activate();
    }
  }, true);
  // Firefox versions without View Transitions and keyboard tab changes use a soft entrance.
  let pending = false;
  const observer = new MutationObserver(records => {
    if (pending || records.every(r => r.target instanceof Element && r.target.closest('.read-glass'))) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      const next = mode();
      if (!next || next === lastMode) return;
      if (lastMode && !switching && !reduced.matches) {
        clearTimeout(enterTimer);
        document.body.classList.remove('report-enter');
        requestAnimationFrame(() => {
          document.body.classList.add('report-enter');
          enterTimer = setTimeout(() => document.body.classList.remove('report-enter'), 500);
        });
      }
      lastMode = next;
    });
  });
  observer.observe(document.body, {subtree: true, childList: true});
})();
'''

index = root / 'site' / 'index.html'
page = index.read_text(encoding='utf-8')
tag = '<script id="team10-reading-progress">' + READING_PROGRESS_JS + '</script>'
assert '</body>' in page, 'Missing closing body in the exported site'
tag += '<script id="team10-report-transitions">' + REPORT_TRANSITIONS_JS + '</script>'
page = page.replace('</body>', tag + '\n</body>', 1)
index.write_text(page, encoding='utf-8')
print('Готово: site/index.html. Запуск: python -m http.server --directory site 8000')

