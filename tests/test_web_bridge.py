"""The browser bridge: key-by-key play with the game's own menus (runs in a subprocess,
because the bridge replaces the curses module for the whole interpreter)."""
import json
import os
import subprocess
import sys

SCRIPT = r'''
import json, sys, io, contextlib
from jedi_fugitive.web import bridge, cursesstub as c
out = {}
with contextlib.redirect_stdout(io.StringIO()):
    s = json.loads(bridge.start('small', seed=7))
    out['start'] = s['ready'] and s['hud']['hp'] > 0
    t0 = s['hud']['turn']
    s = json.loads(bridge.press(c.KEY_RIGHT))
    out['move_ticks'] = s['hud']['turn'] == t0 + 1
    s = json.loads(bridge.press(ord('i')))                  # inventory: a modal menu
    out['inventory_prompt'] = bool(s['prompt']) and any('INVENTORY' in l for l in s['prompt']['lines'])
    t1 = s['hud']['turn']
    s = json.loads(bridge.answer(c.KEY_DOWN))               # the cursor moves (action replayed)
    out['menu_navigates'] = bool(s['prompt'])
    s = json.loads(bridge.answer(27))                       # Esc closes it, no time passes
    out['esc_closes_free'] = s['prompt'] is None and s['hud']['turn'] == t1
    s = json.loads(bridge.press(ord('J')))                  # the journal opens too
    out['journal_prompt'] = bool(s['prompt'])
    s = json.loads(bridge.cancel())
    s = json.loads(bridge.set_view(21, 15))
    out['view'] = len(s['map']) == 15 and len(s['map'][0]) == 21
print(json.dumps(out))
'''


def test_bridge_plays_and_handles_menus(tmp_path):
    env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), '..', 'src'),
               JEDI_FUGITIVE_SAVE_DIR=str(tmp_path))
    res = subprocess.run([sys.executable, '-c', SCRIPT], capture_output=True, text=True, env=env, timeout=300)
    assert res.returncode == 0, res.stderr[-2000:]
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert all(out.values()), out
