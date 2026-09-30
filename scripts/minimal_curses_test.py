import curses

def main(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Minimal curses test successful. Press any key to exit.")
    stdscr.refresh()
    stdscr.getkey()

if __name__ == "__main__":
    curses.wrapper(main)
