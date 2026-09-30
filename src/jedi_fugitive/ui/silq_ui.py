import curses
from typing import Tuple, Optional, List, Dict, Any
from jedi_fugitive.ui.dialog import UIMessageBuffer

class SILQUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.panels = {}
        self.messages = UIMessageBuffer()
        self.term_h, self.term_w = stdscr.getmaxyx()
        self.colors_inited = False
        self.popups: List[Dict[str, Any]] = []

    def init_colors(self):
        if self.colors_inited:
            return
        try:
            import random
            curses.start_color()
            curses.use_default_colors()
            
            # DYNAMIC COLOR SCHEMES: Randomize world colors each game for fresh visual variety
            # Store the seed for consistency during this game session
            if not hasattr(self, '_color_seed'):
                self._color_seed = random.randint(0, 999999)
            random.seed(self._color_seed)
            
            # Define 5 different Sith-themed color palettes
            sith_palettes = [
                # Palette 1: Classic Blood & Shadow
                {'primary': curses.COLOR_RED, 'secondary': curses.COLOR_MAGENTA, 'accent': curses.COLOR_YELLOW},
                # Palette 2: Toxic Corruption
                {'primary': curses.COLOR_GREEN, 'secondary': curses.COLOR_YELLOW, 'accent': curses.COLOR_RED},
                # Palette 3: Ancient Tomb
                {'primary': curses.COLOR_CYAN, 'secondary': curses.COLOR_BLUE, 'accent': curses.COLOR_WHITE},
                # Palette 4: Dark Lightning
                {'primary': curses.COLOR_MAGENTA, 'secondary': curses.COLOR_CYAN, 'accent': curses.COLOR_WHITE},
                # Palette 5: Infernal Fire
                {'primary': curses.COLOR_YELLOW, 'secondary': curses.COLOR_RED, 'accent': curses.COLOR_MAGENTA},
            ]
            
            # Randomly select palette
            palette = random.choice(sith_palettes)
            random.seed()  # Reset seed for gameplay randomness
            
            # Apply dynamic palette to color pairs
            curses.init_pair(1, palette['primary'], -1)      # headers / danger
            curses.init_pair(2, palette['primary'], -1)      # enemy / danger / damage
            curses.init_pair(3, palette['accent'], -1)       # items / loot
            curses.init_pair(4, curses.COLOR_WHITE, -1)      # floor / text (always white for readability)
            curses.init_pair(5, palette['secondary'], -1)    # wall / frame
            curses.init_pair(6, palette['primary'], -1)      # hp / life force
            curses.init_pair(7, palette['secondary'], -1)    # abilities / dark force
            curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK) # inverted (dark mode)
            curses.init_pair(9, curses.COLOR_WHITE, palette['primary'])   # alert / pop damage
            curses.init_pair(10, curses.COLOR_BLACK, palette['primary'])  # corruption emphasis
            curses.init_pair(14, curses.COLOR_WHITE, palette['secondary'])  # highlight
            # additional pairs for projectiles / taunts / minor accents
            try:
                curses.init_pair(11, palette['primary'], -1)     # dark side bolts
                curses.init_pair(12, palette['primary'], -1)     # enemy bolts
                curses.init_pair(13, palette['accent'], -1)      # neutral projectiles
                curses.init_pair(15, palette['secondary'], -1)   # taunt / dark whispers
            except Exception:
                pass
            self.colors_inited = True
        except curses.error:
            self.colors_inited = False

    def _safe_subwin(self, h:int, w:int, y:int, x:int) -> Optional[curses.window]:
        try:
            if h <= 0 or w <= 0:
                return None
            return self.stdscr.subwin(h, w, y, x)
        except curses.error:
            return None

    def centered_dialog(self, lines, title: str = ""):
        """Display a centered dialog with lines and return last key pressed.

        In headless or non-interactive stubs, if getch() returns -1 we return None
        immediately so callers can fallback to message-buffer behavior.
        """
        try:
            height = len(lines) + 4
            width = max(len(title) + 8, max((len(l) for l in lines), default=10) + 4)
            th, tw = self.stdscr.getmaxyx()
            y = max(0, (th - height)//2)
            x = max(0, (tw - width)//2)
            win = curses.newwin(height, width, y, x)
            win.bkgd(' ', curses.color_pair(8)) # White on Black
            win.clear()
            # Border with secondary color (Sith aesthetic)
            win.attron(curses.color_pair(5) | curses.A_BOLD)
            win.border()
            win.attroff(curses.color_pair(5) | curses.A_BOLD)
            
            try:
                if title:
                    # Decorative title
                    display_title = f" ◈ {title} ◈ "
                    win.addstr(0, (width - len(display_title)) // 2, display_title, curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass
            for i, ln in enumerate(lines):
                try:
                    win.addstr(2 + i, 2, ln[:width-4], curses.color_pair(4))
                except curses.error:
                    pass
            # hint line
            try:
                hint = "Press any key to continue"
                win.addstr(height-2, (width - len(hint)) // 2, hint, curses.A_DIM | curses.color_pair(4))
            except curses.error:
                pass
            win.refresh()
            # wait for a key, but detect headless stubs (getch -> -1)
            try:
                key = self.stdscr.getch()
                if key == -1:
                    return None
                return key
            except Exception:
                return None
        except Exception:
            return None

    def create_layout(self, map_w, map_h, stats_w, abil_w, msg_h, cmd_h):
        """Create or update layout panes. Simplified and consistent naming."""
        # refresh terminal size
        self.term_h, self.term_w = self.stdscr.getmaxyx()
        # clamp sizes to terminal
        map_w = min(map_w, max(10, self.term_w - 4))
        stats_w = min(stats_w, max(10, self.term_w - map_w - 2))
        abil_w = min(abil_w, max(8, self.term_w - map_w - stats_w - 2))
        map_h = min(map_h, max(6, self.term_h - 6))
        msg_h = min(msg_h, max(3, self.term_h - map_h - 3))
        cmd_h = min(cmd_h, max(1, self.term_h - map_h - msg_h - 1))

        # create main panels (use subwin if possible, fallback to newwin)
        def mkwin(h, w, y, x):
            win = self._safe_subwin(h, w, y, x)
            if not win:
                try:
                    win = curses.newwin(max(1,h), max(1,w), max(0,y), max(0,x))
                except Exception:
                    return None
            return win

        self.panels = {}
        # map at left
        self.panels['map'] = mkwin(map_h, map_w, 0, 0)
        sx = map_w + 1
        self.panels['stats'] = mkwin(map_h, stats_w, 0, sx)
        ax = map_w + stats_w + 2
        self.panels['abilities'] = mkwin(map_h, abil_w, 0, ax)

        # Calculate positions for commands and messages at bottom (full width)
        msg_y = map_h + cmd_h + 1
        cmd_y = map_h + 1
        
        # commands panel above messages (full width)
        self.panels['commands'] = mkwin(cmd_h, self.term_w - 2, cmd_y, 1)
        # messages panel at bottom (full width)
        self.panels['messages'] = mkwin(msg_h, self.term_w - 2, msg_y, 1)

        # always ensure minimal fallback map panel exists
        if not self.panels.get('map'):
            self.panels = {'map': mkwin(self.term_h-2, self.term_w-2, 0, 1), 'messages': self.panels.get('messages')}

    def dim_overlay(self):
        try:
            overlay = curses.newwin(self.term_h, self.term_w, 0, 0)
            overlay.bkgd(' ', curses.A_DIM)
            return overlay
        except curses.error:
            return None

    def popup_dialogue(self, items, title: str = "MENU", show_details=True, footer_text=None, allow_inspect=False):
        """Enhanced popup dialogue box for inventory, crafting, and other interactions.
        
        Args:
            items: List of tuples (name, description, metadata_dict) or simple strings
            title: Title of the dialogue box
            show_details: Whether to show item details in right panel
            footer_text: Custom footer instructions
            allow_inspect: Whether to allow 'x' key for detailed inspection
            
        Returns:
            Selected index or None if cancelled
        """
        if not items:
            return None
            
        # Parse items into uniform format
        parsed_items = []
        for item in items:
            if isinstance(item, tuple) and len(item) >= 2:
                parsed_items.append(item)
            elif isinstance(item, str):
                parsed_items.append((item, "", {}))
            else:
                parsed_items.append((str(item), "", {}))
        
        try:
            th, tw = self.stdscr.getmaxyx()
            
            # Calculate dimensions - MUCH larger popup for lore text and long descriptions
            min_width = 80  # Increased from 70
            min_height = 25  # Increased from 20
            
            # Adjust based on content - allow more width for long descriptions
            content_width = max(len(title) + 10, max((len(item[0]) + len(item[1]) + 5 for item in parsed_items), default=40))
            # Also check description length for wrapping
            max_desc_len = max((len(str(item[1])) for item in parsed_items), default=0)
            width = min(tw - 4, max(min_width, content_width + 20, max_desc_len + 10))
            height = min(th - 4, max(min_height, len(parsed_items) + 12))
            
            y = max(0, (th - height) // 2)
            x = max(0, (tw - width) // 2)
            
            win = curses.newwin(height, width, y, x)
            win.bkgd(' ', curses.color_pair(8))
            
            selected = 0
            scroll_offset = 0
            max_visible = height - 6  # Space for title, borders, footer
            
            while True:
                win.clear()
                
                # Draw double-line border for enhanced look
                win.attron(curses.color_pair(5) | curses.A_BOLD)
                win.border()
                win.attroff(curses.color_pair(5) | curses.A_BOLD)
                
                # Draw title bar with decorative elements
                try:
                    title_text = f" ╣ {title} ╠ "
                    title_x = (width - len(title_text)) // 2
                    win.addstr(0, title_x, title_text, curses.color_pair(1) | curses.A_BOLD)
                except curses.error:
                    pass
                
                # Draw divider line
                try:
                    win.addstr(2, 1, "─" * (width - 2), curses.color_pair(5))
                except curses.error:
                    pass
                
                # Calculate visible range
                if selected < scroll_offset:
                    scroll_offset = selected
                elif selected >= scroll_offset + max_visible:
                    scroll_offset = selected - max_visible + 1
                
                # Draw items
                visible_items = parsed_items[scroll_offset:scroll_offset + max_visible]
                for i, (name, desc, meta) in enumerate(visible_items):
                    actual_idx = i + scroll_offset
                    y_pos = 3 + i
                    
                    if actual_idx == selected:
                        # Highlighted selection
                        color = curses.color_pair(14) | curses.A_BOLD | curses.A_REVERSE
                        prefix = "▶ "
                    else:
                        color = curses.color_pair(3)
                        prefix = "  "
                    
                    try:
                        # Item name and number
                        item_num = f"{actual_idx + 1})"
                        item_text = f"{prefix}{item_num:3s} {name}"
                        
                        # Add description if it fits
                        max_text_width = width - 6
                        if show_details and desc and len(item_text) < max_text_width - 3:
                            remaining = max_text_width - len(item_text) - 3
                            if len(desc) <= remaining:
                                item_text += f" - {desc}"
                            else:
                                item_text += f" - {desc[:remaining-3]}..."
                        
                        win.addstr(y_pos, 2, item_text[:max_text_width], color)
                    except curses.error:
                        pass
                
                # Draw scroll indicators
                if scroll_offset > 0:
                    try:
                        win.addstr(3, width - 2, "▲", curses.color_pair(1) | curses.A_BOLD)
                    except curses.error:
                        pass
                if scroll_offset + max_visible < len(parsed_items):
                    try:
                        win.addstr(height - 3, width - 2, "▼", curses.color_pair(1) | curses.A_BOLD)
                    except curses.error:
                        pass
                
                # Draw footer with controls
                try:
                    footer_y = height - 2
                    win.addstr(footer_y - 1, 1, "─" * (width - 2), curses.color_pair(5))
                    
                    if footer_text:
                        footer = footer_text
                    else:
                        footer = "↑↓:Navigate │ Enter:Select │ ESC:Cancel"
                        if allow_inspect:
                            footer += " │ X:Inspect"
                    
                    footer_x = (width - len(footer)) // 2
                    win.addstr(footer_y, footer_x, footer, curses.color_pair(6))
                except curses.error:
                    pass
                
                # Show count
                try:
                    count_text = f" {selected + 1}/{len(parsed_items)} "
                    win.addstr(footer_y, width - len(count_text) - 2, count_text, curses.color_pair(6) | curses.A_DIM)
                except curses.error:
                    pass
                
                win.refresh()
                
                # Handle input
                key = self.stdscr.getch()
                
                if key in (curses.KEY_UP, ord('k')):
                    if selected > 0:
                        selected -= 1
                elif key in (curses.KEY_DOWN, ord('j')):
                    if selected < len(parsed_items) - 1:
                        selected += 1
                elif key == curses.KEY_PPAGE:  # Page Up
                    selected = max(0, selected - max_visible)
                elif key == curses.KEY_NPAGE:  # Page Down
                    selected = min(len(parsed_items) - 1, selected + max_visible)
                elif key == curses.KEY_HOME:
                    selected = 0
                elif key == curses.KEY_END:
                    selected = len(parsed_items) - 1
                elif key in (curses.KEY_ENTER, ord('\n'), ord('\r'), ord(' ')):
                    return selected
                elif key == 27:  # ESC
                    return None
                elif allow_inspect and key in (ord('x'), ord('X')):
                    return ('inspect', selected)
                elif ord('1') <= key <= ord('9'):
                    # Quick select by number
                    idx = key - ord('1')
                    if idx < len(parsed_items):
                        return idx
                        
        except Exception:
            return None
    
    def centered_menu(self, lines, title: str = "MENU"):
        """Display a centered menu and return selected index."""
        height = len(lines) + 4
        width = max(len(title)+8, max((len(l) for l in lines), default=10) + 4)
        try:
            th, tw = self.stdscr.getmaxyx()
            y = max(0, (th - height)//2)
            x = max(0, (tw - width)//2)
            win = curses.newwin(height, width, y, x)
            win.bkgd(' ', curses.color_pair(8))
            
            selected = 0
            while True:
                # Clear and redraw the entire menu each time
                win.clear()
                # Border with secondary color (Sith aesthetic)
                win.attron(curses.color_pair(5) | curses.A_BOLD)
                win.border()
                win.attroff(curses.color_pair(5) | curses.A_BOLD)

                try:
                    display_title = f" ◈ {title} ◈ "
                    win.addstr(0, (width - len(display_title)) // 2, display_title, curses.color_pair(1) | curses.A_BOLD)
                except curses.error:
                    pass
                
                # Draw menu options with selection highlight
                for i, ln in enumerate(lines):
                    if i == selected:
                        # Highlighted item: Inverted or bright color
                        color = curses.color_pair(14) | curses.A_BOLD | curses.A_REVERSE
                        prefix = " ▶ "
                    else:
                        color = curses.color_pair(3)
                        prefix = "   "
                    
                    try:
                        # Center the text or left align with padding?
                        # Left align looks better for lists
                        text = f"{prefix}{ln}"
                        win.addstr(2 + i, 2, text[:width-4], color)
                    except curses.error:
                        pass
                win.refresh()
                
                # Get input
                key = self.stdscr.getch()
                if key == curses.KEY_UP and selected > 0:
                    selected -= 1
                elif key == curses.KEY_DOWN and selected < len(lines) - 1:
                    selected += 1
                elif key in (curses.KEY_ENTER, ord('\n'), ord('\r')):
                    return selected
                elif key == 27:  # Esc
                    return None
        except curses.error:
            return None

    def message_panel_draw(self):
        panel = self.panels.get('messages')
        if not panel: return
        panel.clear()
        try:
            panel.border()
            # SITH AESTHETIC: Dark side terminology
            panel.addstr(0,2," ◈ DARK CHRONICLES ◈ ", curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        h,w = panel.getmaxyx()
        lines = self.messages.messages[-(h-2):]
        for i, m in enumerate(lines):
            text = f"{m.get('timestamp','')} {m.get('text','')}".strip()
            try:
                panel.addstr(1+i, 2, text[:w-4], curses.color_pair(3))
            except curses.error:
                pass
        try:
            panel.refresh()
        except curses.error:
            pass

    def draw_commands(self, text: str):
        """Render the commands box (text shown above the message panel)."""
        panel = getattr(self, "panels", {}).get("commands")
        if not panel:
            return
        try:
            panel.clear()
            try: panel.border()
            except Exception: pass
            # SITH AESTHETIC: Dark side terminology
            title = " ◈ DARK POWERS ◈ "
            try:
                panel.addstr(0, 2, title, curses.color_pair(7) | curses.A_BOLD)
            except Exception:
                pass
            lines = (text or "").splitlines()
            max_h, max_w = panel.getmaxyx()
            for i, line in enumerate(lines[: max_h - 2]):
                try:
                    panel.addstr(1 + i, 2, line[: max_w - 4])
                except Exception:
                    pass
            try:
                panel.refresh()
            except Exception:
                pass
        except Exception:
            # fail silently so UI doesn't crash the game loop
            pass

    # --- popup support for damage/taunts ---
    def add_popup(self, x: int, y: int, text: str, color_pair: int = 9, ttl: int = 6,
                  echo: bool = True, echo_text: Optional[str] = None):
        # store popups in map coordinates; age=0 means freshly created
        self.popups.append({"x": x, "y": y, "text": text, "color": color_pair, "ttl": ttl, "age": 0})
        # optionally echo to the messages buffer (lower part)
        if echo:
            if echo_text:
                self.messages.add(echo_text, color_pair)
            else:
                self.messages.add(text, color_pair)

    def tick_popups(self):
        # increment age and purge expired
        new = []
        for p in self.popups:
            p["age"] += 1
            if p["age"] < p["ttl"]:
                new.append(p)
        self.popups = new

    def draw_popups(self, panel=None):
        """Draw simple popup lines into the provided panel (or messages panel). Defensive and no complex annotations."""
        try:
            if panel is None:
                panel = getattr(self, "panels", {}).get("messages")
            if panel is None:
                return
            # gather popups (expecting self.popups to be a list of dicts with 'text' or raw strings)
            raw_popups = getattr(self, "popups", []) or []
            popups = []
            for p in raw_popups:
                if isinstance(p, dict):
                    text = p.get("text") or p.get("msg") or ""
                else:
                    text = str(p)
                popups.append(text)

            # clear panel area
            try:
                panel.erase()
            except Exception:
                try:
                    panel.clear()
                except Exception:
                    pass

            try:
                maxy, maxx = panel.getmaxyx()
            except Exception:
                maxy, maxx = 0, 0

            # draw the last popups that fit
            start = max(0, len(popups) - maxy) if maxy > 0 else 0
            y = 0
            for line in popups[start:]:
                if y >= maxy:
                    break
                try:
                    s = str(line)
                    # addnstr is safer when width limited
                    if hasattr(panel, "addnstr"):
                        panel.addnstr(y, 0, s, max(0, maxx - 1))
                    else:
                        panel.addstr(y, 0, s[: max(0, maxx - 1)])
                except Exception:
                    try:
                        # best-effort fallback
                        panel.addstr(y, 0, (str(line)[: max(0, maxx - 1)]) if maxx > 1 else "")
                    except Exception:
                        pass
                y += 1

            try:
                if hasattr(panel, "noutrefresh"):
                    panel.noutrefresh()
                else:
                    panel.refresh()
            except Exception:
                try:
                    panel.refresh()
                except Exception:
                    pass
        except Exception:
            # swallow errors so UI code doesn't crash the game loop
            try:
                msgs = getattr(self, "panels", {}).get("messages")
                if msgs and hasattr(msgs, "addstr"):
                    try:
                        msgs.addstr(0, 0, "Popup draw failed.")
                        msgs.refresh()
                    except Exception:
                        pass
            except Exception:
                pass

    def draw_sith_codex(self, codex, show_codex: bool = False):
        """Draw Sith Codex overlay showing discovered lore entries.
        
        Args:
            codex: SithCodex instance
            show_codex: Whether to display the full codex panel (toggled with 'v' key)
        """
        if not show_codex or not codex:
            return
            
        try:
            # Create centered overlay window
            th, tw = self.stdscr.getmaxyx()
            panel_h = min(40, th - 4)
            panel_w = min(80, tw - 4)
            y = max(0, (th - panel_h) // 2)
            x = max(0, (tw - panel_w) // 2)
            
            win = curses.newwin(panel_h, panel_w, y, x)
            win.bkgd(' ', curses.color_pair(8))
            win.clear()
            win.border()
            
            # Title - SITH AESTHETIC
            title = " ◈◈◈ SITH CODEX ◈◈◈ "
            try:
                win.addstr(0, (panel_w - len(title)) // 2, title, 
                          curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass
            
            # Calculate discovery progress
            total_entries = 0
            discovered_count = len(codex.discovered_entries)
            for cat, entries in codex.categories.items():
                total_entries += len(entries)
            
            # Progress header
            progress_line = f"Discovered: {discovered_count}/{total_entries}"
            try:
                win.addstr(2, 2, progress_line, curses.color_pair(3) | curses.A_BOLD)
            except curses.error:
                pass
            
            # Display categories and progress
            line = 4
            for category, entries in codex.categories.items():
                if line >= panel_h - 3:
                    break
                    
                # Count discovered in this category
                cat_discovered = sum(1 for (c, _) in codex.discovered_entries if c == category)
                cat_total = len(entries)
                
                # Category header
                cat_title = category.replace('_', ' ').title()
                cat_line = f"{cat_title}: {cat_discovered}/{cat_total}"
                try:
                    win.addstr(line, 2, cat_line, curses.color_pair(7) | curses.A_BOLD)
                    line += 1
                except curses.error:
                    pass
                
                # Show discovered entries in this category
                for entry_id in entries.keys():
                    if line >= panel_h - 3:
                        break
                    if (category, entry_id) in codex.discovered_entries:
                        entry = entries[entry_id]
                        title = entry.get('title', entry_id)
                        prefix = "★ " if entry.get('force_echo') else "  "
                        try:
                            win.addstr(line, 4, f"{prefix}{title}"[:panel_w-6], 
                                      curses.color_pair(6) if entry.get('force_echo') else curses.color_pair(4))
                            line += 1
                        except curses.error:
                            pass
                line += 1
            
            # Footer hint
            hint = "Press 'v' to close | ★ = Force Echo"
            try:
                win.addstr(panel_h - 2, 2, hint[:panel_w-4], curses.A_DIM)
            except curses.error:
                pass
            
            win.refresh()
        except Exception:
            pass
