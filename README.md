# PASJ Program Builder

加速器学会年会の抄録JSONから、次の印刷用PDFを生成するツールです。

- 加速器学会年会プログラム集
- Author Index（著者索引）

PythonでHTML/CSSを生成し、Vivliostyle CLIでPDFに組版します。
元の抄録データがExcelまたはCSVの場合は、`pasj_program_to_json.py`でビルド用のJSONに変換できます。

## 必要な環境

- Python 3
- Node.js 22.12.0以降
- Vivliostyle CLI 11.1.0
- 日本語フォント：Noto Sans CJK JP
- 欧文フォント：Nimbus Roman（未導入の場合は、利用可能なセリフフォントへフォールバック）
- openpyxl（ExcelファイルをJSONへ変換する場合のみ）

### Ubuntu／Debianでの準備

Python、フォント、VivliostyleがPDF生成に使用するブラウザ関連ライブラリをインストールします。

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

Node.jsは、後述のバージョン管理ツールを使う方法を推奨します。ディストリビューション標準の`nodejs`パッケージはバージョンが古い場合があります。

### macOSでの準備

先に[Homebrew公式サイト](https://brew.sh/ja/)の手順でHomebrewをインストールしてから、Python、Node.js、Noto Sans CJKをインストールします。

```bash
brew update
brew install python node
brew install --cask font-noto-sans-cjk
```

macOSでは`libgbm1`を追加でインストールする必要はありません。Nimbus Romanがない場合は、Times New Romanなど、利用可能な欧文フォントへフォールバックします。

### Node.js環境

このプロジェクトでは、Node.js 22.12.0以降とNode.jsに同梱されるnpmを使用します。まず、現在の環境を確認します。

```bash
node --version
npm --version
```

`node --version`が`v22.12.0`以上であれば、そのまま利用できます。

#### Homebrewを使う場合（macOS）

HomebrewでNode.jsをインストールまたは更新します。

```bash
brew install node
```

すでにHomebrew版のNode.jsを導入している場合は、次のコマンドで更新できます。

```bash
brew update
brew upgrade node
```

#### nvmを使う場合（macOS／Linux）

複数のNode.jsバージョンを切り替える場合は、Node Version Manager（nvm）が便利です。[nvmの公式手順](https://github.com/nvm-sh/nvm#installing-and-updating)に従ってインストールした後、最新のLTS版を導入します。

```bash
nvm install --lts
nvm use --lts
nvm alias default 'lts/*'
```

新しいターミナルを開いた後は、次のコマンドで使用中のバージョンを確認できます。

```bash
node --version
npm --version
```

Pythonのバージョンも確認します。

```bash
python3 --version
```

### プロジェクト内だけで準備する場合

OS全体にNode.jsを入れない場合は、Node.jsのLinux x64配布版を`.tools/node`として展開し、PATHへ追加してからnpmを実行します。

```bash
export PATH="$PWD/.tools/node/bin:$PATH"
npm install
```

Pythonの仮想環境は次のように作成します。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Pythonパッケージ

ExcelファイルをJSONへ変換する場合は`openpyxl`が必要です。プロジェクト用の仮想環境を作成してインストールする方法を推奨します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

CSVから変換する場合や、作成済みのJSONからHTMLを生成するだけの場合は、追加のPythonパッケージは必要ありません。

### Vivliostyle CLI

Vivliostyle CLIをグローバルインストールする場合は、次を実行します。

```bash
npm install -g @vivliostyle/cli@11.1.0
vivliostyle --version
```

グローバルインストールを行わない場合は、ビルド時に`npx`で実行できます。

```bash
npx --yes @vivliostyle/cli@11.1.0 build
```

### フォントの確認

Ubuntu／Debianでは、次のコマンドで使用されるフォントを確認できます。

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

最初に、利用するJSONファイルを明示してプログラムとAuthor IndexのHTML/CSSを生成します。

```bash
python3 build_program.py --input abstract_2025.json --year 2025
python3 build_author_index.py --input abstract_2025.json
```

2026年のJSONファイルを使う場合も、両方のコマンドに同じ`--input`を指定します。

```bash
python3 build_program.py --input abstract_2026.json --year 2026
python3 build_author_index.py --input abstract_2026.json
```

続いてPDFを生成します。

```bash
PASJ_YEAR=2026 vivliostyle build
```

Vivliostyle CLIをグローバルインストールしていない場合は、次のコマンドでも実行できます。

```bash
PASJ_YEAR=2026 npx --yes @vivliostyle/cli@11.1.0 build
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

抄録JSONに座長情報がない場合や、セッションの表示名を変更する場合は、外部の座長設定JSONを利用できます。利用する場合に限り、`--chair chair_2025.json`を指定します。外部JSONに`chair`が設定されている場合は、抄録JSONの座長情報より優先されます。

座長設定のキーにはセッション名を使用します。

```json
{
  "加速構造": {
    "chair": "吉井（KEK）"
  },
  "加速構造・ビーム診断": {
    "heading": "加速構造 ／ ビーム診断・ビーム制御",
    "chair": "福田（KEK）／小林（KEK）"
  }
}
```

`chair`には座長の表示名を指定します。プログラム上のセッション名とは異なる見出しを表示する場合は、`heading`も指定できます。

入力ファイル、出力ディレクトリ、座長情報ファイルはオプションで変更できます。

```bash
python3 build_program.py \
  --input abstract_2025.json \
  --year 2025 \
  --output-dir dist \
  --chair chair_2025.json
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

GitHubのActions画面から`.github/workflows/build-pdf.yml`を手動で実行し、次の3項目を指定します。

- `json_file`: 利用するJSONファイルのパス
- `year`: PDFタイトルと開催日の曜日計算に使用する4桁の年
- `chair`: `use`（`chair_2025.json`を利用）または `do-not-use`（利用しない）

暗黙のデフォルト値はなく、pushによる自動実行も行いません。
ワークフローでは、`year`を`build_program.py`の`--year`とVivliostyleの`PASJ_YEAR`の両方に渡すため、開催日の曜日とPDFタイトルに同じ年が使われます。

ワークフローでは、次の処理を実行します。

1. Noto CJK、Nimbus Roman、Chrome用ライブラリのインストール
2. プログラムとAuthor IndexのHTML/CSS生成
3. Vivliostyle CLI 11.1.0によるPDF生成
4. 2つのPDFを`pasj-pdfs`というArtifactとして保存

生成したPDFは、GitHub Actionsの実行結果にあるArtifactsから取得できます。
