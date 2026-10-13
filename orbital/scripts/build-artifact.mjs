// Builds a single-file page for hosting as an artifact: the bundled game inlined
// into one HTML fragment (the host adds the document skeleton).
import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';

execSync('npx vite build', { stdio: 'inherit' });
const assets = readdirSync('dist/assets').filter((f) => f.endsWith('.js'));
if (assets.length !== 1) throw new Error(`expected one bundle, found ${assets.length}`);
const js = readFileSync(`dist/assets/${assets[0]}`, 'utf8').replace(/<\/script/gi, '<\\/script');
const b64 = (f) => readFileSync(`public/${f}`).toString('base64');
// The page is a fragment, so the icon tags travel with it (inline, as the page has no files next to it).
const head = `<meta name="apple-mobile-web-app-title" content="Orbital Race">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#02020a">
<link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,${b64('apple-touch-icon.png')}">
<link rel="icon" type="image/png" href="data:image/png;base64,${b64('icon-48.png')}">
`;
const html = `<title>Orbital Race</title>
${head}
<canvas id="game"></canvas>
<div id="overlay"></div>
<script type="module">${js}</script>
`;
mkdirSync('dist-artifact', { recursive: true });
writeFileSync('dist-artifact/orbital-race.html', html);
console.log(`artifact: ${(html.length / 1024).toFixed(1)} KB`);
