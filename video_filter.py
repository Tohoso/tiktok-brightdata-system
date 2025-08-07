#!/usr/bin/env python3
"""
TikTok Video Filter
24時間以内・50万再生以上の動画を高精度でフィルタリング
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pytz
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException as LangDetectError

class VideoFilter:
    """TikTok動画フィルタリングクラス"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初期化
        
        Args:
            config: フィルタリング設定
        """
        self.config = config
        self.min_views = config.get('min_views', 500000)
        self.time_range_hours = config.get('time_range_hours', 24)
        self.exclude_verified = config.get('exclude_verified', True)
        self.target_languages = config.get('languages', ['ja', 'jp'])
        self.target_region = config.get('target_region', 'JP')
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # 日本語検出パターン
        self.japanese_patterns = [
            r'[\u3040-\u309F]',  # ひらがな
            r'[\u30A0-\u30FF]',  # カタカナ
            r'[\u4E00-\u9FAF]',  # 漢字
            r'[\uFF65-\uFF9F]'   # 半角カタカナ
        ]
        
        # 除外キーワード（観光客・外国人投稿）
        self.exclude_keywords = [
            'tourist', 'travel', 'visit', 'vacation', 'trip',
            'foreigner', 'gaijin', 'english', 'korean', 'chinese',
            'study abroad', 'exchange student', 'backpacker'
        ]
        
        # 日本関連キーワード（真の日本コンテンツ判定用）
        self.japan_keywords = [
            '日本', 'にほん', 'ニッポン', '東京', '大阪', '京都',
            '渋谷', '新宿', '原宿', '秋葉原', 'アニメ', 'マンガ',
            'ラーメン', '寿司', '居酒屋', 'コンビニ', '電車',
            'JR', '地下鉄', '駅', '神社', '寺', '桜', '紅葉'
        ]
    
    def filter_videos(self, videos: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        動画リストをフィルタリング
        
        Args:
            videos: 動画データのリスト
            
        Returns:
            (フィルタリング済み動画リスト, フィルタリング統計)
        """
        if not videos:
            return [], {"total": 0, "filtered": 0, "filter_stats": {}}
        
        self.logger.info(f"フィルタリング開始: {len(videos)}件の動画")
        
        filtered_videos = []
        filter_stats = {
            "total_input": len(videos),
            "passed_time_filter": 0,
            "passed_views_filter": 0,
            "passed_verified_filter": 0,
            "passed_language_filter": 0,
            "passed_region_filter": 0,
            "final_output": 0,
            "rejection_reasons": {}
        }
        
        for video in videos:
            try:
                # フィルタリング実行
                passed, reason = self._apply_filters(video)
                
                if passed:
                    # 追加情報を付与
                    enhanced_video = self._enhance_video_data(video)
                    filtered_videos.append(enhanced_video)
                    filter_stats["final_output"] += 1
                else:
                    # 除外理由を記録
                    if reason not in filter_stats["rejection_reasons"]:
                        filter_stats["rejection_reasons"][reason] = 0
                    filter_stats["rejection_reasons"][reason] += 1
                    
            except Exception as e:
                self.logger.warning(f"動画フィルタリングエラー: {e}")
                filter_stats["rejection_reasons"]["processing_error"] = \
                    filter_stats["rejection_reasons"].get("processing_error", 0) + 1
        
        # 統計情報を更新
        filter_stats["filter_rate"] = (
            filter_stats["final_output"] / filter_stats["total_input"] * 100
            if filter_stats["total_input"] > 0 else 0
        )
        
        self.logger.info(
            f"フィルタリング完了: {filter_stats['final_output']}/{filter_stats['total_input']}件 "
            f"({filter_stats['filter_rate']:.1f}%)"
        )
        
        return filtered_videos, filter_stats
    
    def _apply_filters(self, video: Dict[str, Any]) -> Tuple[bool, str]:
        """
        個別動画にフィルターを適用
        
        Args:
            video: 動画データ
            
        Returns:
            (フィルター通過フラグ, 除外理由)
        """
        # 1. 時間フィルター（24時間以内）
        if not self._check_time_filter(video):
            return False, "time_range"
        
        # 2. 再生数フィルター（50万再生以上）
        if not self._check_views_filter(video):
            return False, "view_count"
        
        # 3. 認証済みアカウント除外
        if not self._check_verified_filter(video):
            return False, "verified_account"
        
        # 4. 言語フィルター（日本語）
        if not self._check_language_filter(video):
            return False, "language"
        
        # 5. 地域フィルター（日本コンテンツ）
        if not self._check_region_filter(video):
            return False, "region"
        
        # 6. 品質フィルター（スパム・低品質除外）
        if not self._check_quality_filter(video):
            return False, "quality"
        
        return True, "passed"
    
    def _check_time_filter(self, video: Dict[str, Any]) -> bool:
        """24時間以内の投稿かチェック"""
        try:
            create_time = video.get('create_time') or video.get('createTime')
            if not create_time:
                return False
            
            # 投稿時間をパース
            if isinstance(create_time, str):
                # 複数の日時フォーマットに対応
                time_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S.%f'
                ]
                
                post_time = None
                for fmt in time_formats:
                    try:
                        post_time = datetime.strptime(create_time, fmt)
                        break
                    except ValueError:
                        continue
                
                if not post_time:
                    # Unix timestamp の可能性
                    try:
                        post_time = datetime.fromtimestamp(float(create_time))
                    except (ValueError, TypeError):
                        return False
            
            elif isinstance(create_time, (int, float)):
                # Unix timestamp
                post_time = datetime.fromtimestamp(create_time)
            else:
                return False
            
            # 現在時刻との差を計算
            now = datetime.now()
            time_diff = now - post_time
            
            # 24時間以内かチェック
            return time_diff <= timedelta(hours=self.time_range_hours)
            
        except Exception as e:
            self.logger.warning(f"時間フィルターエラー: {e}")
            return False
    
    def _check_views_filter(self, video: Dict[str, Any]) -> bool:
        """50万再生以上かチェック"""
        try:
            view_count = video.get('view_count') or video.get('viewCount') or video.get('stats', {}).get('playCount')
            
            if view_count is None:
                return False
            
            # 文字列の場合は数値に変換
            if isinstance(view_count, str):
                # "1.2M", "500K" などの表記に対応
                view_count = self._parse_count_string(view_count)
            
            return int(view_count) >= self.min_views
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"再生数フィルターエラー: {e}")
            return False
    
    def _parse_count_string(self, count_str: str) -> int:
        """再生数文字列を数値に変換"""
        if not isinstance(count_str, str):
            return int(count_str)
        
        count_str = count_str.upper().replace(',', '').replace(' ', '')
        
        # K, M, B の変換
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, multiplier in multipliers.items():
            if count_str.endswith(suffix):
                number = float(count_str[:-1])
                return int(number * multiplier)
        
        return int(float(count_str))
    
    def _check_verified_filter(self, video: Dict[str, Any]) -> bool:
        """認証済みアカウント除外チェック"""
        if not self.exclude_verified:
            return True
        
        # 複数のフィールドをチェック
        is_verified = (
            video.get('is_verified') or 
            video.get('author', {}).get('verified') or
            video.get('authorMeta', {}).get('verified') or
            False
        )
        
        return not is_verified
    
    def _check_language_filter(self, video: Dict[str, Any]) -> bool:
        """日本語コンテンツかチェック"""
        try:
            # テキストコンテンツを収集
            text_content = self._extract_text_content(video)
            
            if not text_content:
                return False
            
            # 1. 日本語文字パターンチェック
            japanese_score = self._calculate_japanese_score(text_content)
            
            # 2. 言語検出
            detected_lang = self._detect_language(text_content)
            
            # 3. 日本関連キーワードチェック
            keyword_score = self._calculate_keyword_score(text_content)
            
            # 総合判定
            is_japanese = (
                japanese_score > 0.3 or  # 30%以上日本語文字
                detected_lang in ['ja', 'jp'] or
                keyword_score > 0.2  # 20%以上日本関連キーワード
            )
            
            return is_japanese
            
        except Exception as e:
            self.logger.warning(f"言語フィルターエラー: {e}")
            return False
    
    def _extract_text_content(self, video: Dict[str, Any]) -> str:
        """動画からテキストコンテンツを抽出"""
        text_parts = []
        
        # 説明文
        description = video.get('description') or video.get('desc') or ''
        text_parts.append(description)
        
        # ハッシュタグ
        hashtags = video.get('hashtags') or video.get('challenges') or []
        if isinstance(hashtags, list):
            text_parts.extend(hashtags)
        elif isinstance(hashtags, str):
            text_parts.append(hashtags)
        
        # 音楽情報
        music_title = video.get('music_title') or video.get('music', {}).get('title') or ''
        text_parts.append(music_title)
        
        # ユーザー情報
        author_nickname = video.get('author_nickname') or video.get('author', {}).get('nickname') or ''
        text_parts.append(author_nickname)
        
        return ' '.join(text_parts).lower()
    
    def _calculate_japanese_score(self, text: str) -> float:
        """日本語文字の割合を計算"""
        if not text:
            return 0.0
        
        japanese_chars = 0
        total_chars = len(text)
        
        for pattern in self.japanese_patterns:
            japanese_chars += len(re.findall(pattern, text))
        
        return japanese_chars / total_chars if total_chars > 0 else 0.0
    
    def _detect_language(self, text: str) -> str:
        """言語検出"""
        try:
            if len(text.strip()) < 10:  # 短すぎるテキストは検出困難
                return 'unknown'
            
            detected = detect(text)
            return detected
        except LangDetectError:
            return 'unknown'
    
    def _calculate_keyword_score(self, text: str) -> float:
        """日本関連キーワードの割合を計算"""
        if not text:
            return 0.0
        
        words = text.split()
        japan_word_count = 0
        
        for keyword in self.japan_keywords:
            if keyword.lower() in text:
                japan_word_count += 1
        
        return japan_word_count / len(words) if words else 0.0
    
    def _check_region_filter(self, video: Dict[str, Any]) -> bool:
        """地域フィルター（日本コンテンツ）"""
        try:
            # 1. 地域情報チェック
            region = video.get('region') or video.get('country') or ''
            if region.upper() == self.target_region:
                return True
            
            # 2. 除外キーワードチェック
            text_content = self._extract_text_content(video)
            for exclude_keyword in self.exclude_keywords:
                if exclude_keyword.lower() in text_content:
                    return False
            
            # 3. 日本関連コンテンツの詳細チェック
            return self._is_authentic_japanese_content(video)
            
        except Exception as e:
            self.logger.warning(f"地域フィルターエラー: {e}")
            return True  # エラー時はパス
    
    def _is_authentic_japanese_content(self, video: Dict[str, Any]) -> bool:
        """真の日本コンテンツかチェック"""
        try:
            text_content = self._extract_text_content(video)
            
            # 日本語文字の密度
            japanese_score = self._calculate_japanese_score(text_content)
            
            # 日本関連キーワード
            keyword_score = self._calculate_keyword_score(text_content)
            
            # フォロワー数（一般人判定）
            follower_count = video.get('follower_count') or video.get('author', {}).get('followerCount') or 0
            is_regular_user = follower_count < 100000  # 10万フォロワー未満
            
            # 総合判定
            authenticity_score = (
                japanese_score * 0.4 +
                keyword_score * 0.3 +
                (0.3 if is_regular_user else 0.1)
            )
            
            return authenticity_score > 0.4
            
        except Exception as e:
            self.logger.warning(f"真正性チェックエラー: {e}")
            return True
    
    def _check_quality_filter(self, video: Dict[str, Any]) -> bool:
        """品質フィルター（スパム・低品質除外）"""
        try:
            # 1. 説明文の長さチェック
            description = video.get('description', '')
            if len(description) < 5:  # 短すぎる説明文
                return False
            
            # 2. エンゲージメント率チェック
            view_count = int(video.get('view_count', 0))
            like_count = int(video.get('like_count', 0))
            comment_count = int(video.get('comment_count', 0))
            
            if view_count > 0:
                engagement_rate = (like_count + comment_count) / view_count
                if engagement_rate < 0.001:  # 0.1%未満は低品質の可能性
                    return False
            
            # 3. スパムパターンチェック
            spam_patterns = [
                r'(.)\1{10,}',  # 同じ文字の連続
                r'[!]{5,}',     # 感嘆符の連続
                r'[?]{5,}',     # 疑問符の連続
                r'www\.',       # URL
                r'http',        # URL
            ]
            
            for pattern in spam_patterns:
                if re.search(pattern, description):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"品質フィルターエラー: {e}")
            return True
    
    def _enhance_video_data(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """動画データに追加情報を付与"""
        enhanced = video.copy()
        
        try:
            # フィルタリング通過時刻
            enhanced['filtered_at'] = datetime.now().isoformat()
            
            # 言語スコア
            text_content = self._extract_text_content(video)
            enhanced['japanese_score'] = self._calculate_japanese_score(text_content)
            enhanced['keyword_score'] = self._calculate_keyword_score(text_content)
            enhanced['detected_language'] = self._detect_language(text_content)
            
            # エンゲージメント率
            view_count = int(video.get('view_count', 0))
            like_count = int(video.get('like_count', 0))
            comment_count = int(video.get('comment_count', 0))
            
            if view_count > 0:
                enhanced['engagement_rate'] = (like_count + comment_count) / view_count
            else:
                enhanced['engagement_rate'] = 0.0
            
            # 投稿からの経過時間
            create_time = video.get('create_time')
            if create_time:
                try:
                    if isinstance(create_time, str):
                        post_time = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    else:
                        post_time = datetime.fromtimestamp(create_time)
                    
                    time_diff = datetime.now() - post_time.replace(tzinfo=None)
                    enhanced['hours_since_post'] = time_diff.total_seconds() / 3600
                except:
                    enhanced['hours_since_post'] = None
            
        except Exception as e:
            self.logger.warning(f"データ拡張エラー: {e}")
        
        return enhanced


def test_video_filter():
    """Video Filter のテスト"""
    
    # テスト用設定
    config = {
        'min_views': 500000,
        'time_range_hours': 24,
        'exclude_verified': True,
        'languages': ['ja', 'jp'],
        'target_region': 'JP'
    }
    
    filter_engine = VideoFilter(config)
    
    print("TikTok Video Filter テスト")
    print("=" * 50)
    
    # テストデータ
    test_videos = [
        {
            'video_id': 'test_001',
            'description': '今日の東京は暑いですね！🌞 #東京 #暑い #日本',
            'view_count': 1000000,
            'like_count': 50000,
            'comment_count': 1000,
            'create_time': datetime.now().isoformat(),
            'is_verified': False,
            'author': {'followerCount': 5000}
        },
        {
            'video_id': 'test_002',
            'description': 'Amazing trip to Tokyo! #travel #tourist #japan',
            'view_count': 800000,
            'like_count': 40000,
            'comment_count': 800,
            'create_time': (datetime.now() - timedelta(hours=30)).isoformat(),
            'is_verified': False,
            'author': {'followerCount': 3000}
        },
        {
            'video_id': 'test_003',
            'description': 'ラーメン美味しい！ #ラーメン #グルメ #日本料理',
            'view_count': 300000,
            'like_count': 15000,
            'comment_count': 300,
            'create_time': datetime.now().isoformat(),
            'is_verified': True,
            'author': {'followerCount': 200000}
        }
    ]
    
    # フィルタリング実行
    filtered_videos, stats = filter_engine.filter_videos(test_videos)
    
    print(f"📊 フィルタリング結果:")
    print(f"入力: {stats['total_input']}件")
    print(f"出力: {stats['final_output']}件")
    print(f"通過率: {stats['filter_rate']:.1f}%")
    
    print(f"\n📋 除外理由:")
    for reason, count in stats['rejection_reasons'].items():
        print(f"  {reason}: {count}件")
    
    print(f"\n✅ 通過した動画:")
    for video in filtered_videos:
        print(f"  {video['video_id']}: {video['description'][:50]}...")


if __name__ == "__main__":
    test_video_filter()

