// Concatena src/*.js en una sola página: dist/fragment.html (para publicar) y dist/index.html (autónoma).
const fs = require('fs'), path = require('path');
const order = ['data', 'director', 'model', 'story', 'settlement', 'battle', 'ui', 'sfx', 'render', 'scenes1', 'scenes2', 'scenes3', 'main'];
const code = order.map(n => fs.readFileSync(path.join(__dirname, 'src', n + '.js'), 'utf8')).join('\n');
if (code.includes('</script')) throw new Error('</script> dentro del código');
const tpl = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');
const frag = tpl.replace('/*__CODE__*/', () => code);
fs.mkdirSync(path.join(__dirname, 'dist'), {recursive: true});
fs.writeFileSync(path.join(__dirname, 'dist', 'fragment.html'), frag);
fs.writeFileSync(path.join(__dirname, 'dist', 'index.html'), '<!doctype html>\n<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n' + frag.replace('</style>\n', '</style>\n</head><body>\n') + '\n</body></html>\n');
console.log('OK', (frag.length / 1024).toFixed(0) + ' KB');
