# DetectPoints 利用者の手引

## 1. はじめに

DetectPointsは、ハイキングマップなどの地図画像から円形のポイントマーカーを自動で検出し、その座標と名称を抽出するツールです。この手引では、初心者の方でも簡単に使用できるよう、セットアップから実際の使用方法まで詳しく説明します。

## 2. システム要件

### 2.1 動作環境
- **OS**: Windows 10/11, macOS, Linux
- **Python**: 3.8以上
- **メモリ**: 最低4GB（高解像度画像処理時は8GB推奨）
- **ストレージ**: 500MB以上の空き容量

### 2.2 対応画像形式
- **形式**: PNG
- **サイズ**: 制限なし（ただし大きいほど処理時間が長くなります）
- **対象ポイント**: 円形の赤色系（臙脂・赤）または白抜きマーカー

## 3. インストール手順

### 3.1 Pythonの確認
コマンドプロンプト（Windowsの場合）またはターミナル（Mac/Linuxの場合）で以下のコマンドを実行してください：

```bash
python --version
```

Python 3.8以上が表示されれば準備完了です。インストールされていない場合は、[Python公式サイト](https://www.python.org/)からダウンロードしてください。

### 3.2 必要なライブラリのインストール
DetectPointsフォルダで以下のコマンドを実行してください：

```bash
pip install -r requirements.txt
```

### 3.3 Tesseract OCRのインストール（日本語文字認識に必要）

#### Windows
1. [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)からダウンロード
2. インストール時に「Japanese」言語パックを選択
3. 環境変数にパスを追加（通常は自動設定されます）

#### Mac
```bash
brew install tesseract tesseract-lang
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-jpn
```

## 4. 基本的な使用方法

### 4.1 ポイント検出の実行

#### 最も簡単な使用方法
```bash
python detect_points.py your_map.png
```

この場合、結果は `your_map_points.json` として保存されます。

#### 出力ファイル名を指定する場合
```bash
python detect_points.py your_map.png -o result.json
```

### 4.2 検出結果の確認

#### 基本的な確認
```bash
python verify_points.py your_map.png your_map_points.json
```

これにより：
- コンソールに検出レポートが表示されます
- `your_map_points_verification.png` として確認用画像が保存されます

#### インタラクティブモードでの確認（推奨）
```bash
python verify_points.py your_map.png your_map_points.json --interactive
```

画面に検出結果が表示され、以下のキー操作が可能です：
- **'l' キー**: ポイント番号の表示/非表示切り替え
- **'i' キー**: ポイント名の表示/非表示切り替え
- **'s' キー**: 現在の表示を画像として保存
- **'r' キー**: 詳細レポートをコンソールに表示
- **'q' キーまたはESC**: 終了

## 5. 実践例

### 5.1 基本的なワークフロー

1. **準備**: ハイキングマップのPNG画像を用意
2. **検出**: `python detect_points.py hiking_map.png`
3. **確認**: `python verify_points.py hiking_map.png hiking_map_points.json --interactive`
4. **修正**: 必要に応じて検出パラメータを調整

### 5.2 出力ファイルの理解

検出が完了すると、以下のようなJSONファイルが生成されます：

```json
{
  "image_info": {
    "filename": "hiking_map.png",
    "width": 1920,
    "height": 1080
  },
  "points": [
    {
      "id": "山頂",
      "name": "山頂", 
      "x": 960,
      "y": 540,
      "relative_x": 0.5000,
      "relative_y": 0.5000,
      "radius": 15
    }
  ],
  "total_points": 1
}
```

- **id/name**: 検出されたポイント名（OCRで抽出）
- **x, y**: 画像内の絶対座標（ピクセル単位）
- **relative_x, relative_y**: 相対座標（0.0-1.0の範囲）
- **radius**: 検出された円の半径

## 6. トラブルシューティング

### 6.1 よくある問題と対処法

#### 「画像ファイルを読み込めません」エラー
- ファイルパスが正しいか確認
- PNG形式の画像か確認
- ファイルが破損していないか確認

#### 「検出されたポイントが0個」の場合
- 画像に円形のポイントが含まれているか確認
- ポイントの色が赤系または白色系か確認
- 画像の解像度が適切か確認（あまりに小さいと検出困難）

#### OCRで文字が正しく認識されない
- Tesseractの日本語言語パックがインストールされているか確認
- 画像の解像度を上げる
- ポイント周辺の文字が鮮明か確認

#### 処理が遅い
- 画像サイズを小さくする
- 不要な背景要素を除去する
- より高性能なコンピュータを使用する

### 6.2 エラーメッセージと対処法

| エラーメッセージ | 原因 | 対処法 |
|----------------|------|--------|
| `ModuleNotFoundError: No module named 'cv2'` | OpenCVがインストールされていない | `pip install opencv-python` |
| `TesseractNotFoundError` | Tesseractがインストールされていない | Tesseractをシステムにインストール |
| `FileNotFoundError` | ファイルが見つからない | ファイルパスを確認 |
| `JSON decode error` | JSONファイルが破損 | 検出処理を再実行 |

## 7. 高度な使用方法

### 7.1 レポートファイルの出力
```bash
python verify_points.py your_map.png your_map_points.json -r report.txt
```

詳細な分析レポートがテキストファイルとして保存されます。

### 7.2 カスタム検証画像の生成
```bash
python verify_points.py your_map.png your_map_points.json -o custom_verification.png --show-ids
```

ポイント名も含めた検証画像が生成されます。

### 7.3 一括処理（複数画像）
```bash
# バッチファイル例（Windows）
for %%f in (*.png) do (
    python detect_points.py "%%f"
    python verify_points.py "%%f" "%%~nf_points.json" -o "%%~nf_verification.png"
)
```

## 8. ベストプラクティス

### 8.1 画像準備のコツ
- **解像度**: 1000x1000ピクセル以上推奨
- **コントラスト**: ポイントと背景のコントラストを明確に
- **ノイズ**: 不要な要素は可能な限り除去
- **形状**: ポイントはできるだけ円形に近い形状にする

### 8.2 効率的な作業フロー
1. **テスト実行**: 小さなサンプル画像で動作確認
2. **パラメータ調整**: 必要に応じて検出設定を調整
3. **一括処理**: 複数画像を効率的に処理
4. **結果検証**: インタラクティブモードで結果を確認
5. **品質チェック**: 生成されたJSONデータの妥当性を確認

### 8.3 データの活用
生成されたJSONデータは以下の用途に活用できます：
- 地図アプリケーションでのポイント表示
- GPS座標との対応付け
- 統計分析やデータマイニング
- 他のシステムとの連携

## 9. サポートとヘルプ

### 9.1 ログファイルの確認
処理中に表示されるメッセージを記録しておくと、問題解決に役立ちます。

### 9.2 テストデータ
小さなサンプル画像で動作テストを行い、期待通りの結果が得られることを確認してください。

### 9.3 パフォーマンスチューニング
大量の画像を処理する場合は、以下を検討してください：
- 画像の前処理による最適化
- バッチ処理スクリプトの作成
- ハードウェアリソースの増強

## 10. 更新履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|----------|
| 1.0.0 | 2024-XX-XX | 初回リリース |

---

**注意**: このソフトウェアは教育・研究目的で作成されています。商用利用する場合は、使用している各ライブラリのライセンスを確認してください。