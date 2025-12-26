# -*- coding: utf-8 -*-
"""Anomaly detection for unusual institutional and broker trading patterns."""

import os
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from .base import AIAnalysisBase

class AnomalyDetectionEngine(AIAnalysisBase):
    """AI-powered anomaly detection for unusual market behavior."""
    
    def __init__(self):
        super().__init__()
        self.docs_dir = os.path.join("docs", "data")
        self.timeseries_dir = os.path.join(self.docs_dir, "timeseries")
        self.output_dir = os.path.join(self.docs_dir, "ai_analysis")
        
    def detect_anomalies(self, sensitivity: str = "medium") -> Optional[Dict[str, Any]]:
        """Detect various types of anomalies in the market data."""
        if not self.enabled:
            return None
        
        try:
            # Collect different types of anomalies
            anomalies = {
                "institutional_anomalies": self._detect_institutional_anomalies(sensitivity),
                "broker_anomalies": self._detect_broker_anomalies(sensitivity),
                "volume_anomalies": self._detect_volume_anomalies(sensitivity),
                "pattern_anomalies": self._detect_pattern_anomalies(sensitivity)
            }
            
            # Filter out empty anomaly lists
            anomalies = {k: v for k, v in anomalies.items() if v}
            
            if not any(anomalies.values()):
                self.logger.info("No significant anomalies detected")
                return None
            
            # Generate AI insights for detected anomalies
            insights = self._generate_anomaly_insights(anomalies, sensitivity)
            
            result = {
                "anomalies": anomalies,
                "ai_insights": insights,
                "detection_summary": self._create_detection_summary(anomalies),
                "sensitivity_level": sensitivity,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model_used": self.model,
                    "analysis_type": "anomaly_detection",
                    "total_anomalies": sum(len(v) for v in anomalies.values())
                }
            }
            
            # Save results
            output_file = os.path.join(self.output_dir, "anomaly_detection.json")
            self._save_analysis_result(result, output_file)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to detect anomalies: {e}")
            return None
    
    def _detect_institutional_anomalies(self, sensitivity: str) -> List[Dict[str, Any]]:
        """Detect anomalies in institutional holdings."""
        try:
            anomalies = []
            thresholds = self._get_institutional_thresholds(sensitivity)
            
            # Load institutional rankings for different windows
            for window in [5, 20, 60]:
                up_file = os.path.join(self.docs_dir, f"top_three_inst_change_{window}_up.json")
                down_file = os.path.join(self.docs_dir, f"top_three_inst_change_{window}_down.json")
                
                up_data = self._load_json_data(up_file) or []
                down_data = self._load_json_data(down_file) or []
                
                # Check for extreme changes
                for stock in up_data[:10]:  # Top 10 gainers
                    change = stock.get("change", 0)
                    if abs(change) > thresholds["extreme_change"]:
                        anomaly = {
                            "type": "extreme_institutional_increase",
                            "stock_code": stock.get("code"),
                            "stock_name": stock.get("name"),
                            "market": stock.get("market"),
                            "change": change,
                            "current_ratio": stock.get("three_inst_ratio", 0),
                            "timeframe": f"{window}d",
                            "severity": self._calculate_severity(abs(change), thresholds["extreme_change"], thresholds["critical_change"])
                        }
                        anomalies.append(anomaly)
                
                for stock in down_data[:10]:  # Top 10 decliners
                    change = stock.get("change", 0)
                    if abs(change) > thresholds["extreme_change"]:
                        anomaly = {
                            "type": "extreme_institutional_decrease",
                            "stock_code": stock.get("code"),
                            "stock_name": stock.get("name"),
                            "market": stock.get("market"),
                            "change": change,
                            "current_ratio": stock.get("three_inst_ratio", 0),
                            "timeframe": f"{window}d",
                            "severity": self._calculate_severity(abs(change), thresholds["extreme_change"], thresholds["critical_change"])
                        }
                        anomalies.append(anomaly)
            
            # Detect sudden direction reversals
            reversal_anomalies = self._detect_direction_reversals(thresholds)
            anomalies.extend(reversal_anomalies)
            
            # Detect concentration anomalies
            concentration_anomalies = self._detect_concentration_anomalies(thresholds)
            anomalies.extend(concentration_anomalies)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect institutional anomalies: {e}")
            return []
    
    def _detect_broker_anomalies(self, sensitivity: str) -> List[Dict[str, Any]]:
        """Detect anomalies in broker trading patterns."""
        try:
            anomalies = []
            thresholds = self._get_broker_thresholds(sensitivity)
            
            # Load broker data
            ranking_file = os.path.join(self.docs_dir, "broker_ranking.json")
            trades_file = os.path.join(self.docs_dir, "broker_trades_latest.json")
            
            ranking_data = self._load_json_data(ranking_file) or []
            trades_data = self._load_json_data(trades_file) or []
            
            if not ranking_data and not trades_data:
                return anomalies
            
            # Detect unusual broker positions
            for broker in ranking_data[:20]:  # Top 20 brokers
                net_amount = broker.get("net_amount", 0)
                if abs(net_amount) > thresholds["extreme_position"]:
                    anomaly = {
                        "type": "extreme_broker_position",
                        "broker_name": broker.get("name", "Unknown"),
                        "net_amount": net_amount,
                        "direction": "大量買超" if net_amount > 0 else "大量賣超",
                        "severity": self._calculate_severity(abs(net_amount), thresholds["extreme_position"], thresholds["critical_position"])
                    }
                    anomalies.append(anomaly)
            
            # Detect concentrated trading on specific stocks
            stock_activity = self._analyze_stock_concentration(trades_data, thresholds)
            anomalies.extend(stock_activity)
            
            # Detect unusual broker behavior patterns
            behavior_anomalies = self._detect_broker_behavior_anomalies(trades_data, thresholds)
            anomalies.extend(behavior_anomalies)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect broker anomalies: {e}")
            return []
    
    def _detect_volume_anomalies(self, sensitivity: str) -> List[Dict[str, Any]]:
        """Detect anomalies in trading volume patterns."""
        try:
            anomalies = []
            thresholds = self._get_volume_thresholds(sensitivity)
            
            # Load trades data
            trades_file = os.path.join(self.docs_dir, "broker_trades_latest.json")
            trades_data = self._load_json_data(trades_file) or []
            
            if not trades_data:
                return anomalies
            
            # Analyze volume by stock
            stock_volumes = {}
            for trade in trades_data:
                code = trade.get("code")
                amount = trade.get("amount", 0)
                
                if code not in stock_volumes:
                    stock_volumes[code] = {"total": 0, "trades": 0, "name": trade.get("name", "")}
                
                stock_volumes[code]["total"] += amount
                stock_volumes[code]["trades"] += 1
            
            # Detect unusually high volume
            for code, data in stock_volumes.items():
                if data["total"] > thresholds["extreme_volume"]:
                    anomaly = {
                        "type": "extreme_volume",
                        "stock_code": code,
                        "stock_name": data["name"],
                        "volume": data["total"],
                        "trade_count": data["trades"],
                        "avg_trade_size": data["total"] / data["trades"] if data["trades"] > 0 else 0,
                        "severity": self._calculate_severity(data["total"], thresholds["extreme_volume"], thresholds["critical_volume"])
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect volume anomalies: {e}")
            return []
    
    def _detect_pattern_anomalies(self, sensitivity: str) -> List[Dict[str, Any]]:
        """Detect anomalies in trading patterns."""
        try:
            anomalies = []
            thresholds = self._get_pattern_thresholds(sensitivity)
            
            # Load latest stock data
            latest_file = os.path.join(self.docs_dir, "stock_three_inst_latest.json")
            latest_data = self._load_json_data(latest_file) or []
            
            if not latest_data:
                return anomalies
            
            # Detect unusual institutional distribution patterns
            foreign_ratios = [stock.get("foreign_ratio", 0) for stock in latest_data]
            trust_ratios = [stock.get("trust_ratio", 0) for stock in latest_data]
            dealer_ratios = [stock.get("dealer_ratio", 0) for stock in latest_data]
            
            # Calculate statistical measures
            foreign_stats = self._calculate_stats(foreign_ratios)
            trust_stats = self._calculate_stats(trust_ratios)
            dealer_stats = self._calculate_stats(dealer_ratios)
            
            # Detect statistical anomalies
            if foreign_stats["std"] > thresholds["high_volatility"]:
                anomaly = {
                    "type": "high_foreign_volatility",
                    "description": "外資持股分布異常分散",
                    "std_dev": foreign_stats["std"],
                    "mean": foreign_stats["mean"],
                    "severity": "medium"
                }
                anomalies.append(anomaly)
            
            # Detect unusual correlations
            correlation_anomalies = self._detect_correlation_anomalies(latest_data, thresholds)
            anomalies.extend(correlation_anomalies)
            
            # Detect market structure anomalies
            structure_anomalies = self._detect_market_structure_anomalies(latest_data, thresholds)
            anomalies.extend(structure_anomalies)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect pattern anomalies: {e}")
            return []
    
    def _detect_direction_reversals(self, thresholds: Dict) -> List[Dict[str, Any]]:
        """Detect sudden direction reversals in institutional holdings."""
        try:
            anomalies = []
            
            # Load different timeframe data
            short_term = self._load_json_data(os.path.join(self.docs_dir, "top_three_inst_change_5_up.json")) or []
            medium_term = self._load_json_data(os.path.join(self.docs_dir, "top_three_inst_change_20_up.json")) or []
            
            if not short_term or not medium_term:
                return anomalies
            
            # Create lookup for medium term trends
            medium_lookup = {stock.get("code"): stock.get("change", 0) for stock in medium_term}
            
            # Check for reversals
            for stock in short_term[:20]:  # Top 20 short term gainers
                code = stock.get("code")
                short_change = stock.get("change", 0)
                medium_change = medium_lookup.get(code, 0)
                
                # Check if short term and medium term trends are opposite
                if short_change > 2 and medium_change < -1:  # Strong short-term gain but medium-term loss
                    anomaly = {
                        "type": "trend_reversal",
                        "stock_code": code,
                        "stock_name": stock.get("name"),
                        "short_term_change": short_change,
                        "medium_term_change": medium_change,
                        "reversal_magnitude": abs(short_change - medium_change),
                        "severity": "medium"
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect direction reversals: {e}")
            return []
    
    def _detect_concentration_anomalies(self, thresholds: Dict) -> List[Dict[str, Any]]:
        """Detect unusual concentration in institutional holdings."""
        try:
            anomalies = []
            
            # Load latest data
            latest_file = os.path.join(self.docs_dir, "stock_three_inst_latest.json")
            latest_data = self._load_json_data(latest_file) or []
            
            if not latest_data:
                return anomalies
            
            # Calculate concentration metrics
            total_stocks = len(latest_data)
            high_inst_stocks = [stock for stock in latest_data if stock.get("three_inst_ratio", 0) > 50]
            very_high_inst_stocks = [stock for stock in latest_data if stock.get("three_inst_ratio", 0) > 70]
            
            concentration_ratio = len(high_inst_stocks) / total_stocks if total_stocks > 0 else 0
            
            if concentration_ratio > thresholds["high_concentration"]:
                anomaly = {
                    "type": "high_institutional_concentration",
                    "description": f"法人高度集中持股比例異常: {concentration_ratio:.1%}",
                    "high_concentration_stocks": len(high_inst_stocks),
                    "very_high_concentration_stocks": len(very_high_inst_stocks),
                    "total_stocks": total_stocks,
                    "concentration_ratio": concentration_ratio,
                    "severity": "high" if concentration_ratio > 0.3 else "medium"
                }
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception:
            return []
    
    def _analyze_stock_concentration(self, trades_data: List[Dict], thresholds: Dict) -> List[Dict[str, Any]]:
        """Analyze concentration of broker activity on specific stocks."""
        try:
            anomalies = []
            
            # Count activity by stock
            stock_activity = {}
            total_volume = 0
            
            for trade in trades_data:
                code = trade.get("code")
                amount = trade.get("amount", 0)
                broker = trade.get("broker")
                
                if code not in stock_activity:
                    stock_activity[code] = {
                        "volume": 0,
                        "brokers": set(),
                        "name": trade.get("name", "")
                    }
                
                stock_activity[code]["volume"] += amount
                stock_activity[code]["brokers"].add(broker)
                total_volume += amount
            
            # Check for concentration
            for code, activity in stock_activity.items():
                volume_ratio = activity["volume"] / total_volume if total_volume > 0 else 0
                broker_count = len(activity["brokers"])
                
                if volume_ratio > thresholds["stock_concentration"] and broker_count > 5:
                    anomaly = {
                        "type": "concentrated_stock_activity",
                        "stock_code": code,
                        "stock_name": activity["name"],
                        "volume_ratio": volume_ratio,
                        "broker_count": broker_count,
                        "total_volume": activity["volume"],
                        "severity": "high" if volume_ratio > 0.2 else "medium"
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception:
            return []
    
    def _detect_broker_behavior_anomalies(self, trades_data: List[Dict], thresholds: Dict) -> List[Dict[str, Any]]:
        """Detect unusual broker behavior patterns."""
        try:
            anomalies = []
            
            # Analyze broker behavior
            broker_patterns = {}
            
            for trade in trades_data:
                broker = trade.get("broker")
                side = trade.get("side")
                amount = trade.get("amount", 0)
                
                if broker not in broker_patterns:
                    broker_patterns[broker] = {"buy": 0, "sell": 0, "stocks": set()}
                
                if side == "買":
                    broker_patterns[broker]["buy"] += amount
                elif side == "賣":
                    broker_patterns[broker]["sell"] += amount
                
                broker_patterns[broker]["stocks"].add(trade.get("code"))
            
            # Check for unusual patterns
            for broker, pattern in broker_patterns.items():
                total_volume = pattern["buy"] + pattern["sell"]
                net_ratio = abs(pattern["buy"] - pattern["sell"]) / total_volume if total_volume > 0 else 0
                stock_count = len(pattern["stocks"])
                
                # Detect extreme one-sided trading
                if net_ratio > thresholds["extreme_directional"] and total_volume > thresholds["min_volume_for_anomaly"]:
                    anomaly = {
                        "type": "extreme_directional_trading",
                        "broker_name": broker,
                        "net_ratio": net_ratio,
                        "direction": "極度偏多" if pattern["buy"] > pattern["sell"] else "極度偏空",
                        "total_volume": total_volume,
                        "stock_count": stock_count,
                        "severity": "high" if net_ratio > 0.9 else "medium"
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception:
            return []
    
    def _detect_correlation_anomalies(self, latest_data: List[Dict], thresholds: Dict) -> List[Dict[str, Any]]:
        """Detect unusual correlation patterns."""
        try:
            anomalies = []
            
            if len(latest_data) < 50:  # Need sufficient data
                return anomalies
            
            # Separate by market
            twse_stocks = [s for s in latest_data if s.get("market") == "TWSE"]
            tpex_stocks = [s for s in latest_data if s.get("market") == "TPEX"]
            
            if len(twse_stocks) < 20 or len(tpex_stocks) < 20:
                return anomalies
            
            # Calculate average institutional ratios
            twse_avg = sum(s.get("three_inst_ratio", 0) for s in twse_stocks) / len(twse_stocks)
            tpex_avg = sum(s.get("three_inst_ratio", 0) for s in tpex_stocks) / len(tpex_stocks)
            
            # Check for unusual divergence
            divergence = abs(twse_avg - tpex_avg)
            if divergence > thresholds["market_divergence"]:
                anomaly = {
                    "type": "market_divergence",
                    "description": "上市上櫃法人持股比例異常分歧",
                    "twse_avg": twse_avg,
                    "tpex_avg": tpex_avg,
                    "divergence": divergence,
                    "severity": "medium"
                }
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception:
            return []
    
    def _detect_market_structure_anomalies(self, latest_data: List[Dict], thresholds: Dict) -> List[Dict[str, Any]]:
        """Detect anomalies in market structure."""
        try:
            anomalies = []
            
            # Calculate distribution metrics
            inst_ratios = [stock.get("three_inst_ratio", 0) for stock in latest_data]
            
            if not inst_ratios:
                return anomalies
            
            # Check distribution shape
            zero_holdings = sum(1 for ratio in inst_ratios if ratio < 1)
            high_holdings = sum(1 for ratio in inst_ratios if ratio > 50)
            very_high_holdings = sum(1 for ratio in inst_ratios if ratio > 80)
            
            total_stocks = len(inst_ratios)
            zero_ratio = zero_holdings / total_stocks
            high_ratio = high_holdings / total_stocks
            
            # Detect unusual distributions
            if zero_ratio > thresholds["high_zero_ratio"]:
                anomaly = {
                    "type": "high_zero_institutional_holdings",
                    "description": f"法人零持股股票比例異常高: {zero_ratio:.1%}",
                    "zero_holdings_count": zero_holdings,
                    "total_stocks": total_stocks,
                    "zero_ratio": zero_ratio,
                    "severity": "medium"
                }
                anomalies.append(anomaly)
            
            if high_ratio > thresholds["high_concentration_ratio"]:
                anomaly = {
                    "type": "high_concentration_distribution",
                    "description": f"法人高持股股票比例異常: {high_ratio:.1%}",
                    "high_holdings_count": high_holdings,
                    "very_high_holdings_count": very_high_holdings,
                    "total_stocks": total_stocks,
                    "concentration_ratio": high_ratio,
                    "severity": "medium"
                }
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception:
            return []
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of values."""
        try:
            if not values:
                return {"mean": 0, "std": 0, "min": 0, "max": 0}
            
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std = math.sqrt(variance)
            
            return {
                "mean": mean,
                "std": std,
                "min": min(values),
                "max": max(values)
            }
        except Exception:
            return {"mean": 0, "std": 0, "min": 0, "max": 0}
    
    def _calculate_severity(self, value: float, threshold: float, critical_threshold: float) -> str:
        """Calculate severity level based on value and thresholds."""
        try:
            if value >= critical_threshold:
                return "critical"
            elif value >= threshold * 1.5:
                return "high"
            elif value >= threshold:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"
    
    def _get_institutional_thresholds(self, sensitivity: str) -> Dict[str, float]:
        """Get thresholds for institutional anomaly detection."""
        base_thresholds = {
            "extreme_change": 10.0,      # 10% change in holdings
            "critical_change": 20.0,     # 20% critical threshold
            "high_concentration": 0.25,  # 25% of stocks with high institutional holdings
            "trend_reversal": 5.0        # 5% reversal threshold
        }
        
        multipliers = {
            "low": 1.5,
            "medium": 1.0,
            "high": 0.7
        }
        
        multiplier = multipliers.get(sensitivity, 1.0)
        return {k: v * multiplier for k, v in base_thresholds.items()}
    
    def _get_broker_thresholds(self, sensitivity: str) -> Dict[str, float]:
        """Get thresholds for broker anomaly detection."""
        base_thresholds = {
            "extreme_position": 50000,        # 50K shares net position
            "critical_position": 100000,      # 100K shares critical
            "stock_concentration": 0.15,      # 15% of total volume in one stock
            "extreme_directional": 0.8,       # 80% directional bias
            "min_volume_for_anomaly": 10000   # Minimum volume to flag anomaly
        }
        
        multipliers = {
            "low": 1.5,
            "medium": 1.0,
            "high": 0.7
        }
        
        multiplier = multipliers.get(sensitivity, 1.0)
        return {k: v * multiplier for k, v in base_thresholds.items()}
    
    def _get_volume_thresholds(self, sensitivity: str) -> Dict[str, float]:
        """Get thresholds for volume anomaly detection."""
        base_thresholds = {
            "extreme_volume": 100000,    # 100K shares volume
            "critical_volume": 200000    # 200K shares critical
        }
        
        multipliers = {
            "low": 1.5,
            "medium": 1.0,
            "high": 0.7
        }
        
        multiplier = multipliers.get(sensitivity, 1.0)
        return {k: v * multiplier for k, v in base_thresholds.items()}
    
    def _get_pattern_thresholds(self, sensitivity: str) -> Dict[str, float]:
        """Get thresholds for pattern anomaly detection."""
        base_thresholds = {
            "high_volatility": 15.0,            # High standard deviation
            "market_divergence": 10.0,          # Market divergence threshold
            "high_zero_ratio": 0.3,             # 30% zero holdings
            "high_concentration_ratio": 0.2     # 20% high concentration
        }
        
        multipliers = {
            "low": 1.3,
            "medium": 1.0,
            "high": 0.8
        }
        
        multiplier = multipliers.get(sensitivity, 1.0)
        return {k: v * multiplier for k, v in base_thresholds.items()}
    
    def _create_detection_summary(self, anomalies: Dict[str, List]) -> Dict[str, Any]:
        """Create summary of detected anomalies."""
        try:
            total_anomalies = sum(len(v) for v in anomalies.values())
            
            summary = {
                "total_anomalies": total_anomalies,
                "by_category": {},
                "severity_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "top_concerns": []
            }
            
            # Count by category
            for category, anomaly_list in anomalies.items():
                summary["by_category"][category] = len(anomaly_list)
            
            # Count by severity and collect top concerns
            all_anomalies = []
            for anomaly_list in anomalies.values():
                all_anomalies.extend(anomaly_list)
            
            for anomaly in all_anomalies:
                severity = anomaly.get("severity", "medium")
                summary["severity_distribution"][severity] += 1
                
                # Collect critical and high severity as top concerns
                if severity in ["critical", "high"]:
                    concern = {
                        "type": anomaly.get("type"),
                        "description": self._generate_anomaly_description(anomaly),
                        "severity": severity
                    }
                    summary["top_concerns"].append(concern)
            
            # Limit top concerns to 5
            summary["top_concerns"] = summary["top_concerns"][:5]
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to create detection summary: {e}")
            return {"error": "摘要生成失敗"}
    
    def _generate_anomaly_description(self, anomaly: Dict) -> str:
        """Generate description for an anomaly."""
        anomaly_type = anomaly.get("type", "")
        
        if "extreme_institutional" in anomaly_type:
            stock_name = anomaly.get("stock_name", anomaly.get("stock_code", ""))
            change = anomaly.get("change", 0)
            direction = "增加" if "increase" in anomaly_type else "減少"
            return f"{stock_name} 法人持股{direction} {abs(change):.1f}%"
        
        elif "extreme_broker_position" in anomaly_type:
            broker = anomaly.get("broker_name", "某券商")
            direction = anomaly.get("direction", "")
            return f"{broker} {direction}"
        
        elif "extreme_volume" in anomaly_type:
            stock_name = anomaly.get("stock_name", anomaly.get("stock_code", ""))
            volume = anomaly.get("volume", 0)
            return f"{stock_name} 交易量異常 ({self._format_number(volume)}張)"
        
        else:
            return anomaly.get("description", f"異常類型: {anomaly_type}")
    
    def _generate_anomaly_insights(self, anomalies: Dict[str, List], sensitivity: str) -> Optional[Dict[str, Any]]:
        """Generate AI insights for detected anomalies."""
        try:
            # Prepare context for AI analysis
            context = self._prepare_anomaly_context(anomalies, sensitivity)
            
            system_prompt = f"""你是一位專業的金融異常行為分析師，專精於識別和解釋台股市場的異常交易模式。
請以繁體中文分析以下異常檢測結果，提供專業見解。

分析重點：
1. 異常行為的可能原因和背景
2. 異常程度的嚴重性評估
3. 對市場可能產生的影響
4. 投資人應該注意的風險和機會

請保持客觀分析，避免恐慌性解讀。"""

            user_prompt = f"請分析以下市場異常檢測結果：\n\n{context}"
            
            messages = [{"role": "user", "content": user_prompt}]
            
            ai_response = self._call_openai(messages, system_prompt)
            
            if ai_response:
                return {
                    "summary": self._extract_summary(ai_response),
                    "detailed_analysis": ai_response,
                    "risk_assessment": self._assess_anomaly_risks(anomalies),
                    "recommendations": self._generate_anomaly_recommendations(anomalies)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate anomaly insights: {e}")
            return None
    
    def _prepare_anomaly_context(self, anomalies: Dict[str, List], sensitivity: str) -> str:
        """Prepare context string for anomaly analysis."""
        context = f"【異常檢測分析報告】\n"
        context += f"檢測敏感度: {sensitivity}\n\n"
        
        total_anomalies = sum(len(v) for v in anomalies.values())
        context += f"總計檢測到 {total_anomalies} 項異常\n\n"
        
        for category, anomaly_list in anomalies.items():
            if not anomaly_list:
                continue
                
            category_names = {
                "institutional_anomalies": "法人持股異常",
                "broker_anomalies": "券商交易異常", 
                "volume_anomalies": "成交量異常",
                "pattern_anomalies": "模式異常"
            }
            
            context += f"📊 {category_names.get(category, category)} ({len(anomaly_list)}項):\n"
            
            # Show top 3 anomalies in each category
            for i, anomaly in enumerate(anomaly_list[:3], 1):
                description = self._generate_anomaly_description(anomaly)
                severity = anomaly.get("severity", "medium")
                context += f"{i}. {description} (嚴重度: {severity})\n"
            
            if len(anomaly_list) > 3:
                context += f"...及其他 {len(anomaly_list) - 3} 項異常\n"
            
            context += "\n"
        
        return context
    
    def _assess_anomaly_risks(self, anomalies: Dict[str, List]) -> Dict[str, str]:
        """Assess risks based on detected anomalies."""
        try:
            risks = {}
            
            # Count severe anomalies
            critical_count = 0
            high_count = 0
            
            for anomaly_list in anomalies.values():
                for anomaly in anomaly_list:
                    severity = anomaly.get("severity", "medium")
                    if severity == "critical":
                        critical_count += 1
                    elif severity == "high":
                        high_count += 1
            
            # Overall risk level
            if critical_count > 0:
                risks["overall_risk"] = "高風險：發現重大異常，建議密切關注"
            elif high_count > 3:
                risks["overall_risk"] = "中高風險：多項高度異常，建議謹慎操作"
            elif high_count > 0:
                risks["overall_risk"] = "中等風險：發現異常行為，建議持續監控"
            else:
                risks["overall_risk"] = "低風險：異常程度可控"
            
            # Specific risk factors
            if "institutional_anomalies" in anomalies and anomalies["institutional_anomalies"]:
                risks["institutional_risk"] = "法人大幅調整持股，可能影響股價穩定性"
            
            if "broker_anomalies" in anomalies and anomalies["broker_anomalies"]:
                risks["liquidity_risk"] = "券商異常活動，可能影響市場流動性"
            
            if "volume_anomalies" in anomalies and anomalies["volume_anomalies"]:
                risks["volatility_risk"] = "異常交易量，市場波動性可能增加"
            
            return risks
            
        except Exception:
            return {"assessment_error": "風險評估失敗"}
    
    def _generate_anomaly_recommendations(self, anomalies: Dict[str, List]) -> List[str]:
        """Generate recommendations based on detected anomalies."""
        try:
            recommendations = []
            
            # General recommendations based on anomaly types
            if any(anomalies.values()):
                recommendations.append("密切監控異常股票的後續發展")
                recommendations.append("關注法人和券商的持續行為變化")
            
            if "institutional_anomalies" in anomalies and anomalies["institutional_anomalies"]:
                recommendations.append("留意法人大幅調整持股的原因和影響")
                
            if "broker_anomalies" in anomalies and anomalies["broker_anomalies"]:
                recommendations.append("觀察主力券商的交易意圖和策略")
            
            if "volume_anomalies" in anomalies and anomalies["volume_anomalies"]:
                recommendations.append("注意異常交易量股票的基本面變化")
            
            # Risk management
            recommendations.append("分散投資，避免過度集中於異常標的")
            recommendations.append("設定適當的停損點，控制風險")
            
            return recommendations
            
        except Exception:
            return ["建議尋求專業投資諮詢"]