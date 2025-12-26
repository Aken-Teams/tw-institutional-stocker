# -*- coding: utf-8 -*-
"""Broker behavior pattern analysis using AI."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from .base import AIAnalysisBase

class BrokerPatternAnalysis(AIAnalysisBase):
    """AI-powered analysis of broker trading patterns."""
    
    def __init__(self):
        super().__init__()
        self.docs_dir = os.path.join("docs", "data")
        self.output_dir = os.path.join(self.docs_dir, "ai_analysis")
        
    def analyze_broker_patterns(self, top_n: int = 15) -> Optional[Dict[str, Any]]:
        """Analyze broker trading patterns and identify key players."""
        if not self.enabled:
            return None
        
        # Load broker data
        ranking_file = os.path.join(self.docs_dir, "broker_ranking.json")
        trends_file = os.path.join(self.docs_dir, "broker_trends.json")
        latest_trades_file = os.path.join(self.docs_dir, "broker_trades_latest.json")
        
        ranking_data = self._load_json_data(ranking_file) or []
        trends_data = self._load_json_data(trends_file) or {}
        latest_trades = self._load_json_data(latest_trades_file) or []
        
        if not ranking_data and not latest_trades:
            self.logger.warning("No broker data available for analysis")
            return None
        
        # Prepare analysis data
        analysis_data = {
            "top_brokers": ranking_data[:top_n],
            "trading_patterns": self._extract_trading_patterns(latest_trades),
            "market_activity": self._analyze_market_activity(latest_trades),
            "broker_trends": trends_data,
            "analysis_date": datetime.now().isoformat()
        }
        
        # Generate AI insights
        insights = self._generate_broker_insights(analysis_data)
        
        result = {
            **analysis_data,
            "ai_insights": insights,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model,
                "analysis_type": "broker_pattern"
            }
        }
        
        # Save results
        output_file = os.path.join(self.output_dir, "broker_pattern_analysis.json")
        self._save_analysis_result(result, output_file)
        
        return result
    
    def _extract_trading_patterns(self, trades: List[Dict]) -> Dict[str, Any]:
        """Extract trading patterns from broker trades data."""
        try:
            if not trades:
                return {}
            
            # Group by broker
            broker_stats = {}
            stock_activity = {}
            
            for trade in trades:
                broker = trade.get("broker", "Unknown")
                stock = trade.get("code", "Unknown")
                side = trade.get("side", "Unknown")
                amount = trade.get("amount", 0)
                
                # Broker statistics
                if broker not in broker_stats:
                    broker_stats[broker] = {"buy": 0, "sell": 0, "net": 0, "stocks": set()}
                
                if side.lower() == "買":
                    broker_stats[broker]["buy"] += amount
                elif side.lower() == "賣":
                    broker_stats[broker]["sell"] += amount
                
                broker_stats[broker]["net"] = broker_stats[broker]["buy"] - broker_stats[broker]["sell"]
                broker_stats[broker]["stocks"].add(stock)
                
                # Stock activity
                if stock not in stock_activity:
                    stock_activity[stock] = {"brokers": set(), "total_volume": 0}
                
                stock_activity[stock]["brokers"].add(broker)
                stock_activity[stock]["total_volume"] += abs(amount)
            
            # Convert sets to counts for JSON serialization
            for broker in broker_stats:
                broker_stats[broker]["unique_stocks"] = len(broker_stats[broker]["stocks"])
                del broker_stats[broker]["stocks"]
            
            for stock in stock_activity:
                stock_activity[stock]["broker_count"] = len(stock_activity[stock]["brokers"])
                del stock_activity[stock]["brokers"]
            
            # Find most active stocks and brokers
            top_stocks = sorted(stock_activity.items(), 
                              key=lambda x: x[1]["total_volume"], reverse=True)[:10]
            top_brokers = sorted(broker_stats.items(),
                               key=lambda x: abs(x[1]["net"]), reverse=True)[:10]
            
            return {
                "total_trades": len(trades),
                "unique_brokers": len(broker_stats),
                "unique_stocks": len(stock_activity),
                "top_active_stocks": [{"code": k, **v} for k, v in top_stocks],
                "top_active_brokers": [{"broker": k, **v} for k, v in top_brokers],
                "market_sentiment": self._calculate_market_sentiment(broker_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract trading patterns: {e}")
            return {}
    
    def _analyze_market_activity(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analyze overall market activity from broker data."""
        try:
            if not trades:
                return {}
            
            total_buy = sum(trade.get("amount", 0) for trade in trades if trade.get("side") == "買")
            total_sell = sum(trade.get("amount", 0) for trade in trades if trade.get("side") == "賣")
            
            buy_trades = [trade for trade in trades if trade.get("side") == "買"]
            sell_trades = [trade for trade in trades if trade.get("side") == "賣"]
            
            return {
                "total_buy_amount": total_buy,
                "total_sell_amount": total_sell,
                "net_flow": total_buy - total_sell,
                "buy_trade_count": len(buy_trades),
                "sell_trade_count": len(sell_trades),
                "avg_buy_size": total_buy / len(buy_trades) if buy_trades else 0,
                "avg_sell_size": total_sell / len(sell_trades) if sell_trades else 0,
                "market_balance": "買盤強勢" if total_buy > total_sell else "賣盤強勢" if total_sell > total_buy else "均衡"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze market activity: {e}")
            return {}
    
    def _calculate_market_sentiment(self, broker_stats: Dict[str, Dict]) -> str:
        """Calculate market sentiment based on broker net positions."""
        try:
            net_positions = [stats["net"] for stats in broker_stats.values()]
            positive_count = sum(1 for net in net_positions if net > 0)
            negative_count = sum(1 for net in net_positions if net < 0)
            
            if positive_count > negative_count * 1.5:
                return "樂觀"
            elif negative_count > positive_count * 1.5:
                return "謹慎"
            else:
                return "中性"
                
        except Exception:
            return "未知"
    
    def _generate_broker_insights(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI insights for broker pattern analysis."""
        try:
            top_brokers = data.get("top_brokers", [])[:5]
            patterns = data.get("trading_patterns", {})
            activity = data.get("market_activity", {})
            
            context = self._prepare_broker_context(top_brokers, patterns, activity)
            
            system_prompt = f"""你是一位專業的台股券商分點分析師，專精於分析主力券商的交易行為和市場動向。
請以繁體中文分析以下券商交易數據，提供專業見解。

分析重點：
1. 主力券商的交易行為模式
2. 市場資金流向和集中度
3. 特定股票的券商關注度
4. 可能的市場影響和趨勢

請保持客觀分析，避免具體投資建議。"""

            user_prompt = f"請分析以下券商交易模式數據：\n\n{context}"
            
            messages = [{"role": "user", "content": user_prompt}]
            
            ai_response = self._call_openai(messages, system_prompt)
            
            if ai_response:
                return {
                    "summary": self._extract_summary(ai_response),
                    "detailed_analysis": ai_response,
                    "key_findings": self._extract_key_findings(patterns, activity),
                    "market_indicators": self._extract_market_indicators(data)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate broker insights: {e}")
            return None
    
    def _prepare_broker_context(self, top_brokers: List[Dict], patterns: Dict, activity: Dict) -> str:
        """Prepare context string for broker analysis."""
        context = "【券商分點交易分析】\n\n"
        
        if top_brokers:
            context += "🏢 主力券商排名（依淨買超）：\n"
            for i, broker in enumerate(top_brokers[:5], 1):
                net_amount = broker.get("net_amount", 0)
                context += f"{i}. {broker.get('name', 'Unknown')} "
                context += f"淨額: {self._format_number(net_amount)} 張\n"
        
        if patterns:
            context += f"\n📊 交易概況：\n"
            context += f"• 總交易筆數: {patterns.get('total_trades', 0):,}\n"
            context += f"• 參與券商數: {patterns.get('unique_brokers', 0)}\n"
            context += f"• 涉及股票數: {patterns.get('unique_stocks', 0)}\n"
            context += f"• 市場情緒: {patterns.get('market_sentiment', 'N/A')}\n"
        
        if activity:
            net_flow = activity.get("net_flow", 0)
            market_balance = activity.get("market_balance", "未知")
            context += f"\n💰 資金流向：\n"
            context += f"• 整體淨流量: {self._format_number(net_flow)} 張\n"
            context += f"• 市場狀況: {market_balance}\n"
            context += f"• 平均買單大小: {self._format_number(activity.get('avg_buy_size', 0))} 張\n"
            context += f"• 平均賣單大小: {self._format_number(activity.get('avg_sell_size', 0))} 張\n"
        
        if patterns and patterns.get("top_active_stocks"):
            context += "\n🔥 最活躍股票：\n"
            for i, stock in enumerate(patterns["top_active_stocks"][:3], 1):
                context += f"{i}. {stock['code']} "
                context += f"(券商數: {stock.get('broker_count', 0)}, "
                context += f"總量: {self._format_number(stock.get('total_volume', 0))} 張)\n"
        
        return context
    
    def _extract_key_findings(self, patterns: Dict, activity: Dict) -> Dict[str, Any]:
        """Extract key findings from broker analysis."""
        try:
            findings = {}
            
            if patterns:
                findings["concentration"] = "高" if patterns.get("unique_stocks", 0) < 20 else "中" if patterns.get("unique_stocks", 0) < 50 else "低"
                findings["broker_participation"] = "活躍" if patterns.get("unique_brokers", 0) > 100 else "一般"
                findings["market_sentiment"] = patterns.get("market_sentiment", "未知")
            
            if activity:
                net_flow = activity.get("net_flow", 0)
                findings["fund_flow_direction"] = "流入" if net_flow > 0 else "流出" if net_flow < 0 else "平衡"
                findings["trading_intensity"] = "高" if activity.get("total_buy_amount", 0) + activity.get("total_sell_amount", 0) > 1000000 else "一般"
            
            return findings
            
        except Exception:
            return {}
    
    def _extract_market_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract market indicators from broker data."""
        try:
            patterns = data.get("trading_patterns", {})
            activity = data.get("market_activity", {})
            
            indicators = {}
            
            # Calculate concentration index
            if patterns.get("top_active_brokers"):
                top_3_volume = sum(abs(broker.get("net", 0)) for broker in patterns["top_active_brokers"][:3])
                total_volume = sum(abs(broker.get("net", 0)) for broker in patterns["top_active_brokers"])
                indicators["concentration_ratio"] = (top_3_volume / total_volume * 100) if total_volume > 0 else 0
            
            # Market momentum
            if activity:
                total_buy = activity.get("total_buy_amount", 0)
                total_sell = activity.get("total_sell_amount", 0)
                if total_buy + total_sell > 0:
                    indicators["buy_pressure_ratio"] = total_buy / (total_buy + total_sell) * 100
                
                indicators["net_flow_magnitude"] = abs(activity.get("net_flow", 0))
            
            return indicators
            
        except Exception:
            return {}
    
    def analyze_individual_broker(self, broker_name: str) -> Optional[Dict[str, Any]]:
        """Analyze individual broker's trading pattern."""
        if not self.enabled:
            return None
        
        # Load broker data
        latest_trades_file = os.path.join(self.docs_dir, "broker_trades_latest.json")
        trends_file = os.path.join(self.docs_dir, "broker_trends.json")
        
        latest_trades = self._load_json_data(latest_trades_file) or []
        trends_data = self._load_json_data(trends_file) or {}
        
        # Filter trades for specific broker
        broker_trades = [trade for trade in latest_trades if trade.get("broker") == broker_name]
        
        if not broker_trades:
            self.logger.warning(f"No trades found for broker: {broker_name}")
            return None
        
        # Analyze broker's activity
        analysis_data = self._analyze_single_broker(broker_name, broker_trades, trends_data)
        
        # Generate AI insights
        insights = self._generate_individual_broker_insights(broker_name, analysis_data)
        
        result = {
            "broker_name": broker_name,
            "analysis_data": analysis_data,
            "ai_insights": insights,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model,
                "analysis_type": "individual_broker"
            }
        }
        
        # Save results
        safe_name = broker_name.replace("/", "_").replace("\\", "_")
        output_file = os.path.join(self.output_dir, f"broker_analysis_{safe_name}.json")
        self._save_analysis_result(result, output_file)
        
        return result
    
    def _analyze_single_broker(self, broker_name: str, trades: List[Dict], trends: Dict) -> Dict[str, Any]:
        """Analyze single broker's trading behavior."""
        try:
            buy_trades = [t for t in trades if t.get("side") == "買"]
            sell_trades = [t for t in trades if t.get("side") == "賣"]
            
            total_buy = sum(t.get("amount", 0) for t in buy_trades)
            total_sell = sum(t.get("amount", 0) for t in sell_trades)
            
            # Stock preferences
            stock_activity = {}
            for trade in trades:
                stock = trade.get("code")
                if stock not in stock_activity:
                    stock_activity[stock] = {"buy": 0, "sell": 0, "net": 0}
                
                amount = trade.get("amount", 0)
                if trade.get("side") == "買":
                    stock_activity[stock]["buy"] += amount
                else:
                    stock_activity[stock]["sell"] += amount
                
                stock_activity[stock]["net"] = stock_activity[stock]["buy"] - stock_activity[stock]["sell"]
            
            top_positions = sorted(stock_activity.items(), 
                                 key=lambda x: abs(x[1]["net"]), reverse=True)[:10]
            
            return {
                "total_buy_amount": total_buy,
                "total_sell_amount": total_sell,
                "net_position": total_buy - total_sell,
                "buy_trade_count": len(buy_trades),
                "sell_trade_count": len(sell_trades),
                "total_stocks": len(stock_activity),
                "top_positions": [{"stock": k, **v} for k, v in top_positions],
                "trading_style": self._determine_trading_style(total_buy, total_sell, len(stock_activity)),
                "avg_trade_size": (total_buy + total_sell) / len(trades) if trades else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze single broker: {e}")
            return {}
    
    def _determine_trading_style(self, total_buy: float, total_sell: float, stock_count: int) -> str:
        """Determine broker's trading style based on activity."""
        net_ratio = abs((total_buy - total_sell) / (total_buy + total_sell)) if (total_buy + total_sell) > 0 else 0
        
        if net_ratio > 0.7:
            return "單邊操作" + ("偏多" if total_buy > total_sell else "偏空")
        elif stock_count > 20:
            return "分散投資"
        elif stock_count < 5:
            return "集中投資"
        else:
            return "平衡操作"
    
    def _generate_individual_broker_insights(self, broker_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI insights for individual broker."""
        try:
            context = self._prepare_individual_broker_context(broker_name, data)
            
            system_prompt = f"""你是一位專業的券商分析師，請分析特定券商的交易行為模式。
請以繁體中文提供客觀分析，重點包括：

1. 券商的交易風格和策略特點
2. 主要操作的股票類型和偏好
3. 資金配置和風險管理特徵
4. 在市場中的角色和影響力

請保持客觀分析，避免具體投資建議。"""

            user_prompt = f"請分析以下券商的交易行為：\n\n{context}"
            
            messages = [{"role": "user", "content": user_prompt}]
            
            ai_response = self._call_openai(messages, system_prompt)
            
            if ai_response:
                return {
                    "summary": self._extract_summary(ai_response),
                    "detailed_analysis": ai_response,
                    "trading_characteristics": self._extract_trading_characteristics(data)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate individual broker insights: {e}")
            return None
    
    def _prepare_individual_broker_context(self, broker_name: str, data: Dict[str, Any]) -> str:
        """Prepare context for individual broker analysis."""
        context = f"【{broker_name} 券商分析】\n\n"
        
        context += f"交易概況：\n"
        context += f"• 買入金額: {self._format_number(data.get('total_buy_amount', 0))} 張\n"
        context += f"• 賣出金額: {self._format_number(data.get('total_sell_amount', 0))} 張\n"
        context += f"• 淨部位: {self._format_number(data.get('net_position', 0))} 張\n"
        context += f"• 交易股票數: {data.get('total_stocks', 0)}\n"
        context += f"• 交易風格: {data.get('trading_style', 'N/A')}\n"
        context += f"• 平均交易規模: {self._format_number(data.get('avg_trade_size', 0))} 張\n\n"
        
        top_positions = data.get("top_positions", [])
        if top_positions:
            context += "主要持倉（前5檔）：\n"
            for i, pos in enumerate(top_positions[:5], 1):
                context += f"{i}. {pos['stock']} "
                context += f"淨額: {self._format_number(pos.get('net', 0))} 張 "
                context += f"(買: {self._format_number(pos.get('buy', 0))}, "
                context += f"賣: {self._format_number(pos.get('sell', 0))})\n"
        
        return context
    
    def _extract_trading_characteristics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trading characteristics from broker data."""
        try:
            net_pos = data.get("net_position", 0)
            total_volume = data.get("total_buy_amount", 0) + data.get("total_sell_amount", 0)
            stock_count = data.get("total_stocks", 0)
            
            return {
                "direction_bias": "做多" if net_pos > 0 else "做空" if net_pos < 0 else "中性",
                "position_size": "大額" if total_volume > 100000 else "中額" if total_volume > 10000 else "小額",
                "diversification": "高度分散" if stock_count > 30 else "適度分散" if stock_count > 10 else "集中",
                "net_exposure_ratio": abs(net_pos) / total_volume if total_volume > 0 else 0,
                "trading_frequency": "高頻" if data.get("buy_trade_count", 0) + data.get("sell_trade_count", 0) > 50 else "一般"
            }
        except Exception:
            return {}