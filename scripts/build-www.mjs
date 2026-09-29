// アプリに入れるファイルだけを www/ に書き出す。
// Web 版（GitHub Pages）はリポジトリ直下のファイルをそのまま使うので、直下の構成は変えない。
import { cp, mkdir, rm } from 'node:fs/promises';

const FILES = ['index.html', 'manifest.webmanifest', 'icon-180.png', 'icon-192.png', 'icon-512.png'];

await rm('www', { recursive: true, force: true });
await mkdir('www');
for (const f of FILES) await cp(f, `www/${f}`);
console.log(`www/ に ${FILES.length} ファイルを書き出しました`);
