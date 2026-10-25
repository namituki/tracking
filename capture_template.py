#!/usr/bin/env python3
"""対象ウィンドウをキャプチャし、ドラッグで範囲選択してテンプレート画像を保存する。"""
import argparse
import os
import sys

import cv2
import mss
import numpy as np

from window_utils import find_window


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--app")
    p.add_argument("--title")
    p.add_argument("--window-id", type=int)
    p.add_argument("--out", default="templates/target.png")
    args = p.parse_args()

    win = find_window(args.app, args.title, args.window_id)
    if win is None:
        sys.exit("ウィンドウが見つかりません。 python tracker.py --list で確認してください。")

    with (getattr(mss, "MSS", None) or mss.mss)() as sct:
        shot = sct.grab({"left": win["left"], "top": win["top"],
                         "width": win["width"], "height": win["height"]})
    bgr = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
    scale = shot.width / win["width"]  # Retinaなら2.0

    disp = bgr if scale <= 1 else cv2.resize(bgr, None, fx=1 / scale, fy=1 / scale)
    print("追跡したい対象をドラッグで囲み、Enter/Spaceで確定 (cでキャンセル)")
    x, y, w, h = cv2.selectROI("Select target", disp, showCrosshair=False)
    cv2.destroyAllWindows()
    if w == 0 or h == 0:
        sys.exit("キャンセルしました。")

    x, y, w, h = [int(round(v * scale)) for v in (x, y, w, h)]
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    if not cv2.imwrite(args.out, bgr[y:y + h, x:x + w]):
        sys.exit(f"保存に失敗しました: {os.path.abspath(args.out)}")
    print(f"保存しました: {os.path.abspath(args.out)} ({w}x{h}px)")


if __name__ == "__main__":
    main()
