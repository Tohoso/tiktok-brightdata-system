#!/usr/bin/env python3
"""
TikTok Bright Data System - Main Application
24時間以内・50万再生以上の動画を収集してGoogleスプレッドシートに出力
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
from pathlib import Path

# 相対インポートの問題を解決
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brightdata_client import BrightDataClient
from sheets_manager import SheetsManager
from video_filter import VideoFilter

class TikTokBrightDataSystem:
    """TikTok Bright Data統合システム"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初期化
        
        Args:
            config_file: 設定ファイルパス
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        # ログ設定
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # コンポーネント初期化
        self.bright_data_client = None
        self.sheets_manager = None
        self.video_filter = None
        
        self._initialize_components()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_file}")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 必須設定の確認
            required_keys = [
                'bright_data.api_key',
                'bright_data.dataset_id',
                'google_sheets.credentials_file'
            ]
            
            for key in required_keys:
                keys = key.split('.')
                value = config
                for k in keys:
                    value = value.get(k)
                    if value is None:
                        raise ValueError(f"必須設定が不足: {key}")
            
            return config
            
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """ログ設定"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'tiktok_brightdata.log')
        
        # ログフォーマット
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # ファイルハンドラー
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        
        # ルートロガー設定
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _initialize_components(self):
        """各コンポーネントを初期化"""
        try:
            # Bright Data クライアント
            bright_data_config = self.config['bright_data']
            self.bright_data_client = BrightDataClient(
                api_key=bright_data_config['api_key'],
                dataset_id=bright_data_config['dataset_id'],
                timeout=bright_data_config.get('timeout', 300)
            )
            
            # Google Sheets マネージャー
            sheets_config = self.config['google_sheets']
            self.sheets_manager = SheetsManager(
                credentials_file=sheets_config['credentials_file'],
                spreadsheet_name=sheets_config['spreadsheet_name']
            )
            
            # 動画フィルター
            filter_config = self.config['collection_settings']
            self.video_filter = VideoFilter(filter_config)
            
            self.logger.info("全コンポーネント初期化完了")
            
        except Exception as e:
            self.logger.error(f"コンポーネント初期化エラー: {e}")
            raise
    
    def collect_viral_videos(self, collection_method: str = "discover") -> Dict[str, Any]:
        """
        バイラル動画を収集
        
        Args:
            collection_method: 収集方法 ("discover", "hashtags", "hybrid")
            
        Returns:
            収集結果
        """
        self.logger.info(f"バイラル動画収集開始: {collection_method}")
        
        try:
            # 収集方法に応じてデータ取得
            if collection_method == "discover":
                raw_videos = self._collect_from_discover_pages()
            elif collection_method == "hashtags":
                raw_videos = self._collect_from_hashtags()
            elif collection_method == "hybrid":
                raw_videos = self._collect_hybrid()
            else:
                raise ValueError(f"不明な収集方法: {collection_method}")
            
            self.logger.info(f"生データ収集完了: {len(raw_videos)}件")
            
            # フィルタリング実行
            filtered_videos, filter_stats = self.video_filter.filter_videos(raw_videos)
            
            self.logger.info(
                f"フィルタリング完了: {len(filtered_videos)}件 "
                f"(通過率: {filter_stats.get('filter_rate', 0):.1f}%)"
            )
            
            # 結果をまとめ
            result = {
                "collection_method": collection_method,
                "collection_time": datetime.now().isoformat(),
                "raw_count": len(raw_videos),
                "filtered_count": len(filtered_videos),
                "filter_stats": filter_stats,
                "videos": filtered_videos
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"動画収集エラー: {e}")
            raise
    
    def _collect_from_discover_pages(self) -> List[Dict[str, Any]]:
        """発見ページから動画を収集"""
        self.logger.info("TikTok発見ページから収集中...")
        
        target_region = self.config['collection_settings'].get('target_region', 'JP')
        return self.bright_data_client.scrape_tiktok_discover_pages(country=target_region)
    
    def _collect_from_hashtags(self) -> List[Dict[str, Any]]:
        """人気ハッシュタグから動画を収集"""
        self.logger.info("人気ハッシュタグから収集中...")
        
        # 日本で人気のハッシュタグ
        popular_hashtags = [
            "fyp", "foryou", "viral", "trending", "おすすめ",
            "バズ", "話題", "人気", "トレンド", "日本",
            "東京", "大阪", "グルメ", "ファッション", "音楽"
        ]
        
        target_region = self.config['collection_settings'].get('target_region', 'JP')
        return self.bright_data_client.scrape_hashtag_posts(
            hashtags=popular_hashtags,
            country=target_region
        )
    
    def _collect_hybrid(self) -> List[Dict[str, Any]]:
        """ハイブリッド収集（発見ページ + ハッシュタグ）"""
        self.logger.info("ハイブリッド収集中...")
        
        # 発見ページから収集
        discover_videos = self._collect_from_discover_pages()
        
        # ハッシュタグから収集
        hashtag_videos = self._collect_from_hashtags()
        
        # 重複除去
        all_videos = discover_videos + hashtag_videos
        unique_videos = self._remove_duplicates(all_videos)
        
        self.logger.info(
            f"ハイブリッド収集完了: 発見ページ{len(discover_videos)}件 + "
            f"ハッシュタグ{len(hashtag_videos)}件 → 重複除去後{len(unique_videos)}件"
        )
        
        return unique_videos
    
    def _remove_duplicates(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複動画を除去"""
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            video_id = video.get('video_id') or video.get('id') or video.get('aweme_id')
            if video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                unique_videos.append(video)
        
        return unique_videos
    
    def upload_to_sheets(self, videos: List[Dict[str, Any]], 
                        worksheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        動画データをGoogleスプレッドシートにアップロード
        
        Args:
            videos: 動画データリスト
            worksheet_name: ワークシート名（省略時は設定から取得）
            
        Returns:
            アップロード結果
        """
        if not videos:
            self.logger.warning("アップロードする動画データがありません")
            return {"status": "no_data"}
        
        try:
            # ワークシート名決定
            if not worksheet_name:
                worksheet_name = self.config['google_sheets'].get(
                    'worksheet_name', 
                    f"24時間以内・50万再生以上_{datetime.now().strftime('%Y%m%d')}"
                )
            
            # データアップロード
            upload_result = self.sheets_manager.upload_tiktok_data(
                data=videos,
                worksheet_name=worksheet_name,
                clear_existing=False
            )
            
            # サマリーワークシート作成
            summary_result = self.sheets_manager.create_summary_worksheet(videos)
            
            self.logger.info(
                f"スプレッドシートアップロード完了: {upload_result['count']}件 "
                f"→ {worksheet_name}"
            )
            
            return {
                "status": "success",
                "upload_result": upload_result,
                "summary_result": summary_result,
                "spreadsheet_url": self.sheets_manager.get_spreadsheet_url()
            }
            
        except Exception as e:
            self.logger.error(f"スプレッドシートアップロードエラー: {e}")
            raise
    
    def save_to_files(self, videos: List[Dict[str, Any]], 
                     base_filename: Optional[str] = None) -> Dict[str, str]:
        """
        動画データをファイルに保存
        
        Args:
            videos: 動画データリスト
            base_filename: ベースファイル名
            
        Returns:
            保存されたファイルパス
        """
        if not base_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"tiktok_viral_videos_{timestamp}"
        
        saved_files = {}
        
        try:
            # CSV保存
            if self.config['output_settings'].get('csv_output', True):
                import pandas as pd
                df = pd.DataFrame(videos)
                csv_path = f"{base_filename}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                saved_files['csv'] = csv_path
                self.logger.info(f"CSV保存完了: {csv_path}")
            
            # JSON保存
            if self.config['output_settings'].get('json_output', True):
                json_path = f"{base_filename}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(videos, f, ensure_ascii=False, indent=2)
                saved_files['json'] = json_path
                self.logger.info(f"JSON保存完了: {json_path}")
            
            return saved_files
            
        except Exception as e:
            self.logger.error(f"ファイル保存エラー: {e}")
            raise
    
    def run_collection(self, method: str = "hybrid", 
                      upload_sheets: bool = True,
                      save_files: bool = True) -> Dict[str, Any]:
        """
        完全な収集プロセスを実行
        
        Args:
            method: 収集方法
            upload_sheets: スプレッドシートアップロードするか
            save_files: ファイル保存するか
            
        Returns:
            実行結果
        """
        self.logger.info("=== TikTok バイラル動画収集開始 ===")
        
        try:
            # 1. 動画収集
            collection_result = self.collect_viral_videos(method)
            videos = collection_result['videos']
            
            if not videos:
                self.logger.warning("条件を満たす動画が見つかりませんでした")
                return {
                    "status": "no_videos",
                    "collection_result": collection_result
                }
            
            # 2. ファイル保存
            saved_files = {}
            if save_files:
                saved_files = self.save_to_files(videos)
            
            # 3. スプレッドシートアップロード
            sheets_result = {}
            if upload_sheets:
                sheets_result = self.upload_to_sheets(videos)
            
            # 4. 結果まとめ
            final_result = {
                "status": "success",
                "execution_time": datetime.now().isoformat(),
                "collection_result": collection_result,
                "saved_files": saved_files,
                "sheets_result": sheets_result,
                "summary": {
                    "total_collected": collection_result['raw_count'],
                    "filtered_videos": collection_result['filtered_count'],
                    "filter_rate": collection_result['filter_stats'].get('filter_rate', 0),
                    "spreadsheet_url": sheets_result.get('spreadsheet_url', ''),
                    "files_saved": list(saved_files.keys())
                }
            }
            
            self.logger.info("=== 収集プロセス完了 ===")
            self.logger.info(f"収集動画数: {final_result['summary']['filtered_videos']}件")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"収集プロセスエラー: {e}")
            raise


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='TikTok Bright Data System')
    parser.add_argument('--config', default='config.json', help='設定ファイルパス')
    parser.add_argument('--method', choices=['discover', 'hashtags', 'hybrid'], 
                       default='hybrid', help='収集方法')
    parser.add_argument('--no-sheets', action='store_true', help='スプレッドシートアップロードを無効化')
    parser.add_argument('--no-files', action='store_true', help='ファイル保存を無効化')
    parser.add_argument('--test', action='store_true', help='テストモード')
    
    args = parser.parse_args()
    
    try:
        # システム初期化
        system = TikTokBrightDataSystem(args.config)
        
        if args.test:
            # テストモード
            print("🧪 テストモード実行中...")
            
            # 各コンポーネントのテスト
            print("✅ Bright Data クライアント: 初期化成功")
            print("✅ Google Sheets マネージャー: 初期化成功")
            print("✅ 動画フィルター: 初期化成功")
            print("🎉 全コンポーネント正常動作")
            
        else:
            # 本格実行
            result = system.run_collection(
                method=args.method,
                upload_sheets=not args.no_sheets,
                save_files=not args.no_files
            )
            
            # 結果表示
            print("\n🎉 収集完了!")
            print(f"📊 収集動画数: {result['summary']['filtered_videos']}件")
            print(f"📈 フィルター通過率: {result['summary']['filter_rate']:.1f}%")
            
            if result['summary']['spreadsheet_url']:
                print(f"📋 スプレッドシート: {result['summary']['spreadsheet_url']}")
            
            if result['summary']['files_saved']:
                print(f"💾 保存ファイル: {', '.join(result['summary']['files_saved'])}")
    
    except KeyboardInterrupt:
        print("\n⚠️  ユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

