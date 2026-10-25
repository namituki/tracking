# エイム練習 & 画像認識マウス追跡

## デモ動画

https://github.com/user-attachments/assets/68cf9bdf-40a3-40e1-a548-09dfbd721b6e

## エイム練習 (Web)
エイム練習を試す：
<a href="https://namituki.github.io/tracking/" target="_blank">https://namituki.github.io/tracking/</a>

ローカルで実行する場合は `index.html` をブラウザで開いてください。

## 画像認識マウス追跡 (macOS / Python)

特定ウィンドウ内で、用意した画像と一致する場所をリアルタイムに探し、マウスを追従させます。

### ファイル構成
- `main.py` … ウィンドウ選択 -> テンプレート作成 -> 追跡開始 を一括実行
- `tracker.py` … 本体 (認識 + マウス操作)
- `capture_template.py` … 対象ウィンドウから探したい画像を切り出して保存
- `window_utils.py` … ウィンドウ検索 (Quartz)
- `requirements.txt` / `templates/`

### セットアップ(mac用ね)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### macOSの権限 (必須)
システム設定 > プライバシーとセキュリティ で、**実行するアプリ (ターミナル / iTerm / VS Code など)** を次に追加し、アプリを再起動:
1. **画面収録とシステムオーディオ録音** … 画面キャプチャとウィンドウ名取得に必要
2. **アクセシビリティ** … マウス操作に必要

### 使い方

#### 方法1: main.pyで一括実行 (おすすめ)
```bash
source .venv/bin/activate
python main.py --click --click-cooldown 0.5 --threshold 0.9
```
ウィンドウ一覧が表示されるので番号を選択し、テンプレートを作成して追跡開始します。

#### 方法2: 個別に実行
```bash
# 1. ウィンドウ名を確認
python tracker.py --list

# 2. テンプレート画像を作る (ドラッグで囲んで Enter)
python capture_template.py --app "Safari"

# 3. まずはマウスを動かさず認識だけ確認
python tracker.py --app "Safari" --no-mouse

# 4. 本番 (マウス追従)
python tracker.py --app "Safari"
```

### 主なオプション
| オプション | 説明 | 既定 |
|---|---|---|
| `--threshold` | 一致度の下限 (0-1)。誤検出が多ければ上げる | 0.45 |
| `--scales 0.8,1.0,1.25` | 大きさが変わる対象に対応 (遅くなる) | 1.0 |
| `--smooth` | 追従の滑らかさ (1=即時) | 0.5 |
| `--fps` | 目標フレームレート | 30 |
| `--click` | 見つかったらクリック | off |
| `--click-cooldown` | クリック間隔(秒) | 1.0 |
| `--no-mouse` | 認識のみ | off |

### 停止方法
- `Ctrl+W` でウィンドウを閉じる
- プレビューウィンドウ上で `q` / ターミナルで `Ctrl+C`
- **マウスを画面左上の角へ移動** (フェイルセーフ)
- プレビュー上で `m` を押すとマウス操作だけON/OFF
- ### 作者からの一言。こいつ全然止まらない。

### うまく見つからないとき
- テンプレートは必ず `capture_template.py` で同じ環境から切り出す (Retinaのピクセルサイズが一致するため)
- 拡大率・見た目が変わる対象は `--scales` を指定、背景が透ける/動く対象は `--threshold` を下げる
- ウィンドウの一部が他のウィンドウで隠れていると認識できません (画面に見えている内容を撮影するため)
- `--list` でタイトルが空欄なら画面収録の許可を確認
