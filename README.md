# PASJ Program Builder

`abstract.json` から次の印刷用PDFを生成するツールです。

- PASJ2025プログラム集
- Author Index（著者索引）

PythonでHTML/CSSを生成し、Vivliostyle CLIでPDFに組版します。

## 必要な環境

- Python 3
- Node.js 20以降
- Vivliostyle CLI
- 日本語フォント：Noto Sans CJK JP
- 欧文フォント：Nimbus Roman（未導入の場合は利用可能なserifフォントへフォールバック）

Vivliostyle CLIをグローバルインストールする場合は、次を実行します。

```bash
npm install -g @vivliostyle/cli@11.1.0
```

## ローカルでのビルド

最初に、プログラムとAuthor IndexのHTML/CSSを生成します。

```bash
python3 build_program.py
python3 build_author_index.py
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

`build_program.py` は `abstract.json` の発表情報をセッション単位でまとめます。JSONに含まれない座長名や表示用セッション名は、`program_overrides.json` で補完できます。

設定キーは次の形式です。

```text
日付|会場|セッション名
```

入力ファイル、出力ディレクトリ、補完設定ファイルはオプションで変更できます。

```bash
python3 build_program.py \
  --input abstract.json \
  --output-dir dist \
  --overrides program_overrides.json
```

タイトル内の `<sub>`、`<sup>`、`<i>`、`<em>`、`<b>`、`<strong>`、`<br>` は、安全なインラインHTMLとして保持されます。

## Author Index

`build_author_index.py` は `abstract.json` の `coauthors` から、姓のアルファベット順で著者索引を生成します。同一著者が複数の発表に含まれる場合は、対応する講演番号を1行にまとめます。

```bash
python3 build_author_index.py \
  --input abstract.json \
  --output-dir dist
```

## GitHub Actions

`.github/workflows/build-pdf.yml` が、`main` ブランチへの対象ファイルのpush時に自動実行されます。GitHubのActions画面から `workflow_dispatch` による手動実行もできます。

Workflowでは次を実行します。

1. Noto CJK、Nimbus Roman、Chrome用ライブラリのインストール
2. プログラムとAuthor IndexのHTML/CSS生成
3. Vivliostyle CLI 11.1.0によるPDF生成
4. 2つのPDFを `pasj-pdfs` Artifactとして保存

生成したPDFは、GitHubのWorkflow実行結果にあるArtifactsから取得できます。
