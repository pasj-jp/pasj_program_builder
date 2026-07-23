# PASJ Program Builder

選択した抄録JSONファイルから次の印刷用PDFを生成するツールです。

- PASJ2025プログラム集
- Author Index（著者索引）

PythonでHTML/CSSを生成し、Vivliostyle CLIでPDFに組版します。
元データがExcelまたはCSVの場合は、`pasj_program_to_json.py`でビルド用のJSONへ変換できます。

## 必要な環境

- Python 3
- Node.js 20以降
- Vivliostyle CLI 11.1.0
- 日本語フォント：Noto Sans CJK JP
- 欧文フォント：Nimbus Roman（未導入の場合は利用可能なserifフォントへフォールバック）
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

macOSには`libgbm1`の追加インストールは必要ありません。Nimbus Romanがなくても、Times New Romanなど利用可能な欧文フォントへフォールバックします。

Homebrewを使わずNode.jsを管理したい場合は、次のnvmを利用できます。

### Node.js環境

このプロジェクトではNode.js 20以降と、Node.jsに同梱されるnpmを使用します。まず現在の環境を確認します。

```bash
node --version
npm --version
```

`node --version`が`v20`以上であれば、そのまま利用できます。

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

新しいターミナルを開いた後も、次のコマンドで選択中のバージョンを確認できます。

```bash
node --version
npm --version
```

最後にPythonも確認します。

```bash
python3 --version
```

### Pythonパッケージ

ExcelファイルをJSONへ変換する場合は`openpyxl`が必要です。プロジェクト用の仮想環境を作成してインストールする方法を推奨します。

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install openpyxl
```

CSVから変換する場合や、作成済みJSONからHTMLを生成するだけの場合、追加のPythonパッケージは必要ありません。

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

別のOSでは、Noto Sans CJK JPをインストールするか、日本語表示が可能なフォントを用意してください。Nimbus Romanがない場合、CSSで指定された利用可能なserifフォントへフォールバックします。

## 抄録JSONの作成

`pasj_program_to_json.py`は、加速器学会のプログラムをビルドで利用する構造化JSONへ変換します。入力形式はExcel（`.xlsx`）とCSVに対応しているため、Excelを事前にCSVへ変換したり、不要な列を手作業で削除したりする必要はありません。

Excelファイルを変換する場合は、入力ファイルと出力ファイルを指定します。

```bash
python3 pasj_program_to_json.py program.xlsx abstract_2026.json
```

通常は先頭のシートを読み込みます。別のシートを使用する場合は、`--sheet`でシート名を指定します。

```bash
python3 pasj_program_to_json.py program.xlsx abstract_2026.json \
  --sheet "IAP-v18"
```

CSVファイルも同じ形式で変換できます。

```bash
python3 pasj_program_to_json.py program.csv abstract_2026.json
```

出力には、スクリプト内で定義されたプログラム情報と連名者情報だけが含まれます。Excelの開催日は、`8月26日`のような表記へ変換されます。

## ローカルでのビルド

最初に、利用するJSONファイルを明示してプログラムとAuthor IndexのHTML/CSSを生成します。

```bash
python3 build_program.py --input abstract_2025.json --year 2025
python3 build_author_index.py --input abstract_2025.json
```

2026年のJSONファイルを使う場合も、両方のコマンドに同じ `--input` を指定します。

```bash
python3 build_program.py --input abstract_2026.json --year 2026
python3 build_author_index.py --input abstract_2026.json
```

続いてPDFを生成します。

```bash
vivliostyle build
```

Vivliostyle CLIをグローバルインストールしていない場合は、次のコマンドでも実行できます。

```bash
npx --yes @vivliostyle/cli@11.1.0 build
```

`vivliostyle.config.js` の設定により、プログラムとAuthor Indexが続けてビルドされます。

## 生成物

中間生成物：

- `dist/program.html`
- `dist/program.css`
- `dist/author_index.html`
- `dist/author_index.css`

最終生成物：

- `dist/program.pdf`
- `dist/author_index.pdf`

`dist/` は生成ディレクトリのため、Gitの管理対象外です。

## プログラム集

`build_program.py` は指定した抄録JSONの発表情報をセッション単位でまとめます。JSONに含まれない座長名は、`chair_2025.json` から追加できます。このファイルには座長名に加え、必要なセッションの表示名も含まれます。

座長情報を利用する場合だけ、`--chair chair_2025.json` を指定します。省略した場合は座長情報を利用しません。

設定キーは次の形式です。

```text
日付|会場|セッション名
```

入力ファイル、出力ディレクトリ、座長情報ファイルはオプションで変更できます。

```bash
python3 build_program.py \
  --input abstract_2025.json \
  --year 2025 \
  --output-dir dist \
  --chair chair_2025.json
```

タイトル内の `<sub>`、`<sup>`、`<i>`、`<em>`、`<b>`、`<strong>`、`<br>` は、安全なインラインHTMLとして保持されます。

`--year`を指定すると、JSON内の開催日から曜日を計算して見出しに表示します。省略した場合は曜日を表示しません。

## Author Index

`build_author_index.py` は指定した抄録JSONの `coauthors` から、姓のアルファベット順で著者索引を生成します。同一著者が複数の発表に含まれる場合は、対応する講演番号を1行にまとめます。

```bash
python3 build_author_index.py \
  --input abstract_2025.json \
  --output-dir dist
```

## GitHub Actions

GitHubのActions画面から `.github/workflows/build-pdf.yml` を手動実行し、次の2項目を選択します。

- `json_file`: 利用するJSONファイルのパス
- `chair`: `use`（`chair_2025.json`を利用）または `do-not-use`（利用しない）

暗黙のデフォルトはなく、pushによる自動実行も行いません。
Workflowでは`--year`を指定しないため、ファイル名にかかわらず実行でき、開催日の曜日は表示されません。

Workflowでは次を実行します。

1. Noto CJK、Nimbus Roman、Chrome用ライブラリのインストール
2. プログラムとAuthor IndexのHTML/CSS生成
3. Vivliostyle CLI 11.1.0によるPDF生成
4. 2つのPDFを `pasj-pdfs` Artifactとして保存

生成したPDFは、GitHubのWorkflow実行結果にあるArtifactsから取得できます。
