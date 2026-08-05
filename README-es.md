[English](https://github.com/amigojapan/rad-tui-IDE/) [日本語](https://github.com/amigojapan/rad-tui-IDE/blob/main/README-jp.md)

# RAD-TUI-IDE 🖥️

**Rapid Application Development - Entorno de Desarrollo Integrado con Interfaz de Usuario de Terminal**

Un IDE visual inspirado en Visual Basic 1.0 para MS-DOS que funciona en la terminal de Linux, Windows PowerShell o la terminal de macOS. Diseñe formularios, coloque controles, escriba código y ejecute sus aplicaciones, ¡todo en la terminal!

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)
![Language](https://img.shields.io/badge/language-Python%20%7C%20FreeBASIC-orange.svg)

<a href="https://www.youtube.com/watch?v=Vh_pqqD16a4"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_play_button_icon_%282013%E2%80%932017%29.svg" alt="Ver el vídeo" width="100"></a>

![screenshot](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/latestRAD-TUI-IDEscreenshot.png)

## Proyectos de ejemplo:
![tsukinoeditor](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/tsukinoeditor.png)

![minesweeper](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/minesweeper.png)

![tictactoe](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/tictactoe.png)

![calc](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/calc.png)

## Guía de instalación y uso

### Linux (Debian / Ubuntu / Linux Mint)

**1. Instalar Python y venv**
Asegúrese de que los repositorios de su sistema estén actualizados e instale Python 3 junto con el módulo `venv`:
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

**2. Configurar y Ejecutar**
Cree un entorno virtual en su directorio principal, actívelo y ejecute la aplicación:
```bash
cd ~
python3 -m venv rad-tui-ide
source rad-tui-ide/bin/activate
pip install rad-tui-ide
rad-tui-ide
```
*(Nota: Para Arch, Fedora u otras distribuciones, use su administrador de paquetes respectivo como `pacman` o `dnf` para instalar Python 3).*

### macOS

**1. Instalar Homebrew**
Ejecute el siguiente comando en su terminal para instalar Homebrew (si aún no lo ha hecho):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Instalar Python**
Actualice Homebrew e instale Python 3:
```bash
brew update
brew install python3
```

**3. Configurar y Ejecutar**
Cree un entorno virtual, instale el paquete y ejecute el IDE:
```bash
cd ~
python3 -m venv rad-tui-ide
source rad-tui-ide/bin/activate
pip install rad-tui-ide
rad-tui-ide
```

### Windows

**1. Instalar Python**
Descargue e instale Python 3 desde el [sitio web oficial de Python](https://www.python.org/downloads/) o mediante Microsoft Store. **Asegúrese de marcar la casilla que dice "Add Python to PATH"** durante la instalación.

**2. Configurar y Ejecutar**
Abra PowerShell o el símbolo del sistema y ejecute los siguientes comandos:
```powershell
cd $env:USERPROFILE
python -m venv rad-tui-ide

# Activar el entorno virtual
# En PowerShell:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.
ad-tui-ide\Scripts\Activate.ps1
# O en el Símbolo del sistema:
# .
ad-tui-ide\Scriptsctivate.bat

# Instalar y ejecutar
pip install rad-tui-ide
pip install windows-curses
rad-tui-ide
```

## parámetros　パラメター parámetros
-run scriptname.json

-dark-mode modo obscuro

-jp 日本語にする

-es Cambiar a español

## Comunidad
Únase a nuestra comunidad en IRC en irc.libera.chat en el canal #VoxAssist.
Haga clic en [este enlace](https://web.libera.chat/) para unirse a través de la web y entrar al canal #voxAssist.

## 🎯 Concepto

RAD-TUI-IDE recrea la magia de los primeros entornos de programación visual de los años 90 como VB1 para MS-DOS, pero para las terminales de Linux modernas. Proporciona:

- **Diseñador Visual de Formularios** - Arrastre y suelte controles en formularios
- **Editor de Propiedades** - Edite las propiedades de los controles en tiempo real
- **Editor de Código** - Escriba código Python con resaltado de sintaxis en el editor Tsukino
- **Modo de Ejecución** - Pruebe sus aplicaciones al instante
- **Gestión de Proyectos** - Guarde y cargue proyectos como archivos JSON

## 🚀 Características

### Entorno de Diseño Visual
- 🖱️ **Interfaz basada en ratón** - Apunte, haga clic, arrastre y cambie de tamaño
- 🪟 **Ventanas arrastrables** - Mueva formularios y cuadros de herramientas libremente
- 🎨 **11 tipos de controles** incluyendo botones, etiquetas, cuadros de texto y más
- 📐 **Redimensionamiento visual** - Agarre los tiradores para cambiar el tamaño de los controles
- ✏️ **Edición de propiedades** - Edite nombres, leyendas, posiciones y dimensiones

### Desarrollo de Código
- 🐍 **Código subyacente en Python** - Escriba controladores de eventos en Python
- 🌈 **Resaltado de sintaxis** - Palabras clave, cadenas, números y comentarios
- ▶️ **Ejecución en tiempo de ejecución** - Ejecute sus formularios con la ejecución de código en vivo
- 🐛 **Visualización de errores en tiempo de ejecución** - Vea los errores en un cuadro de mensaje

### Gestión de Proyectos
- 💾 **Guardar/Cargar proyectos** - Archivos de proyecto basados en JSON
- 📁 **Menú Archivo** - Operaciones estándar de guardar/cargar/salir
- 🔄 **Cambio Diseño/Ejecución** - Cambie entre los modos de tiempo de diseño y tiempo de ejecución

## 🎮 Cómo Ejecutar

```bash
pip install rad-tui-ide

rad-tui-ide

rad-tui-ide -dark-mode

rad-tui-ide -run scriptname.json
```

## 🕹️ Guía del Usuario

### Empezando
1. Ejecute la aplicación, verá:
   - Un **Cuadro de herramientas (Toolbox)** a la izquierda con los controles disponibles
   - Una ventana de **Formulario (Form)** en el centro (su superficie de diseño)
   - Una ventana de **Propiedades (Properties)** a la derecha

### Diseñando un Formulario

| Acción | Cómo Hacerlo |
|--------|--------|
| **Añadir un control** | Haga clic en una herramienta en la caja de herramientas, luego haga clic en el formulario |
| **Mover un control** | Seleccione la herramienta "Mover/Tam (Move/Size)", luego arrastre el control |
| **Cambiar tamaño** | Seleccione el control, luego arrastre el tirador ■ |
| **Editar propiedades**| Haga clic en el valor de una propiedad en la ventana Propiedades |
| **Escribir código** | Haga doble clic en un botón para abrir el editor de código |

### Controles Disponibles

| Herramienta | Descripción |
|------|-------------|
| Check Box | Control de casilla de verificación (booleano) |
| Combo Box | Control de selección desplegable |
| Command Btn | Botón que se puede presionar (el más común) |
| Frame | Contenedor de agrupación |
| HScrollBar | Barra de desplazamiento horizontal |
| Label | Pantalla de texto estático |
| List Box | Lista desplazable |
| Option Btn | Botón de opción (Radio button) |
| Text Box | Campo de entrada de texto |
| Timer | Temporizador en segundo plano |
| VScrollBar | Barra de desplazamiento vertical |

### Escribiendo Código

Haga doble clic en un **Command Button (Botón de comando)** para abrir el editor de código. El editor de código soporta:

```python
def on_click_btnOK():
    msgbox("Hola, Mundo!")
    txtName.caption = "Texto actualizado"
```

**Funciones especiales:**
- `msgbox(text)` - Muestra un cuadro de mensaje
- Acceda a otros controles por su `name_id`: `txtName.caption`, `btnOK.caption`

## 🛠️ Detalles Técnicos

### Implementación en Python
- Utiliza la biblioteca `curses` para la interfaz de usuario de la terminal
- Soporta eventos de ratón (requiere terminal con soporte para ratón)
- Resaltado de sintaxis de Python

## 📝 Requisitos

### Versión de Python
- Python 3.6+
- Terminal Linux con:
  - Soporte para ratón (xterm, gnome-terminal, konsole, etc.)
  - Soporte de caracteres UTF-8
  - Tamaño mínimo de terminal de 80x25

## 📜 Licencia

Este proyecto está licenciado bajo la **GNU General Public License v3.0** (GPL v3).

Vea [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

Inspirado por:
- Microsoft Visual Basic 1.0 para MS-DOS (1992)
- La simplicidad de los primeros entornos de programación visual
- El atractivo perdurable de las aplicaciones basadas en terminal
