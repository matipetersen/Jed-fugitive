# Headless check for intro/narrative messages after world generation
from jedi_fugitive.game.game_manager import GameManager

# minimal dummy stdscr
class DummyStdscr:
    def getmaxyx(self): return (40, 140)
    def getch(self): return -1
    def clear(self): pass
    def refresh(self): pass

if __name__ == '__main__':
    stdscr = DummyStdscr()
    gm = GameManager(stdscr)
    gm.initialize()
    # generate world (map_features.generate_world) which should add intro messages
    gm.generate_world()
    # print messages buffer lines
    msgs = []
    try:
        mb = getattr(gm.ui, 'messages', None)
        if mb is None:
            print('No message buffer found on UI')
        else:
            for m in mb.messages:
                print(m.get('text'))
    except Exception as e:
        print('Error reading messages:', e)
