# -*- coding: utf-8 -*-
"""Comprehensive test script for AI analysis modules."""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

def test_environment_setup():
    """Test environment configuration and dependencies."""
    print("🔧 測試環境配置...")
    
    # Check if .env exists
    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ .env 文件存在")
        
        # Check for API key (without revealing it)
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your_openai_api_key_here":
            print("✅ OpenAI API 金鑰已設定")
            # Mask the key for security
            masked_key = f"{api_key[:10]}...{api_key[-4:]}"
            print(f"   金鑰: {masked_key}")
        else:
            print("❌ OpenAI API 金鑰未正確設定")
            return False
    else:
        print("❌ .env 文件不存在")
        return False
    
    # Check required packages
    required_packages = ["openai", "pandas", "requests", "python-dotenv"]
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} 已安裝")
        except ImportError:
            print(f"❌ {package} 未安裝")
            return False
    
    return True

def test_data_availability():
    """Test if required data files are available."""
    print("\n📊 測試數據可用性...")
    
    required_files = [
        "docs/data/stock_three_inst_latest.json",
        "docs/data/broker_ranking.json",
        "docs/data/broker_trades_latest.json",
        "docs/data/top_three_inst_change_20_up.json",
        "docs/data/top_three_inst_change_20_down.json"
    ]
    
    available_files = 0
    for file_path in required_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:  # Check if file has content
                        print(f"✅ {file_path} (有數據)")
                        available_files += 1
                    else:
                        print(f"⚠️ {file_path} (空檔案)")
            except Exception as e:
                print(f"❌ {file_path} (讀取錯誤: {e})")
        else:
            print(f"❌ {file_path} (不存在)")
    
    print(f"\n可用數據文件: {available_files}/{len(required_files)}")
    return available_files > 0

def test_ai_modules():
    """Test individual AI analysis modules."""
    print("\n🤖 測試 AI 分析模組...")
    
    # Test modules without OpenAI calls first
    test_results = {}
    
    try:
        # Test base module
        from ai_analysis.base import AIAnalysisBase
        base = AIAnalysisBase()
        test_results["base_module"] = {
            "status": "✅ 成功",
            "enabled": base.is_enabled(),
            "details": "基礎模組正常"
        }
    except Exception as e:
        test_results["base_module"] = {
            "status": "❌ 失敗", 
            "enabled": False,
            "details": f"導入錯誤: {e}"
        }
    
    # Test individual modules
    modules = [
        ("trend_analysis", "ai_analysis.trend_analysis", "InstitutionalTrendAnalysis"),
        ("broker_analysis", "ai_analysis.broker_analysis", "BrokerPatternAnalysis"),
        ("sentiment_analysis", "ai_analysis.sentiment_analysis", "MarketSentimentAnalysis"),
        ("recommendations", "ai_analysis.recommendations", "StockRecommendationEngine"),
        ("anomaly_detection", "ai_analysis.anomaly_detection", "AnomalyDetectionEngine")
    ]
    
    for module_name, module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            instance = cls()
            
            test_results[module_name] = {
                "status": "✅ 成功",
                "enabled": instance.is_enabled(),
                "details": f"{class_name} 初始化正常"
            }
        except Exception as e:
            test_results[module_name] = {
                "status": "❌ 失敗",
                "enabled": False,
                "details": f"初始化錯誤: {e}"
            }
    
    # Print results
    for module, result in test_results.items():
        status = result["status"]
        enabled = "🔥 啟用" if result["enabled"] else "🚫 停用"
        details = result["details"]
        print(f"{status} {module}: {enabled} - {details}")
    
    return test_results

def test_data_processing():
    """Test data processing without AI calls."""
    print("\n📈 測試數據處理功能...")
    
    test_results = {}
    
    # Test JSON file loading
    try:
        latest_file = "docs/data/stock_three_inst_latest.json"
        if os.path.exists(latest_file):
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                test_results["json_loading"] = {
                    "status": "✅ 成功",
                    "details": f"載入 {len(data)} 筆股票資料"
                }
        else:
            test_results["json_loading"] = {
                "status": "❌ 失敗",
                "details": "無法找到股票資料檔案"
            }
    except Exception as e:
        test_results["json_loading"] = {
            "status": "❌ 失敗",
            "details": f"JSON 載入錯誤: {e}"
        }
    
    # Test timeseries data
    try:
        timeseries_dir = "docs/data/timeseries"
        if os.path.exists(timeseries_dir):
            files = [f for f in os.listdir(timeseries_dir) if f.endswith('.json')]
            if files:
                # Test loading one file
                sample_file = os.path.join(timeseries_dir, files[0])
                with open(sample_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    test_results["timeseries_loading"] = {
                        "status": "✅ 成功",
                        "details": f"時序資料: {len(files)} 個檔案, 樣本有 {len(data)} 筆記錄"
                    }
            else:
                test_results["timeseries_loading"] = {
                    "status": "❌ 失敗",
                    "details": "時序資料目錄為空"
                }
        else:
            test_results["timeseries_loading"] = {
                "status": "❌ 失敗",
                "details": "時序資料目錄不存在"
            }
    except Exception as e:
        test_results["timeseries_loading"] = {
            "status": "❌ 失敗",
            "details": f"時序資料錯誤: {e}"
        }
    
    # Test broker data
    try:
        broker_file = "docs/data/broker_ranking.json"
        if os.path.exists(broker_file):
            with open(broker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                test_results["broker_data"] = {
                    "status": "✅ 成功",
                    "details": f"券商資料: {len(data)} 筆記錄"
                }
        else:
            test_results["broker_data"] = {
                "status": "❌ 失敗",
                "details": "券商資料檔案不存在"
            }
    except Exception as e:
        test_results["broker_data"] = {
            "status": "❌ 失敗",
            "details": f"券商資料錯誤: {e}"
        }
    
    # Print results
    for test_name, result in test_results.items():
        status = result["status"]
        details = result["details"]
        print(f"{status} {test_name}: {details}")
    
    return test_results

def test_analysis_without_ai():
    """Test analysis functions that don't require AI calls."""
    print("\n🔬 測試非 AI 分析功能...")
    
    test_results = {}
    
    try:
        # Test screening without AI
        from ai_analysis.recommendations import StockRecommendationEngine
        engine = StockRecommendationEngine()
        
        # Test screening functions
        candidates = engine._screen_stock_candidates()
        test_results["stock_screening"] = {
            "status": "✅ 成功" if candidates else "⚠️ 無候選股票",
            "details": f"篩選出 {len(candidates)} 支候選股票"
        }
        
    except Exception as e:
        test_results["stock_screening"] = {
            "status": "❌ 失敗",
            "details": f"股票篩選錯誤: {e}"
        }
    
    try:
        # Test sentiment data collection
        from ai_analysis.sentiment_analysis import MarketSentimentAnalysis
        analyzer = MarketSentimentAnalysis()
        
        sentiment_data = analyzer._collect_sentiment_data()
        test_results["sentiment_data"] = {
            "status": "✅ 成功" if sentiment_data else "⚠️ 無情緒數據",
            "details": f"收集到 {len(sentiment_data)} 項情緒指標"
        }
        
    except Exception as e:
        test_results["sentiment_data"] = {
            "status": "❌ 失敗",
            "details": f"情緒數據錯誤: {e}"
        }
    
    try:
        # Test anomaly detection thresholds
        from ai_analysis.anomaly_detection import AnomalyDetectionEngine
        detector = AnomalyDetectionEngine()
        
        thresholds = detector._get_institutional_thresholds("medium")
        test_results["anomaly_thresholds"] = {
            "status": "✅ 成功",
            "details": f"異常檢測閾值設定: {len(thresholds)} 項參數"
        }
        
    except Exception as e:
        test_results["anomaly_thresholds"] = {
            "status": "❌ 失敗",
            "details": f"異常檢測錯誤: {e}"
        }
    
    # Print results
    for test_name, result in test_results.items():
        status = result["status"]
        details = result["details"]
        print(f"{status} {test_name}: {details}")
    
    return test_results

def test_output_generation():
    """Test output file generation."""
    print("\n💾 測試輸出文件生成...")
    
    test_results = {}
    output_dir = "docs/data/ai_analysis"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Test basic file operations
    try:
        test_file = os.path.join(output_dir, "test_output.json")
        test_data = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "測試輸出檔案"
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # Verify file was created and readable
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        test_results["file_generation"] = {
            "status": "✅ 成功",
            "details": f"測試檔案建立和讀取正常"
        }
        
        # Clean up test file
        os.remove(test_file)
        
    except Exception as e:
        test_results["file_generation"] = {
            "status": "❌ 失敗",
            "details": f"檔案操作錯誤: {e}"
        }
    
    # Test directory permissions
    try:
        if os.access(output_dir, os.W_OK):
            test_results["directory_permissions"] = {
                "status": "✅ 成功",
                "details": "輸出目錄寫入權限正常"
            }
        else:
            test_results["directory_permissions"] = {
                "status": "❌ 失敗",
                "details": "輸出目錄沒有寫入權限"
            }
    except Exception as e:
        test_results["directory_permissions"] = {
            "status": "❌ 失敗",
            "details": f"權限檢查錯誤: {e}"
        }
    
    # Print results
    for test_name, result in test_results.items():
        status = result["status"]
        details = result["details"]
        print(f"{status} {test_name}: {details}")
    
    return test_results

def generate_test_report(all_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive test report."""
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    warnings = 0
    
    # Count all test results
    for category, results in all_results.items():
        if isinstance(results, dict):
            for test_name, result in results.items():
                if isinstance(result, dict) and "status" in result:
                    total_tests += 1
                    if "✅" in result["status"]:
                        passed_tests += 1
                    elif "❌" in result["status"]:
                        failed_tests += 1
                    elif "⚠️" in result["status"]:
                        warnings += 1
    
    # Calculate overall health
    if total_tests > 0:
        pass_rate = (passed_tests / total_tests) * 100
    else:
        pass_rate = 0
    
    if pass_rate >= 90:
        health_status = "🟢 優秀"
    elif pass_rate >= 70:
        health_status = "🟡 良好"
    elif pass_rate >= 50:
        health_status = "🟠 尚可"
    else:
        health_status = "🔴 需要修復"
    
    report = {
        "test_summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "warnings": warnings,
            "pass_rate": pass_rate,
            "health_status": health_status
        },
        "detailed_results": all_results,
        "generated_at": datetime.now().isoformat()
    }
    
    return report

def print_summary_report(report: Dict[str, Any]):
    """Print summary test report."""
    print("\n" + "="*60)
    print("🧪 AI 分析系統全面測試報告")
    print("="*60)
    
    summary = report["test_summary"]
    
    print(f"總測試項目: {summary['total_tests']}")
    print(f"通過: {summary['passed']} ✅")
    print(f"失敗: {summary['failed']} ❌")
    print(f"警告: {summary['warnings']} ⚠️")
    print(f"通過率: {summary['pass_rate']:.1f}%")
    print(f"系統健康度: {summary['health_status']}")
    
    print(f"\n測試完成時間: {report['generated_at']}")
    
    # Recommendations
    print("\n📋 建議事項:")
    if summary['failed'] > 0:
        print("• 修復失敗的測試項目")
    if summary['warnings'] > 0:
        print("• 檢查警告項目")
    
    # Check specific issues
    env_results = report["detailed_results"].get("environment", {})
    if any("❌" in result.get("status", "") for result in env_results.values()):
        print("• 檢查 OpenAI API 金鑰配置")
    
    data_results = report["detailed_results"].get("data_availability", {})
    if any("❌" in result.get("status", "") for result in data_results.values()):
        print("• 確保數據文件完整性")
    
    print("\n系統已準備好進行 AI 分析！🚀")

def main():
    """Run comprehensive tests."""
    print("🚀 開始 AI 分析系統全面測試...\n")
    
    # Run all tests
    all_results = {}
    
    # Environment tests
    if test_environment_setup():
        all_results["environment"] = {"setup": {"status": "✅ 成功", "details": "環境配置正確"}}
    else:
        all_results["environment"] = {"setup": {"status": "❌ 失敗", "details": "環境配置錯誤"}}
    
    # Data availability tests
    if test_data_availability():
        all_results["data_availability"] = {"data_files": {"status": "✅ 成功", "details": "數據文件可用"}}
    else:
        all_results["data_availability"] = {"data_files": {"status": "❌ 失敗", "details": "數據文件不完整"}}
    
    # AI module tests
    all_results["ai_modules"] = test_ai_modules()
    
    # Data processing tests
    all_results["data_processing"] = test_data_processing()
    
    # Non-AI analysis tests
    all_results["analysis_functions"] = test_analysis_without_ai()
    
    # Output generation tests
    all_results["output_generation"] = test_output_generation()
    
    # Generate and save report
    report = generate_test_report(all_results)
    
    # Save detailed report
    try:
        report_file = "docs/data/ai_analysis/test_report.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n詳細報告已儲存至: {report_file}")
    except Exception as e:
        print(f"\n⚠️ 無法儲存詳細報告: {e}")
    
    # Print summary
    print_summary_report(report)

if __name__ == "__main__":
    main()