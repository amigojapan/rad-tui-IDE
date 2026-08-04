# RAD-TUI-IDE 🖥️

**Rapid Application Development - ターミナル・ユーザー・インターフェース IDE**

MS-DOS用 Visual Basic 1.0 にインスパイアされた、Linux ターミナル、Windows PowerShell、または macOS ターミナルで動作するビジュアルIDEです。ターミナル上で、フォームの設計、コントロールの配置、コードの記述、そしてアプリケーションの実行のすべてを行うことができます！

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)
![Language](https://img.shields.io/badge/language-Python%20%7C%20FreeBASIC-orange.svg)

<a href="https://www.youtube.com/watch?v=YmBmVDsr3bo"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_play_button_icon_%282013%E2%80%932017%29.svg" alt="動画を見る" width="100"></a>

![screenshot](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/latestRAD-TUI-IDEscreenshot.png)

## プロジェクト例:
![tsukinoeditor](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/tsukinoeditor.png)

![minesweeper](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/minesweeper.png)

![tictactoe](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/tictactoe.png)

![calc](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/calc.png)

## インストールと使用ガイド

### Linux (Debian / Ubuntu / Linux Mint)

**1. Python と venv のインストール**
システムリポジトリが最新であることを確認し、Python 3 と `venv` モジュールをインストールします:
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

**2. セットアップと実行**
ホームディレクトリに仮想環境を作成し、それをアクティブにして、アプリケーションを起動します:
```bash
cd ~
python3 -m venv rad-tui-ide
source rad-tui-ide/bin/activate
pip install rad-tui-ide
rad-tui-ide
```
*(注: Arch、Fedora、またはその他のディストリビューションの場合は、`pacman` や `dnf` などのそれぞれのパッケージマネージャーを使用して Python 3 をインストールしてください)*

### macOS

**1. Homebrew のインストール**
ターミナルで以下のコマンドを実行して、Homebrewをインストールします（まだインストールしていない場合）:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Python のインストール**
Homebrew を更新し、Python 3 をインストールします:
```bash
brew update
brew install python3
```

**3. セットアップと実行**
仮想環境を作成し、パッケージをインストールして、IDEを実行します:
```bash
cd ~
python3 -m venv rad-tui-ide
source rad-tui-ide/bin/activate
pip install rad-tui-ide
rad-tui-ide
```

### Windows

**1. Python のインストール**
[Python 公式ウェブサイト](https://www.python.org/downloads/) または Microsoft Store から Python 3 をダウンロードしてインストールします。**インストール時に必ず "Add Python to PATH"（PythonをPATHに追加する）のボックスにチェックを入れてください。**

**2. セットアップと実行**
PowerShell または コマンドプロンプトを開き、以下のコマンドを実行します:
```powershell
cd $env:USERPROFILE
python -m venv rad-tui-ide

# 仮想環境をアクティブにする
# PowerShell の場合:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.
ad-tui-ide\Scripts\Activate.ps1
# または コマンドプロンプト の場合:
# .
ad-tui-ide\Scriptsctivate.bat

# インストールと実行
pip install rad-tui-ide
pip install windows-curses
rad-tui-ide
```

## parameters　パラメター parámetros
-jp 日本語にする
-es Cambiar a español 
-dark-mode starts the ide in dark-mode

## 集まり場
IRCでirc.libera.chat #VoxAssistチャネルで
リベラチャットは<a href=https://libera.chat/>このリンクで</a>入って#voxAssistチャネルに入ってください。

## 🎯 コンセプト

RAD-TUI-IDE は、MS-DOS用のVB1のような90年代初頭のビジュアルプログラミング環境の魔法を、現代のLinuxターミナルのために再現したものです。以下の機能を提供します:

- **ビジュアル・フォーム・デザイナー** - コントロールをフォームにドラッグ＆ドロップ
- **プロパティエディター** - リアルタイムでコントロールのプロパティを編集
- **コードエディター** - Tsukinoエディターでシンタックスハイライト付きのPythonコードを記述
- **ランタイム（実行）モード** - アプリケーションを即座にテスト
- **プロジェクト管理** - プロジェクトをJSONファイルとして保存および読み込み

## 🚀 機能

### ビジュアルデザイン環境
- 🖱️ **マウス駆動のインターフェース** - ポイント、クリック、ドラッグ、サイズ変更
- 🪟 **ドラッグ可能なウィンドウ** - フォームとツールボックスを自由に移動
- 🎨 **11種類のコントロールタイプ** (ボタン、ラベル、テキストボックスなど)
- 📐 **視覚的なサイズ変更** - ハンドルをつかんでコントロールのサイズを変更
- ✏️ **プロパティ編集** - 名前、キャプション、位置、サイズを編集

### コード開発
- 🐍 **Python コードビハインド** - Python でイベントハンドラを記述
- 🌈 **シンタックスハイライト** - キーワード、文字列、数値、コメント
- ▶️ **ランタイム実行** - ライブコード実行でフォームを実行
- 🐛 **ランタイムエラー表示** - メッセージボックスでエラーを確認

### プロジェクト管理
- 💾 **プロジェクトの保存/読み込み** - JSONベースのプロジェクトファイル
- 📁 **ファイルメニュー** - 標準的な保存/読み込み/終了操作
- 🔄 **デザイン/ランタイム 切り替え** - デザインタイムモードとランタイムモードを切り替え

## 🎮 実行方法

```bash
pip install rad-tui-ide

rad-tui-ide

rad-tui-ide -dark-mode

rad-tui-ide -run scriptname.json
```

## 🕹️ ユーザーガイド

### はじめに
1. アプリケーションを実行すると、以下が表示されます:
   - 左側に利用可能なコントロールを持つ **ツールボックス (Toolbox)**
   - 中央に **フォーム (Form)** ウィンドウ (デザイン画面)
   - 右側に **プロパティ (Properties)** ウィンドウ

### フォームの設計

| アクション | 方法 |
|--------|--------|
| **コントロールの追加** | ツールボックスでツールをクリックし、フォーム上をクリックします |
| **コントロールの移動** | "Move/Size (移動/ｻｲｽﾞ)"ツールを選択し、コントロールをドラッグします |
| **サイズ変更** | コントロールを選択し、■ ハンドルをドラッグします |
| **プロパティの編集**| プロパティウィンドウでプロパティの値を変更します |
| **コードの記述** | ボタンをダブルクリックしてコードエディタを開きます |

### 利用可能なコントロール

| ツール | 説明 |
|------|-------------|
| Check Box | 真偽値（ブール値）チェックボックスコントロール |
| Combo Box | ドロップダウン選択コントロール |
| Command Btn | クリック可能なボタン（最も一般的） |
| Frame | グループ化コンテナ |
| HScrollBar | 水平スクロールバー |
| Label | 静的テキスト表示 |
| List Box | スクロール可能なリスト |
| Option Btn | ラジオボタン |
| Text Box | テキスト入力フィールド |
| Timer | バックグラウンドタイマー |
| VScrollBar | 垂直スクロールバー |

### コードの記述

**コマンドボタン (Command Btn)** をダブルクリックしてコードエディタを開きます。コードエディタは以下をサポートしています:

```python
def on_click_btnOK():
    msgbox("こんにちは、世界！")
    txtName.caption = "更新されたテキスト"
```

**特別な関数:**
- `msgbox(text)` - メッセージボックスを表示します
- `name_id` で他のコントロールにアクセスします: `txtName.caption`、`btnOK.caption`

## 🛠️ 技術詳細

### Python 実装
- ターミナルUIに `curses` ライブラリを使用
- マウスイベントのサポート（マウスサポート付きのターミナルが必要）
- Pythonのシンタックスハイライト

## 📝 動作環境

### Python バージョン
- Python 3.6以上
- 以下の条件を満たすLinuxターミナル:
  - マウスサポート (xterm, gnome-terminal, konsole など)
  - UTF-8 文字サポート
  - 最小ターミナルサイズ 80x25

## 📜 ライセンス

このプロジェクトは **GNU General Public License v3.0** (GPL v3) の下でライセンスされています。

詳細については [LICENSE](LICENSE) を参照してください。

## 🙏 謝辞

インスピレーション:
- Microsoft Visual Basic 1.0 for MS-DOS (1992)
- 初期ビジュアルプログラミング環境のシンプルさ
- ターミナルベースのアプリケーションの不朽の魅力
