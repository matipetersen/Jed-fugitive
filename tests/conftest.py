import os
import tempfile

# Autosaves happen every 200 ticks; keep test runs out of the player's real save folder.
os.environ.setdefault('JEDI_FUGITIVE_SAVE_DIR', tempfile.mkdtemp(prefix='jf-test-saves-'))
