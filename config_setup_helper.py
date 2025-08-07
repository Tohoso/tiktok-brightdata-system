#!/usr/bin/env python3
"""
TikTok Bright Data System - 設定ファイル作成ヘルパー
APIキーの設定を対話的にサポート
"""

import os
import json
import getpass
from pathlib import Path

def create_config_interactive():
    """対話的に設定ファイルを作成"""
    print("🔧 TikTok Bright Data System - 設定ファイル作成")
    print("="*60)
    
    config = {}
    
    # Bright Data設定
    print("\n📡 Bright Data API設定")
    print("-" * 30)
    
    api_key = getpass.getpass("Bright Data APIキーを入力してください: ")
    if not api_key:
        print("❌ APIキーが入力されていません")
        return False
    
    config["bright_data"] = {
        "api_key": api_key,
        "dataset_id": "gd_l7q7dkf244hwjntr0",
        "timeout": 300,
        "base_url": "https://api.brightdata.com/datasets/v3"
    }
    
    # Google Sheets設定
    print("\n📊 Google Sheets設定")
    print("-" * 30)
    
    credentials_file = input("Google認証ファイル名 [google_credentials.json]: ").strip()
    if not credentials_file:
        credentials_file = "google_credentials.json"
    
    spreadsheet_name = input("スプレッドシート名 [TikTok バイラル動画分析]: ").strip()
    if not spreadsheet_name:
        spreadsheet_name = "TikTok バイラル動画分析"
    
    worksheet_name = input("ワークシート名 [24時間以内・50万再生以上]: ").strip()
    if not worksheet_name:
        worksheet_name = "24時間以内・50万再生以上"
    
    config["google_sheets"] = {
        "credentials_file": credentials_file,
        "spreadsheet_name": spreadsheet_name,
        "worksheet_name": worksheet_name
    }
    
    # 収集設定
    print("\n🎯 収集設定")
    print("-" * 30)
    
    min_views = input("最小再生数 [500000]: ").strip()
    if not min_views:
        min_views = 500000
    else:
        try:
            min_views = int(min_views)
        except ValueError:
            min_views = 500000
    
    time_range = input("時間範囲（時間） [24]: ").strip()
    if not time_range:
        time_range = 24
    else:
        try:
            time_range = int(time_range)
        except ValueError:
            time_range = 24
    
    exclude_verified = input("認証済みアカウント除外 [y/N]: ").strip().lower()
    exclude_verified = exclude_verified in ['y', 'yes', 'true', '1']
    
    config["collection_settings"] = {
        "min_views": min_views,
        "time_range_hours": time_range,
        "exclude_verified": exclude_verified,
        "languages": ["ja", "jp"],
        "target_region": "JP"
    }
    
    # 出力設定
    config["output_settings"] = {
        "csv_output": True,
        "json_output": True
    }
    
    # ログ設定
    config["logging"] = {
        "level": "INFO",
        "file": "tiktok_brightdata.log"
    }
    
    # 設定ファイル保存
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("\n✅ config.json を作成しました")
        return True
        
    except Exception as e:
        print(f"\n❌ 設定ファイルの作成に失敗: {e}")
        return False

def validate_config():
    """設定ファイルの検証"""
    print("\n🔍 設定ファイルの検証")
    print("-" * 30)
    
    if not os.path.exists("config.json"):
        print("❌ config.json が見つかりません")
        return False
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 必須項目チェック
        required_keys = [
            ("bright_data", "api_key"),
            ("bright_data", "dataset_id"),
            ("google_sheets", "credentials_file"),
            ("google_sheets", "spreadsheet_name"),
            ("collection_settings", "min_views"),
            ("collection_settings", "time_range_hours")
        ]
        
        for section, key in required_keys:
            if section not in config or key not in config[section]:
                print(f"❌ 必須項目が不足: {section}.{key}")
                return False
            
            if not config[section][key]:
                print(f"❌ 値が設定されていません: {section}.{key}")
                return False
        
        # APIキー形式チェック
        api_key = config["bright_data"]["api_key"]
        if not api_key.startswith("bd_"):
            print("⚠️  APIキーの形式が正しくない可能性があります")
            print("   正しい形式: bd_xxxxxxxxxx...")
        
        # Google認証ファイルチェック
        credentials_file = config["google_sheets"]["credentials_file"]
        if not os.path.exists(credentials_file):
            print(f"⚠️  Google認証ファイルが見つかりません: {credentials_file}")
            print("   Google Cloud Consoleからダウンロードして配置してください")
        
        print("✅ 設定ファイルの検証完了")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSONフォーマットエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 検証エラー: {e}")
        return False

def show_config_summary():
    """設定内容の表示"""
    if not os.path.exists("config.json"):
        print("❌ config.json が見つかりません")
        return
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        print("\n📋 現在の設定内容")
        print("="*50)
        
        # Bright Data設定
        print("\n📡 Bright Data:")
        api_key = config["bright_data"]["api_key"]
        masked_key = api_key[:8] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else "*" * len(api_key)
        print(f"  APIキー: {masked_key}")
        print(f"  データセットID: {config['bright_data']['dataset_id']}")
        print(f"  タイムアウト: {config['bright_data']['timeout']}秒")
        
        # Google Sheets設定
        print("\n📊 Google Sheets:")
        print(f"  認証ファイル: {config['google_sheets']['credentials_file']}")
        print(f"  スプレッドシート名: {config['google_sheets']['spreadsheet_name']}")
        print(f"  ワークシート名: {config['google_sheets']['worksheet_name']}")
        
        # 収集設定
        print("\n🎯 収集設定:")
        print(f"  最小再生数: {config['collection_settings']['min_views']:,}回")
        print(f"  時間範囲: {config['collection_settings']['time_range_hours']}時間以内")
        print(f"  認証済み除外: {'はい' if config['collection_settings']['exclude_verified'] else 'いいえ'}")
        print(f"  対象言語: {', '.join(config['collection_settings']['languages'])}")
        print(f"  対象地域: {config['collection_settings']['target_region']}")
        
    except Exception as e:
        print(f"❌ 設定表示エラー: {e}")

def create_env_file():
    """環境変数ファイルの作成"""
    print("\n🔐 環境変数ファイル作成")
    print("-" * 30)
    
    if not os.path.exists("config.json"):
        print("❌ config.json が見つかりません")
        return False
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        api_key = config["bright_data"]["api_key"]
        
        env_content = f"""# TikTok Bright Data System - 環境変数
# セキュリティのため、APIキーは環境変数で管理することを推奨

# Bright Data API
BRIGHT_DATA_API_KEY={api_key}

# 使用方法:
# source .env  # Linux/macOS
# または
# set -a; source .env; set +a  # より確実な方法
"""
        
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ .env ファイルを作成しました")
        print("⚠️  .env ファイルは機密情報を含むため、Gitにコミットしないでください")
        
        # .gitignoreに追加
        gitignore_path = ".gitignore"
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as f:
                gitignore_content = f.read()
            
            if ".env" not in gitignore_content:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    f.write("\n# Environment variables\n.env\n")
                print("✅ .gitignore に .env を追加しました")
        
        return True
        
    except Exception as e:
        print(f"❌ 環境変数ファイル作成エラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 TikTok Bright Data System - 設定ヘルパー")
    print("="*60)
    
    while True:
        print("\n📋 メニュー:")
        print("1. 新しい設定ファイルを作成")
        print("2. 設定ファイルを検証")
        print("3. 設定内容を表示")
        print("4. 環境変数ファイルを作成")
        print("5. 終了")
        
        choice = input("\n選択してください (1-5): ").strip()
        
        if choice == "1":
            create_config_interactive()
        elif choice == "2":
            validate_config()
        elif choice == "3":
            show_config_summary()
        elif choice == "4":
            create_env_file()
        elif choice == "5":
            print("\n👋 設定ヘルパーを終了します")
            break
        else:
            print("❌ 無効な選択です")

if __name__ == "__main__":
    main()

