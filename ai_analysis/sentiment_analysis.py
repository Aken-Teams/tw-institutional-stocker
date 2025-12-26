# -*- coding: utf-8 -*-
"""Market sentiment analysis using AI."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from .base import AIAnalysisBase

class MarketSentimentAnalysis(AIAnalysisBase):
    """AI-powered market sentiment analysis based on institutional and broker data."""
    
    def __init__(self):
        super().__init__()
        self.docs_dir = os.path.join("docs", "data")
        self.output_dir = os.path.join(self.docs_dir, "ai_analysis")
        
    def analyze_market_sentiment(self) -> Optional[Dict[str, Any]]:
        """Analyze overall market sentiment from multiple data sources."""
        if not self.enabled:
            return None
        
        # Collect data from multiple sources
        sentiment_data = self._collect_sentiment_data()
        
        if not sentiment_data:
            self.logger.warning("Insufficient data for sentiment analysis")
            return None
        
        # Generate AI insights
        insights = self._generate_sentiment_insights(sentiment_data)
        
        result = {
            "sentiment_data": sentiment_data,
            "ai_insights": insights,
            "sentiment_score": self._calculate_sentiment_score(sentiment_data),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model,
                "analysis_type": "market_sentiment"
            }
        }
        
        # Save results
        output_file = os.path.join(self.output_dir, "market_sentiment_analysis.json")
        self._save_analysis_result(result, output_file)
        
        return result
    
    def _collect_sentiment_data(self) -> Dict[str, Any]:
        """Collect sentiment indicators from various data sources."""
        try:
            sentiment_data = {}
            
            # 1. Institutional holdings sentiment
            inst_sentiment = self._analyze_institutional_sentiment()
            if inst_sentiment:
                sentiment_data["institutional"] = inst_sentiment
            
            # 2. Broker trading sentiment
            broker_sentiment = self._analyze_broker_sentiment()
            if broker_sentiment:
                sentiment_data["broker"] = broker_sentiment
            
            # 3. Market momentum indicators
            momentum_indicators = self._calculate_momentum_indicators()
            if momentum_indicators:
                sentiment_data["momentum"] = momentum_indicators
            
            # 4. Cross-market analysis
            cross_market = self._analyze_cross_market_sentiment()
            if cross_market:
                sentiment_data["cross_market"] = cross_market
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect sentiment data: {e}")
            return {}
    
    def _analyze_institutional_sentiment(self) -> Optional[Dict[str, Any]]:
        """Analyze sentiment from institutional holdings changes."""
        try:
            # Load institutional rankings for different windows
            windows = [5, 20, 60]
            inst_sentiment = {}
            
            for window in windows:
                up_file = os.path.join(self.docs_dir, f"top_three_inst_change_{window}_up.json")
                down_file = os.path.join(self.docs_dir, f"top_three_inst_change_{window}_down.json")
                
                up_data = self._load_json_data(up_file) or []
                down_data = self._load_json_data(down_file) or []
                
                if up_data or down_data:
                    window_sentiment = self._calculate_window_sentiment(up_data, down_data, window)
                    inst_sentiment[f"{window}d"] = window_sentiment
            
            if inst_sentiment:
                # Calculate overall institutional sentiment
                short_term = inst_sentiment.get("5d", {})
                medium_term = inst_sentiment.get("20d", {})
                long_term = inst_sentiment.get("60d", {})
                
                return {
                    "by_timeframe": inst_sentiment,
                    "overall_direction": self._determine_overall_direction(short_term, medium_term, long_term),
                    "strength": self._calculate_sentiment_strength(inst_sentiment),
                    "consistency": self._calculate_consistency(inst_sentiment)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to analyze institutional sentiment: {e}")
            return None
    
    def _calculate_window_sentiment(self, up_data: List[Dict], down_data: List[Dict], window: int) -> Dict[str, Any]:
        """Calculate sentiment for a specific time window."""
        try:
            # Calculate metrics
            avg_gain = sum(stock.get("change", 0) for stock in up_data[:10]) / min(len(up_data), 10) if up_data else 0
            avg_loss = sum(stock.get("change", 0) for stock in down_data[:10]) / min(len(down_data), 10) if down_data else 0
            
            gain_magnitude = sum(abs(stock.get("change", 0)) for stock in up_data[:10])
            loss_magnitude = sum(abs(stock.get("change", 0)) for stock in down_data[:10])
            
            # Sentiment indicators
            momentum_ratio = gain_magnitude / (gain_magnitude + loss_magnitude) if (gain_magnitude + loss_magnitude) > 0 else 0.5
            
            return {
                "avg_gain": avg_gain,
                "avg_loss": avg_loss,
                "gain_magnitude": gain_magnitude,
                "loss_magnitude": loss_magnitude,
                "momentum_ratio": momentum_ratio,
                "sentiment_label": self._classify_sentiment(momentum_ratio, avg_gain, abs(avg_loss))
            }
            
        except Exception:
            return {}
    
    def _classify_sentiment(self, momentum_ratio: float, avg_gain: float, avg_loss: float) -> str:
        """Classify sentiment based on metrics."""
        if momentum_ratio > 0.6 and avg_gain > abs(avg_loss):
            return "強烈樂觀"
        elif momentum_ratio > 0.55:
            return "樂觀"
        elif momentum_ratio < 0.4 and avg_loss > avg_gain:
            return "強烈悲觀"
        elif momentum_ratio < 0.45:
            return "悲觀"
        else:
            return "中性"
    
    def _analyze_broker_sentiment(self) -> Optional[Dict[str, Any]]:
        """Analyze sentiment from broker trading data."""
        try:
            broker_ranking_file = os.path.join(self.docs_dir, "broker_ranking.json")
            broker_trades_file = os.path.join(self.docs_dir, "broker_trades_latest.json")
            
            ranking_data = self._load_json_data(broker_ranking_file) or []
            trades_data = self._load_json_data(broker_trades_file) or []
            
            if not ranking_data and not trades_data:
                return None
            
            # Analyze broker sentiment indicators
            net_flows = []
            if ranking_data:
                net_flows = [broker.get("net_amount", 0) for broker in ranking_data[:20]]
            
            # Calculate trading intensity
            total_volume = 0
            buy_volume = 0
            sell_volume = 0
            
            if trades_data:
                for trade in trades_data:
                    amount = trade.get("amount", 0)
                    total_volume += amount
                    if trade.get("side") == "買":
                        buy_volume += amount
                    else:
                        sell_volume += amount
            
            # Broker sentiment metrics
            positive_brokers = sum(1 for flow in net_flows if flow > 0)
            negative_brokers = sum(1 for flow in net_flows if flow < 0)
            
            return {
                "net_flow_ratio": buy_volume / (buy_volume + sell_volume) if (buy_volume + sell_volume) > 0 else 0.5,
                "positive_broker_ratio": positive_brokers / len(net_flows) if net_flows else 0.5,
                "total_net_flow": sum(net_flows),
                "trading_intensity": total_volume,
                "average_position_size": sum(net_flows) / len(net_flows) if net_flows else 0,
                "sentiment_label": self._classify_broker_sentiment(
                    buy_volume / (buy_volume + sell_volume) if (buy_volume + sell_volume) > 0 else 0.5,
                    positive_brokers / len(net_flows) if net_flows else 0.5
                )
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze broker sentiment: {e}")
            return None
    
    def _classify_broker_sentiment(self, flow_ratio: float, positive_ratio: float) -> str:
        """Classify broker sentiment based on trading metrics."""
        combined_score = (flow_ratio + positive_ratio) / 2
        
        if combined_score > 0.65:
            return "積極樂觀"
        elif combined_score > 0.55:
            return "溫和樂觀"
        elif combined_score < 0.35:
            return "積極悲觀"
        elif combined_score < 0.45:
            return "溫和悲觀"
        else:
            return "中性觀望"
    
    def _calculate_momentum_indicators(self) -> Optional[Dict[str, Any]]:
        """Calculate market momentum indicators."""
        try:
            # Load recent institutional data to calculate momentum
            latest_file = os.path.join(self.docs_dir, "stock_three_inst_latest.json")
            latest_data = self._load_json_data(latest_file) or []
            
            if not latest_data:
                return None
            
            # Calculate various momentum metrics
            foreign_ratios = [stock.get("foreign_ratio", 0) for stock in latest_data]
            trust_ratios = [stock.get("trust_ratio", 0) for stock in latest_data]
            dealer_ratios = [stock.get("dealer_ratio", 0) for stock in latest_data]
            total_ratios = [stock.get("three_inst_ratio", 0) for stock in latest_data]
            
            return {
                "average_foreign_holding": sum(foreign_ratios) / len(foreign_ratios) if foreign_ratios else 0,
                "average_trust_holding": sum(trust_ratios) / len(trust_ratios) if trust_ratios else 0,
                "average_dealer_holding": sum(dealer_ratios) / len(dealer_ratios) if dealer_ratios else 0,
                "average_total_institutional": sum(total_ratios) / len(total_ratios) if total_ratios else 0,
                "high_institutional_stocks": sum(1 for ratio in total_ratios if ratio > 50),
                "low_institutional_stocks": sum(1 for ratio in total_ratios if ratio < 20),
                "market_coverage": len([r for r in total_ratios if r > 0]) / len(total_ratios) if total_ratios else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate momentum indicators: {e}")
            return None
    
    def _analyze_cross_market_sentiment(self) -> Optional[Dict[str, Any]]:
        """Analyze cross-market sentiment (TWSE vs TPEX)."""
        try:
            latest_file = os.path.join(self.docs_dir, "stock_three_inst_latest.json")
            latest_data = self._load_json_data(latest_file) or []
            
            if not latest_data:
                return None
            
            twse_stocks = [stock for stock in latest_data if stock.get("market") == "TWSE"]
            tpex_stocks = [stock for stock in latest_data if stock.get("market") == "TPEX"]
            
            if not twse_stocks or not tpex_stocks:
                return None
            
            # Calculate market-specific metrics
            twse_avg = sum(stock.get("three_inst_ratio", 0) for stock in twse_stocks) / len(twse_stocks)
            tpex_avg = sum(stock.get("three_inst_ratio", 0) for stock in tpex_stocks) / len(tpex_stocks)
            
            return {
                "twse_average_institutional": twse_avg,
                "tpex_average_institutional": tpex_avg,
                "market_preference": "上市" if twse_avg > tpex_avg else "上櫃",
                "cross_market_divergence": abs(twse_avg - tpex_avg),
                "twse_stock_count": len(twse_stocks),
                "tpex_stock_count": len(tpex_stocks)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze cross-market sentiment: {e}")
            return None
    
    def _determine_overall_direction(self, short_term: Dict, medium_term: Dict, long_term: Dict) -> str:
        """Determine overall market direction from different timeframes."""
        try:
            directions = []
            
            for timeframe in [short_term, medium_term, long_term]:
                if timeframe:
                    sentiment = timeframe.get("sentiment_label", "中性")
                    if "樂觀" in sentiment:
                        directions.append(1)
                    elif "悲觀" in sentiment:
                        directions.append(-1)
                    else:
                        directions.append(0)
            
            if not directions:
                return "未明"
            
            avg_direction = sum(directions) / len(directions)
            
            if avg_direction > 0.3:
                return "上升趨勢"
            elif avg_direction < -0.3:
                return "下降趨勢"
            else:
                return "橫盤整理"
                
        except Exception:
            return "未明"
    
    def _calculate_sentiment_strength(self, sentiment_data: Dict) -> str:
        """Calculate the strength of sentiment signals."""
        try:
            strengths = []
            
            for timeframe_data in sentiment_data.values():
                momentum_ratio = timeframe_data.get("momentum_ratio", 0.5)
                deviation = abs(momentum_ratio - 0.5)
                strengths.append(deviation)
            
            if not strengths:
                return "弱"
            
            avg_strength = sum(strengths) / len(strengths)
            
            if avg_strength > 0.2:
                return "強"
            elif avg_strength > 0.1:
                return "中"
            else:
                return "弱"
                
        except Exception:
            return "未知"
    
    def _calculate_consistency(self, sentiment_data: Dict) -> str:
        """Calculate consistency across different timeframes."""
        try:
            sentiments = []
            
            for timeframe_data in sentiment_data.values():
                sentiment = timeframe_data.get("sentiment_label", "中性")
                if "樂觀" in sentiment:
                    sentiments.append(1)
                elif "悲觀" in sentiment:
                    sentiments.append(-1)
                else:
                    sentiments.append(0)
            
            if not sentiments:
                return "低"
            
            # Check if all sentiments are in the same direction
            if len(set(sentiments)) == 1:
                return "高"
            elif len(set(sentiments)) == 2 and 0 not in sentiments:
                return "中"
            else:
                return "低"
                
        except Exception:
            return "未知"
    
    def _calculate_sentiment_score(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall sentiment score from all indicators."""
        try:
            scores = []
            weights = []
            
            # Institutional sentiment (weight: 0.4)
            if "institutional" in sentiment_data:
                inst_data = sentiment_data["institutional"]
                overall_dir = inst_data.get("overall_direction", "橫盤整理")
                
                if "上升" in overall_dir:
                    scores.append(0.7)
                elif "下降" in overall_dir:
                    scores.append(-0.7)
                else:
                    scores.append(0.0)
                weights.append(0.4)
            
            # Broker sentiment (weight: 0.3)
            if "broker" in sentiment_data:
                broker_data = sentiment_data["broker"]
                flow_ratio = broker_data.get("net_flow_ratio", 0.5)
                scores.append((flow_ratio - 0.5) * 2)  # Scale to -1 to 1
                weights.append(0.3)
            
            # Momentum indicators (weight: 0.2)
            if "momentum" in sentiment_data:
                momentum_data = sentiment_data["momentum"]
                coverage = momentum_data.get("market_coverage", 0.5)
                scores.append((coverage - 0.5) * 2)  # Scale to -1 to 1
                weights.append(0.2)
            
            # Cross-market sentiment (weight: 0.1)
            if "cross_market" in sentiment_data:
                cross_data = sentiment_data["cross_market"]
                # Simple score based on preference
                scores.append(0.1)  # Neutral for cross-market
                weights.append(0.1)
            
            if not scores:
                return {"score": 0.0, "label": "中性", "confidence": "低"}
            
            # Calculate weighted average
            total_weight = sum(weights)
            if total_weight > 0:
                weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            else:
                weighted_score = sum(scores) / len(scores)
            
            # Determine label and confidence
            label = self._score_to_label(weighted_score)
            confidence = self._calculate_confidence(scores, weights)
            
            return {
                "score": round(weighted_score, 3),
                "label": label,
                "confidence": confidence,
                "components": {
                    "institutional": scores[0] if len(scores) > 0 else None,
                    "broker": scores[1] if len(scores) > 1 else None,
                    "momentum": scores[2] if len(scores) > 2 else None,
                    "cross_market": scores[3] if len(scores) > 3 else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate sentiment score: {e}")
            return {"score": 0.0, "label": "未知", "confidence": "低"}
    
    def _score_to_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score > 0.5:
            return "強烈樂觀"
        elif score > 0.2:
            return "樂觀"
        elif score > 0.05:
            return "偏樂觀"
        elif score < -0.5:
            return "強烈悲觀"
        elif score < -0.2:
            return "悲觀"
        elif score < -0.05:
            return "偏悲觀"
        else:
            return "中性"
    
    def _calculate_confidence(self, scores: List[float], weights: List[float]) -> str:
        """Calculate confidence level of sentiment analysis."""
        try:
            if len(scores) < 2:
                return "低"
            
            # Check consistency of signals
            positive_count = sum(1 for s in scores if s > 0.1)
            negative_count = sum(1 for s in scores if s < -0.1)
            neutral_count = len(scores) - positive_count - negative_count
            
            total_weight = sum(weights) if weights else len(scores)
            
            if total_weight > 0.8 and (positive_count > len(scores) * 0.7 or negative_count > len(scores) * 0.7):
                return "高"
            elif total_weight > 0.5 and (positive_count > len(scores) * 0.5 or negative_count > len(scores) * 0.5):
                return "中"
            else:
                return "低"
                
        except Exception:
            return "低"
    
    def _generate_sentiment_insights(self, sentiment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI insights for market sentiment."""
        try:
            context = self._prepare_sentiment_context(sentiment_data)
            
            system_prompt = f"""你是一位專業的股市情緒分析師，擅長從法人持股和券商交易數據中解讀市場情緒。
請以繁體中文分析以下市場情緒數據，提供專業見解。

分析重點：
1. 當前市場情緒的主要特徵和強度
2. 不同時間框架下的情緒變化趨勢
3. 法人和券商行為所反映的市場預期
4. 情緒指標的可靠性和風險提醒

請保持客觀分析，避免具體投資建議。"""

            user_prompt = f"請分析以下市場情緒數據：\n\n{context}"
            
            messages = [{"role": "user", "content": user_prompt}]
            
            ai_response = self._call_openai(messages, system_prompt)
            
            if ai_response:
                return {
                    "summary": self._extract_summary(ai_response),
                    "detailed_analysis": ai_response,
                    "risk_assessment": self._assess_sentiment_risks(sentiment_data),
                    "market_outlook": self._generate_market_outlook(sentiment_data)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate sentiment insights: {e}")
            return None
    
    def _prepare_sentiment_context(self, sentiment_data: Dict[str, Any]) -> str:
        """Prepare context string for sentiment analysis."""
        context = "【市場情緒綜合分析】\n\n"
        
        # Institutional sentiment
        if "institutional" in sentiment_data:
            inst_data = sentiment_data["institutional"]
            context += "📊 法人情緒指標：\n"
            context += f"• 整體方向: {inst_data.get('overall_direction', 'N/A')}\n"
            context += f"• 信號強度: {inst_data.get('strength', 'N/A')}\n"
            context += f"• 時間一致性: {inst_data.get('consistency', 'N/A')}\n\n"
        
        # Broker sentiment
        if "broker" in sentiment_data:
            broker_data = sentiment_data["broker"]
            context += "🏢 券商情緒指標：\n"
            context += f"• 資金流向比例: {self._format_percentage(broker_data.get('net_flow_ratio', 0) * 100)}\n"
            context += f"• 正向券商比例: {self._format_percentage(broker_data.get('positive_broker_ratio', 0) * 100)}\n"
            context += f"• 情緒標籤: {broker_data.get('sentiment_label', 'N/A')}\n\n"
        
        # Momentum indicators
        if "momentum" in sentiment_data:
            momentum_data = sentiment_data["momentum"]
            context += "📈 動能指標：\n"
            context += f"• 平均法人持股: {self._format_percentage(momentum_data.get('average_total_institutional', 0))}\n"
            context += f"• 市場覆蓋率: {self._format_percentage(momentum_data.get('market_coverage', 0) * 100)}\n"
            context += f"• 高法人持股股票: {momentum_data.get('high_institutional_stocks', 0)} 檔\n\n"
        
        # Cross-market analysis
        if "cross_market" in sentiment_data:
            cross_data = sentiment_data["cross_market"]
            context += "🔄 跨市場分析：\n"
            context += f"• 上市平均法人持股: {self._format_percentage(cross_data.get('twse_average_institutional', 0))}\n"
            context += f"• 上櫃平均法人持股: {self._format_percentage(cross_data.get('tpex_average_institutional', 0))}\n"
            context += f"• 市場偏好: {cross_data.get('market_preference', 'N/A')}\n\n"
        
        return context
    
    def _assess_sentiment_risks(self, sentiment_data: Dict[str, Any]) -> Dict[str, str]:
        """Assess risks based on sentiment analysis."""
        try:
            risks = {}
            
            # Check for extreme sentiment
            if "institutional" in sentiment_data:
                inst_strength = sentiment_data["institutional"].get("strength", "弱")
                inst_direction = sentiment_data["institutional"].get("overall_direction", "橫盤整理")
                
                if inst_strength == "強" and ("上升" in inst_direction or "下降" in inst_direction):
                    risks["sentiment_extreme"] = "高度情緒化，注意反轉風險"
            
            # Check for inconsistency
            if "institutional" in sentiment_data:
                consistency = sentiment_data["institutional"].get("consistency", "低")
                if consistency == "低":
                    risks["signal_inconsistency"] = "多時間框架信號不一致，方向不明確"
            
            # Check for data quality
            data_sources = len(sentiment_data)
            if data_sources < 2:
                risks["data_insufficient"] = "數據來源不足，分析可靠性降低"
            
            return risks
            
        except Exception:
            return {"analysis_error": "風險評估失敗"}
    
    def _generate_market_outlook(self, sentiment_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate market outlook based on sentiment."""
        try:
            outlook = {}
            
            # Short-term outlook
            if "institutional" in sentiment_data:
                inst_data = sentiment_data["institutional"]
                by_timeframe = inst_data.get("by_timeframe", {})
                
                if "5d" in by_timeframe:
                    short_sentiment = by_timeframe["5d"].get("sentiment_label", "中性")
                    outlook["short_term"] = f"短期({short_sentiment})"
                
                if "20d" in by_timeframe:
                    medium_sentiment = by_timeframe["20d"].get("sentiment_label", "中性")
                    outlook["medium_term"] = f"中期({medium_sentiment})"
                
                if "60d" in by_timeframe:
                    long_sentiment = by_timeframe["60d"].get("sentiment_label", "中性")
                    outlook["long_term"] = f"長期({long_sentiment})"
            
            # Overall trend
            if "institutional" in sentiment_data:
                overall_direction = sentiment_data["institutional"].get("overall_direction", "橫盤整理")
                outlook["trend"] = overall_direction
            
            return outlook
            
        except Exception:
            return {"outlook_error": "展望分析失敗"}