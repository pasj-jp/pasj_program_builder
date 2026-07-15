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

## 補足

- `program_overrides.json` は、JSON に無い座長や表示用セッション名を補うための設定です。
- キーは `日付|会場|セッション名` です。
- 現状は Word テンプレートの「セッション見出し + 各発表2行」の見た目を参考にしています。
