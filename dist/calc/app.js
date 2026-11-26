// RAD-TUI web runtime (Pyodide + DOM)
const projectName = "Calculator";
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
  const __pythonCode = "\nimport js\nclass JSControl:\n    def __init__(self, name_id, caption=\"\"):\n        super().__setattr__('_name_id', name_id)\n        super().__setattr__('caption', caption)\n        super().__setattr__('text', caption)\n        super().__setattr__('checked', False)\n    def __setattr__(self, k, v):\n        super().__setattr__(k, v)\n        if k in ('caption','text','checked','value'):\n            try: js.updateControl(self._name_id, k, str(v))\n            except: pass\n\ndef msgbox(text, title=\"Message\", style=None):\n    js.msgbox(str(text), str(title))\n\ndef end_app():\n    js.end_app()\n\ndef input_box(prompt, title=\"Input\", default=\"\"):\n    return js.prompt(str(prompt), str(default)) or str(default)\n\ntxtDisplay = JSControl(\"txtDisplay\", \"0\")\nbtn7 = JSControl(\"btn7\", \"7\")\nbtn8 = JSControl(\"btn8\", \"8\")\nbtn9 = JSControl(\"btn9\", \"9\")\nbtnDivide = JSControl(\"btnDivide\", \"/\")\nbtn4 = JSControl(\"btn4\", \"4\")\nbtn5 = JSControl(\"btn5\", \"5\")\nbtn6 = JSControl(\"btn6\", \"6\")\nbtnMultiply = JSControl(\"btnMultiply\", \"*\")\nbtn1 = JSControl(\"btn1\", \"1\")\nbtn2 = JSControl(\"btn2\", \"2\")\nbtn3 = JSControl(\"btn3\", \"3\")\nbtnSubtract = JSControl(\"btnSubtract\", \"-\")\nbtnClear = JSControl(\"btnClear\", \"C\")\nbtn0 = JSControl(\"btn0\", \"0\")\nbtnEquals = JSControl(\"btnEquals\", \"=\")\nbtnAdd = JSControl(\"btnAdd\", \"+\")\ndef on_change_txtDisplay():\n    pass\n\n\ndef on_click_btn7():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"7\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"7\"\n\n\ndef on_click_btn8():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"8\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"8\"\n\n\ndef on_click_btn9():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"9\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"9\"\n\n\ndef on_click_btnDivide():\n    txtDisplay.caption = txtDisplay.caption + \"/\"\n\n\ndef on_click_btn4():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"4\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"4\"\n\n\ndef on_click_btn5():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"5\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"5\"\n\n\ndef on_click_btn6():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"6\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"6\"\n\n\ndef on_click_btnMultiply():\n    txtDisplay.caption = txtDisplay.caption + \"*\"\n\n\ndef on_click_btn1():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"1\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"1\"\n\n\ndef on_click_btn2():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"2\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"2\"\n\n\ndef on_click_btn3():\n    if txtDisplay.caption == \"0\":\n        txtDisplay.caption = \"3\"\n    else:\n        txtDisplay.caption = txtDisplay.caption + \"3\"\n\n\ndef on_click_btnSubtract():\n    txtDisplay.caption = txtDisplay.caption + \"-\"\n\n\ndef on_click_btnClear():\n    txtDisplay.caption = \"0\"\n\n\ndef on_click_btn0():\n    if txtDisplay.caption != \"0\":\n        txtDisplay.caption = txtDisplay.caption + \"0\"\n\n\ndef on_click_btnEquals():\n    try:\n        result = eval(txtDisplay.caption)\n        txtDisplay.caption = str(result)\n    except:\n        txtDisplay.caption = \"Error\"\n\n\ndef on_click_btnAdd():\n    txtDisplay.caption = txtDisplay.caption + \"+\"\n";

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
