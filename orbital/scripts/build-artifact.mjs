// Builds a single-file page for hosting as an artifact: the bundled game inlined
// into one HTML fragment (the host adds the document skeleton).
import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';

execSync('npx vite build', { stdio: 'inherit' });
const assets = readdirSync('dist/assets').filter((f) => f.endsWith('.js'));
if (assets.length !== 1) throw new Error(`expected one bundle, found ${assets.length}`);
const js = readFileSync(`dist/assets/${assets[0]}`, 'utf8').replace(/<\/script/gi, '<\\/script');
const html = `<title>Orbital Race</title>
<canvas id="game"></canvas>
<div id="overlay"></div>
<script type="module">${js}</script>
`;
mkdirSync('dist-artifact', { recursive: true });
writeFileSync('dist-artifact/orbital-race.html', html);
console.log(`artifact: ${(html.length / 1024).toFixed(1)} KB`);
