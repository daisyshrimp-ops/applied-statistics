"""Attach build-prepared notebook charts to the authored report flow."""
cell("""def saved_notebook_charts(study):
    def chart(index):
        return REPORTS[study][index].get('figures',[])
    return chart
sprint2_charts=saved_notebook_charts('sprint2')
uicrit_charts=saved_notebook_charts('uicrit')""")
for _i,_source in enumerate(CELLS):
    if 'def author_flow(' in _source:
        _source=_source.replace('outputs=True,headers=True):','outputs=True,headers=True,charts=None):')
        _source=_source.replace("            figures=''.join",'''            if charts is not None and '<figure' in rendered:
                fresh=iter(charts(i))
                rendered=_re.sub(r'<figure\\b.*?</figure>',lambda match:next(fresh),rendered,flags=_re.S)
            figures=''.join''')
        CELLS[_i]=_source
        continue
    _tree=ast.parse(_source)
    _changed=False
    for _node in ast.walk(_tree):
        if isinstance(_node,ast.Call) and isinstance(_node.func,ast.Name) and _node.func.id=='author_flow' and _node.args and isinstance(_node.args[0],ast.Constant) and _node.args[0].value in ('sprint2','uicrit'):
            _node.keywords.append(ast.keyword(arg='charts',value=ast.Name(id=_node.args[0].value+'_charts',ctx=ast.Load())))
            _changed=True
    if _changed:
        ast.fix_missing_locations(_tree);CELLS[_i]=ast.unparse(_tree)
    # Existing live UICrit model/reference lines share the same blue palette.
    if "Доп. КТиД" in _source and 'mo.stop' in _source:
        CELLS[_i]=CELLS[_i].replace('#D58A55','#203747')

# A reading window uses the same browser chrome without unnecessary tabs.
cell('''
def reading_window(content,address):
    chrome='<div class="workspace-chrome"><span class="browser-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="browser-address">'+html.escape(address)+'</span><span aria-hidden="true">↗</span></div>'
    return mo.Html('<div class="native-browser-window question-window">'+chrome+'<div class="native-browser-content">'+mo.as_html(content).text+'</div></div>')
''')
for _i,_source in enumerate(CELLS):
    if "author_flow('uicrit', 2, 4," in _source:
        _source=_source.replace("author_flow('uicrit', 2, 4, first_heading=True, outputs=False, charts=uicrit_charts)","author_flow('uicrit', 2, 3, first_heading=True, outputs=False, charts=uicrit_charts), reading_window(author_flow('uicrit', 3, 4, outputs=False, charts=uicrit_charts), 'research / uicrit / hypothesis')")
    if '_screen = ui_screens.sample' in _source:
        _caption='Это визуальный пример случайного выбора одного экрана, а не проверка гипотезы. Столбики показывают средние, точки — отдельные оценки.'
        _source=_source.replace("controls_window('Случайный экран: столбики — средние, точки — отдельные оценки', [ui_screen_pick])","controls_window("+repr(_caption)+", [ui_screen_pick])")
        _source=_source.replace("mo.Html('<p class=\"experiment-caption\">"+_caption+"</p>'), ","")
    CELLS[_i]=_source
