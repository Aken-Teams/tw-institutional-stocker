# -*- coding: utf-8 -*-
"""AI-powered stock recommendations based on institutional and broker data."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from .base import AIAnalysisBase

class StockRecommendationEngine(AIAnalysisBase):
    """AI-powered stock recommendation engine."""
    
    def __init__(self):
        super().__init__()
        self.docs_dir = os.path.join("docs", "data")
        self.timeseries_dir = os.path.join(self.docs_dir, "timeseries")
        self.output_dir = os.path.join(self.docs_dir, "ai_analysis")
        
    def generate_recommendations(self, max_recommendations: int = 20) -> Optional[Dict[str, Any]]:
        """Generate stock recommendations based on multiple criteria."""
        if not self.enabled:
            return None
        
        try:
            # Screen stocks based on multiple criteria
            candidates = self._screen_stock_candidates()
            
            if not candidates:
                self.logger.warning("No candidate stocks found for recommendations")
                return None
            
            # Rank and select top candidates
            top_candidates = self._rank_candidates(candidates, max_recommendations)
            
            # Generate AI analysis for each recommendation
            recommendations = []
            for candidate in top_candidates:
                analysis = self._analyze_candidate(candidate)
                if analysis:
                    recommendations.append(analysis)
            
            # Generate overall market context
            market_context = self._generate_market_context()
            
            result = {
                "recommendations": recommendations,
                "market_context": market_context,
                "screening_criteria": self._get_screening_criteria(),
                "total_candidates_screened": len(candidates),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model_used": self.model,
                    "analysis_type": "stock_recommendations",
                    "recommendation_count": len(recommendations)
                }
            }
            
            # Save results
            output_file = os.path.join(self.output_dir, "stock_recommendations.json")
            self._save_analysis_result(result, output_file)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return None
    
    def _screen_stock_candidates(self) -> List[Dict[str, Any]]:
        """Screen stocks based on institutional and broker activity."""
        try:
            candidates = []
            
            # Load data sources
            latest_stocks = self._load_json_data(os.path.join(self.docs_dir, "stock_three_inst_latest.json")) or []
            broker_trades = self._load_json_data(os.path.join(self.docs_dir, "broker_trades_latest.json")) or []
            
            # Create broker activity lookup
            broker_activity = self._create_broker_activity_lookup(broker_trades)
            
            # Screen stocks
            for stock in latest_stocks:
                code = stock.get("code")
                if not code:
                    continue
                
                # Load individual stock timeseries
                timeseries_file = os.path.join(self.timeseries_dir, f"{code}.json")
                timeseries_data = self._load_json_data(timeseries_file) or []
                
                if len(timeseries_data) < 10:  # Need at least 10 days of data
                    continue
                
                # Calculate screening metrics
                metrics = self._calculate_screening_metrics(stock, timeseries_data, broker_activity.get(code, {}))
                
                if self._passes_screening(metrics):
                    candidate = {
                        "stock_info": stock,
                        "timeseries_data": timeseries_data[-30:],  # Last 30 days
                        "metrics": metrics,
                        "broker_activity": broker_activity.get(code, {})
                    }
                    candidates.append(candidate)
            
            self.logger.info(f"Found {len(candidates)} candidates after screening")
            return candidates
            
        except Exception as e:
            self.logger.error(f"Failed to screen stock candidates: {e}")
            return []
    
    def _create_broker_activity_lookup(self, broker_trades: List[Dict]) -> Dict[str, Dict]:
        """Create lookup table for broker activity by stock."""
        try:
            activity = {}
            
            for trade in broker_trades:
                code = trade.get("code")
                if not code:
                    continue
                
                if code not in activity:
                    activity[code] = {
                        "total_volume": 0,
                        "buy_volume": 0,
                        "sell_volume": 0,
                        "broker_count": set(),
                        "net_flow": 0
                    }
                
                amount = trade.get("amount", 0)
                side = trade.get("side", "")
                broker = trade.get("broker", "")
                
                activity[code]["total_volume"] += amount
                activity[code]["broker_count"].add(broker)
                
                if side == "買":
                    activity[code]["buy_volume"] += amount
                    activity[code]["net_flow"] += amount
                elif side == "賣":
                    activity[code]["sell_volume"] += amount
                    activity[code]["net_flow"] -= amount
            
            # Convert sets to counts
            for code in activity:
                activity[code]["unique_brokers"] = len(activity[code]["broker_count"])
                del activity[code]["broker_count"]
            
            return activity
            
        except Exception as e:
            self.logger.error(f"Failed to create broker activity lookup: {e}")
            return {}
    
    def _calculate_screening_metrics(self, stock: Dict, timeseries: List[Dict], broker_activity: Dict) -> Dict[str, Any]:
        """Calculate metrics for stock screening."""
        try:
            metrics = {}
            
            # Basic stock info
            metrics["code"] = stock.get("code")
            metrics["name"] = stock.get("name")
            metrics["market"] = stock.get("market")
            
            # Institutional metrics
            current_ratio = stock.get("three_inst_ratio", 0)
            foreign_ratio = stock.get("foreign_ratio", 0)
            trust_ratio = stock.get("trust_ratio", 0)
            dealer_ratio = stock.get("dealer_ratio", 0)
            
            metrics["current_inst_ratio"] = current_ratio
            metrics["foreign_ratio"] = foreign_ratio
            metrics["trust_ratio"] = trust_ratio
            metrics["dealer_ratio"] = dealer_ratio
            
            # Calculate trends from timeseries
            if len(timeseries) >= 5:
                recent_ratios = [data.get("three_inst_ratio", 0) for data in timeseries[-5:]]
                metrics["5d_trend"] = recent_ratios[-1] - recent_ratios[0] if recent_ratios else 0
                
                if len(timeseries) >= 20:
                    medium_ratios = [data.get("three_inst_ratio", 0) for data in timeseries[-20:]]
                    metrics["20d_trend"] = medium_ratios[-1] - medium_ratios[0] if medium_ratios else 0
                else:
                    metrics["20d_trend"] = 0
            else:
                metrics["5d_trend"] = 0
                metrics["20d_trend"] = 0
            
            # Volatility metrics
            if len(timeseries) >= 10:
                ratios = [data.get("three_inst_ratio", 0) for data in timeseries[-10:]]
                max_ratio = max(ratios)
                min_ratio = min(ratios)
                metrics["volatility"] = max_ratio - min_ratio
                metrics["stability_score"] = 1 / (1 + metrics["volatility"]) if metrics["volatility"] > 0 else 1
            else:
                metrics["volatility"] = 0
                metrics["stability_score"] = 1
            
            # Broker activity metrics
            metrics["broker_volume"] = broker_activity.get("total_volume", 0)
            metrics["broker_net_flow"] = broker_activity.get("net_flow", 0)
            metrics["broker_count"] = broker_activity.get("unique_brokers", 0)
            metrics["broker_interest"] = metrics["broker_count"] * metrics["broker_volume"] if metrics["broker_count"] > 0 else 0
            
            # Composite scores
            metrics["momentum_score"] = self._calculate_momentum_score(metrics)
            metrics["quality_score"] = self._calculate_quality_score(metrics)
            metrics["activity_score"] = self._calculate_activity_score(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate screening metrics: {e}")
            return {}
    
    def _calculate_momentum_score(self, metrics: Dict) -> float:
        """Calculate momentum score based on trends."""
        try:
            short_trend = metrics.get("5d_trend", 0)
            medium_trend = metrics.get("20d_trend", 0)
            
            # Weight short-term trend more heavily
            momentum = (short_trend * 0.7 + medium_trend * 0.3)
            
            # Normalize to 0-1 scale
            return max(0, min(1, (momentum + 10) / 20))
            
        except Exception:
            return 0.5
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate quality score based on institutional participation."""
        try:
            inst_ratio = metrics.get("current_inst_ratio", 0)
            stability = metrics.get("stability_score", 0)
            
            # Prefer moderate to high institutional participation with stability
            ratio_score = min(1, inst_ratio / 50)  # Scale to 0-1, cap at 50%
            
            return (ratio_score * 0.6 + stability * 0.4)
            
        except Exception:
            return 0.5
    
    def _calculate_activity_score(self, metrics: Dict) -> float:
        """Calculate activity score based on broker engagement."""
        try:
            broker_count = metrics.get("broker_count", 0)
            net_flow = metrics.get("broker_net_flow", 0)
            
            # Score based on broker participation and positive net flow
            count_score = min(1, broker_count / 10)  # Scale to 0-1, cap at 10 brokers
            flow_score = max(0, min(1, (net_flow + 1000) / 2000))  # Scale net flow
            
            return (count_score * 0.6 + flow_score * 0.4)
            
        except Exception:
            return 0.5
    
    def _passes_screening(self, metrics: Dict) -> bool:
        """Determine if stock passes screening criteria."""
        try:
            # Basic filtering criteria
            inst_ratio = metrics.get("current_inst_ratio", 0)
            momentum_score = metrics.get("momentum_score", 0)
            quality_score = metrics.get("quality_score", 0)
            activity_score = metrics.get("activity_score", 0)
            
            # Screening thresholds
            min_inst_ratio = 10  # At least 10% institutional holding
            min_momentum = 0.4   # Above average momentum
            min_quality = 0.3    # Minimum quality threshold
            min_activity = 0.2   # Minimum activity threshold
            
            return (
                inst_ratio >= min_inst_ratio and
                momentum_score >= min_momentum and
                quality_score >= min_quality and
                activity_score >= min_activity
            )
            
        except Exception:
            return False
    
    def _rank_candidates(self, candidates: List[Dict], max_count: int) -> List[Dict]:
        """Rank candidates and return top performers."""
        try:
            # Calculate composite score for ranking
            for candidate in candidates:
                metrics = candidate.get("metrics", {})
                
                momentum = metrics.get("momentum_score", 0)
                quality = metrics.get("quality_score", 0)
                activity = metrics.get("activity_score", 0)
                
                # Weighted composite score
                composite_score = (
                    momentum * 0.4 +    # Momentum is most important
                    quality * 0.35 +    # Quality is important for stability
                    activity * 0.25     # Activity shows market interest
                )
                
                candidate["composite_score"] = composite_score
            
            # Sort by composite score and return top candidates
            ranked_candidates = sorted(candidates, key=lambda x: x.get("composite_score", 0), reverse=True)
            
            return ranked_candidates[:max_count]
            
        except Exception as e:
            self.logger.error(f"Failed to rank candidates: {e}")
            return candidates[:max_count] if candidates else []
    
    def _analyze_candidate(self, candidate: Dict) -> Optional[Dict[str, Any]]:
        """Generate AI analysis for a candidate stock."""
        try:
            stock_info = candidate.get("stock_info", {})
            metrics = candidate.get("metrics", {})
            timeseries = candidate.get("timeseries_data", [])
            broker_activity = candidate.get("broker_activity", {})
            
            # Prepare context for AI analysis
            context = self._prepare_candidate_context(stock_info, metrics, timeseries, broker_activity)
            
            system_prompt = f"""你是一位專業的股票分析師，專精於基於法人持股和券商交易數據的投資分析。
請以繁體中文分析以下股票，提供客觀的投資觀點。

分析重點：
1. 法人持股變化趨勢的意義
2. 券商活動反映的市場關注度
3. 技術面和基本面的綜合評估
4. 潛在風險和機會點

請提供客觀分析，避免明確的買賣建議，改以投資觀點呈現。"""

            user_prompt = f"請分析以下股票的投資價值：\n\n{context}"
            
            messages = [{"role": "user", "content": user_prompt}]
            
            ai_response = self._call_openai(messages, system_prompt)
            
            if ai_response:
                return {
                    "stock_code": stock_info.get("code"),
                    "stock_name": stock_info.get("name"),
                    "market": stock_info.get("market"),
                    "composite_score": candidate.get("composite_score", 0),
                    "key_metrics": {
                        "current_inst_ratio": metrics.get("current_inst_ratio", 0),
                        "momentum_score": metrics.get("momentum_score", 0),
                        "quality_score": metrics.get("quality_score", 0),
                        "activity_score": metrics.get("activity_score", 0),
                        "5d_trend": metrics.get("5d_trend", 0),
                        "broker_interest": metrics.get("broker_interest", 0)
                    },
                    "investment_thesis": self._extract_investment_thesis(ai_response),
                    "risk_factors": self._extract_risk_factors(ai_response),
                    "ai_analysis": ai_response,
                    "recommendation_strength": self._calculate_recommendation_strength(candidate)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to analyze candidate: {e}")
            return None
    
    def _prepare_candidate_context(self, stock_info: Dict, metrics: Dict, timeseries: List, broker_activity: Dict) -> str:
        """Prepare context string for candidate analysis."""
        context = f"【{metrics.get('code')} {metrics.get('name')} 投資分析】\n\n"
        
        context += f"基本資訊：\n"
        context += f"• 市場: {stock_info.get('market', 'N/A')}\n"
        context += f"• 目前法人持股比例: {self._format_percentage(metrics.get('current_inst_ratio', 0))}\n"
        context += f"• 外資持股: {self._format_percentage(metrics.get('foreign_ratio', 0))}\n"
        context += f"• 投信持股: {self._format_percentage(metrics.get('trust_ratio', 0))}\n"
        context += f"• 自營商持股: {self._format_percentage(metrics.get('dealer_ratio', 0))}\n\n"
        
        context += f"趨勢分析：\n"
        context += f"• 5日法人持股變化: {self._format_percentage(metrics.get('5d_trend', 0))}\n"
        context += f"• 20日法人持股變化: {self._format_percentage(metrics.get('20d_trend', 0))}\n"
        context += f"• 持股波動性: {self._format_percentage(metrics.get('volatility', 0))}\n\n"
        
        if broker_activity:
            context += f"券商活動：\n"
            context += f"• 參與券商數: {broker_activity.get('unique_brokers', 0)}\n"
            context += f"• 總交易量: {self._format_number(broker_activity.get('total_volume', 0))} 張\n"
            context += f"• 淨流量: {self._format_number(broker_activity.get('net_flow', 0))} 張\n\n"
        
        context += f"評分指標：\n"
        context += f"• 動能評分: {metrics.get('momentum_score', 0):.2f}\n"
        context += f"• 品質評分: {metrics.get('quality_score', 0):.2f}\n"
        context += f"• 活躍評分: {metrics.get('activity_score', 0):.2f}\n"
        
        return context
    
    def _extract_investment_thesis(self, ai_response: str) -> str:
        """Extract investment thesis from AI response."""
        try:
            lines = ai_response.split('\n')
            thesis_lines = []
            
            # Look for key investment points
            for line in lines:
                line = line.strip()
                if any(keyword in line for keyword in ['投資', '機會', '優勢', '潛力', '看好']):
                    thesis_lines.append(line)
            
            if thesis_lines:
                return ' '.join(thesis_lines[:2])  # Take first 2 relevant lines
            else:
                # Fallback to first few lines
                return ' '.join(lines[:2]) if lines else "投資論點待進一步分析"
            
        except Exception:
            return "投資論點提取失敗"
    
    def _extract_risk_factors(self, ai_response: str) -> List[str]:
        """Extract risk factors from AI response."""
        try:
            lines = ai_response.split('\n')
            risk_factors = []
            
            # Look for risk-related content
            for line in lines:
                line = line.strip()
                if any(keyword in line for keyword in ['風險', '注意', '警示', '謹慎', '不確定']):
                    if line and len(line) > 10:  # Filter out short lines
                        risk_factors.append(line)
            
            return risk_factors[:3]  # Return top 3 risk factors
            
        except Exception:
            return ["風險因子提取失敗"]
    
    def _calculate_recommendation_strength(self, candidate: Dict) -> str:
        """Calculate recommendation strength based on composite score."""
        try:
            score = candidate.get("composite_score", 0)
            
            if score >= 0.8:
                return "強烈關注"
            elif score >= 0.7:
                return "積極關注"
            elif score >= 0.6:
                return "適度關注"
            elif score >= 0.5:
                return "謹慎關注"
            else:
                return "一般關注"
                
        except Exception:
            return "未評級"
    
    def _generate_market_context(self) -> Dict[str, Any]:
        """Generate market context for recommendations."""
        try:
            # Load market sentiment if available
            sentiment_file = os.path.join(self.output_dir, "market_sentiment_analysis.json")
            sentiment_data = self._load_json_data(sentiment_file)
            
            # Load institutional trend analysis if available
            trend_files = [
                os.path.join(self.output_dir, "trend_analysis_20d.json"),
                os.path.join(self.output_dir, "trend_analysis_60d.json")
            ]
            
            trend_data = None
            for file_path in trend_files:
                if os.path.exists(file_path):
                    trend_data = self._load_json_data(file_path)
                    break
            
            context = {
                "market_environment": "中性" if not sentiment_data else sentiment_data.get("sentiment_score", {}).get("label", "中性"),
                "institutional_trend": "平穩" if not trend_data else trend_data.get("ai_insights", {}).get("summary", "平穩"),
                "recommendation_basis": "基於法人持股變化、券商活動和技術指標的綜合分析",
                "time_horizon": "中短期 (1-3個月)",
                "risk_disclaimer": "本分析僅供參考，投資前請自行評估風險"
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to generate market context: {e}")
            return {"context_error": "市場環境分析失敗"}
    
    def _get_screening_criteria(self) -> Dict[str, str]:
        """Get screening criteria used for recommendations."""
        return {
            "minimum_institutional_holding": "10%以上",
            "momentum_requirement": "近期法人持股呈現正向趨勢",
            "quality_threshold": "持股結構穩定",
            "activity_requirement": "有券商關注和交易活動",
            "data_requirement": "至少10個交易日完整數據"
        }
    
    def generate_watchlist(self, focus_area: str = "momentum", max_stocks: int = 10) -> Optional[Dict[str, Any]]:
        """Generate focused watchlist based on specific criteria."""
        if not self.enabled:
            return None
        
        try:
            candidates = self._screen_stock_candidates()
            
            if not candidates:
                return None
            
            # Filter based on focus area
            filtered_candidates = self._filter_by_focus(candidates, focus_area)
            
            # Rank and select
            top_candidates = self._rank_candidates(filtered_candidates, max_stocks)
            
            # Create watchlist
            watchlist = []
            for candidate in top_candidates:
                stock_info = candidate.get("stock_info", {})
                metrics = candidate.get("metrics", {})
                
                watchlist_item = {
                    "code": stock_info.get("code"),
                    "name": stock_info.get("name"),
                    "market": stock_info.get("market"),
                    "focus_score": candidate.get("composite_score", 0),
                    "key_metric": self._get_key_metric_for_focus(metrics, focus_area),
                    "reason": self._get_watchlist_reason(focus_area, metrics)
                }
                watchlist.append(watchlist_item)
            
            result = {
                "watchlist": watchlist,
                "focus_area": focus_area,
                "criteria": self._get_focus_criteria(focus_area),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_screened": len(candidates),
                    "focus_filtered": len(filtered_candidates),
                    "final_selection": len(watchlist)
                }
            }
            
            # Save watchlist
            output_file = os.path.join(self.output_dir, f"watchlist_{focus_area}.json")
            self._save_analysis_result(result, output_file)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate watchlist: {e}")
            return None
    
    def _filter_by_focus(self, candidates: List[Dict], focus_area: str) -> List[Dict]:
        """Filter candidates based on focus area."""
        try:
            if focus_area == "momentum":
                return [c for c in candidates if c.get("metrics", {}).get("momentum_score", 0) > 0.6]
            elif focus_area == "quality":
                return [c for c in candidates if c.get("metrics", {}).get("quality_score", 0) > 0.7]
            elif focus_area == "activity":
                return [c for c in candidates if c.get("metrics", {}).get("activity_score", 0) > 0.5]
            elif focus_area == "growth":
                return [c for c in candidates if c.get("metrics", {}).get("5d_trend", 0) > 1 and c.get("metrics", {}).get("20d_trend", 0) > 0]
            else:
                return candidates
                
        except Exception:
            return candidates
    
    def _get_key_metric_for_focus(self, metrics: Dict, focus_area: str) -> float:
        """Get key metric for specific focus area."""
        if focus_area == "momentum":
            return metrics.get("momentum_score", 0)
        elif focus_area == "quality":
            return metrics.get("quality_score", 0)
        elif focus_area == "activity":
            return metrics.get("activity_score", 0)
        elif focus_area == "growth":
            return metrics.get("5d_trend", 0)
        else:
            return metrics.get("composite_score", 0)
    
    def _get_watchlist_reason(self, focus_area: str, metrics: Dict) -> str:
        """Get reason for inclusion in watchlist."""
        if focus_area == "momentum":
            return f"近期動能強勁 (評分: {metrics.get('momentum_score', 0):.2f})"
        elif focus_area == "quality":
            return f"持股品質穩定 (評分: {metrics.get('quality_score', 0):.2f})"
        elif focus_area == "activity":
            return f"券商活躍關注 (評分: {metrics.get('activity_score', 0):.2f})"
        elif focus_area == "growth":
            return f"法人持股增長 ({self._format_percentage(metrics.get('5d_trend', 0))})"
        else:
            return "綜合指標良好"
    
    def _get_focus_criteria(self, focus_area: str) -> Dict[str, str]:
        """Get criteria for specific focus area."""
        criteria_map = {
            "momentum": {
                "focus": "近期法人持股動能",
                "threshold": "動能評分 > 0.6",
                "timeframe": "5-20個交易日"
            },
            "quality": {
                "focus": "持股結構穩定性",
                "threshold": "品質評分 > 0.7",
                "timeframe": "長期穩定"
            },
            "activity": {
                "focus": "券商交易活躍度",
                "threshold": "活躍評分 > 0.5",
                "timeframe": "近期交易日"
            },
            "growth": {
                "focus": "法人持股成長",
                "threshold": "5日變化 > 1% 且 20日變化 > 0",
                "timeframe": "短中期趨勢"
            }
        }
        
        return criteria_map.get(focus_area, {"focus": "綜合評估", "threshold": "綜合評分", "timeframe": "多時間框架"})