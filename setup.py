#!/usr/bin/env python3
"""
TikTok Bright Data System - セットアップスクリプト
システムの初期設定と依存関係のインストール
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def install_dependencies():
    """依存関係をインストール"""
    print("📦 依存関係をインストール中...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 依存関係のインストール完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依存関係のインストールに失敗: {e}")
        return False

def create_config_file():
    """設定ファイルを作成"""
    print("⚙️  設定ファイルを作成中...")
    
    config_template = "config.json.template"
    config_file = "config.json"
    
    if os.path.exists(config_file):
        print(f"⚠️  {config_file} は既に存在します。スキップします。")
        return True
    
    if not os.path.exists(config_template):
        print(f"❌ テンプレートファイル {config_template} が見つかりません")
        return False
    
    try:
        # テンプレートをコピー
        with open(config_template, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"✅ {config_file} を作成しました")
        print(f"📝 {config_file} を編集して、APIキーと認証情報を設定してください")
        return True
        
    except Exception as e:
        print(f"❌ 設定ファイルの作成に失敗: {e}")
        return False

def create_credentials_template():
    """Google認証情報テンプレートを作成"""
    print("🔐 Google認証情報テンプレートを作成中...")
    
    credentials_template = "google_credentials.json.template"
    
    if os.path.exists(credentials_template):
        print(f"⚠️  {credentials_template} は既に存在します。スキップします。")
        return True
    
    template_content = {
        "type": "service_account",
        "project_id": "YOUR_PROJECT_ID",
        "private_key_id": "YOUR_PRIVATE_KEY_ID",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n",
        "client_email": "YOUR_SERVICE_ACCOUNT_EMAIL",
        "client_id": "YOUR_CLIENT_ID",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "YOUR_CERT_URL"
    }
    
    try:
        with open(credentials_template, 'w', encoding='utf-8') as f:
            json.dump(template_content, f, indent=2, ensure_ascii=False)
        
        print(f"✅ {credentials_template} を作成しました")
        print("📝 Google Cloud Consoleからサービスアカウントキーをダウンロードし、")
        print("   google_credentials.json として保存してください")
        return True
        
    except Exception as e:
        print(f"❌ 認証情報テンプレートの作成に失敗: {e}")
        return False

def create_directories():
    """必要なディレクトリを作成"""
    print("📁 ディレクトリを作成中...")
    
    directories = [
        "logs",
        "output",
        "temp"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            print(f"✅ {directory}/ ディレクトリを作成")
        except Exception as e:
            print(f"❌ {directory}/ ディレクトリの作成に失敗: {e}")
            return False
    
    return True

def check_python_version():
    """Python バージョンをチェック"""
    print("🐍 Python バージョンをチェック中...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8以上が必要です。現在のバージョン: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def run_basic_test():
    """基本的な動作テストを実行"""
    print("🧪 基本動作テストを実行中...")
    
    try:
        # インポートテスト
        from video_filter import VideoFilter
        from brightdata_client import BrightDataClient
        from sheets_manager import SheetsManager
        
        print("✅ 全モジュールのインポート成功")
        
        # 基本機能テスト
        config = {
            'min_views': 500000,
            'time_range_hours': 24,
            'exclude_verified': True,
            'languages': ['ja', 'jp'],
            'target_region': 'JP'
        }
        
        video_filter = VideoFilter(config)
        print("✅ VideoFilter 初期化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本動作テストに失敗: {e}")
        return False

def display_next_steps():
    """次のステップを表示"""
    print("\n" + "="*60)
    print("🎉 セットアップ完了!")
    print("="*60)
    
    print("\n📋 次のステップ:")
    print("1. config.json を編集:")
    print("   - Bright Data APIキーを設定")
    print("   - Google Sheets設定を更新")
    
    print("\n2. Google認証情報を設定:")
    print("   - Google Cloud Consoleでサービスアカウント作成")
    print("   - 認証情報をダウンロードして google_credentials.json として保存")
    
    print("\n3. システムテスト実行:")
    print("   python main.py --test")
    
    print("\n4. 本格実行:")
    print("   python main.py --method hybrid")
    
    print("\n📚 詳細な使用方法:")
    print("   README.md を参照してください")

def main():
    """メイン関数"""
    print("🚀 TikTok Bright Data System セットアップ開始")
    print("="*60)
    
    # Python バージョンチェック
    if not check_python_version():
        sys.exit(1)
    
    # 依存関係インストール
    if not install_dependencies():
        sys.exit(1)
    
    # ディレクトリ作成
    if not create_directories():
        sys.exit(1)
    
    # 設定ファイル作成
    if not create_config_file():
        sys.exit(1)
    
    # 認証情報テンプレート作成
    if not create_credentials_template():
        sys.exit(1)
    
    # 基本動作テスト
    if not run_basic_test():
        print("⚠️  基本動作テストに失敗しましたが、セットアップは継続します")
    
    # 次のステップ表示
    display_next_steps()

if __name__ == "__main__":
    main()

