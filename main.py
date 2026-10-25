#!/usr/bin/env python3
"""ウィンドウ一覧 → 番号で選択 → テンプレート作成 → 追跡開始 を一括で行う。

使い方:
    python main.py                # 通常
    python main.py --no-mouse     # 認識確認のみ (以降の引数は tracker.py にそのまま渡される)
    python main.py --click --threshold 0.9
"""
import os
import subprocess
import sys

from window_utils import list_windows

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE, "templates", "target.png")


def choose_window():
    while True:
        wins = list_windows()
        if not wins:
            print("ウィンドウが見つかりません。画面収録の許可を確認してください。")
            sys.exit(1)
        print("\n=== ウィンドウ一覧 ===")
        for i, w in enumerate(wins, 1):
            title = w["title"][:40] or "(タイトルなし)"
            print(f'[{i:>2}] {w["owner"]:<22} | {title:<40} | {w["width"]}x{w["height"]}')
        ans = input("\n番号を入力 (r=一覧更新, q=終了): ").strip().lower()
        if ans == "q":
            sys.exit(0)
        if ans == "r":
            continue
        if ans.isdigit() and 1 <= int(ans) <= len(wins):
            return wins[int(ans) - 1]
        print("無効な入力です。")


def run(script, *args):
    return subprocess.call([sys.executable, os.path.join(BASE, script), *args], cwd=BASE)


def main():
    extra = sys.argv[1:]
    win = choose_window()
    wid = str(win["id"])
    print(f'\n選択: {win["owner"]} {win["title"]}')

    if os.path.exists(TEMPLATE):
        ans = input("既存のテンプレートがあります。作り直しますか? [Y/n]: ").strip().lower()
        make = ans != "n"
    else:
        make = True

    if make:
        print("\nテンプレート作成: 追跡したい対象をドラッグで囲んで Enter を押してください。")
        if run("capture_template.py", "--window-id", wid, "--out", TEMPLATE) != 0:
            print("テンプレート作成を中止しました。")
            sys.exit(1)

    print("\n追跡を開始します。")
    run("tracker.py", "--window-id", wid, "--template", TEMPLATE, *extra)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n終了しました。")
