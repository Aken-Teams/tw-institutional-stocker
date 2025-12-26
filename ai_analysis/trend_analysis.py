# -*- coding: utf-8 -*-
"""Institutional holdings trend analysis using AI."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from .base import AIAnalysisBase

class InstitutionalTrendAnalysis(AIAnalysisBase):
    """AI-powered analysis of institutional holdings trends."""
    
    def __init__(self):
        super().__init__()
        self.docs_dir = os.path.join("docs", "data")
        self.timeseries_dir = os.path.join(self.docs_dir, "timeseries")
        self.output_dir = os.path.join(self.docs_dir, "ai_analysis")
        
    def analyze_top_changes(self, window: int = 20, top_n: int = 10) -> Optional[Dict[str, Any]]:
        """Analyze top institutional holdings changes with AI insights."""
        if not self.enabled:
            return None
            
        # Load ranking data
        up_file = os.path.join(self.docs_dir, f"top_three_inst_change_{window}_up.json")
        down_file = os.path.join(self.docs_dir, f"top_three_inst_change_{window}_down.json")
        
        up_data = self._load_json_data(up_file) or []
        down_data = self._load_json_data(down_file) or []
        
        if not up_data and not down_data:
            self.logger.warning("No ranking data available for trend analysis")
            return None
        
        # Prepare data for AI analysis
        analysis_data = {
            "top_gainers": up_data[:top_n],
            "top_decliners": down_data[:top_n],
            "window_days": window,
            "analysis_date": datetime.now().isoformat()
        }
        
        # Generate AI insights
        insights = self._generate_trend_insights(analysis_data)
        
        result = {
            **analysis_data,
            "ai_insights": insights,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model,
                "analysis_type": "institutional_trend"
            }
        }
        
        # Save results
        output_file = os.path.join(self.output_dir, f"trend_analysis_{window}d.json")
        self._save_analysis_result(result, output_file)
        
        return result
    
    def _generate_trend_insights(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI insights for trend analysis."""
        try:
            # Prepare context for AI
            gainers = data["top_gainers"][:5]  # Top 5 for context
            decliners = data["top_decliners"][:5]
            window = data["window_days"]
            
            context = self._prepare_trend_context(gainers, decliners, window)
            
            system_prompt = f"""你是一位專業的台股分析師，專精於三大法人（外資、投信、自營商）持股分析。
請以繁體中文分析以下數據，提供專業且易懂的見解。

分析重點：
1. 法人持股變化的主要趨勢和模式
2. 特定產業或個股的法人偏好
3. 可能的市場影響因素
4. 投資人應該注意的風險和機會

請保持客觀分析，避免具體投資建議。"""

            user_prompt = f"請分析以下{window}日法人持股變化數據：\n\n{context}"
            
            messages = [{"role": "user", "content": user_prompt}]
            
            ai_response = self._call_openai(messages, system_prompt)
            
            if ai_response:
                return {
                    "summary": self._extract_summary(ai_response),
                    "detailed_analysis": ai_response,
                    "key_trends": self._extract_key_trends(gainers, decliners),
                    "sector_analysis": self._analyze_sectors(gainers, decliners)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate trend insights: {e}")
            return None
    
    def _prepare_trend_context(self, gainers: List[Dict], decliners: List[Dict], window: int) -> str:
        """Prepare context string for AI analysis."""
        context = f"【{window}日法人持股變化分析】\n\n"
        
        context += "📈 持股增加最多的前5檔：\n"
        for i, stock in enumerate(gainers, 1):
            context += f"{i}. {stock['code']} {stock['name']} "
            context += f"({stock['market']}) "
            context += f"持股比例: {self._format_percentage(stock['three_inst_ratio'])} "
            context += f"變化: +{self._format_percentage(stock['change'])}\n"
        
        context += "\n📉 持股減少最多的前5檔：\n"
        for i, stock in enumerate(decliners, 1):
            context += f"{i}. {stock['code']} {stock['name']} "
            context += f"({stock['market']}) "
            context += f"持股比例: {self._format_percentage(stock['three_inst_ratio'])} "
            context += f"變化: {self._format_percentage(stock['change'])}\n"
        
        return context
    
    def _extract_summary(self, ai_response: str) -> str:
        """Extract key summary from AI response."""
        lines = ai_response.split('\n')
        summary_lines = []
        
        for line in lines[:3]:  # First 3 lines as summary
            line = line.strip()
            if line and not line.startswith('#'):
                summary_lines.append(line)
        
        return ' '.join(summary_lines) if summary_lines else ai_response[:200] + "..."
    
    def _extract_key_trends(self, gainers: List[Dict], decliners: List[Dict]) -> Dict[str, Any]:
        """Extract key statistical trends."""
        try:
            gainer_changes = [stock['change'] for stock in gainers]
            decliner_changes = [stock['change'] for stock in decliners]
            
            return {
                "avg_gainer_change": sum(gainer_changes) / len(gainer_changes) if gainer_changes else 0,
                "avg_decliner_change": sum(decliner_changes) / len(decliner_changes) if decliner_changes else 0,
                "max_gain": max(gainer_changes) if gainer_changes else 0,
                "max_decline": min(decliner_changes) if decliner_changes else 0,
                "gainer_count": len(gainers),
                "decliner_count": len(decliners)
            }
        except Exception:
            return {}
    
    def _analyze_sectors(self, gainers: List[Dict], decliners: List[Dict]) -> Dict[str, Any]:
        """Analyze sector distribution (simplified)."""
        try:
            # Simplified sector analysis based on stock codes
            tech_codes = ['23', '24', '31', '36']  # Common tech sector prefixes
            finance_codes = ['28']  # Finance sector
            
            gainer_sectors = self._categorize_stocks(gainers, tech_codes, finance_codes)
            decliner_sectors = self._categorize_stocks(decliners, tech_codes, finance_codes)
            
            return {
                "gainers_by_sector": gainer_sectors,
                "decliners_by_sector": decliner_sectors
            }
        except Exception:
            return {}
    
    def _categorize_stocks(self, stocks: List[Dict], tech_codes: List[str], finance_codes: List[str]) -> Dict[str, int]:
        """Categorize stocks by sector based on code prefixes."""
        sectors = {"科技": 0, "金融": 0, "其他": 0}
        
        for stock in stocks:
            code = stock.get('code', '')
            if any(code.startswith(prefix) for prefix in tech_codes):
                sectors["科技"] += 1
            elif any(code.startswith(prefix) for prefix in finance_codes):
                sectors["金融"] += 1
            else:
                sectors["其他"] += 1
        
        return sectors
    
    def analyze_individual_stock(self, stock_code: str, days_back: int = 60) -> Optional[Dict[str, Any]]:
        """Analyze individual stock's institutional holdings trend."""
        if not self.enabled:
            return None
        
        # Load individual stock data
        stock_file = os.path.join(self.timeseries_dir, f"{stock_code}.json")
        stock_data = self._load_json_data(stock_file)
        
        if not stock_data:
            self.logger.warning(f"No data found for stock {stock_code}")
            return None
        
        # Get recent data
        recent_data = stock_data[-days_back:] if len(stock_data) > days_back else stock_data
        
        # Generate AI analysis
        insights = self._generate_individual_insights(stock_code, recent_data)
        
        result = {
            "stock_code": stock_code,
            "stock_name": recent_data[-1].get("name", "") if recent_data else "",
            "analysis_period_days": len(recent_data),
            "current_holdings": {
                "foreign_ratio": recent_data[-1].get("foreign_ratio", 0),
                "trust_ratio": recent_data[-1].get("trust_ratio", 0), 
                "dealer_ratio": recent_data[-1].get("dealer_ratio", 0),
                "total_ratio": recent_data[-1].get("three_inst_ratio", 0)
            } if recent_data else {},
            "ai_insights": insights,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model,
                "analysis_type": "individual_stock_trend"
            }
        }
        
        # Save results
        output_file = os.path.join(self.output_dir, f"individual_analysis_{stock_code}.json")
        self._save_analysis_result(result, output_file)
        
        return result
    
    def _generate_individual_insights(self, stock_code: str, data: List[Dict]) -> Optional[Dict[str, Any]]:
        """Generate AI insights for individual stock."""
        try:
            if not data:
                return None
            
            stock_name = data[-1].get("name", stock_code)
            
            # Prepare trend data
            context = self._prepare_individual_context(stock_code, stock_name, data)
            
            system_prompt = f"""你是一位專業的台股分析師，請分析個股的三大法人持股趨勢。
請以繁體中文提供客觀分析，重點包括：

1. 法人持股的變化趨勢
2. 各法人（外資、投信、自營商）的行為模式
3. 持股變化的可能原因
4. 值得關注的趨勢變化

請保持客觀分析，避免具體投資建議。"""

            user_prompt = f"請分析以下個股法人持股趨勢：\n\n{context}"
            
            messages = [{"role": "user", "content": user_prompt}]
            
            ai_response = self._call_openai(messages, system_prompt)
            
            if ai_response:
                return {
                    "summary": self._extract_summary(ai_response),
                    "detailed_analysis": ai_response,
                    "trend_metrics": self._calculate_trend_metrics(data)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate individual stock insights: {e}")
            return None
    
    def _prepare_individual_context(self, code: str, name: str, data: List[Dict]) -> str:
        """Prepare context for individual stock analysis."""
        if not data:
            return ""
        
        recent = data[-1]
        context = f"【{code} {name} 法人持股分析】\n\n"
        
        context += f"目前持股狀況（{recent.get('date', 'N/A')}）：\n"
        context += f"• 外資持股比例: {self._format_percentage(recent.get('foreign_ratio', 0))}\n"
        context += f"• 投信持股比例: {self._format_percentage(recent.get('trust_ratio', 0))}\n"
        context += f"• 自營商持股比例: {self._format_percentage(recent.get('dealer_ratio', 0))}\n"
        context += f"• 三大法人合計: {self._format_percentage(recent.get('three_inst_ratio', 0))}\n\n"
        
        if len(data) >= 2:
            prev = data[-2]
            context += f"與前一交易日比較：\n"
            context += f"• 外資變化: {self._format_percentage(recent.get('foreign_ratio', 0) - prev.get('foreign_ratio', 0))}\n"
            context += f"• 投信變化: {self._format_percentage(recent.get('trust_ratio', 0) - prev.get('trust_ratio', 0))}\n"
            context += f"• 自營商變化: {self._format_percentage(recent.get('dealer_ratio', 0) - prev.get('dealer_ratio', 0))}\n"
        
        if len(data) >= 5:
            context += f"\n近5日趨勢（最高/最低）：\n"
            recent_5 = data[-5:]
            foreign_values = [d.get('foreign_ratio', 0) for d in recent_5]
            trust_values = [d.get('trust_ratio', 0) for d in recent_5]
            dealer_values = [d.get('dealer_ratio', 0) for d in recent_5]
            
            context += f"• 外資: {self._format_percentage(min(foreign_values))} ~ {self._format_percentage(max(foreign_values))}\n"
            context += f"• 投信: {self._format_percentage(min(trust_values))} ~ {self._format_percentage(max(trust_values))}\n"
            context += f"• 自營商: {self._format_percentage(min(dealer_values))} ~ {self._format_percentage(max(dealer_values))}\n"
        
        return context
    
    def _calculate_trend_metrics(self, data: List[Dict]) -> Dict[str, Any]:
        """Calculate trend metrics for the stock."""
        try:
            if len(data) < 2:
                return {}
            
            # Calculate various trend metrics
            foreign_trend = [d.get('foreign_ratio', 0) for d in data[-10:]]  # Last 10 days
            trust_trend = [d.get('trust_ratio', 0) for d in data[-10:]]
            dealer_trend = [d.get('dealer_ratio', 0) for d in data[-10:]]
            
            return {
                "foreign_trend_direction": "上升" if foreign_trend[-1] > foreign_trend[0] else "下降",
                "trust_trend_direction": "上升" if trust_trend[-1] > trust_trend[0] else "下降", 
                "dealer_trend_direction": "上升" if dealer_trend[-1] > dealer_trend[0] else "下降",
                "foreign_volatility": max(foreign_trend) - min(foreign_trend),
                "trust_volatility": max(trust_trend) - min(trust_trend),
                "dealer_volatility": max(dealer_trend) - min(dealer_trend),
                "data_points": len(data)
            }
        except Exception:
            return {}