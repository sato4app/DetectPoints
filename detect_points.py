#!/usr/bin/env python3
"""
ハイキングマップのポイント検出スクリプト
PNG画像から円形のポイントマーカー（臙脂、赤、白抜き）を自動検出し、
座標と名称をJSON形式で出力します。
"""

import cv2
import numpy as np
import json
import argparse
import os
from typing import List, Dict, Tuple
import pytesseract

class HikingPointDetector:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"画像ファイルを読み込めません: {image_path}")
        self.original_image = self.image.copy()
        self.height, self.width = self.image.shape[:2]
        
    def detect_circles(self) -> List[Tuple[int, int, int]]:
        """
        Hough変換を使用して円形のポイントを検出
        """
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # ガウシアンぼかしでノイズ除去
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # 複数のパラメータセットで円検出を実行し、結果を統合
        all_circles = []
        
        # パラメータセット1：標準的な検出
        circles1 = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=30,
            minRadius=5,
            maxRadius=18
        )
        if circles1 is not None:
            all_circles.extend(circles1[0, :])
        
        # パラメータセット2：より敏感な検出
        circles2 = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=18,
            param1=30,
            param2=20,
            minRadius=4,
            maxRadius=15
        )
        if circles2 is not None:
            all_circles.extend(circles2[0, :])
        
        # 重複する円を除去
        if len(all_circles) > 0:
            circles = np.array([all_circles])
        else:
            circles = None
        
        detected_circles = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            # 重複する円を除去
            for (x, y, r) in circles:
                # 画像境界内かチェック
                if 0 <= x < self.width and 0 <= y < self.height:
                    # 既存の円と重複しているかチェック
                    is_duplicate = False
                    for (ex_x, ex_y, ex_r) in detected_circles:
                        distance = np.sqrt((x - ex_x)**2 + (y - ex_y)**2)
                        if distance < (r + ex_r) * 0.7:  # 重複判定
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        detected_circles.append((x, y, r))
        
        return detected_circles
    
    def filter_circles_by_color(self, circles: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        色に基づいて円をフィルタリング（臙脂、赤、白抜きのポイント）
        """
        filtered_circles = []
        
        for x, y, r in circles:
            # 円の中心周辺の色を取得
            roi = self.image[max(0, y-r):min(self.height, y+r), 
                           max(0, x-r):min(self.width, x+r)]
            
            if roi.size == 0:
                continue
                
            # BGRからHSVに変換
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # 赤色系の範囲を定義（臙脂色と赤色）- より広範囲にカバー
            # 赤色の範囲1 (0-15)
            lower_red1 = np.array([0, 80, 50])
            upper_red1 = np.array([15, 255, 255])
            
            # 赤色の範囲2 (165-180)
            lower_red2 = np.array([165, 80, 50])
            upper_red2 = np.array([180, 255, 255])
            
            # 赤色マスクを作成
            mask1 = cv2.inRange(hsv_roi, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv_roi, lower_red2, upper_red2)
            red_mask = mask1 + mask2
            
            # 白色の範囲（白抜きポイント用）
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 30, 255])
            white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)
            
            # 赤色または白色のピクセルが一定割合以上ある場合、ポイントとして認識
            red_ratio = np.sum(red_mask > 0) / red_mask.size
            white_ratio = np.sum(white_mask > 0) / white_mask.size
            
            # より緩い閾値でより多くのポイントを検出
            if red_ratio > 0.06 or white_ratio > 0.15:
                filtered_circles.append((x, y, r))
        
        return filtered_circles
    
    def extract_text_near_point(self, x: int, y: int, r: int) -> str:
        """
        ポイント周辺のテキストを抽出（OCR使用）
        """
        # テキスト検索範囲を拡張
        margin = r * 3
        x1 = max(0, x - margin)
        y1 = max(0, y - margin)
        x2 = min(self.width, x + margin)
        y2 = min(self.height, y + margin)
        
        # ROI（関心領域）を抽出
        roi = self.original_image[y1:y2, x1:x2]
        
        if roi.size == 0:
            return f"point_{x}_{y}"
        
        # OCR用に前処理
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # コントラストを上げる
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray_roi)
        
        try:
            # OCRでテキスト抽出（ID認識に特化した設定）
            text = pytesseract.image_to_string(
                enhanced, 
                lang='eng',  # IDは英数字なので英語のみ
                config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ).strip()
            
            # テキストのクリーンアップとIDパターンの抽出
            import re
            # IDパターン（1-2文字のアルファベット + 数字）を検索
            id_pattern = re.search(r'[A-Z]{1,2}\d+', text)
            if id_pattern:
                return id_pattern.group(0)
            
            # パターンが見つからない場合、全体をクリーンアップ
            text = ''.join(c for c in text if c.isalnum()).strip()
            
            # 空文字の場合はデフォルト名を返す
            if not text or len(text) < 2:
                return f"point_{x}_{y}"
            
            return text[:10]  # IDは短いので10文字に制限
            
        except Exception as e:
            print(f"OCRエラー (座標: {x}, {y}): {e}")
            return f"point_{x}_{y}"
    
    def detect_and_extract_points(self) -> List[Dict]:
        """
        ポイントを検出してJSON用のデータを作成
        """
        print("円形ポイントを検出中...")
        circles = self.detect_circles()
        print(f"検出された円: {len(circles)}個")
        
        print("色によるフィルタリング中...")
        filtered_circles = self.filter_circles_by_color(circles)
        print(f"フィルタリング後: {len(filtered_circles)}個")
        
        points_data = []
        
        for i, (x, y, r) in enumerate(filtered_circles):
            print(f"ポイント {i+1}/{len(filtered_circles)} のテキスト抽出中...")
            
            # テキスト抽出
            point_name = self.extract_text_near_point(x, y, r)
            
            # 相対座標（0.0-1.0の範囲）
            relative_x = x / self.width
            relative_y = y / self.height
            
            point_data = {
                "id": point_name,
                "name": point_name,
                "x": int(x),
                "y": int(y),
                "relative_x": round(float(relative_x), 4),
                "relative_y": round(float(relative_y), 4),
                "radius": int(r)
            }
            
            points_data.append(point_data)
        
        return points_data
    
    def save_results(self, points_data: List[Dict], output_path: str):
        """
        結果をJSONファイルに保存
        """
        result = {
            "image_info": {
                "filename": os.path.basename(self.image_path),
                "width": int(self.width),
                "height": int(self.height)
            },
            "points": points_data,
            "total_points": len(points_data)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"結果を保存しました: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='ハイキングマップのポイント検出')
    parser.add_argument('input_image', help='入力PNG画像ファイル')
    parser.add_argument('-o', '--output', help='出力JSONファイル名')
    
    args = parser.parse_args()
    
    # 出力ファイル名を生成（入力ファイルと同じフォルダに出力）
    if args.output:
        output_path = args.output
    else:
        input_dir = os.path.dirname(os.path.abspath(args.input_image))
        base_name = os.path.splitext(os.path.basename(args.input_image))[0]
        output_path = os.path.join(input_dir, f"{base_name}_points.json")
    
    try:
        # ポイント検出器を初期化
        detector = HikingPointDetector(args.input_image)
        
        # ポイントを検出・抽出
        points_data = detector.detect_and_extract_points()
        
        # 結果を保存
        detector.save_results(points_data, output_path)
        
        print(f"\n=== 検出完了 ===")
        print(f"検出されたポイント数: {len(points_data)}")
        print(f"出力ファイル: {output_path}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())