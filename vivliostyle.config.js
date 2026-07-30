const year = process.env.PASJ_YEAR || String(new Date().getFullYear());

if (!/^\d{4}$/.test(year)) {
  throw new Error('PASJ_YEAR must be a four-digit year (for example, 2026).');
}

module.exports = [
  {
    title: `PASJ${year} Program`,
    language: 'ja',
    entry: 'dist/program.html',
    output: 'dist/program.pdf',
  },
  {
    title: `PASJ${year} Author Index`,
    language: 'en',
    entry: 'dist/author_index.html',
    output: 'dist/author_index.pdf',
  },
];
