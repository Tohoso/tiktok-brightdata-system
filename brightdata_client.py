#!/usr/bin/env python3
"""
Bright Data TikTok Scraper API Client
24時間以内・50万再生以上の動画を効率的に収集
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

class BrightDataClient:
    """Bright Data TikTok Scraper APIクライアント"""
    
    def __init__(self, api_key: str, dataset_id: str, timeout: int = 300):
        """
        初期化
        
        Args:
            api_key: Bright Data APIキー
            dataset_id: TikTokスクレイパーのデータセットID
            timeout: タイムアウト時間（秒）
        """
        self.api_key = api_key
        self.dataset_id = dataset_id
        self.timeout = timeout
        self.base_url = "https://api.brightdata.com/datasets/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
    
    def trigger_keyword_scraping(self, keywords: List[str], 
                               country: str = "JP",
                               num_posts_per_keyword: int = 200) -> Dict[str, Any]:
        """
        キーワードベースのスクレイピングジョブを開始
        
        Args:
            keywords: 検索キーワード一覧
            country: 対象国（JP=日本）
            num_posts_per_keyword: キーワードあたりの投稿数
            
        Returns:
            ジョブ情報（snapshot_idを含む）
        """
        try:
            # リクエストボディ構築（JSON配列形式）
            request_data = []
            for keyword in keywords:
                request_data.append({
                    "search_keyword": keyword,
                    "country": country,
                    "num_of_posts": num_posts_per_keyword
                })
            
            self.logger.info(f"キーワードスクレイピングジョブ開始: {len(keywords)}件のキーワード")
            
            # API呼び出し（新しいエンドポイント形式）
            url = f"{self.base_url}/trigger"
            params = {
                "dataset_id": self.dataset_id,
                "include_errors": "true",
                "type": "discover_new",
                "discover_by": "keyword"
            }
            
            response = self.session.post(
                url,
                params=params,
                json=request_data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(f"ジョブ開始成功: snapshot_id={result.get('snapshot_id')}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"キーワードスクレイピングジョブ開始エラー: {e}")
            raise
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            raise
    
    def get_job_status(self, snapshot_id: str) -> Dict[str, Any]:
        """
        ジョブステータスを取得
        
        Args:
            snapshot_id: ジョブのスナップショットID
            
        Returns:
            ジョブステータス情報
        """
        try:
            response = self.session.get(
                f"{self.base_url}/snapshot/{snapshot_id}",
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ジョブステータス取得エラー: {e}")
            raise
    
    def wait_for_completion(self, snapshot_id: str, 
                          max_wait_time: int = 1800,
                          check_interval: int = 30) -> List[Dict[str, Any]]:
        """
        ジョブ完了まで待機し、結果を取得
        
        Args:
            snapshot_id: ジョブのスナップショットID
            max_wait_time: 最大待機時間（秒）
            check_interval: チェック間隔（秒）
            
        Returns:
            スクレイピング結果のリスト
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status = self.get_job_status(snapshot_id)
                job_status = status.get('status', 'unknown')
                
                self.logger.info(f"ジョブステータス: {job_status}")
                
                if job_status == 'completed':
                    self.logger.info("ジョブ完了、結果を取得中...")
                    return self.get_results(snapshot_id)
                elif job_status == 'failed':
                    error_msg = status.get('error', 'Unknown error')
                    raise Exception(f"ジョブ失敗: {error_msg}")
                elif job_status in ['running', 'pending']:
                    self.logger.info(f"ジョブ実行中... {check_interval}秒後に再チェック")
                    time.sleep(check_interval)
                else:
                    self.logger.warning(f"不明なステータス: {job_status}")
                    time.sleep(check_interval)
                    
            except Exception as e:
                self.logger.error(f"ジョブ監視エラー: {e}")
                time.sleep(check_interval)
        
        raise TimeoutError(f"ジョブが{max_wait_time}秒以内に完了しませんでした")
    
    def get_results(self, snapshot_id: str) -> List[Dict[str, Any]]:
        """
        スクレイピング結果を取得
        
        Args:
            snapshot_id: ジョブのスナップショットID
            
        Returns:
            スクレイピング結果のリスト
        """
        try:
            response = self.session.get(
                f"{self.base_url}/snapshot/{snapshot_id}",
                params={"format": "json"},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # レスポンスがJSONの場合とNDJSONの場合を処理
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                data = response.json()
                # データが配列の場合はそのまま、オブジェクトの場合はdataフィールドを取得
                if isinstance(data, list):
                    return data
                else:
                    return data.get('data', [])
            else:
                # NDJSON形式の場合
                results = []
                for line in response.text.strip().split('\n'):
                    if line.strip():
                        results.append(json.loads(line))
                return results
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"結果取得エラー: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析エラー: {e}")
            raise
    
    def get_job_results(self, snapshot_id: str) -> List[Dict[str, Any]]:
        """
        ジョブ結果を取得（get_resultsのエイリアス）
        
        Args:
            snapshot_id: ジョブのスナップショットID
            
        Returns:
            スクレイピング結果のリスト
        """
        return self.get_results(snapshot_id)
    
    def scrape_tiktok_discover_pages(self, country: str = "JP") -> List[Dict[str, Any]]:
        """
        TikTok発見ページをスクレイピング
        
        Args:
            country: 対象国コード
            
        Returns:
            スクレイピング結果
        """
        # 日本のTikTok発見ページURL
        discover_urls = [
            "https://www.tiktok.com/discover",
            "https://www.tiktok.com/trending",
            "https://www.tiktok.com/foryou",
            "https://www.tiktok.com/explore"
        ]
        
        self.logger.info(f"TikTok発見ページのスクレイピング開始: {country}")
        
        # ジョブ開始
        job_result = self.trigger_scraping_job(
            urls=discover_urls,
            country=country,
            additional_params={
                "include_posts": True,
                "max_posts_per_page": 100
            }
        )
        
        snapshot_id = job_result.get('snapshot_id')
        if not snapshot_id:
            raise Exception("snapshot_idが取得できませんでした")
        
        # 結果待機・取得
        return self.wait_for_completion(snapshot_id)
    
    def scrape_hashtag_posts(self, hashtags: List[str], 
                           country: str = "JP") -> List[Dict[str, Any]]:
        """
        ハッシュタグ投稿をスクレイピング
        
        Args:
            hashtags: ハッシュタグリスト
            country: 対象国コード
            
        Returns:
            スクレイピング結果
        """
        # ハッシュタグURLを構築
        hashtag_urls = [
            f"https://www.tiktok.com/tag/{hashtag.lstrip('#')}"
            for hashtag in hashtags
        ]
        
        self.logger.info(f"ハッシュタグ投稿のスクレイピング開始: {len(hashtags)}件")
        
        # ジョブ開始
        job_result = self.trigger_scraping_job(
            urls=hashtag_urls,
            country=country,
            additional_params={
                "include_posts": True,
                "max_posts_per_hashtag": 50
            }
        )
        
        snapshot_id = job_result.get('snapshot_id')
        if not snapshot_id:
            raise Exception("snapshot_idが取得できませんでした")
        
        # 結果待機・取得
        return self.wait_for_completion(snapshot_id)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        API使用統計を取得
        
        Returns:
            使用統計情報
        """
        try:
            response = self.session.get(
                f"{self.base_url}/get_usage_stats",
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"使用統計取得エラー: {e}")
            raise


def test_brightdata_client():
    """Bright Data クライアントのテスト"""
    import os
    
    # テスト用設定（実際のAPIキーは設定ファイルから読み込み）
    api_key = os.getenv('BRIGHT_DATA_API_KEY', 'test_key')
    dataset_id = "gd_l7q7dkf244hwjntr0"  # TikTokスクレイパーのデータセットID
    
    client = BrightDataClient(api_key, dataset_id)
    
    print("Bright Data TikTokスクレイパークライアント テスト")
    print("=" * 50)
    
    # モックテスト（実際のAPIキーがない場合）
    if api_key == 'test_key':
        print("⚠️  実際のAPIキーが設定されていません")
        print("設定ファイルにAPIキーを設定してから実行してください")
        return
    
    try:
        # 使用統計取得テスト
        print("📊 使用統計取得テスト...")
        stats = client.get_usage_stats()
        print(f"✅ 使用統計取得成功: {stats}")
        
        # 小規模テスト
        print("\n🔍 小規模スクレイピングテスト...")
        test_urls = ["https://www.tiktok.com/discover"]
        
        job_result = client.trigger_scraping_job(test_urls)
        print(f"✅ ジョブ開始成功: {job_result}")
        
        # 結果取得（短時間で完了する場合のみ）
        snapshot_id = job_result.get('snapshot_id')
        if snapshot_id:
            print(f"📋 ジョブ監視中: {snapshot_id}")
            # 実際の運用では wait_for_completion を使用
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")


if __name__ == "__main__":
    test_brightdata_client()

