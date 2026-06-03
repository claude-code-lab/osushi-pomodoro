#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
時すでにおすし (Toki Sudeni Osushi)
強制ポモドーロタイマー

25分間の集中タイムが終わると、ターミナルがお寿司で埋め尽くされ、
5分間の強制休憩タイムが終わるまで画面が復帰しません。

Usage:
    osushi                   # 25分タイマーをバックグラウンドで開始
    osushi --minutes 30      # 30分タイマー（-m 30 も可）
    osushi --loop            # 終了後に自動で次のポモドーロを開始
    osushi --loop --break 3  # ループ時の休憩を3分に（-b 3 も可）
    osushi status            # 実行中タイマーの残り時間を表示
    osushi cancel            # 実行中タイマーをキャンセル
    osushi --test            # 5秒テストモード
    osushi --help            # ヘルプ表示
"""

import curses
import time
import random
import sys
import os
import shutil
import signal
import json
import subprocess

# ── 設定 ──────────────────────────────────────────────────────────────
WORK_SECONDS  = 25 * 60   # 25分

STATE_FILE = os.path.expanduser("~/.osushi_state")

# ── ANSI エスケープ ───────────────────────────────────────────────────
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
BLINK   = "\033[5m"
RESET   = "\033[0m"
CLEAR   = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

# ── ブロック体タイマー数字 (5行, 幅3) ────────────────────────────────
DIGITS = {
    "0": ["┌─┐", "│ │", "│ │", "│ │", "└─┘"],
    "1": [" ┐ ", " │ ", " │ ", " │ ", " ┴ "],
    "2": ["┌─┐", "  │", "┌─┘", "│  ", "└─┘"],
    "3": ["┌─┐", "  │", " ─┤", "  │", "└─┘"],
    "4": ["┐ ┐", "│ │", "└─┤", "  │", "  ┘"],
    "5": ["┌─┐", "│  ", "└─┐", "  │", "└─┘"],
    "6": ["┌─┐", "│  ", "├─┐", "│ │", "└─┘"],
    "7": ["┌─┐", "  │", "  │", "  │", "  ┘"],
    "8": ["┌─┐", "│ │", "├─┤", "│ │", "└─┘"],
    "9": ["┌─┐", "│ │", "└─┤", "  │", "└─┘"],
    ":": ["   ", " · ", "   ", " · ", "   "],
}

# ── お寿司パターン (ロック画面の背景) ───────────────────────────────
SUSHI_ROWS = [
    "🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 🍣 ",
    "🍱  🐟  🦐  🦑  🐠  🍙  🥢  🫙  🍤  🍱  🐟  🦐 ",
    "><> ><((°> ~~~ >=> ><> ><(((°> ~~~><> ><°>  ",
    "🍣🍱🐟🦐🦑🐠🍙🥢🫙🍤🍣🍱🐟🦐🦑🐠🍙🥢",
    "  ><>  ~~  ><((°>  ~~~  >=>  ~~  ><>  ~~  ",
    "🐠 🦑 🍣 🐟 🦐 🍱 🥢 🍙 🫙 🍤 🐠 🦑 🍣 🐟 ",
    "><{{{°>  ~~>=>~~  ><>  )><(  ~~  ><((°>  >>=",
]

ENCOURAGEMENT = [
    "🎯 集中タイム！フォーカス！",
    "💪 あと少し！頑張れ！",
    "🚀 いい調子！そのまま！",
    "🧠 脳みそフル回転中...",
    "☕ コーヒーは後で！今は集中！",
    "💡 今のこの瞬間を大切に！",
    "🔥 絶好調！この調子！",
    "⭐ もうすぐ寿司タイム...👀",
    "📺 ドラマの感想を考えておこう...",
    "🎵 集中BGMを流そう！",
]


# ═══════════════════════════════════════════════════════════════════════
#  フェーズ1: タイマー (curses)
# ═══════════════════════════════════════════════════════════════════════

class PomodoroTimer:
    def __init__(self, stdscr: "curses._CursesWindow", work_seconds: int):
        self.stdscr        = stdscr
        self.work_seconds  = work_seconds
        self.start_time    = time.time()
        self.done          = False

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN,   -1)  # 残り多め
        curses.init_pair(2, curses.COLOR_YELLOW,  -1)  # 残り少なめ
        curses.init_pair(3, curses.COLOR_RED,     -1)  # 残りわずか
        curses.init_pair(4, curses.COLOR_CYAN,    -1)  # ヘッダー/魚
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # メッセージ
        curses.curs_set(0)

    def _draw_digit(self, y: int, x: int, ch: str, color_attr: int) -> int:
        for row, line in enumerate(DIGITS.get(ch, ["   "] * 5)):
            try:
                self.stdscr.addstr(y + row, x, line, color_attr)
            except curses.error:
                pass
        return len(DIGITS[ch][0]) if ch in DIGITS else 3

    def _draw_big_clock(self, y: int, w: int, minutes: int, seconds: int, color_attr: int):
        label = f"{minutes:02d}:{seconds:02d}"
        # 幅計算: 各文字3 + スペース1 (最後なし)
        total_w = len(label) * 3 + (len(label) - 1)
        x = max(0, (w - total_w) // 2)
        for ch in label:
            cw = self._draw_digit(y, x, ch, color_attr | curses.A_BOLD)
            x += cw + 1

    def _draw_frame(self):
        h, w = self.stdscr.getmaxyx()
        elapsed   = int(time.time() - self.start_time)
        remaining = max(0, self.work_seconds - elapsed)
        minutes   = remaining // 60
        seconds   = remaining % 60

        if remaining == 0:
            self.done = True
            return

        self.stdscr.erase()

        # ヘッダー
        header = "[ 時すでにおすし - 強制ポモドーロタイマー ]"
        try:
            self.stdscr.addstr(
                1, max(0, (w - len(header)) // 2), header,
                curses.color_pair(4) | curses.A_BOLD,
            )
        except curses.error:
            pass

        # 大きな時計
        if remaining > 5 * 60:
            c = curses.color_pair(1)
        elif remaining > 60:
            c = curses.color_pair(2)
        else:
            c = curses.color_pair(3) | curses.A_BLINK
        self._draw_big_clock(h // 2 - 4, w, minutes, seconds, c)

        # プログレスバー
        progress  = elapsed / self.work_seconds
        bar_w     = min(50, w - 8)
        bar_x     = (w - bar_w - 2) // 2
        bar_y     = h // 2 + 3
        filled    = int(bar_w * progress)
        bar       = "█" * filled + "░" * (bar_w - filled)
        pct       = f" {progress * 100:.0f}%"
        try:
            self.stdscr.addstr(bar_y,     bar_x, f"[{bar}]",  c)
            self.stdscr.addstr(bar_y + 1, bar_x + bar_w - len(pct) + 1, pct, curses.color_pair(2))
        except curses.error:
            pass

        # 応援メッセージ (10秒ごとに切り替え)
        msg = ENCOURAGEMENT[int(time.time()) // 10 % len(ENCOURAGEMENT)]
        try:
            self.stdscr.addstr(
                bar_y + 3, max(0, (w - len(msg)) // 2), msg,
                curses.color_pair(5),
            )
        except curses.error:
            pass

        # 泳ぐ魚アニメ
        fish   = "><((°>"
        fish_x = int(time.time() * 8) % max(1, w - len(fish))
        try:
            self.stdscr.addstr(h - 2, fish_x, fish, curses.color_pair(4))
        except curses.error:
            pass

        # 終了ヒント
        try:
            self.stdscr.addstr(h - 1, 0, "Ctrl+C: 終了", curses.A_DIM)
        except curses.error:
            pass

        self.stdscr.refresh()

    def run(self):
        self.stdscr.nodelay(True)
        while not self.done:
            self._draw_frame()
            time.sleep(0.1)
            try:
                if self.stdscr.getch() == 3:   # Ctrl+C
                    sys.exit(0)
            except curses.error:
                pass


def run_timer(work_seconds: int):
    def _inner(stdscr):
        PomodoroTimer(stdscr, work_seconds).run()
    curses.wrapper(_inner)


# ═══════════════════════════════════════════════════════════════════════
#  状態ファイル管理 / cancel / status
# ═══════════════════════════════════════════════════════════════════════

def _save_state(pid: int, start: float, work_seconds: int):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"pid": pid, "start": start, "work_seconds": work_seconds}, f)
    except Exception:
        pass

def _load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return None

def _clear_state():
    try:
        os.remove(STATE_FILE)
    except Exception:
        pass


def cmd_cancel():
    state = _load_state()
    if not state:
        print(f"  {YELLOW}実行中のタイマーはありません{RESET}")
        return
    pid = state["pid"]
    try:
        os.kill(pid, signal.SIGTERM)
        _clear_state()
        print(f"  {GREEN}✅ タイマーをキャンセルしました (PID: {pid}){RESET}")
    except ProcessLookupError:
        _clear_state()
        print(f"  {YELLOW}タイマーはすでに終了しています{RESET}")


def cmd_status():
    state = _load_state()
    if not state:
        print(f"  {DIM}実行中のタイマーはありません{RESET}")
        return
    pid = state["pid"]
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        _clear_state()
        print(f"  {DIM}タイマーはすでに終了しています{RESET}")
        return
    elapsed      = int(time.time() - state["start"])
    work_seconds = state["work_seconds"]
    remaining    = max(0, work_seconds - elapsed)
    m, s         = remaining // 60, remaining % 60
    progress     = min(1.0, elapsed / work_seconds)
    bar_w        = 30
    filled       = int(bar_w * progress)
    bar          = "█" * filled + "░" * (bar_w - filled)
    print(f"\n{BOLD}{CYAN}🍣 時すでにおすし — ステータス{RESET}")
    print(f"  PID     : {DIM}{pid}{RESET}")
    if remaining > 0:
        print(f"  残り時間: {YELLOW}{BOLD}{m:02d}:{s:02d}{RESET}")
    else:
        print(f"  状態    : {MAGENTA}休憩中...{RESET}")
    print(f"  [{bar}] {progress * 100:.0f}%\n")


# ═══════════════════════════════════════════════════════════════════════
#  macOS 通知
# ═══════════════════════════════════════════════════════════════════════

def _notify(title: str, message: str, sound: str = "Glass"):
    try:
        import subprocess
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}" sound name "{sound}"'],
            check=False, timeout=5,
        )
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════
#  フェーズ2: お寿司フラッド (ANSI)
# ═══════════════════════════════════════════════════════════════════════

def _sushi_line(row: int, cols: int, t_offset: int = 0) -> str:
    pattern = SUSHI_ROWS[row % len(SUSHI_ROWS)]
    offset  = (row * 7 + t_offset) % len(pattern)
    chunk   = pattern[offset:] + pattern[:offset]
    return (chunk * (cols // len(chunk) + 2))[:cols]


def _row_color(row: int) -> str:
    return [CYAN, GREEN, YELLOW, MAGENTA, BLUE, RED, WHITE][row % 7]


def flood_animation():
    cols, rows = shutil.get_terminal_size((80, 24))
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    # 上から順に埋めていく
    for reveal in range(1, rows + 1):
        sys.stdout.write(CLEAR)
        for row in range(rows):
            if row < reveal:
                sys.stdout.write(f"{_row_color(row)}{_sushi_line(row, cols)}{RESET}\n")
            else:
                sys.stdout.write("\n")
        sys.stdout.flush()
        time.sleep(0.024)

    time.sleep(0.8)

    # ガタガタ揺らす
    for shake in range(4):
        sys.stdout.write(CLEAR)
        offset = 2 if shake % 2 == 0 else 0
        for row in range(rows):
            sys.stdout.write(
                f"{_row_color(row)}{_sushi_line(row, cols, offset)}{RESET}\n"
            )
        sys.stdout.flush()
        time.sleep(0.16)

_UNLOCK_ART = [
    "╔══════════════════════════════════════╗",
    "║       🎉  お疲れ様でした！  🎉       ║",
    "║  🍣  ゆっくり休憩してください！  🍣  ║",
    "╚══════════════════════════════════════╝",
]


def _show_victory():
    cols, rows = shutil.get_terminal_size((80, 24))
    box_w = len(_UNLOCK_ART[0])
    left  = " " * max(0, (cols - box_w) // 2)
    cy    = rows // 2 - len(_UNLOCK_ART) // 2

    for color in (GREEN, CYAN, GREEN, CYAN):
        sys.stdout.write(CLEAR + HIDE_CURSOR)
        for _ in range(cy):
            sys.stdout.write("\n")
        for line in _UNLOCK_ART:
            sys.stdout.write(f"{left}{BOLD}{color}{line}{RESET}\n")
        sys.stdout.flush()
        time.sleep(0.35)

    sys.stdout.write(CLEAR + SHOW_CURSOR)
    sys.stdout.flush()


# ═══════════════════════════════════════════════════════════════════════
#  エントリーポイント
# ═══════════════════════════════════════════════════════════════════════

def main():
    global WORK_SECONDS

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return

    if "cancel" in sys.argv:
        cmd_cancel()
        return

    if "status" in sys.argv:
        cmd_status()
        return


    if "--test" in sys.argv or "-t" in sys.argv:
        WORK_SECONDS = 5
        print(f"{YELLOW}テストモード: 5秒タイマー{RESET}")

    for flag in ("--minutes", "-m"):
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            try:
                WORK_SECONDS = int(sys.argv[idx + 1]) * 60
            except (IndexError, ValueError):
                print(f"{RED}使い方: osushi {flag} <分数>{RESET}")
                return

    loop_break = 5 * 60
    for flag in ("--break", "-b"):
        if flag in sys.argv:
            idx = sys.argv.index(flag)
            try:
                loop_break = int(sys.argv[idx + 1]) * 60
            except (IndexError, ValueError):
                print(f"{RED}使い方: osushi {flag} <分数>{RESET}")
                return

    loop_mode  = "--loop" in sys.argv
    work_label = f"{WORK_SECONDS}秒" if WORK_SECONDS < 60 else f"{WORK_SECONDS // 60}分"

    print(f"\n{BOLD}{CYAN}╔═══════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║{YELLOW}   🍣  時すでにおすし 強制ポモドーロ  🍣   {CYAN}║{RESET}")
    print(f"{BOLD}{CYAN}╚═══════════════════════════════════════════╝{RESET}")
    print()
    print(f"  {GREEN}・{RESET} {work_label}後にターミナルがお寿司で埋め尽くされます")
    print(f"  {GREEN}・{RESET} タイトルバーで残り時間を確認できます")
    if loop_mode:
        print(f"  {GREEN}・{RESET} {CYAN}ループモード: 次のポモドーロを自動開始{RESET}")
    print()

    parent_pgid = os.getpgrp()
    pid = os.fork()
    if pid > 0:
        print(f"  {BOLD}バックグラウンドで起動しました{RESET}  "
              f"{DIM}(osushi cancel でキャンセル / osushi status で確認){RESET}")
        print()
        return

    # ── 子プロセス ────────────────────────────────────────────────────
    os.setpgrp()
    signal.signal(signal.SIGHUP,  signal.SIG_IGN)
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)
    signal.signal(signal.SIGTTIN, signal.SIG_IGN)

    pomodoro_count = 0

    while True:
        pomodoro_count += 1
        start = time.time()
        _save_state(os.getpid(), start, WORK_SECONDS)

        try:
            tty_fd = os.open("/dev/tty", os.O_RDWR)
        except OSError:
            tty_fd = None

        # カウントダウン（タイトルバー更新）
        while True:
            elapsed   = int(time.time() - start)
            remaining = max(0, WORK_SECONDS - elapsed)
            if tty_fd is not None:
                m, s   = remaining // 60, remaining % 60
                prefix = f"#{pomodoro_count} " if loop_mode else ""
                try:
                    os.write(tty_fd, f"\033]0;🍣 {prefix}{m:02d}:{s:02d} - 時すでにおすし\007".encode())
                except OSError:
                    pass
            if remaining == 0:
                break
            time.sleep(1)

        if tty_fd is not None:
            os.close(tty_fd)

        sys.stdout = open("/dev/tty", "w", buffering=1)
        sys.stdin  = open("/dev/tty", "r")

        count_label = f" #{pomodoro_count}" if loop_mode else ""
        _notify("🍣 時すでにおすし！！！", f"ポモドーロ{count_label}終了！お疲れ様でした 🍣")

        flood_animation()
        _show_victory()

        sys.stdout.write("\033]0;\007")
        sys.stdout.flush()

        if not loop_mode:
            _clear_state()
            break

        # ループ: 休憩カウントダウン → 次のポモドーロへ
        break_label = f"{loop_break}秒" if loop_break < 60 else f"{loop_break // 60}分"
        print(f"\n{BOLD}{CYAN}🍣 ポモドーロ #{pomodoro_count} 完了！{break_label}休憩後に #{pomodoro_count + 1} を開始{RESET}\n")
        start_break = time.time()
        while True:
            remaining = max(0, loop_break - int(time.time() - start_break))
            m, s = remaining // 60, remaining % 60
            sys.stdout.write(f"\r  ☕ 休憩中 {m:02d}:{s:02d}  ")
            sys.stdout.flush()
            if remaining == 0:
                break
            time.sleep(1)
        sys.stdout.write("\r" + " " * 20 + "\r")
        sys.stdout.flush()
        subprocess.Popen(["afplay", "/System/Library/Sounds/Ping.aiff"])

        sys.stdout = open(os.devnull, "w")
        sys.stdin  = open(os.devnull, "r")


if __name__ == "__main__":
    main()
