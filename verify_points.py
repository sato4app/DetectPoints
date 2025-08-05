#!/usr/bin/env python3
"""
ポイント検出結果の確認・検証スクリプト
detect.pyで生成されたJSONファイルを読み込み、
元画像上に検出結果を可視化して確認します。
"""

import cv2
import numpy as np
import json
import argparse
import os
from typing import List, Dict, Tuple

class PointVerifier:
    def __init__(self, image_path: str, json_path: str):
        self.image_path = image_path
        self.json_path = json_path
        
        # 画像を読み込み
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"画像ファイルを読み込めません: {image_path}")
        
        # JSONデータを読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.points = self.data.get('points', [])
        self.height, self.width = self.image.shape[:2]
        
    def draw_detected_points(self, show_labels: bool = True, show_ids: bool = False) -> np.ndarray:
        """
        検出されたポイントを画像上に描画
        """
        result_image = self.image.copy()
        
        # 色の定義
        colors = {
            'circle': (0, 255, 0),      # 緑（円）
            'center': (0, 0, 255),      # 赤（中心点）
            'text': (255, 255, 255),    # 白（テキスト）
            'text_bg': (0, 0, 0)        # 黒（テキスト背景）
        }
        
        for i, point in enumerate(self.points):
            x = int(point['x'])
            y = int(point['y'])
            r = int(point['radius'])
            name = point.get('name', f"Point_{i+1}")
            point_id = point.get('id', f"id_{i+1}")
            
            # 円を描画
            cv2.circle(result_image, (x, y), r, colors['circle'], 2)
            
            # 中心点を描画
            cv2.circle(result_image, (x, y), 3, colors['center'], -1)
            
            # ラベルを描画
            if show_labels:
                label = f"{i+1}"
                if show_ids:
                    label += f": {point_id}"
                
                # テキストサイズを取得
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 1
                (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
                
                # テキスト位置を調整（円の上に配置）
                text_x = x - text_width // 2
                text_y = y - r - 10
                
                # 画像境界をチェックして調整
                if text_y < text_height:
                    text_y = y + r + text_height + 10
                if text_x < 0:
                    text_x = 0
                elif text_x + text_width > self.width:
                    text_x = self.width - text_width
                
                # テキスト背景を描画
                cv2.rectangle(result_image, 
                            (text_x - 2, text_y - text_height - 2),
                            (text_x + text_width + 2, text_y + baseline + 2),
                            colors['text_bg'], -1)
                
                # テキストを描画
                cv2.putText(result_image, label,
                          (text_x, text_y),
                          font, font_scale, colors['text'], thickness)
        
        return result_image
    
    def generate_report(self) -> str:
        """
        検証レポートを生成
        """
        report = []
        report.append("=== ポイント検出結果レポート ===\n")
        
        # 基本情報
        image_info = self.data.get('image_info', {})
        report.append(f"画像ファイル: {image_info.get('filename', 'Unknown')}")
        report.append(f"画像サイズ: {image_info.get('width', 'Unknown')} x {image_info.get('height', 'Unknown')}")
        report.append(f"検出ポイント数: {self.data.get('total_points', len(self.points))}\n")
        
        # 各ポイントの詳細
        report.append("検出されたポイント一覧:")
        report.append("-" * 50)
        
        for i, point in enumerate(self.points):
            report.append(f"ポイント {i+1}:")
            report.append(f"  ID: {point.get('id', 'N/A')}")
            report.append(f"  名称: {point.get('name', 'N/A')}")
            report.append(f"  座標: ({point['x']}, {point['y']})")
            report.append(f"  相対座標: ({point['relative_x']:.4f}, {point['relative_y']:.4f})")
            report.append(f"  半径: {point['radius']}")
            report.append("")
        
        # 統計情報
        if self.points:
            radii = [p['radius'] for p in self.points]
            report.append("統計情報:")
            report.append(f"  平均半径: {np.mean(radii):.2f}")
            report.append(f"  最小半径: {min(radii)}")
            report.append(f"  最大半径: {max(radii)}")
            
            # 分布情報
            x_coords = [p['relative_x'] for p in self.points]
            y_coords = [p['relative_y'] for p in self.points]
            report.append(f"  X座標範囲: {min(x_coords):.4f} - {max(x_coords):.4f}")
            report.append(f"  Y座標範囲: {min(y_coords):.4f} - {max(y_coords):.4f}")
        
        return "\n".join(report)
    
    def save_verification_image(self, output_path: str, show_labels: bool = True, show_ids: bool = False):
        """
        検証画像を保存
        """
        result_image = self.draw_detected_points(show_labels, show_ids)
        cv2.imwrite(output_path, result_image)
        print(f"検証画像を保存しました: {output_path}")
    
    def interactive_verification(self):
        """
        インタラクティブな検証モード
        """
        print("\n=== インタラクティブ検証モード ===")
        print("キー操作:")
        print("  'l' - ラベル表示の切り替え")
        print("  'i' - ID表示の切り替え")
        print("  's' - 現在の表示を画像として保存")
        print("  'r' - レポートを表示")
        print("  'q' または ESC - 終了")
        print("  その他のキー - 表示を更新")
        
        show_labels = True
        show_ids = False
        
        while True:
            # 画像を描画
            display_image = self.draw_detected_points(show_labels, show_ids)
            
            # ウィンドウサイズを調整
            max_width = 1200
            max_height = 800
            h, w = display_image.shape[:2]
            
            if w > max_width or h > max_height:
                scale = min(max_width / w, max_height / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                display_image = cv2.resize(display_image, (new_w, new_h))
            
            cv2.imshow('Point Verification', display_image)
            
            key = cv2.waitKey(0) & 0xFF
            
            if key == ord('q') or key == 27:  # 'q' または ESC
                break
            elif key == ord('l'):  # ラベル表示切り替え
                show_labels = not show_labels
                print(f"ラベル表示: {'ON' if show_labels else 'OFF'}")
            elif key == ord('i'):  # ID表示切り替え
                show_ids = not show_ids
                print(f"ID表示: {'ON' if show_ids else 'OFF'}")
            elif key == ord('s'):  # 保存
                timestamp = cv2.getTickCount()
                save_path = f"verification_result_{int(timestamp)}.png"
                result_image = self.draw_detected_points(show_labels, show_ids)
                cv2.imwrite(save_path, result_image)
                print(f"画像を保存しました: {save_path}")
            elif key == ord('r'):  # レポート表示
                print("\n" + self.generate_report())
        
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description='ポイント検出結果の検証')
    parser.add_argument('image', help='元のPNG画像ファイル')
    parser.add_argument('json_file', help='検出結果のJSONファイル')
    parser.add_argument('-o', '--output', help='検証画像の出力ファイル名')
    parser.add_argument('-r', '--report', help='レポートファイルの出力先')
    parser.add_argument('--interactive', action='store_true', help='インタラクティブモードで実行')
    parser.add_argument('--show-ids', action='store_true', help='ポイントIDを表示')
    
    args = parser.parse_args()
    
    try:
        # 検証器を初期化
        verifier = PointVerifier(args.image, args.json_file)
        
        # レポート生成
        report = verifier.generate_report()
        print(report)
        
        # レポートファイル保存
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nレポートを保存しました: {args.report}")
        
        # 検証画像保存
        if args.output:
            verifier.save_verification_image(args.output, True, args.show_ids)
        
        # インタラクティブモード
        if args.interactive:
            verifier.interactive_verification()
        else:
            # 非インタラクティブモードの場合、デフォルト画像を保存
            if not args.output:
                base_name = os.path.splitext(os.path.basename(args.json_file))[0]
                default_output = f"{base_name}_verification.png"
                verifier.save_verification_image(default_output, True, args.show_ids)
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())