// RAD-TUI web runtime (Pyodide + DOM)
const projectName = "Hello World";
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
  const codeSections = [];
  if(project.code) codeSections.push(project.code);
  for(const c of project.controls||[]){ if(c.code) codeSections.push(c.code); }
  const userCode = codeSections.join("\n\n");
  // build Python preamble: controls as JS-synced objects
  const controlsInit = (project.controls||[]).map(c=>{
    const cap = (c.caption||'').replace(/"/g,'\\"').replace(/\n/g,'\\n');
    return `${c.name_id} = JSControl("${c.name_id}", "${cap}")`;
  }).join("\n");

  const preamble = `
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
`;

  try{
    pyodide = await loadPyodide();
    document.getElementById('loading').textContent = 'Python ready — running ' + projectName;
    pyodide.runPython(preamble + "\\n" + controlsInit + "\\n" + userCode);
    // fire on_load
    try{ pyodide.runPython("on_load_frmMain() if 'on_load_frmMain' in dir() else (on_load_form() if 'on_load_form' in dir() else None)"); }catch(e){}
    bindEvents();
    document.getElementById('loading').style.display='none';
  }catch(e){
    document.getElementById('loading').textContent = 'Fallback mode (no Pyodide): ' + e;
    bindEventsFallback(project, userCode);
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
