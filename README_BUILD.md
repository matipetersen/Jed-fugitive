Building standalone executables
==============================

This project is a terminal-based Python game. Below are instructions and CI automation to produce standalone executables for macOS and Windows.

Notes and constraints
- Building Windows executables on macOS is not supported by PyInstaller directly. Use GitHub Actions (workflow included) or a Windows runner.
- The game uses curses; Windows needs the `windows-curses` package at runtime. The `requirements.txt` includes a platform-specific marker to install that on Windows.

Local macOS build (recommended)
1. Ensure Python 3.11+ is installed.
2. From the repository root:

```bash
./scripts/build_mac.sh
```

This will create a virtualenv, install PyInstaller, and build a single-file executable at `dist/jedi-fugitive`.

Local Windows build (on Windows machine)
1. Open PowerShell and run the script:

```powershell
scripts\build_windows.ps1 -Python python
```

Using CI (GitHub Actions)
- A workflow is included at `.github/workflows/build.yml`. It builds both macOS and Windows artifacts on dedicated runners and uploads them as build artifacts.

Running the produced artifact
- macOS/Linux: open a terminal, make the file executable (if needed) and run:

```bash
./dist/jedi-fugitive
```

- Windows: run `dist\jedi-fugitive.exe` from PowerShell/Command Prompt.

Troubleshooting
- If the game fails with curses initialization errors, run in a proper terminal and set `TERM` appropriately, e.g. `export TERM=xterm-256color`.
- If additional dependencies exist, add them to `requirements.txt`.
