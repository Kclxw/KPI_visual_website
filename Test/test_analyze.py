"""
测试分析API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_ifir_odm_analyze():
    print("=" * 50)
    print("测试 IFIR ODM 分析")
    
    data = {
        "time_range": {"start_month": "2024-01", "end_month": "2025-12"},
        "filters": {"odms": ["FOXCONN", "TPV"]}
    }
    
    r = requests.post(f"{BASE_URL}/api/ifir/odm-analysis/analyze", json=data)
    result = r.json()
    
    print(f"  code: {result.get('code')}")
    print(f"  message: {result.get('message')}")
    
    if result.get("data"):
        data = result["data"]
        print(f"  cards: {len(data.get('cards', []))}")
        
        if data.get("summary"):
            print(f"  summary.odm_pie: {len(data['summary'].get('odm_pie', []))}")
        
        for card in data.get("cards", []):
            print(f"\n  ODM: {card['odm']}")
            print(f"    trend points: {len(card['trend'])}")
            print(f"    top models: {len(card['top_models'])}")
            
            if card["trend"]:
                print(f"    Last 3 trends: {card['trend'][-3:]}")
            
            if card["top_models"]:
                print(f"    Top models: {card['top_models'][:3]}")

def test_ra_odm_analyze():
    print("\n" + "=" * 50)
    print("测试 RA ODM 分析")
    
    data = {
        "time_range": {"start_month": "2024-01", "end_month": "2025-12"},
        "filters": {"odms": ["FOXCONN", "TPV"]}
    }
    
    r = requests.post(f"{BASE_URL}/api/ra/odm-analysis/analyze", json=data)
    result = r.json()
    
    print(f"  code: {result.get('code')}")
    print(f"  message: {result.get('message')}")
    
    if result.get("data"):
        data = result["data"]
        print(f"  cards: {len(data.get('cards', []))}")
        
        for card in data.get("cards", []):
            print(f"\n  ODM: {card['odm']}")
            print(f"    trend points: {len(card['trend'])}")
            print(f"    top models: {len(card['top_models'])}")
            
            if card["trend"]:
                print(f"    Last 3 trends: {card['trend'][-3:]}")

if __name__ == "__main__":
    test_ifir_odm_analyze()
    test_ra_odm_analyze()
    print("\n" + "=" * 50)
    print("测试完成")
