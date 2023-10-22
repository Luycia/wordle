# Wordle
A terminal version of the Wordle puzzle game (like the online version of the [Nytimes](https://www.nytimes.com/games/wordle/index.html)). This game also provides a solver that recommends good advice according to information theory (explanation video [3Blue1Brown](https://www.youtube.com/watch?v=v68zYyaEmEA)).

## Build project
- Move to root project: `cd wordle`
- Create virtual environment: `python -m venv .venv`
- Activate virtual environmen:
    - Unix: `source .venv/bin/activate`
    - Windows:
        - for cmd `.venv\Scripts\activate.bat`
        - for powershell `.venv\Scripts\Activate.ps1`
- Install necessary packages: `pip install -r requirements.txt`
- Install pyinstaller `pip install pyinstaller`
- Build app:
    - MacOS: `pyinstaller -F --add-data "data:data" --icon build/icon.icns --osx-bundle-identifier com.luycia.games --name wordle src/app.py`
    - Windows: `pyinstaller -F --add-data "data:data" --icon build/icon.ico --name wordle src/app.py`
