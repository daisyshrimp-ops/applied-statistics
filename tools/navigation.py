"""Full notebook outline and routes to native reactive panes, derived from headings."""
import re as _re_nav
import html as _html_nav
import json as _json_nav
chapter_map={}
white_tree=ast.parse(legacy)
for node in ast.walk(white_tree):
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_white_items' for t in node.targets):
        white=ast.literal_eval(node.value)
        break
white=[(a,t,l) for a,t,l in white if a not in ('cat-mark','ktid','refs','resume','resume-text','source')]
white += [('sampling-population','5 Выборка и генеральная совокупность',2),('resume','6 Итоговые выводы',2),('refs','7 Литература и критерии',2),('cat-mark','Таблица критериев',3)]
chapter_map['Спринт 1']=white
NAV_ROUTES={}
def pane_route(index):
    if 22<=index<28:return {'anchor':'extra-eda','tab':'Эстетика'}
    if 28<=index<34:return {'anchor':'extra-eda','tab':'Удобство'}
    if 57<=index<60:return {'anchor':'extra-heatmap','tab':'Карта'}
    if 60<=index<67:return {'anchor':'extra-heatmap','tab':'Сравнение'}
    if 67<=index<79:
        label='Равномерность' if index<70 else 'Люди и Gemini' if index<73 else 'Тема и зона' if index<76 else 'Устойчивость'
        return {'anchor':'extra-heatmap','tab':'Проверки','select':label}
    if 86<=index<89:return {'anchor':'extra-rating-comments','tab':'Темы'}
    if 89<=index<92:return {'anchor':'extra-rating-comments','tab':'Проверки'}
    if 92<=index<98:return {'anchor':'extra-rating-comments','tab':'Расположение'}
    return None
for study,mode,cover in [('sprint2','Спринт 2','sprint2'),('uicrit','Доп. КТиД','extra')]:
    outline=[(cover,'Обложка',2)]+([('s2-guide','Как читать отчёт',2)] if study=='sprint2' else [])
    for i,item in enumerate(REPORT_SOURCE[study]):
        if i<(2 if study=='uicrit' else 1):continue
        if study=='uicrit' and i in (4,9,20):continue
        if study=='sprint2' and _re_nav.fullmatch(r'#+\s*Code\s*',item['source'].strip()):continue
        if item['kind']=='markdown':
            for level,attrs,body in _re_nav.findall(r'<h([1-6])([^>]*)>(.*?)</h[1-6]>',item['html'],flags=_re_nav.S):
                ident=_re_nav.search(r'id="([^"]+)"',attrs)
                if ident:
                    label=_html_nav.unescape(_re_nav.sub('<[^>]*>','',body)).strip()
                    outline.append((ident[1],label,int(level)))
        if study=='uicrit':
            route=pane_route(i)
            if route:
                for ident in _re_nav.findall(r'id="([^"]+)"',item['html'])+[f'uicrit-cell-{i}']:
                    NAV_ROUTES[ident]=route
    chapter_map[mode]=outline
cell('navigation_chapters = '+repr(chapter_map))
cell('''
_titles={'Спринт 1':'Белое вино · Спринт 1','Спринт 2':'Генераторы · Спринт 2','Доп. КТиД':'Анализ интерфейсов приложений — UICrit'}
_links=''.join(f'<li class="toc-depth-{level}"><a href="#{anchor}">{html.escape(label)}</a></li>' for anchor,label,level in navigation_chapters[project_tabs.value])
mo.Html(f'<button class="toc-toggle" type="button" popovertarget="lab-toc" aria-label="Открыть оглавление"><span class="burger-lines" aria-hidden="true"><i></i><i></i><i></i></span></button><nav id="lab-toc" class="toc-drawer" popover="auto" aria-label="Оглавление исследования"><div class="toc-drawer-head"><div><span class="toc-caption">Оглавление</span><h2>{_titles[project_tabs.value]}</h2></div><button class="toc-close" type="button" popovertarget="lab-toc" popovertargetaction="hide" aria-label="Закрыть оглавление">×</button></div><ol>{_links}</ol></nav>')
''')
