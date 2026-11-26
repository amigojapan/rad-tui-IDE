"""
Web exporter for RAD-TUI v2.2
Transpiles a .json project (form + controls + Python code-behind) into a
standalone browser app: index.html + app.js + style.css + project.json

Initial vertical slice: Label, Button, TextBox/Edit/Memo, CheckBox, ListBox.
Generic projects use Pyodide (Python-in-WASM) to execute the original
event handlers unchanged.  No server required - just `python3 -m http.server`.

Usage:
    python3 -m src.export_web examples/calculator.json dist/calculator
    python3 rad-tui-py.py --export-web examples/calculator.json --out dist
"""
import json
import os
import shutil
import html
from pathlib import Path

# ---- tool-type heuristic (mirrors src/tui_runner.py _tool_type) ----
def effective_type(ctrl):
    tool_type = int(ctrl.get("tool_type", 0))
    name = str(ctrl.get("name_id","")).lower()
    h = int(ctrl.get("h", ctrl.get("height", 1)) or 1)
    # v2.2 definitive
    if name.startswith("tmr"):
        return 10
    if tool_type in (14,15,16) or tool_type >= 17:
        return tool_type
    # name-prefix wins for legacy
    if name.startswith("lbl"): return 1
    if name.startswith("btn"): return 2
    if name.startswith(("txt","edt")): return 4
    if name.startswith(("chk",)): return 5
    if name.startswith(("rad","opt")): return 6
    if name.startswith("lst"): return 7
    if name.startswith(("cmb","cbo")): return 8
    if name.startswith(("frm","fra")): return 9
    if name.startswith("tmr"): return 10
    if name.startswith("img"): return 11
    if name.startswith("pic"): return 12
    if name.startswith(("grd","grid")): return 16
    # fallback by tool_type
    if tool_type == 1: return 5 if "checked" in ctrl else 1
    if tool_type == 9: return 1 if h <= 2 else 9
    if tool_type == 10: return 7 if ctrl.get("items") else 10
    if tool_type in (12,13):
        if ctrl.get("items"): return 7
        if "checked" in ctrl and h <= 2: return 5
        return 4 if h <= 2 else 12
    return tool_type

CTRL_HTML = {
    # label
    1:  lambda c: f'<div class="ctrl label" id="{c["name_id"]}" data-name="{c["name_id"]}">{html.escape(c.get("caption",""))}</div>',
    # button
    2:  lambda c: f'<button class="ctrl button" id="{c["name_id"]}" data-name="{c["name_id"]}">{html.escape(c.get("caption",""))}</button>',
    # textbox / edit
    4:  lambda c: f'<div class="ctrl textbox" id="{c["name_id"]}" data-name="{c["name_id"]}">{html.escape(c.get("caption",""))}</div>',
    14: lambda c: f'<div class="ctrl textbox" id="{c["name_id"]}" data-name="{c["name_id"]}">{html.escape(c.get("caption","") or c.get("text",""))}</div>',
    # checkbox
    5:  lambda c: f'<label class="ctrl checkbox" id="{c["name_id"]}" data-name="{c["name_id"]}"><input type="checkbox" {"checked" if c.get("checked") else ""}> {html.escape(c.get("caption","").removeprefix("[ ]").removeprefix("[X]").strip())}</label>',
    # list
    7:  lambda c: '<select class="ctrl listbox" id="{id}" data-name="{id}" size="{sz}">{opts}</select>'.format(
            id=c["name_id"], sz=max(3, int(c.get("h",5))),
            opts="".join(f'<option{" selected" if i==int(c.get("selected_index",-1)) else ""}>{html.escape(str(x))}</option>' for i,x in enumerate(c.get("items",[])))),
    # frame
    9:  lambda c: f'<fieldset class="ctrl frame" id="{c["name_id"]}" data-name="{c["name_id"]}"><legend>{html.escape(c.get("caption",""))}</legend></fieldset>',
    # memo / textarea
    15: lambda c: f'<textarea class="ctrl memo" id="{c["name_id"]}" data-name="{c["name_id"]}">{html.escape(c.get("caption",""))}</textarea>',
    # grid
    16: lambda c: f'<div class="ctrl grid" id="{c["name_id"]}" data-name="{c["name_id"]}">Grid {html.escape(c.get("name_id",""))}</div>',
}

def render_control(c):
    t = effective_type(c)
    fn = CTRL_HTML.get(t)
    if fn:
        try: return fn(c), t
        except: pass
    # fallback
    return f'<div class="ctrl unknown" id="{c["name_id"]}" data-name="{c["name_id"]}">{html.escape(c.get("caption","") or c["name_id"])} [t{t}]</div>', t

CSS = """*{box-sizing:border-box}
body{background:#0a0a14;color:#c0c0c0;font-family:monospace;margin:0;padding:20px}
.form{position:relative;background:#000080;border:2px solid #c0c0c0;width:var(--fw);height:var(--fh);margin:20px auto;box-shadow:4px 4px #000}
.form-title{background:#c0c0c0;color:#000080;text-align:center;padding:4px;font-weight:bold}
.form-body{position:relative;width:100%;height:calc(100% - 24px)}
.ctrl{position:absolute;overflow:hidden}
.label{color:#fff;padding:2px}
.button{background:#c0c0c0;color:#000;border:2px outset #fff;padding:4px 12px;cursor:pointer}
.button:active{border-style:inset}
.textbox{background:#fff;color:#000;border:2px inset #808080;padding:2px 4px;white-space:pre}
.checkbox{color:#fff;cursor:pointer}
.listbox{background:#fff;color:#000;border:2px inset #808080}
.frame{border:2px groove #808080;color:#fff}
.memo{background:#fff;color:#000;border:2px inset #808080;resize:none}
.status{position:absolute;bottom:0;left:0;right:0;background:#c0c0c0;color:#000;padding:2px 6px;font-size:12px}
#msgbox{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;align-items:center;justify-content:center}
#msgbox .box{background:#c0c0c0;border:2px outset #fff;padding:16px;min-width:260px;color:#000}
#loading{color:#0f0;text-align:center;padding:10px}
"""

PY_PREAMBLE = r"""
import js
class JSControl:
    def __init__(self, name_id, caption=""):
        super().__setattr__('_name_id', name_id)
        super().__setattr__('caption', caption)
        super().__setattr__('text', caption)
        super().__setattr__('checked', False)
    def __setattr__(self, k, v):
        super().__setattr__(k, v)
        if k in ('caption','text','checked','value'):
            try: js.updateControl(self._name_id, k, str(v))
            except: pass

def msgbox(text, title="Message", style=None):
    js.msgbox(str(text), str(title))

def end_app():
    js.end_app()

def input_box(prompt, title="Input", default=""):
    return js.prompt(str(prompt), str(default)) or str(default)
"""

JS_TEMPLATE = r"""// RAD-TUI web runtime (Pyodide + DOM)
const projectName = "__TITLE__";
let pyodide, controls = {}, updatingFromPython = false;

function updateControl(name, prop, val){
  const el = document.getElementById(name);
  if(!el) return;
  updatingFromPython = true;
  if(el.tagName === 'BUTTON') el.textContent = val;
  else if(el.classList.contains('textbox') || el.classList.contains('label')) el.textContent = val;
  else if(el.classList.contains('checkbox')) { el.querySelector('input').checked = (val==='True' || val==='true' || val===true); }
  else if(el.tagName === 'SELECT') { /* list handled via selectedIndex */ }
  updatingFromPython = false;
}
window.updateControl = updateControl;

function msgbox(text, title){ return new Promise(res=>{
  const m=document.getElementById('msgbox');
  document.getElementById('msgbox-title').textContent=title||'Message';
  document.getElementById('msgbox-text').textContent=text;
  m.style.display='flex'; document.getElementById('msgbox-ok').onclick=()=>{m.style.display='none';res();};
});}
function end_app(){ document.getElementById('form').style.opacity=.5; }
window.msgbox = (t,ttl)=>msgbox(t,ttl);
window.alert = (t)=>msgbox(t,'Message');

async function main(){
  const res = await fetch('project.json'); const project = await res.json();
  // Embedded Python code generated server-side (properly escaped)
  const __pythonCode = __PYTHON_CODE__;

  try{
    pyodide = await loadPyodide();
    document.getElementById('loading').textContent = 'Python ready — running ' + projectName;
    console.log("Running Python code:", __pythonCode.slice(0,500));
    pyodide.runPython(__pythonCode);
    // fire on_load
    try{ pyodide.runPython("on_load_frmMain() if 'on_load_frmMain' in dir() else (on_load_form() if 'on_load_form' in dir() else None)"); }catch(e){}
    bindEvents();
    document.getElementById('loading').style.display='none';
  }catch(e){
    console.error("Python load failed", e);
    document.getElementById('loading').textContent = 'Fallback mode: ' + e;
    bindEventsFallback(project, __pythonCode);
  }
}

function bindEvents(){
  document.querySelectorAll('.button').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const name = btn.dataset.name;
      try{ pyodide.runPython(`on_click_${name}()`); }catch(e){ console.error(e); msgbox(String(e),'Runtime error'); }
    });
  });
  document.querySelectorAll('.listbox').forEach(sel=>{
    sel.addEventListener('change', ()=>{
      const name=sel.dataset.name;
      try{ pyodide.runPython(`${name}.selected_index = ${sel.selectedIndex}`); pyodide.runPython(`on_change_${name}() if 'on_change_${name}' in dir() else None`); }catch(e){}
    });
  });
}

function bindEventsFallback(project, code){
  // very small JS fallback for hello_world / calculator display updates
  document.querySelectorAll('.button').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const n=btn.dataset.name;
      if(n==='btnHello') msgbox('Hello, World!','Message');
      if(n==='btnExit') end_app();
      // calculator fallback: eval display
      if(n.startsWith('btn')){ try{ pyodideFallback(n); }catch{} }
    });
  });
}
function pyodideFallback(name){
  const d=document.getElementById('txtDisplay');
  if(!d) return;
  const map={btn7:'7',btn8:'8',btn9:'9',btn4:'4',btn5:'5',btn6:'6',btn1:'1',btn2:'2',btn3:'3',btn0:'0',btnAdd:'+',btnSubtract:'-',btnMultiply:'*',btnDivide:'/',btnClear:'C',btnEquals:'='};
  const v=map[name]; if(!v) return;
  if(v==='C') d.textContent='0';
  else if(v==='='){ try{ d.textContent=String(eval(d.textContent)); }catch{ d.textContent='Error'; } }
  else { d.textContent = d.textContent==='0' ? v : d.textContent+v; }
}
document.addEventListener('DOMContentLoaded', main);
"""

HTML_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — RAD-TUI Web</title>
<link rel="stylesheet" href="style.css">
<script src="https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"></script>
</head><body>
<h2 style="text-align:center">RAD-TUI Web — __TITLE__</h2>
<div id="loading">Loading Python (Pyodide)…</div>
<div class="form" id="form" style="--fw:__FWpx;--fh:__FHpx">
  <div class="form-title">__TITLE__</div>
  <div class="form-body" id="form-body">__CONTROLS__</div>
</div>
<div id="msgbox"><div class="box"><div id="msgbox-title" style="font-weight:bold;margin-bottom:8px"></div><div id="msgbox-text" style="margin-bottom:12px;white-space:pre-wrap"></div><button id="msgbox-ok" class="button">OK</button></div></div>
<script type="module" src="app.js"></script>
</body></html>
"""

def export_project(src_path, out_dir):
    src = Path(src_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    proj = json.loads(src.read_text())
    title = proj.get("title","Untitled")
    fw = int(proj.get("w",40))*8 + 16
    fh = int(proj.get("h",15))*18 + 40
    controls_html=[]
    for c in proj.get("controls",[]):
        h,_ = render_control(c)
        # absolute position (x,y in char cells)
        x = int(c.get("x",0))*8
        y = int(c.get("y",0))*18
        w = int(c.get("w",10))*8
        hh= int(c.get("h",1))*18
        # clamp tiny heights for button/textbox
        if effective_type(c) in (2,): hh=max(hh,24)
        # inject absolute positioning into the control itself (no wrapper)
        if 'class="ctrl' in h:
            h = h.replace('class="ctrl', f'style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px" class="ctrl', 1)
        else:
            h = f'<div style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px">{h}</div>'
        controls_html.append(h)
    # Build Python code server-side with safe escaping (no JS interpolation issues)
    code_sections = []
    if proj.get("code"): code_sections.append(proj["code"])
    for c in proj.get("controls",[]):
        if c.get("code"): code_sections.append(c["code"])
    user_code = "\n\n".join(code_sections)
    controls_init = "\n".join(f'{c["name_id"]} = JSControl("{c["name_id"]}", {json.dumps(c.get("caption",""))})' for c in proj.get("controls",[]))
    full_python = PY_PREAMBLE + "\n" + controls_init + "\n" + user_code
    # sanity check
    try: compile(full_python, "<export>", "exec")
    except SyntaxError as e: print(f"WARN export compile check failed: {e}")

    html_out = HTML_TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__FW", str(fw)).replace("__FH", str(fh)).replace("__CONTROLS__", "\n".join(controls_html))
    js_out = JS_TEMPLATE.replace("__TITLE__", title).replace("__PYTHON_CODE__", json.dumps(full_python))
    (out/"index.html").write_text(html_out)
    (out/"app.js").write_text(js_out)
    (out/"style.css").write_text(CSS)
    shutil.copy(src, out/"project.json")
    return out

if __name__ == "__main__":
    import sys
    if len(sys.argv)<3:
        print("usage: python -m src.export_web <project.json> <out_dir>")
        raise SystemExit(1)
    print(f"Exported to {export_project(sys.argv[1], sys.argv[2])}")
