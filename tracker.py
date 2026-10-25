#!/usr/bin/env python3
"""特定ウィンドウ内でテンプレート画像を探し、マウスをリアルタイム追従させる。"""
import argparse
import os
import sys
import time

import cv2
import mss
import numpy as np
import pyautogui

from window_utils import find_window, list_windows

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True  # マウスを画面左上の角に動かすと強制停止


def parse_args():
    p = argparse.ArgumentParser(description="ウィンドウ内の画像を追跡してマウスを動かす")
    p.add_argument("--list", action="store_true", help="ウィンドウ一覧を表示して終了")
    p.add_argument("--app", help="アプリ名(部分一致) 例: Safari")
    p.add_argument("--title", help="ウィンドウタイトル(部分一致)")
    p.add_argument("--window-id", type=int, help="ウィンドウ番号 (main.pyが指定)")
    p.add_argument("--template", default="templates/target.png", help="探す画像")
    p.add_argument("--threshold", type=float, default=0.45, help="一致度の下限 0-1")
    p.add_argument("--fps", type=float, default=30, help="目標フレームレート")
    p.add_argument("--scales", default="1.0",
                   help="拡大縮小を試す倍率(カンマ区切り) 例: 0.8,1.0,1.25")
    p.add_argument("--smooth", type=float, default=0.5,
                   help="マウス追従の滑らかさ 0-1 (1=即時, 小さいほど緩やか)")
    p.add_argument("--click", action="store_true", help="見つかったらクリックもする")
    p.add_argument("--click-cooldown", type=float, default=1.0, help="クリック間隔(秒)")
    p.add_argument("--no-mouse", action="store_true", help="マウスを動かさず認識だけ確認")
    p.add_argument("--no-preview", action="store_true", help="プレビュー表示を無効化")
    return p.parse_args()


def match(gray, tmpl, scales):
    best = (-1.0, None, None)
    for s in scales:
        t = tmpl if s == 1.0 else cv2.resize(
            tmpl, None, fx=s, fy=s,
            interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        th, tw = t.shape[:2]
        if th > gray.shape[0] or tw > gray.shape[1]:
            continue
        res = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if np.isfinite(mx) and mx > best[0]:
            best = (mx, loc, (tw, th))
    return best


def locate(gray, tmpl, scales, last, threshold):
    """前回位置の周辺だけを先に探して高速化。見失ったら全体を探索。"""
    if last is not None:
        x, y, w, h = last
        m = max(w, h)
        x0, y0 = max(0, x - m), max(0, y - m)
        x1, y1 = min(gray.shape[1], x + w + m), min(gray.shape[0], y + h + m)
        score, loc, size = match(gray[y0:y1, x0:x1], tmpl, scales)
        if loc is not None and score >= threshold:
            return score, (loc[0] + x0, loc[1] + y0), size
    return match(gray, tmpl, scales)


def main():
    args = parse_args()

    if args.list:
        for w in list_windows():
            print(f'{w["owner"]:<24} | {w["title"][:40]:<40} | '
                  f'{w["width"]}x{w["height"]} @({w["left"]},{w["top"]})')
        return
    if not (args.app or args.title or args.window_id):
        sys.exit("--app か --title を指定してください (--list で一覧表示)")

    tmpl = cv2.imread(args.template, cv2.IMREAD_GRAYSCALE)
    if tmpl is None:
        sys.exit(f"テンプレート画像を読み込めません: {os.path.abspath(args.template)}\n"
                 "先に capture_template.py で作成するか、--template でパスを指定してください")
    scales = [float(s) for s in args.scales.split(",")]
    interval = 1.0 / args.fps
    mouse_on = not args.no_mouse
    preview = not args.no_preview

    win, last, last_check, last_click, warned = None, None, 0.0, 0.0, False
    print("開始します。終了: プレビューで q / Ctrl+C / マウスを画面左上の角へ")
    print("プレビュー上で m キー: マウス操作のON/OFF切替")

    with (getattr(mss, "MSS", None) or mss.mss)() as sct:
        while True:
            t0 = time.time()
            if win is None or t0 - last_check > 0.5:
                last_check = t0
                w = find_window(args.app, args.title, args.window_id)
                if w is None:
                    if not warned:
                        print("対象ウィンドウが見つかりません。待機中...")
                        warned = True
                    win, last = None, None
                    time.sleep(0.5)
                    continue
                warned = False
                if win and (w["width"], w["height"]) != (win["width"], win["height"]):
                    last = None
                win = w

            shot = sct.grab({"left": win["left"], "top": win["top"],
                             "width": win["width"], "height": win["height"]})
            gray = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2GRAY)
            scale = shot.width / win["width"]

            score, loc, size = locate(gray, tmpl, scales, last, args.threshold)
            found = loc is not None and score >= args.threshold
            last = (loc[0], loc[1], size[0], size[1]) if found else None

            if found and mouse_on:
                tx = win["left"] + (loc[0] + size[0] / 2) / scale
                ty = win["top"] + (loc[1] + size[1] / 2) / scale
                cx, cy = pyautogui.position()
                nx, ny = cx + (tx - cx) * args.smooth, cy + (ty - cy) * args.smooth
                if abs(tx - cx) > 1 or abs(ty - cy) > 1:
                    pyautogui.moveTo(nx, ny)
                if args.click and t0 - last_click > args.click_cooldown:
                    pyautogui.moveTo(tx, ty)
                    pyautogui.click()
                    last_click = t0

            key = -1
            if preview:
                vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                if found:
                    cv2.rectangle(vis, loc, (loc[0] + size[0], loc[1] + size[1]),
                                  (0, 255, 0), 2)
                label = f"score={score:.2f} {'FOUND' if found else 'lost'} " \
                        f"mouse={'ON' if mouse_on else 'OFF'}"
                cv2.putText(vis, label, (10, 30 * max(1, int(scale))),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6 * max(1, scale),
                            (0, 0, 255), 2)
                if scale > 1:
                    vis = cv2.resize(vis, None, fx=1 / scale, fy=1 / scale)
                cv2.imshow("tracker (q:quit m:mouse)", vis)
                wait = max(1, int((interval - (time.time() - t0)) * 1000))
                key = cv2.waitKey(wait) & 0xFF
            else:
                rest = interval - (time.time() - t0)
                if rest > 0:
                    time.sleep(rest)

            if key == ord("q"):
                break
            if key == ord("m"):
                mouse_on = not mouse_on

    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n停止しました。")
    except pyautogui.FailSafeException:
        print("フェイルセーフが作動したため停止しました。")
