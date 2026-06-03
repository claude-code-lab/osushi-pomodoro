# 時すでにおすし 🍣

[English](README.en.md)

ポモドーロタイマー — 時間になるとターミナルがお寿司に沈む

> 25分経つとターミナル全体がお寿司のアスキーアートで埋め尽くされ、
> お疲れ様でした画面が表示されます。

![demo](https://github.com/claude-code-lab/osushi-pomodoro/releases/download/v1.0.0/demo.gif)

---

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/claude-code-lab/osushi-pomodoro osushi_pomodoro
cd osushi_pomodoro

# インストール (エイリアスを shell の RC ファイルに追加)
make install

# make install 完了後に表示される source コマンドを実行、または新しいターミナルを開く
```

> `$ZDOTDIR` が設定されている場合（例: `~/dotfiles/.config/zsh`）は自動的にそちらへ書き込みます。

---

## アンインストール

```bash
cd osushi_pomodoro

# エイリアスを削除
make uninstall

# make uninstall 完了後に表示される source コマンドを実行

# ディレクトリを削除
cd .. && rm -rf osushi_pomodoro
```

---

## 使い方

```bash
osushi                   # 25分タイマーをバックグラウンドで開始（ターミナルは使い続けられる）
osushi -m 30             # 30分タイマー（--minutes 30 も可）
osushi --loop            # 終了後に自動で次のポモドーロを開始（繰り返しモード）
osushi --loop -b 3       # ループ時の休憩を3分に変更（--break 3 も可）
osushi -m 50 --loop -b 10  # 50分作業 + 10分休憩のループ
osushi status            # 実行中タイマーの残り時間を表示
osushi cancel            # 実行中タイマーをキャンセル
osushi --test            # 5秒でアニメーションを確認（動作テスト用）
osushi --help            # ヘルプ表示
```

---

## 動作フロー

```
1. [バックグラウンド起動]
   osushi コマンドはすぐに返る → ターミナルで作業を続けられる
   タイトルバーに残り時間が表示される（🍣 24:59 - 時すでにおすし）

            ↓ 25分経過

2. [macOS 通知]
   「🍣 時すでにおすし！！！」の通知が届く
   → 他のタブ・アプリにいても気づける

3. [フラッドアニメーション]
   元のタブでお寿司が上から押し寄せる 🍣🍱🐟🦐...

4. [お疲れ様でした画面]
   🎉 お疲れ様でした！ゆっくり休憩してください 🍣

--- ループモード (--loop) の場合 ---

5. [休憩カウントダウン]
   ☕ 休憩中 05:00 → 04:59 → ... → 00:00

6. → 次のポモドーロをバックグラウンドで自動開始
```

---

## カスタマイズ

オプションで実行時に変更:

```bash
osushi -m 45             # 作業時間を45分に
osushi --loop -b 10      # ループ時の休憩を10分に
```

`osushi.py` 先頭の定数でデフォルト値を変更:

```python
WORK_SECONDS = 25 * 60  # ポモドーロ時間（秒）
```

---

## 動作環境

- Python 3.6+
- macOS（通知機能あり） / Linux（通知なし） / Windows は WSL 推奨
- Unicode / 絵文字対応ターミナル（Ghostty, iTerm2, WezTerm, Alacritty など）

> macOS で通知が届かない場合は、システム設定 → 通知 → ターミナル（または Python）の通知を許可してください。

---

*「時すでに遅し」→「時すでにおすし」*

> 本プロジェクトは同名のテレビドラマとは一切関係ありません。

---

*Made with [Claude Code](https://claude.ai/code) (Claude Sonnet 4.6)*
