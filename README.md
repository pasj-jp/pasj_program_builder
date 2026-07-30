# PASJ Program Builder

加速器学会年会の抄録JSONから、次の印刷用PDFを生成するツールです。

- 加速器学会年会プログラム集
- Author Index（著者索引）

PythonでHTML/CSSを生成し、Vivliostyle CLIでPDFに組版します。
元の抄録データがExcelまたはCSVの場合は、`pasj_program_to_json.py`でビルド用のJSONに変換できます。

## 必要な環境

- Python 3
- Node.js 22.12.0以降
- npm
- Vivliostyle CLI 11.1.0（`npm install`でプロジェクト内に導入）
- 日本語フォント：Noto Sans CJK JP（プログラム集では`@fontsource/noto-sans-jp`も利用）
- 欧文フォント：Nimbus Roman（未導入の場合は、利用可能なセリフフォントへフォールバック）
- openpyxl（ExcelファイルをJSONへ変換する場合のみ）

## インストール方法

OSごとに、Python、Node.js、フォント、VivliostyleがPDF生成に使用するブラウザ関連ライブラリを準備します。

Node.jsは22.12.0以降が必要です。OS標準パッケージのNode.jsが古い場合は、`nvm`などのバージョン管理ツールを使用してください。

### Linuxでのインストール

#### RHEL系OS（AlmaLinux、Rocky Linuxなど）

Python、フォント、ブラウザ関連ライブラリをインストールします。

```bash
sudo dnf install -y \
  python3 \
  python3-pip \
  fontconfig \
  google-noto-sans-cjk-fonts \
  urw-base35-fonts \
  mesa-libgbm
sudo fc-cache -f
```

Node.js 22.12.0以降とnpmをインストールします。OSのリポジトリで条件を満たすNode.jsが提供されている場合は、次のようにインストールできます。

```bash
sudo dnf install -y nodejs npm
node --version
npm --version
```

`node --version`が`v22.12.0`未満の場合は、`nvm`でNode.jsのLTS版をインストールしてください。

```bash
nvm install --lts
nvm use --lts
nvm alias default 'lts/*'
```

#### Debian系OS（Ubuntuなど）

Python、フォント、ブラウザ関連ライブラリをインストールします。

```bash
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  fonts-noto-cjk \
  fonts-urw-base35 \
  libgbm1
sudo fc-cache -f
```

Debian系OSの標準`nodejs`パッケージは古いことがあります。まず現在のバージョンを確認します。

```bash
node --version
npm --version
```

`node --version`が`v22.12.0`未満の場合は、`nvm`でNode.jsのLTS版をインストールしてください。

```bash
nvm install --lts
nvm use --lts
nvm alias default 'lts/*'
```

### macOSでのインストール

先に[Homebrew公式サイト](https://brew.sh/ja/)の手順でHomebrewをインストールしてから、Python、Node.js、Noto Sans CJKをインストールします。

```bash
brew update
brew install python node
brew install --cask font-noto-sans-cjk
```

Homebrew版のNode.jsが古い場合は更新します。

```bash
brew upgrade node
```

macOSでは`libgbm1`を追加でインストールする必要はありません。Nimbus Romanがない場合は、Times New Romanなど、利用可能な欧文フォントへフォールバックします。

### Windowsでのインストール

WindowsではWSL上で利用してください。WSLにはUbuntuなどのLinuxディストリビューションを入れ、以降は「Linuxでのインストール」の手順に従います。

Windows側にインストールしたNode.jsやnpmをWSLから使うと、環境によっては正しく動かないことがあります。WSL内で`node --version`と`npm --version`を実行し、Linux側のNode.js 22.12.0以降が使われていることを確認してください。

### バージョン確認

インストール後、使用中のバージョンを確認します。

```bash
python3 --version
node --version
npm --version
```

### プロジェクト共通セットアップ

リポジトリを取得したら、Python仮想環境とNode.js依存パッケージをインストールします。

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
npm install
```

`npm install`により、Vivliostyle CLIと日本語Webフォントがプロジェクト内の`node_modules/`にインストールされます。Vivliostyle CLIをグローバルインストールする必要はありません。

OS全体にNode.jsを入れない場合は、Node.jsのLinux x64配布版を`.tools/node`として展開し、PATHへ追加してから`npm install`を実行することもできます。

```bash
export PATH="$PWD/.tools/node/bin:$PATH"
npm install
```

### Pythonパッケージについて

ExcelファイルをJSONへ変換する場合は`openpyxl`が必要です。プロジェクト用の仮想環境を作成してインストールする方法を推奨します。

CSVから変換する場合や、作成済みのJSONからHTMLを生成するだけの場合は、追加のPythonパッケージは必要ありません。

### フォントの確認

Linuxでは、次のコマンドで使用されるフォントを確認できます。

```bash
fc-match "Noto Sans CJK JP"
fc-match "Nimbus Roman"
```

macOSでは、次のコマンドでNoto Sans CJKが認識されているか確認できます。

```bash
system_profiler SPFontsDataType | grep -i "Noto Sans CJK"
```

その他のOSでは、Noto Sans CJK JPをインストールするか、日本語を表示できるフォントを用意してください。Nimbus Romanがない場合は、CSSで指定された利用可能なセリフフォントへフォールバックします。

## 抄録JSONの作成

`pasj_program_to_json.py`は、加速器学会のプログラムデータをビルド用の構造化JSONに変換します。入力形式はExcel（`.xlsx`）とCSVに対応しているため、Excelを事前にCSVへ変換したり、不要な列を手作業で削除したりする必要はありません。

Excelファイルを変換する場合は、入力ファイルと出力ファイルを指定します。

```bash
python3 pasj_program_to_json.py program_2026_v2.xlsx abstract_2026.json
```

通常は先頭のシートを読み込みます。別のシートを使用する場合は、`--sheet`でシート名を指定します。

```bash
python3 pasj_program_to_json.py program_2026_v2.xlsx abstract_2026.json \
  --sheet "IAP-v20"
```

CSVファイルも同じ形式で変換できます。

```bash
python3 pasj_program_to_json.py program.csv abstract_2026.json
```

出力には、スクリプトで定義されたプログラム情報、座長情報、連名者情報だけが含まれます。Excelの開催日は、`8月26日`のような表記に変換されます。

## ローカルでのビルド

2026年のJSONファイルを使う場合は、HTML/CSS生成からPDF作成まで次のコマンドで実行できます。

```bash
npm run build:2026
```

2025年のJSONファイルを使う場合は次を実行します。

```bash
npm run build:2025
```

手動で実行する場合は、最初に利用するJSONファイルを明示してプログラムとAuthor IndexのHTML/CSSを生成します。

```bash
python3 build_program.py --input abstract_2026.json --year 2026
python3 build_author_index.py --input abstract_2026.json
```

続いてPDFを生成します。

```bash
PASJ_YEAR=2026 npx vivliostyle build
```

この場合、PDFタイトルはそれぞれ`PASJ2026 Program`と`PASJ2026 Author Index`になります。`PASJ_YEAR`には、`build_program.py`の`--year`と同じ年を指定してください。`PASJ_YEAR`を省略すると、コマンドを実行した時点の西暦年が使われます。

`vivliostyle.config.js`の設定により、プログラムとAuthor Indexが続けてビルドされます。

## 生成物

中間生成物：

- `dist/program.html`
- `dist/program.css`
- `dist/author_index.html`
- `dist/author_index.css`

最終生成物：

- `dist/program.pdf`
- `dist/author_index.pdf`

`dist/`は生成ディレクトリのため、Gitの管理対象外です。

## プログラム集

`build_program.py`は、指定した抄録JSONの発表情報をセッション単位でまとめます。各発表の`chair`に座長名が含まれている場合は、同一セッション内の座長名を重複なくまとめて表示します。

入力ファイルと出力ディレクトリはオプションで変更できます。

```bash
python3 build_program.py \
  --input abstract_2026.json \
  --year 2026 \
  --output-dir dist
```

タイトル内の`<sub>`、`<sup>`、`<i>`、`<em>`、`<b>`、`<strong>`、`<br>`は、安全なインラインHTMLとして保持されます。

`--year`を指定すると、JSON内の開催日から曜日を計算して見出しに表示します。省略した場合は曜日を表示しません。

## Author Index

`build_author_index.py`は、指定した抄録JSONの`coauthors`から、姓のアルファベット順で著者索引を生成します。同一著者が複数の発表に含まれる場合は、対応する講演番号を1行にまとめます。

```bash
python3 build_author_index.py \
  --input abstract_2025.json \
  --output-dir dist
```

## GitHub Actions

GitHubのActions画面から`.github/workflows/build-pdf.yml`を手動で実行し、次の2項目を指定します。

- `json_file`: 利用するJSONファイルのパス
- `year`: PDFタイトルと開催日の曜日計算に使用する4桁の年

暗黙のデフォルト値はなく、pushによる自動実行も行いません。
ワークフローでは、`year`を`build_program.py`の`--year`とVivliostyleの`PASJ_YEAR`の両方に渡すため、開催日の曜日とPDFタイトルに同じ年が使われます。

ワークフローでは、次の処理を実行します。

1. Noto CJK、Nimbus Roman、Chrome用ライブラリのインストール
2. `npm ci`によるVivliostyle CLIとフォント依存のインストール
3. プログラムとAuthor IndexのHTML/CSS生成
4. Vivliostyle CLI 11.1.0によるPDF生成
5. 2つのPDFを`pasj-pdfs`というArtifactとして保存

生成したPDFは、GitHub Actionsの実行結果にあるArtifactsから取得できます。
