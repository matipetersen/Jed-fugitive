### Project Structure

```
JediFugitive/
│
├── src/
│   ├── main.py                # Main entry point for the game
│   ├── config.py              # Configuration settings (e.g., game settings, paths)
│   ├── assets/                 # Directory for game assets
│   │   ├── images/            # Images (sprites, backgrounds)
│   │   ├── sounds/            # Sound effects and music
│   │   └── fonts/             # Font files
│   │
│   ├── game/                  # Core game logic
│   │   ├── __init__.py
│   │   ├── game_manager.py     # Game state management
│   │   ├── scene_manager.py     # Scene transitions and management
│   │   ├── input_handler.py     # Input handling (keyboard, mouse)
│   │   ├── physics.py           # Physics calculations and collision detection
│   │   └── ui.py                # User interface components
│   │
│   ├── entities/               # Game entities (characters, enemies, etc.)
│   │   ├── __init__.py
│   │   ├── player.py            # Player character logic
│   │   ├── enemy.py             # Enemy character logic
│   │   └── npc.py               # Non-player character logic
│   │
│   ├── levels/                 # Level design and management
│   │   ├── __init__.py
│   │   ├── level1.py            # Level 1 design
│   │   ├── level2.py            # Level 2 design
│   │   └── level_manager.py      # Level loading and management
│   │
│   ├── items/                  # Items and inventory management
│   │   ├── __init__.py
│   │   ├── item.py              # Item class
│   │   └── inventory.py         # Inventory management
│   │
│   ├── dialogues/              # Dialogue and narrative management
│   │   ├── __init__.py
│   │   ├── dialogue_manager.py   # Dialogue system
│   │   └── dialogues.py         # Predefined dialogues
│   │
│   └── utils/                  # Utility functions and helpers
│       ├── __init__.py
│       ├── logger.py            # Logging utility
│       └── helpers.py           # General helper functions
│
├── tests/                      # Unit tests for the game
│   ├── __init__.py
│   ├── test_game_manager.py     # Tests for game manager
│   ├── test_player.py           # Tests for player logic
│   └── test_dialogue_manager.py  # Tests for dialogue system
│
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── SAVE_SYSTEM.md              # Save/Load system documentation
└── .gitignore                  # Git ignore file
```

## Features

### Save System 🎮
- **Autosave**: Game automatically saves every 20 turns
- **Manual Save**: Press Shift+S to save anytime
- **Load on Startup**: Continue your adventure from where you left off
- See [SAVE_SYSTEM.md](SAVE_SYSTEM.md) for complete documentation

### Being hunted: Heat (Force signature)
Every Force power and every fight leaves a trace (`game/pursuit.py`). Heat
decays while you stay quiet (faster underground; meditation lowers it).
At 30 a patrol is sent to where you were, at 60 patrols come more often with
a Sith warrior and nearby Sith converge, at 90 a Sith Predator is dispatched.

### Sith tombs with identity (`game/tomb_lords.py`)
Each tomb belongs to one Dark Lord (Ajunta Pall, Tulak Hord, Marka Ragnos,
Naga Sadow, Freedon Nadd) with its own trial, garrison and named guardian
beside the corrupted Jedi relic. One holocron fragment (`◊`) lies on each of
the first three floors; recover all three to inherit what that Lord knew
(Protect, Juyo / Vaapad, Force Rage, Force Phantom or Drain, plus a stat).

### Survival: wounds and camping (`game/survival.py`)
Heavy hits leave wounds (leg, arm, torso, head) that the Force cannot heal.
Medkits treat one; **K** makes camp for 40 ticks to rest and treat a wound,
at a risk of being found that grows with Heat, wounds, and inside tombs.

### NPC quests
Survivors on the surface offer deliver / recover / hunt / escort / scout
quests; **Q** shows the quest log.

### Explanation of Structure

1. **src/**: This is the main source directory containing all the game code.
   - **main.py**: The entry point of the game where the game loop is initiated.
   - **config.py**: Contains configuration settings such as screen dimensions, frame rates, and asset paths.
   - **assets/**: A directory for all game assets, organized into subdirectories for images, sounds, and fonts.
   - **game/**: Contains core game logic, including game management, scene management, input handling, physics, and UI components.
   - **entities/**: Contains classes and logic for various game entities like the player, enemies, and NPCs.
   - **levels/**: Contains level designs and a level manager to handle loading and transitioning between levels.
   - **items/**: Manages items and inventory systems, including item definitions and inventory management.
   - **dialogues/**: Manages dialogues and narrative elements, including a dialogue manager and predefined dialogues.
   - **utils/**: Contains utility functions and helpers that can be used throughout the game.

2. **tests/**: A directory for unit tests to ensure the functionality of various components of the game.

3. **requirements.txt**: A file listing the Python dependencies required to run the game.

4. **README.md**: Documentation for the project, including setup instructions, gameplay mechanics, and contribution guidelines.

5. **.gitignore**: A file specifying files and directories that should be ignored by Git.

### Benefits of This Structure

- **Modularity**: Each component of the game is separated into its own file or directory, making it easier to manage and understand.
- **Readability**: The organization allows developers to quickly locate files related to specific functionalities.
- **Maintainability**: Changes can be made to specific components without affecting the entire codebase, reducing the risk of introducing bugs.
- **Scalability**: New features can be added more easily as the project grows, following the established structure.

This structure provides a solid foundation for developing "Jedi Fugitive: Echoes of the Fallen" while promoting best practices in software development.