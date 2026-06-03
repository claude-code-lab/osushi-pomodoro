# Toki Sudeni Osushi 🍣

[Japanese](README.md)

Pomodoro timer — when time's up, your terminal drowns in sushi

> When 25 minutes are up, your entire terminal gets flooded with sushi ASCII art,
> and a "Well done!" screen appears.

![demo](https://github.com/claude-code-lab/osushi-pomodoro/releases/download/v1.0.0/demo.gif)

---

## Install

```bash
# Clone the repository
git clone https://github.com/claude-code-lab/osushi-pomodoro osushi_pomodoro
cd osushi_pomodoro

# Install (adds an alias to your shell RC file)
make install

# Run the source command shown after make install, or open a new terminal
```

> If `$ZDOTDIR` is set (e.g. `~/dotfiles/.config/zsh`), it will write there automatically.

---

## Uninstall

```bash
cd osushi_pomodoro

# Remove the alias
make uninstall

# Run the source command shown after make uninstall

# Remove the directory
cd .. && rm -rf osushi_pomodoro
```

---

## Usage

```bash
osushi                   # Start a 25-minute timer in the background (keep using the terminal)
osushi -m 30             # 30-minute timer (--minutes 30 also works)
osushi --loop            # Automatically start the next pomodoro after each session
osushi --loop -b 3       # Set break duration to 3 minutes in loop mode (--break 3 also works)
osushi -m 50 --loop -b 10  # 50-minute work + 10-minute break loop
osushi status            # Show remaining time of the running timer
osushi cancel            # Cancel the running timer
osushi --test            # Test the animation with a 5-second timer
osushi --help            # Show help
```

---

## How It Works

```
1. [Background launch]
   The osushi command returns immediately → keep working in your terminal
   Remaining time is shown in the title bar (🍣 24:59 - Toki Sudeni Osushi)

            ↓ 25 minutes pass

2. [macOS notification]
   "🍣 Toki Sudeni Osushi!!!" notification appears
   → You'll notice even if you're in another tab or app

3. [Flood animation]
   Sushi pours in from the top of your terminal 🍣🍱🐟🦐...

4. [Well done screen]
   🎉 Good work! Take a break! 🍣

--- In loop mode (--loop) ---

5. [Break countdown]
   ☕ Break 05:00 → 04:59 → ... → 00:00

6. → Next pomodoro starts automatically in the background
```

---

## Customization

Change at runtime with options:

```bash
osushi -m 45             # Set work time to 45 minutes
osushi --loop -b 10      # Set break to 10 minutes in loop mode
```

Change defaults by editing constants at the top of `osushi.py`:

```python
WORK_SECONDS = 25 * 60  # Pomodoro duration (seconds)
```

---

## Requirements

- Python 3.6+
- macOS (with notifications) / Linux (no notifications) / Windows via WSL recommended
- Unicode / emoji-capable terminal (Ghostty, iTerm2, WezTerm, Alacritty, etc.)

> If notifications don't appear on macOS, go to System Settings → Notifications → allow notifications for Terminal (or Python).

---

*"Toki sudeni ososhi" (already too late) → "Toki sudeni osushi" (already... sushi)*

> This project is not affiliated with any TV drama of the same name.

---

*Made with [Claude Code](https://claude.ai/code) (Claude Sonnet 4.6)*
