# -*- coding: utf-8 -*-
"""Main AI analysis orchestrator for Taiwan Institutional Stocker."""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from ai_analysis.base import AIAnalysisBase
from ai_analysis.trend_analysis import InstitutionalTrendAnalysis
from ai_analysis.broker_analysis import BrokerPatternAnalysis
from ai_analysis.sentiment_analysis import MarketSentimentAnalysis
from ai_analysis.recommendations import StockRecommendationEngine
from ai_analysis.anomaly_detection import AnomalyDetectionEngine

class AIAnalysisOrchestrator(AIAnalysisBase):
    """Main orchestrator for all AI analysis modules."""
    
    def __init__(self):
        super().__init__()
        self.output_dir = os.path.join("docs", "data", "ai_analysis")
        
        # Initialize analysis modules
        self.trend_analyzer = InstitutionalTrendAnalysis()
        self.broker_analyzer = BrokerPatternAnalysis()
        self.sentiment_analyzer = MarketSentimentAnalysis()
        self.recommendation_engine = StockRecommendationEngine()
        self.anomaly_detector = AnomalyDetectionEngine()
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run_full_analysis(self, 
                         include_trends: bool = True,
                         include_broker: bool = True,
                         include_sentiment: bool = True,
                         include_recommendations: bool = True,
                         include_anomalies: bool = True,
                         anomaly_sensitivity: str = "medium") -> Dict[str, Any]:
        """Run complete AI analysis suite."""
        
        if not self.enabled:
            self.logger.warning("AI analysis is disabled. Please check your OpenAI API key configuration.")
            return self._create_disabled_response()
        
        self.logger.info("Starting full AI analysis suite...")
        
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "modules_executed": [],
            "results": {},
            "errors": [],
            "summary": {}
        }
        
        # 1. Institutional Trend Analysis
        if include_trends:
            self.logger.info("Running institutional trend analysis...")
            try:
                trend_results = self._run_trend_analysis()
                if trend_results:
                    results["results"]["trend_analysis"] = trend_results
                    results["modules_executed"].append("trend_analysis")
                    self.logger.info("Trend analysis completed successfully")
                else:
                    results["errors"].append("Trend analysis failed or returned no results")
            except Exception as e:
                error_msg = f"Trend analysis error: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # 2. Broker Pattern Analysis
        if include_broker:
            self.logger.info("Running broker pattern analysis...")
            try:
                broker_results = self._run_broker_analysis()
                if broker_results:
                    results["results"]["broker_analysis"] = broker_results
                    results["modules_executed"].append("broker_analysis")
                    self.logger.info("Broker analysis completed successfully")
                else:
                    results["errors"].append("Broker analysis failed or returned no results")
            except Exception as e:
                error_msg = f"Broker analysis error: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # 3. Market Sentiment Analysis
        if include_sentiment:
            self.logger.info("Running market sentiment analysis...")
            try:
                sentiment_results = self._run_sentiment_analysis()
                if sentiment_results:
                    results["results"]["sentiment_analysis"] = sentiment_results
                    results["modules_executed"].append("sentiment_analysis")
                    self.logger.info("Sentiment analysis completed successfully")
                else:
                    results["errors"].append("Sentiment analysis failed or returned no results")
            except Exception as e:
                error_msg = f"Sentiment analysis error: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # 4. Stock Recommendations
        if include_recommendations:
            self.logger.info("Running stock recommendation engine...")
            try:
                recommendation_results = self._run_recommendations()
                if recommendation_results:
                    results["results"]["recommendations"] = recommendation_results
                    results["modules_executed"].append("recommendations")
                    self.logger.info("Recommendations generated successfully")
                else:
                    results["errors"].append("Recommendation engine failed or returned no results")
            except Exception as e:
                error_msg = f"Recommendation engine error: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # 5. Anomaly Detection
        if include_anomalies:
            self.logger.info("Running anomaly detection...")
            try:
                anomaly_results = self._run_anomaly_detection(anomaly_sensitivity)
                if anomaly_results:
                    results["results"]["anomaly_detection"] = anomaly_results
                    results["modules_executed"].append("anomaly_detection")
                    self.logger.info("Anomaly detection completed successfully")
                else:
                    self.logger.info("No significant anomalies detected")
            except Exception as e:
                error_msg = f"Anomaly detection error: {str(e)}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Generate overall summary
        results["summary"] = self._generate_overall_summary(results)
        
        # Save comprehensive results
        self._save_comprehensive_results(results)
        
        self.logger.info(f"Full analysis completed. Executed {len(results['modules_executed'])} modules with {len(results['errors'])} errors.")
        
        return results
    
    def _run_trend_analysis(self) -> Optional[Dict[str, Any]]:
        """Run institutional trend analysis for multiple timeframes."""
        try:
            trend_results = {}
            
            # Analyze different time windows
            for window in [5, 20, 60]:
                analysis = self.trend_analyzer.analyze_top_changes(window=window, top_n=15)
                if analysis:
                    trend_results[f"{window}d_analysis"] = analysis
            
            # Analyze a few individual stocks if data is available
            stock_analyses = self._analyze_sample_stocks()
            if stock_analyses:
                trend_results["individual_stocks"] = stock_analyses
            
            return trend_results if trend_results else None
            
        except Exception as e:
            self.logger.error(f"Failed to run trend analysis: {e}")
            return None
    
    def _analyze_sample_stocks(self) -> Optional[Dict[str, Any]]:
        """Analyze a sample of individual stocks for trends."""
        try:
            # Get sample stocks from top changes
            sample_codes = []
            
            # Try to get some codes from existing rankings
            ranking_file = os.path.join("docs", "data", "top_three_inst_change_20_up.json")
            if os.path.exists(ranking_file):
                with open(ranking_file, 'r', encoding='utf-8') as f:
                    ranking_data = json.load(f)
                    sample_codes = [stock.get("code") for stock in ranking_data[:3]]
            
            if not sample_codes:
                sample_codes = ["2330", "2454", "2317"]  # Default popular stocks
            
            stock_analyses = {}
            for code in sample_codes:
                analysis = self.trend_analyzer.analyze_individual_stock(code, days_back=30)
                if analysis:
                    stock_analyses[code] = analysis
            
            return stock_analyses if stock_analyses else None
            
        except Exception as e:
            self.logger.error(f"Failed to analyze sample stocks: {e}")
            return None
    
    def _run_broker_analysis(self) -> Optional[Dict[str, Any]]:
        """Run broker pattern analysis."""
        try:
            # Overall broker patterns
            broker_results = {}
            
            pattern_analysis = self.broker_analyzer.analyze_broker_patterns(top_n=20)
            if pattern_analysis:
                broker_results["market_patterns"] = pattern_analysis
            
            # Analyze top individual brokers if data available
            broker_ranking_file = os.path.join("docs", "data", "broker_ranking.json")
            if os.path.exists(broker_ranking_file):
                with open(broker_ranking_file, 'r', encoding='utf-8') as f:
                    ranking_data = json.load(f)
                    
                if ranking_data:
                    top_brokers = ranking_data[:3]  # Analyze top 3 brokers
                    individual_analyses = {}
                    
                    for broker_info in top_brokers:
                        broker_name = broker_info.get("name")
                        if broker_name:
                            analysis = self.broker_analyzer.analyze_individual_broker(broker_name)
                            if analysis:
                                individual_analyses[broker_name] = analysis
                    
                    if individual_analyses:
                        broker_results["individual_brokers"] = individual_analyses
            
            return broker_results if broker_results else None
            
        except Exception as e:
            self.logger.error(f"Failed to run broker analysis: {e}")
            return None
    
    def _run_sentiment_analysis(self) -> Optional[Dict[str, Any]]:
        """Run market sentiment analysis."""
        try:
            return self.sentiment_analyzer.analyze_market_sentiment()
        except Exception as e:
            self.logger.error(f"Failed to run sentiment analysis: {e}")
            return None
    
    def _run_recommendations(self) -> Optional[Dict[str, Any]]:
        """Run stock recommendation engine."""
        try:
            recommendation_results = {}
            
            # Generate main recommendations
            main_recs = self.recommendation_engine.generate_recommendations(max_recommendations=15)
            if main_recs:
                recommendation_results["main_recommendations"] = main_recs
            
            # Generate focused watchlists
            focus_areas = ["momentum", "quality", "activity"]
            watchlists = {}
            
            for focus in focus_areas:
                watchlist = self.recommendation_engine.generate_watchlist(
                    focus_area=focus, 
                    max_stocks=8
                )
                if watchlist:
                    watchlists[focus] = watchlist
            
            if watchlists:
                recommendation_results["focused_watchlists"] = watchlists
            
            return recommendation_results if recommendation_results else None
            
        except Exception as e:
            self.logger.error(f"Failed to run recommendations: {e}")
            return None
    
    def _run_anomaly_detection(self, sensitivity: str) -> Optional[Dict[str, Any]]:
        """Run anomaly detection."""
        try:
            return self.anomaly_detector.detect_anomalies(sensitivity=sensitivity)
        except Exception as e:
            self.logger.error(f"Failed to run anomaly detection: {e}")
            return None
    
    def _generate_overall_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary of all analyses."""
        try:
            summary = {
                "execution_summary": {
                    "modules_run": len(results["modules_executed"]),
                    "total_modules": 5,
                    "errors": len(results["errors"]),
                    "success_rate": len(results["modules_executed"]) / 5 * 100
                },
                "key_findings": [],
                "market_overview": {},
                "recommendations_summary": {},
                "risk_alerts": []
            }
            
            analysis_results = results.get("results", {})
            
            # Extract key findings from each module
            if "sentiment_analysis" in analysis_results:
                sentiment_data = analysis_results["sentiment_analysis"]
                sentiment_score = sentiment_data.get("sentiment_score", {})
                summary["market_overview"]["sentiment"] = sentiment_score.get("label", "未知")
                summary["key_findings"].append(
                    f"市場情緒: {sentiment_score.get('label', '未知')} (信心度: {sentiment_score.get('confidence', '未知')})"
                )
            
            # Extract trend findings
            if "trend_analysis" in analysis_results:
                trend_data = analysis_results["trend_analysis"]
                if "20d_analysis" in trend_data:
                    trend_20d = trend_data["20d_analysis"]
                    ai_insights = trend_20d.get("ai_insights", {})
                    if ai_insights:
                        summary["key_findings"].append(
                            f"20日趨勢: {ai_insights.get('summary', '趨勢分析完成')}"
                        )
            
            # Extract anomaly alerts
            if "anomaly_detection" in analysis_results:
                anomaly_data = analysis_results["anomaly_detection"]
                detection_summary = anomaly_data.get("detection_summary", {})
                total_anomalies = detection_summary.get("total_anomalies", 0)
                
                if total_anomalies > 0:
                    summary["risk_alerts"].append(f"檢測到 {total_anomalies} 項市場異常")
                    
                    # Add top concerns
                    top_concerns = detection_summary.get("top_concerns", [])
                    for concern in top_concerns[:3]:
                        summary["risk_alerts"].append(concern.get("description", "異常行為"))
            
            # Extract recommendation summary
            if "recommendations" in analysis_results:
                rec_data = analysis_results["recommendations"]
                if "main_recommendations" in rec_data:
                    main_recs = rec_data["main_recommendations"]
                    rec_count = len(main_recs.get("recommendations", []))
                    summary["recommendations_summary"]["total_recommendations"] = rec_count
                    summary["key_findings"].append(f"生成 {rec_count} 項投資標的推薦")
            
            # Overall market assessment
            summary["market_overview"]["analysis_completeness"] = f"{summary['execution_summary']['success_rate']:.1f}%"
            summary["market_overview"]["data_freshness"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate overall summary: {e}")
            return {"error": "摘要生成失敗"}
    
    def _save_comprehensive_results(self, results: Dict[str, Any]) -> None:
        """Save comprehensive analysis results."""
        try:
            output_file = os.path.join(self.output_dir, "comprehensive_analysis.json")
            
            # Create a simplified version for the main results
            simplified_results = {
                "timestamp": results["analysis_timestamp"],
                "modules_executed": results["modules_executed"],
                "summary": results["summary"],
                "errors": results["errors"]
            }
            
            # Add key insights from each module
            analysis_results = results.get("results", {})
            simplified_results["insights"] = {}
            
            for module_name, module_data in analysis_results.items():
                if isinstance(module_data, dict):
                    # Extract AI insights if available
                    if "ai_insights" in module_data:
                        simplified_results["insights"][module_name] = {
                            "summary": module_data["ai_insights"].get("summary", ""),
                            "available": True
                        }
                    else:
                        # Look for insights in nested data
                        insights_found = False
                        for key, value in module_data.items():
                            if isinstance(value, dict) and "ai_insights" in value:
                                simplified_results["insights"][module_name] = {
                                    "summary": value["ai_insights"].get("summary", ""),
                                    "available": True
                                }
                                insights_found = True
                                break
                        
                        if not insights_found:
                            simplified_results["insights"][module_name] = {
                                "summary": f"{module_name.replace('_', ' ').title()} analysis completed",
                                "available": True
                            }
            
            self._save_analysis_result(simplified_results, output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to save comprehensive results: {e}")
    
    def _create_disabled_response(self) -> Dict[str, Any]:
        """Create response when AI analysis is disabled."""
        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "modules_executed": [],
            "results": {},
            "errors": ["AI analysis is disabled - please check OpenAI API key configuration"],
            "summary": {
                "execution_summary": {
                    "modules_run": 0,
                    "total_modules": 5,
                    "errors": 1,
                    "success_rate": 0
                },
                "message": "請在 .env 文件中設定有效的 OpenAI API 金鑰以啟用 AI 分析功能"
            }
        }
    
    def run_quick_analysis(self) -> Dict[str, Any]:
        """Run a quick analysis with essential modules only."""
        self.logger.info("Running quick AI analysis...")
        
        return self.run_full_analysis(
            include_trends=True,
            include_broker=False,
            include_sentiment=True,
            include_recommendations=True,
            include_anomalies=False
        )
    
    def run_sentiment_only(self) -> Dict[str, Any]:
        """Run sentiment analysis only."""
        self.logger.info("Running sentiment-only analysis...")
        
        return self.run_full_analysis(
            include_trends=False,
            include_broker=False,
            include_sentiment=True,
            include_recommendations=False,
            include_anomalies=False
        )
    
    def run_recommendations_only(self) -> Dict[str, Any]:
        """Run recommendations only."""
        self.logger.info("Running recommendations-only analysis...")
        
        return self.run_full_analysis(
            include_trends=False,
            include_broker=False,
            include_sentiment=False,
            include_recommendations=True,
            include_anomalies=False
        )

def main():
    """Main entry point for AI analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run AI Analysis for Taiwan Institutional Stocker")
    parser.add_argument("--mode", choices=["full", "quick", "sentiment", "recommendations"], 
                       default="full", help="Analysis mode to run")
    parser.add_argument("--anomaly-sensitivity", choices=["low", "medium", "high"], 
                       default="medium", help="Anomaly detection sensitivity")
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = AIAnalysisOrchestrator()
    
    # Run analysis based on mode
    if args.mode == "full":
        results = orchestrator.run_full_analysis(anomaly_sensitivity=args.anomaly_sensitivity)
    elif args.mode == "quick":
        results = orchestrator.run_quick_analysis()
    elif args.mode == "sentiment":
        results = orchestrator.run_sentiment_only()
    elif args.mode == "recommendations":
        results = orchestrator.run_recommendations_only()
    else:
        print(f"Unknown mode: {args.mode}")
        return
    
    # Print summary
    print("\n" + "="*60)
    print("AI Analysis Summary")
    print("="*60)
    
    summary = results.get("summary", {})
    exec_summary = summary.get("execution_summary", {})
    
    print(f"Modules executed: {exec_summary.get('modules_run', 0)}/{exec_summary.get('total_modules', 5)}")
    print(f"Success rate: {exec_summary.get('success_rate', 0):.1f}%")
    print(f"Errors: {exec_summary.get('errors', 0)}")
    
    key_findings = summary.get("key_findings", [])
    if key_findings:
        print("\nKey Findings:")
        for finding in key_findings:
            print(f"• {finding}")
    
    risk_alerts = summary.get("risk_alerts", [])
    if risk_alerts:
        print("\nRisk Alerts:")
        for alert in risk_alerts:
            print(f"⚠️ {alert}")
    
    errors = results.get("errors", [])
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"❌ {error}")
    
    print(f"\nAnalysis completed at: {results.get('analysis_timestamp')}")
    print("Detailed results saved to: docs/data/ai_analysis/")

if __name__ == "__main__":
    main()