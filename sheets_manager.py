#!/usr/bin/env python3
"""
Google Sheets Manager for TikTok Viral Video Analysis
Bright Dataで収集したTikTok動画データをGoogleスプレッドシートに自動出力
"""

import gspread
import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from google.oauth2.service_account import Credentials
import time

class SheetsManager:
    """Googleスプレッドシート管理クラス"""
    
    def __init__(self, credentials_file: str, spreadsheet_name: str):
        """
        初期化
        
        Args:
            credentials_file: Google Service Accountの認証情報ファイル
            spreadsheet_name: スプレッドシート名
        """
        self.credentials_file = credentials_file
        self.spreadsheet_name = spreadsheet_name
        self.client = None
        self.spreadsheet = None
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # 認証・接続
        self._authenticate()
    
    def _authenticate(self):
        """Google Sheets APIに認証・接続"""
        try:
            # 必要なスコープ
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 認証情報読み込み
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scopes
            )
            
            # gspreadクライアント作成
            self.client = gspread.authorize(credentials)
            
            # スプレッドシート取得または作成
            try:
                self.spreadsheet = self.client.open(self.spreadsheet_name)
                self.logger.info(f"既存スプレッドシート接続: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                self.spreadsheet = self.client.create(self.spreadsheet_name)
                self.logger.info(f"新規スプレッドシート作成: {self.spreadsheet_name}")
                
        except Exception as e:
            self.logger.error(f"Google Sheets認証エラー: {e}")
            raise
    
    def create_or_get_worksheet(self, worksheet_name: str, 
                               headers: Optional[List[str]] = None) -> gspread.Worksheet:
        """
        ワークシートを作成または取得
        
        Args:
            worksheet_name: ワークシート名
            headers: ヘッダー行（新規作成時）
            
        Returns:
            ワークシートオブジェクト
        """
        try:
            # 既存ワークシート取得を試行
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            self.logger.info(f"既存ワークシート取得: {worksheet_name}")
            return worksheet
            
        except gspread.WorksheetNotFound:
            # 新規ワークシート作成
            worksheet = self.spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=1000,
                cols=30
            )
            
            # ヘッダー設定
            if headers:
                worksheet.append_row(headers)
                self._format_header_row(worksheet)
            
            self.logger.info(f"新規ワークシート作成: {worksheet_name}")
            return worksheet
    
    def _format_header_row(self, worksheet: gspread.Worksheet):
        """ヘッダー行をフォーマット"""
        try:
            # ヘッダー行を太字に設定
            worksheet.format('1:1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
        except Exception as e:
            self.logger.warning(f"ヘッダーフォーマット警告: {e}")
    
    def upload_tiktok_data(self, data: List[Dict[str, Any]], 
                          worksheet_name: str = "TikTok動画データ",
                          clear_existing: bool = False) -> Dict[str, Any]:
        """
        TikTok動画データをスプレッドシートにアップロード
        
        Args:
            data: TikTok動画データのリスト
            worksheet_name: ワークシート名
            clear_existing: 既存データをクリアするか
            
        Returns:
            アップロード結果
        """
        if not data:
            self.logger.warning("アップロードするデータがありません")
            return {"status": "no_data", "count": 0}
        
        try:
            # データフレーム作成
            df = self._prepare_dataframe(data)
            
            # ワークシート取得・作成
            headers = df.columns.tolist()
            worksheet = self.create_or_get_worksheet(worksheet_name, headers)
            
            # 既存データクリア（オプション）
            if clear_existing:
                worksheet.clear()
                worksheet.append_row(headers)
                self._format_header_row(worksheet)
            
            # データアップロード
            upload_result = self._upload_dataframe(worksheet, df)
            
            # 結果ログ
            self.logger.info(
                f"データアップロード完了: {upload_result['count']}件 "
                f"→ {worksheet_name}"
            )
            
            return upload_result
            
        except Exception as e:
            self.logger.error(f"データアップロードエラー: {e}")
            raise
    
    def _prepare_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        TikTokデータをDataFrameに変換・整形
        
        Args:
            data: 生のTikTokデータ
            
        Returns:
            整形されたDataFrame
        """
        # DataFrameに変換
        df = pd.DataFrame(data)
        
        # 必要な列を定義（存在しない場合は空文字で補完）
        required_columns = [
            'video_id', 'author_username', 'author_nickname', 'description',
            'view_count', 'like_count', 'comment_count', 'share_count',
            'create_time', 'video_url', 'music_title', 'music_author',
            'hashtags', 'is_verified', 'follower_count', 'following_count',
            'duration', 'region', 'language', 'collected_at'
        ]
        
        # 列の存在確認・補完
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # 列順序を統一
        df = df[required_columns]
        
        # データ型変換・クリーニング
        df = self._clean_dataframe(df)
        
        # 日本語列名に変換
        df.columns = [
            '動画ID', 'ユーザー名', '表示名', '説明文',
            '再生数', 'いいね数', 'コメント数', 'シェア数',
            '投稿日時', '動画URL', '音楽タイトル', '音楽作者',
            'ハッシュタグ', '認証済み', 'フォロワー数', 'フォロー数',
            '動画時間', '地域', '言語', '収集日時'
        ]
        
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameのデータクリーニング
        
        Args:
            df: 元のDataFrame
            
        Returns:
            クリーニング済みDataFrame
        """
        # 数値列の変換
        numeric_columns = [
            'view_count', 'like_count', 'comment_count', 'share_count',
            'follower_count', 'following_count', 'duration'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # 日時列の変換
        if 'create_time' in df.columns:
            df['create_time'] = pd.to_datetime(df['create_time'], errors='coerce')
            df['create_time'] = df['create_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 収集日時を追加
        df['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # ハッシュタグの整形
        if 'hashtags' in df.columns:
            df['hashtags'] = df['hashtags'].apply(self._format_hashtags)
        
        # 認証済みフラグの変換
        if 'is_verified' in df.columns:
            df['is_verified'] = df['is_verified'].apply(
                lambda x: '✓' if x else ''
            )
        
        # 空値を空文字に変換
        df = df.fillna('')
        
        return df
    
    def _format_hashtags(self, hashtags) -> str:
        """ハッシュタグを文字列形式に変換"""
        if isinstance(hashtags, list):
            return ', '.join([f"#{tag}" for tag in hashtags])
        elif isinstance(hashtags, str):
            return hashtags
        else:
            return ''
    
    def _upload_dataframe(self, worksheet: gspread.Worksheet, 
                         df: pd.DataFrame) -> Dict[str, Any]:
        """
        DataFrameをワークシートにアップロード
        
        Args:
            worksheet: 対象ワークシート
            df: アップロードするDataFrame
            
        Returns:
            アップロード結果
        """
        try:
            # 既存データの行数を取得
            existing_rows = len(worksheet.get_all_values())
            
            # データを行リストに変換
            data_rows = df.values.tolist()
            
            # バッチアップロード（効率化）
            if data_rows:
                # 開始行を計算（ヘッダーの次から）
                start_row = existing_rows + 1 if existing_rows > 0 else 2
                
                # 範囲を指定してアップロード
                end_row = start_row + len(data_rows) - 1
                range_name = f'A{start_row}:T{end_row}'  # T列まで（20列）
                
                # データをバッチで更新
                worksheet.update(range_name, data_rows)
                
                self.logger.info(f"バッチアップロード完了: {len(data_rows)}行")
            
            return {
                "status": "success",
                "count": len(data_rows),
                "start_row": start_row if data_rows else existing_rows,
                "worksheet_url": worksheet.url
            }
            
        except Exception as e:
            self.logger.error(f"DataFrameアップロードエラー: {e}")
            raise
    
    def create_summary_worksheet(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        サマリーワークシートを作成
        
        Args:
            data: 分析対象データ
            
        Returns:
            サマリー作成結果
        """
        try:
            df = pd.DataFrame(data)
            
            # サマリー統計を計算
            summary_stats = self._calculate_summary_stats(df)
            
            # サマリーワークシート作成
            summary_ws = self.create_or_get_worksheet(
                "サマリー統計",
                ["項目", "値", "備考"]
            )
            
            # サマリーデータをアップロード
            summary_rows = []
            for key, value in summary_stats.items():
                summary_rows.append([key, str(value), ""])
            
            # 既存データクリア
            summary_ws.clear()
            summary_ws.append_row(["項目", "値", "備考"])
            self._format_header_row(summary_ws)
            
            # サマリーデータ追加
            for row in summary_rows:
                summary_ws.append_row(row)
            
            self.logger.info("サマリーワークシート作成完了")
            
            return {
                "status": "success",
                "stats": summary_stats,
                "worksheet_url": summary_ws.url
            }
            
        except Exception as e:
            self.logger.error(f"サマリー作成エラー: {e}")
            raise
    
    def _calculate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """サマリー統計を計算"""
        stats = {}
        
        try:
            # 基本統計
            stats["総動画数"] = len(df)
            stats["収集日時"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 数値列の統計
            if 'view_count' in df.columns:
                stats["平均再生数"] = f"{df['view_count'].mean():,.0f}"
                stats["最大再生数"] = f"{df['view_count'].max():,.0f}"
                stats["最小再生数"] = f"{df['view_count'].min():,.0f}"
            
            if 'like_count' in df.columns:
                stats["平均いいね数"] = f"{df['like_count'].mean():,.0f}"
                stats["最大いいね数"] = f"{df['like_count'].max():,.0f}"
            
            # 認証済みアカウント数
            if 'is_verified' in df.columns:
                verified_count = df['is_verified'].sum() if df['is_verified'].dtype == 'bool' else 0
                stats["認証済みアカウント数"] = verified_count
            
            # 言語分布
            if 'language' in df.columns:
                lang_counts = df['language'].value_counts()
                stats["主要言語"] = lang_counts.index[0] if len(lang_counts) > 0 else "不明"
            
        except Exception as e:
            self.logger.warning(f"統計計算警告: {e}")
            stats["エラー"] = str(e)
        
        return stats
    
    def get_spreadsheet_url(self) -> str:
        """スプレッドシートのURLを取得"""
        return self.spreadsheet.url if self.spreadsheet else ""
    
    def share_spreadsheet(self, email: str, role: str = 'reader'):
        """
        スプレッドシートを共有
        
        Args:
            email: 共有先メールアドレス
            role: 権限（'reader', 'writer', 'owner'）
        """
        try:
            self.spreadsheet.share(email, perm_type='user', role=role)
            self.logger.info(f"スプレッドシート共有完了: {email} ({role})")
        except Exception as e:
            self.logger.error(f"スプレッドシート共有エラー: {e}")
            raise


def test_sheets_manager():
    """Sheets Manager のテスト"""
    import os
    
    # テスト用設定
    credentials_file = "credentials.json"
    spreadsheet_name = "TikTok バイラル動画分析 (テスト)"
    
    print("Google Sheets Manager テスト")
    print("=" * 50)
    
    # 認証情報ファイル確認
    if not os.path.exists(credentials_file):
        print("⚠️  認証情報ファイルが見つかりません")
        print(f"Google Service Accountの認証情報を {credentials_file} に保存してください")
        return
    
    try:
        # Sheets Manager初期化
        sheets_manager = SheetsManager(credentials_file, spreadsheet_name)
        print("✅ Google Sheets接続成功")
        
        # テストデータ作成
        test_data = [
            {
                'video_id': 'test_001',
                'author_username': 'test_user',
                'author_nickname': 'テストユーザー',
                'description': 'テスト動画です',
                'view_count': 1000000,
                'like_count': 50000,
                'comment_count': 1000,
                'share_count': 500,
                'create_time': '2024-08-05 12:00:00',
                'hashtags': ['テスト', 'バイラル'],
                'is_verified': False
            }
        ]
        
        # データアップロードテスト
        print("\n📊 データアップロードテスト...")
        result = sheets_manager.upload_tiktok_data(
            test_data, 
            "テストデータ",
            clear_existing=True
        )
        print(f"✅ アップロード成功: {result}")
        
        # サマリー作成テスト
        print("\n📈 サマリー作成テスト...")
        summary_result = sheets_manager.create_summary_worksheet(test_data)
        print(f"✅ サマリー作成成功: {summary_result}")
        
        # スプレッドシートURL表示
        url = sheets_manager.get_spreadsheet_url()
        print(f"\n🔗 スプレッドシートURL: {url}")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")


if __name__ == "__main__":
    test_sheets_manager()

