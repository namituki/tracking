"""macOS: 画面上のウィンドウ一覧取得・検索 (Quartz)。"""
import Quartz


def list_windows():
    opts = (Quartz.kCGWindowListOptionOnScreenOnly
            | Quartz.kCGWindowListExcludeDesktopElements)
    infos = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID) or []
    result = []
    for w in infos:
        if w.get("kCGWindowLayer", 0) != 0:
            continue
        b = w.get("kCGWindowBounds")
        if not b:
            continue
        width, height = int(b["Width"]), int(b["Height"])
        if width < 50 or height < 50:
            continue
        result.append({
            "id": w.get("kCGWindowNumber"),
            "owner": w.get("kCGWindowOwnerName", "") or "",
            "title": w.get("kCGWindowName", "") or "",
            "left": int(b["X"]),
            "top": int(b["Y"]),
            "width": width,
            "height": height,
        })
    return result


def find_window(app=None, title=None, window_id=None):
    """アプリ名/タイトルの部分一致(大文字小文字無視)で最も大きいウィンドウを返す。"""
    if window_id is not None:
        return next((w for w in list_windows() if w["id"] == window_id), None)
    app = app.lower() if app else None
    title = title.lower() if title else None
    hits = []
    for w in list_windows():
        if app and app not in w["owner"].lower():
            continue
        if title and title not in w["title"].lower():
            continue
        hits.append(w)
    if not hits:
        return None
    return max(hits, key=lambda w: w["width"] * w["height"])
