"""Restore the published reactive first-sprint layout with verbatim author prose."""
_original=(ROOT/'tools/sprint1_layout.py').read_text(encoding="utf-8")
_original_tree=ast.parse(_original)
# Original notebook ranges belonging to each published UI section.
AUTHOR_RANGES={620:(10,19),632:(19,22),642:(22,26),656:(26,33),672:(33,38),683:(38,40),690:(40,43),698:(43,48),717:(48,52),735:(52,58),756:(58,63),773:(63,64),780:(64,67),790:(67,70),804:(70,73),820:(73,80),831:(80,81),838:(81,84),846:(84,89),865:(89,92),883:(92,96),904:(96,101),921:(101,102),928:(102,105),938:(105,108),952:(108,114),968:(114,117),979:(117,118),986:(118,121),994:(121,125),1013:(125,128),1031:(128,132),1052:(132,137),1069:(137,138),1083:(138,143)}
class RestoreSection(ast.NodeTransformer):
    def visit_Call(self,n):
        n=self.generic_visit(n)
        if isinstance(n.func,ast.Name) and n.func.id=='section':
            n.keywords=[k for k in n.keywords if k.arg!='lead']
        if isinstance(n.func,ast.Name) and n.func.id=='verdict':
            n.keywords=[k for k in n.keywords if k.arg!='note']
        if isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='mo' and n.func.attr=='hstack' and n.args and isinstance(n.args[0],ast.List):
            values=n.args[0].elts
            if any(isinstance(v,ast.Name) for v in values):
                return ast.copy_location(ast.Call(func=ast.Name(id='control_bar',ctx=ast.Load()),args=[n.args[0]],keywords=[]),n)
            if values and all(isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='verdict' for v in values):
                return ast.copy_location(ast.Call(func=ast.Name(id='result_grid',ctx=ast.Load()),args=[n.args[0]],keywords=[]),n)
        return n

def plain_ui(item):
    if isinstance(item,ast.Call) and isinstance(item.func,ast.Name) and item.func.id in ('prose','code_panel'):
        return False
    if isinstance(item,ast.Call) and isinstance(item.func,ast.Attribute) and item.func.attr=='Html' and item.args:
        text=ast.unparse(item.args[0])
        if 'class="summary"' in text or "class=\"summary \"" in text:return False
    return True

for node in _original_tree.body:
    if not isinstance(node,ast.FunctionDef) or not 595<=node.lineno<=1083:continue
    line=node.lineno
    if line==606:
        cell("""mo.stop(project_tabs.value!='Спринт 1')
mo.vstack([section('0','Данные','data'),section('0.1','Общее описание данных','data-desc',level=3),author_flow('sprint1',1,7,outputs=False,headers=False),section('0.2','Пропуски и дубликаты','data-dup',level=3),kpis([('Образцов',str(len(df)),'белые вина'),('Пропусков',str(int(df.isna().sum().sum())),'по всей таблице'),('Повторов',str(int(df.duplicated().sum())),'оставлены')]),author_flow('sprint1',7,10,outputs=False,headers=False),author_code('sprint1',1,10)])""")
        continue
    body=node.body[:-1]
    code=textwrap.dedent('\n'.join(_original.splitlines()[body[0].lineno-1:body[-1].end_lineno]))
    parsed=ast.parse(code)
    # Drop old narrative copies and the old copied UI source; keep all calculations and widgets.
    for stmt in parsed.body:
        if isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call) and isinstance(stmt.value.func,ast.Attribute) and stmt.value.func.attr=='vstack' and stmt.value.args and isinstance(stmt.value.args[0],ast.List):
            stmt.value.args[0].elts=[v for v in stmt.value.args[0].elts if plain_ui(v)]
            if line in AUTHOR_RANGES:
                start,end=AUTHOR_RANGES[line]
                if line in (756,904,1052):
                    stmt.value.args[0].elts.append(ast.parse("mo.Html('<p class=\"experiment-caption\">Авторские выводы ниже относятся к исходным параметрам ноутбука.</p>')",mode='eval').body)
                stmt.value.args[0].elts.append(ast.parse(f"author_flow('sprint1',{start},{end},outputs=False,headers=False)",mode='eval').body)
                stmt.value.args[0].elts.append(ast.parse(f"author_code('sprint1',{start},{end})",mode='eval').body)
    if line!=595:parsed=RestoreSection().visit(parsed)
    code=ast.unparse(ast.fix_missing_locations(parsed))
    # The three hypothesis experiments expose alpha as well as mu0 and n.
    for prefix,control_line,plot_line in [('ph',747,756),('sug',895,904),('alc',1043,1052)]:
        if line==control_line:
            code+=f"\n{prefix}_alpha=mo.ui.dropdown({{'0,01':0.01,'0,05':0.05,'0,10':0.10}},value='0,05',label='Уровень значимости α')"
        if line==plot_line:
            code=code.replace(f'control_bar([{prefix}_mu0, {prefix}_hyp_n])',f'control_bar([{prefix}_mu0, {prefix}_hyp_n, {prefix}_alpha])')
            code=code.replace('stats.t.interval(0.95,',f'stats.t.interval(1-{prefix}_alpha.value,')
            code=code.replace("'95% ДИ'",f"f'{{(1-{prefix}_alpha.value)*100:.0f}}% ДИ'")
            tree_hyp=ast.parse(code)
            for call in ast.walk(tree_hyp):
                if isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='verdict':
                    call.keywords.append(ast.keyword(arg='alpha',value=ast.parse(f'{prefix}_alpha.value',mode='eval').body))
            code=ast.unparse(ast.fix_missing_locations(tree_hyp))
    if line==1083:code=code.replace(', corr_method,',', control_bar([corr_method]),')
    cell(code)
cell("""mo.stop(project_tabs.value!='Спринт 1')
_rng=np.random.default_rng(42)
_random=df.sample(n=500,random_state=42)
_parts=[_g.sample(n=max(1,round(500*len(_g)/len(df))),random_state=42) for _,_g in df.groupby('quality')]
_strat=pd.concat(_parts)
_table=pd.DataFrame({'Вся таблица':df[['pH','residual sugar','alcohol']].mean(),'Случайная выборка':_random[['pH','residual sugar','alcohol']].mean(),'По группам quality':_strat[['pH','residual sugar','alcohol']].mean()})
mo.vstack([section('5','Выборка и генеральная совокупность','sampling-population'),html_table(_table),author_flow('sprint1',143,149,outputs=False,headers=False),author_code('sprint1',143,149)])""")
cell("""mo.stop(project_tabs.value!='Спринт 1')
mo.vstack([section('6','Итоговые выводы','resume'),author_flow('sprint1',151,153,outputs=False),section('7','Литература и критерии','refs'),author_flow('sprint1',149,151,outputs=False),mo.Html('<span id="cat-mark"></span><span id="ktid"></span>'),author_flow('sprint1',153,155,outputs=False)])""")
