# new_program

`abstract.json` からプログラム集の印刷用 HTML を生成し、Vivliostyle で PDF に組版するための試作です。

## 生成

```bash
python3 build_program.py
```

生成物:

- `dist/program.html`
- `dist/program.css`

## PDF 化

Vivliostyle CLI が使える環境なら、`new_program` ディレクトリで以下を実行します。

```bash
vivliostyle build
```

または:

```bash
npx @vivliostyle/cli build
```

出力:

- `dist/program.pdf`
- `dist/author_index.pdf`

## Author Index

`abstract.json` の `coauthors` から、姓のアルファベット順で Author Index を生成します。
同じ著者が複数の発表に含まれる場合は、講演番号を1行にまとめます。

```bash
python3 build_author_index.py
```

中間生成物:

- `dist/author_index.html`
- `dist/author_index.css`

入力ファイルと出力ディレクトリは変更できます。

```bash
python3 build_author_index.py --input abstract.json --output-dir dist
```

`author_index_template_2025.docx` のA5判、余白、書体、文字サイズ、2列の比率、
各ページのヘッダーをCSSで再現しています。HTML生成後に `vivliostyle build` を実行すると
最終成果物の `dist/author_index.pdf` が生成されます。

## 補足

- `program_overrides.json` は、JSON に無い座長や表示用セッション名を補うための設定です。
- キーは `日付|会場|セッション名` です。
- 現状は Word テンプレートの「セッション見出し + 各発表2行」の見た目を参考にしています。
