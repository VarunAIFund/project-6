import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from pathlib import Path

class ReportGenerator:
    def __init__(self, reports_dir: str = "./reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def generate_weekly_report(self, 
                             daily_metrics: Dict[str, Dict],
                             engagement_trends: Dict[str, Any],
                             burnout_alerts: Dict[str, Any],
                             activity_patterns: Dict[str, Any],
                             engagement_summary: Dict[str, Any]) -> Dict[str, Any]:
        
        report_date = datetime.now()
        week_start = report_date - timedelta(days=14)
        
        report = {
            'report_metadata': {
                'generated_at': report_date.isoformat(),
                'report_period': {
                    'start': week_start.strftime('%Y-%m-%d'),
                    'end': report_date.strftime('%Y-%m-%d'),
                    'days_analyzed': 7
                },
                'channels_monitored': list(daily_metrics.keys())
            },
            'executive_summary': self.generate_executive_summary(
                engagement_summary, engagement_trends, burnout_alerts
            ),
            'sentiment_analysis': self.generate_sentiment_analysis(daily_metrics, engagement_trends),
            'engagement_metrics': self.generate_engagement_metrics(daily_metrics, engagement_trends),
            'activity_patterns': activity_patterns,
            'burnout_assessment': burnout_alerts,
            'recommendations': self.generate_recommendations(burnout_alerts, engagement_trends),
            'detailed_channel_metrics': self.format_channel_details(daily_metrics, engagement_trends)
        }
        
        return report
    
    def generate_executive_summary(self, engagement_summary: Dict, 
                                 engagement_trends: Dict, burnout_alerts: Dict) -> Dict[str, Any]:
        
        # Calculate key metrics
        total_channels = engagement_summary.get('total_channels_monitored', 0)
        total_messages = engagement_summary.get('total_messages_analyzed', 0)
        overall_sentiment = engagement_summary.get('overall_avg_sentiment', 0.0)
        overall_engagement = engagement_summary.get('overall_avg_engagement', 0.0)
        
        # Sentiment classification
        if overall_sentiment >= 0.3:
            sentiment_description = "very positive"
        elif overall_sentiment >= 0.1:
            sentiment_description = "positive"
        elif overall_sentiment >= -0.1:
            sentiment_description = "neutral"
        elif overall_sentiment >= -0.3:
            sentiment_description = "negative"
        else:
            sentiment_description = "very negative"
        
        # Engagement classification
        if overall_engagement >= 0.7:
            engagement_description = "high"
        elif overall_engagement >= 0.4:
            engagement_description = "moderate"
        else:
            engagement_description = "low"
        
        # Key insights
        insights = []
        
        # Sentiment insights
        sentiment_dist = engagement_summary.get('sentiment_distribution', {})
        positive_pct = sentiment_dist.get('positive', 0)
        negative_pct = sentiment_dist.get('negative', 0)
        
        if positive_pct > 60:
            insights.append(f"✅ Strong team positivity: {positive_pct}% of interactions are positive")
        elif negative_pct > 30:
            insights.append(f"⚠️ Concerning negativity: {negative_pct}% of interactions are negative")
        
        # Trend insights
        positive_trends = sum(1 for trend in engagement_trends.values() 
                            if trend.get('sentiment_trend') == 'increasing')
        negative_trends = sum(1 for trend in engagement_trends.values() 
                            if trend.get('sentiment_trend') == 'decreasing')
        
        if positive_trends > negative_trends:
            insights.append(f"📈 Improving sentiment in {positive_trends} channels")
        elif negative_trends > positive_trends:
            insights.append(f"📉 Declining sentiment in {negative_trends} channels")
        
        # Burnout insights
        if burnout_alerts:
            high_risk = sum(1 for alert in burnout_alerts.values() 
                          if alert.get('risk_level') == 'high')
            if high_risk > 0:
                insights.append(f"🚨 {high_risk} channels showing high burnout risk")
            else:
                insights.append(f"🔶 {len(burnout_alerts)} channels need attention")
        else:
            insights.append("✅ No burnout risks detected")
        
        return {
            'key_metrics': {
                'channels_monitored': total_channels,
                'total_messages': total_messages,
                'overall_sentiment_score': round(overall_sentiment, 3),
                'overall_engagement_score': round(overall_engagement, 3)
            },
            'sentiment_summary': f"Team sentiment is {sentiment_description} (score: {overall_sentiment:.2f})",
            'engagement_summary': f"Team engagement is {engagement_description} (score: {overall_engagement:.2f})",
            'key_insights': insights,
            'weekly_highlights': self.extract_weekly_highlights(engagement_trends, burnout_alerts)
        }
    
    def extract_weekly_highlights(self, engagement_trends: Dict, burnout_alerts: Dict) -> List[str]:
        highlights = []
        
        # Best performing channel
        if engagement_trends:
            best_channel = max(engagement_trends.keys(), 
                             key=lambda ch: engagement_trends[ch].get('recent_avg_sentiment', 0))
            best_sentiment = engagement_trends[best_channel].get('recent_avg_sentiment', 0)
            if best_sentiment > 0.2:
                highlights.append(f"🏆 Most positive channel: {best_channel} (sentiment: {best_sentiment:.2f})")
        
        # Biggest improvement
        improving_channels = [(ch, data.get('sentiment_change', 0)) 
                            for ch, data in engagement_trends.items() 
                            if data.get('sentiment_change', 0) > 20]
        if improving_channels:
            best_improvement = max(improving_channels, key=lambda x: x[1])
            highlights.append(f"📈 Biggest improvement: {best_improvement[0]} (+{best_improvement[1]:.1f}%)")
        
        # Most concerning
        if burnout_alerts:
            high_risk_channels = [ch for ch, alert in burnout_alerts.items() 
                                if alert.get('risk_level') == 'high']
            if high_risk_channels:
                highlights.append(f"⚠️ Needs immediate attention: {', '.join(high_risk_channels)}")
        
        return highlights
    
    def generate_sentiment_analysis(self, daily_metrics: Dict, engagement_trends: Dict) -> Dict[str, Any]:
        channel_sentiments = {}
        
        for channel_name, channel_metrics in daily_metrics.items():
            if not channel_metrics:
                continue
            
            dates = sorted(channel_metrics.keys())
            daily_sentiments = [channel_metrics[date]['avg_sentiment'] for date in dates]
            
            channel_sentiments[channel_name] = {
                'daily_scores': dict(zip(dates, daily_sentiments)),
                'weekly_average': sum(daily_sentiments) / len(daily_sentiments) if daily_sentiments else 0,
                'trend': engagement_trends.get(channel_name, {}).get('sentiment_trend', 'stable'),
                'trend_change': engagement_trends.get(channel_name, {}).get('sentiment_change', 0),
                'best_day': dates[daily_sentiments.index(max(daily_sentiments))] if daily_sentiments else None,
                'worst_day': dates[daily_sentiments.index(min(daily_sentiments))] if daily_sentiments else None
            }
        
        return {
            'by_channel': channel_sentiments,
            'weekly_patterns': self.analyze_weekly_sentiment_patterns(daily_metrics)
        }
    
    def analyze_weekly_sentiment_patterns(self, daily_metrics: Dict) -> Dict[str, Any]:
        day_sentiments = {
            'Monday': [], 'Tuesday': [], 'Wednesday': [], 
            'Thursday': [], 'Friday': [], 'Saturday': [], 'Sunday': []
        }
        
        for channel_metrics in daily_metrics.values():
            for date_str, metrics in channel_metrics.items():
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    day_name = date_obj.strftime('%A')
                    day_sentiments[day_name].append(metrics['avg_sentiment'])
                except:
                    continue
        
        day_averages = {}
        for day, sentiments in day_sentiments.items():
            day_averages[day] = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        best_day = max(day_averages.keys(), key=lambda d: day_averages[d]) if day_averages else None
        worst_day = min(day_averages.keys(), key=lambda d: day_averages[d]) if day_averages else None
        
        return {
            'daily_averages': day_averages,
            'best_day_of_week': best_day,
            'worst_day_of_week': worst_day,
            'monday_blues_confirmed': day_averages.get('Monday', 0) < -0.1,
            'friday_energy': day_averages.get('Friday', 0) > 0.2
        }
    
    def generate_engagement_metrics(self, daily_metrics: Dict, engagement_trends: Dict) -> Dict[str, Any]:
        channel_engagement = {}
        
        for channel_name, channel_metrics in daily_metrics.items():
            if not channel_metrics:
                continue
            
            total_messages = sum(m['message_count'] for m in channel_metrics.values())
            total_reactions = sum(m['reaction_count'] for m in channel_metrics.values())
            total_emojis = sum(m['emoji_count'] for m in channel_metrics.values())
            
            avg_engagement = sum(m['engagement_score'] for m in channel_metrics.values()) / len(channel_metrics)
            
            channel_engagement[channel_name] = {
                'total_messages': total_messages,
                'total_reactions': total_reactions,
                'total_emojis': total_emojis,
                'average_engagement_score': round(avg_engagement, 3),
                'trend': engagement_trends.get(channel_name, {}).get('engagement_trend', 'stable'),
                'messages_per_day': round(total_messages / 7, 1)
            }
        
        return {
            'by_channel': channel_engagement,
            'engagement_ranking': sorted(channel_engagement.keys(), 
                                       key=lambda ch: channel_engagement[ch]['average_engagement_score'], 
                                       reverse=True)
        }
    
    def generate_recommendations(self, burnout_alerts: Dict, engagement_trends: Dict) -> List[str]:
        recommendations = []
        
        # High priority burnout recommendations
        high_risk_channels = [ch for ch, alert in burnout_alerts.items() 
                            if alert.get('risk_level') == 'high']
        
        if high_risk_channels:
            recommendations.extend([
                f"🚨 Schedule immediate team check-ins for: {', '.join(high_risk_channels)}",
                "Review workload distribution and project deadlines",
                "Consider implementing stress-reduction initiatives"
            ])
        
        # Medium risk recommendations
        medium_risk_channels = [ch for ch, alert in burnout_alerts.items() 
                              if alert.get('risk_level') == 'medium']
        
        if medium_risk_channels:
            recommendations.append(
                f"📋 Schedule one-on-one meetings with teams in: {', '.join(medium_risk_channels)}"
            )
        
        # Trend-based recommendations
        declining_channels = [ch for ch, trend in engagement_trends.items() 
                            if trend.get('sentiment_trend') == 'decreasing']
        
        if declining_channels:
            recommendations.append(
                f"📉 Monitor declining sentiment in: {', '.join(declining_channels)}"
            )
        
        # General recommendations
        if not burnout_alerts:
            recommendations.extend([
                "✅ Continue current practices - no major concerns detected",
                "💡 Consider team recognition programs to maintain positive momentum"
            ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def format_channel_details(self, daily_metrics: Dict, engagement_trends: Dict) -> Dict[str, Any]:
        detailed_metrics = {}
        
        for channel_name, channel_metrics in daily_metrics.items():
            if not channel_metrics:
                continue
            
            dates = sorted(channel_metrics.keys())
            
            detailed_metrics[channel_name] = {
                'daily_breakdown': channel_metrics,
                'summary_stats': {
                    'total_days_analyzed': len(dates),
                    'avg_daily_messages': sum(m['message_count'] for m in channel_metrics.values()) / len(channel_metrics),
                    'avg_daily_sentiment': sum(m['avg_sentiment'] for m in channel_metrics.values()) / len(channel_metrics),
                    'avg_engagement_score': sum(m['engagement_score'] for m in channel_metrics.values()) / len(channel_metrics),
                    'total_emoji_usage': sum(m['emoji_count'] for m in channel_metrics.values()),
                    'total_reactions': sum(m['reaction_count'] for m in channel_metrics.values())
                },
                'trends': engagement_trends.get(channel_name, {})
            }
        
        return detailed_metrics
    
    def save_report(self, report: Dict[str, Any], format_type: str = 'json') -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            filename = f"engagement_report_{timestamp}.json"
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        elif format_type == 'csv':
            filename = f"engagement_summary_{timestamp}.csv"
            filepath = self.reports_dir / filename
            
            self.save_csv_summary(report, filepath)
        
        elif format_type == 'html':
            filename = f"engagement_dashboard_{timestamp}.html"
            filepath = self.reports_dir / filename
            
            self.save_html_dashboard(report, filepath)
        
        self.logger.info(f"Report saved: {filepath}")
        return str(filepath)
    
    def save_csv_summary(self, report: Dict[str, Any], filepath: Path):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Channel', 'Avg_Sentiment', 'Avg_Engagement', 
                           'Total_Messages', 'Sentiment_Trend', 'Risk_Level'])
            
            # Write channel data
            for channel, details in report.get('detailed_channel_metrics', {}).items():
                burnout_info = report.get('burnout_assessment', {}).get(channel, {})
                
                writer.writerow([
                    channel,
                    round(details['summary_stats']['avg_daily_sentiment'], 3),
                    round(details['summary_stats']['avg_engagement_score'], 3),
                    int(details['summary_stats']['avg_daily_messages'] * 7),  # Weekly total
                    details['trends'].get('sentiment_trend', 'stable'),
                    burnout_info.get('risk_level', 'low')
                ])
    
    def save_html_dashboard(self, report: Dict[str, Any], filepath: Path):
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Team Engagement Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 8px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 5px; min-width: 200px; }}
        .alert-high {{ background: #e74c3c; color: white; }}
        .alert-medium {{ background: #f39c12; color: white; }}
        .alert-low {{ background: #27ae60; color: white; }}
        .channel-details {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .insights {{ background: #3498db; color: white; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .recommendations {{ background: #9b59b6; color: white; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Team Engagement Dashboard</h1>
        <p>Generated: {generated_at}</p>
        <p>Period: {start_date} to {end_date}</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        {executive_summary}
    </div>
    
    <div class="insights">
        <h2>Key Insights</h2>
        {insights}
    </div>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
        {recommendations}
    </div>
    
    <div>
        <h2>Channel Details</h2>
        {channel_details}
    </div>
</body>
</html>"""
        
        # Format data for HTML
        metadata = report['report_metadata']
        summary = report['executive_summary']
        
        executive_html = f"""
        <div class="metric">
            <strong>Channels Monitored:</strong> {summary['key_metrics']['channels_monitored']}
        </div>
        <div class="metric">
            <strong>Total Messages:</strong> {summary['key_metrics']['total_messages']}
        </div>
        <div class="metric">
            <strong>Overall Sentiment:</strong> {summary['key_metrics']['overall_sentiment_score']}
        </div>
        <div class="metric">
            <strong>Overall Engagement:</strong> {summary['key_metrics']['overall_engagement_score']}
        </div>
        """
        
        insights_html = "<ul>" + "".join([f"<li>{insight}</li>" for insight in summary['key_insights']]) + "</ul>"
        recommendations_html = "<ul>" + "".join([f"<li>{rec}</li>" for rec in report['recommendations']]) + "</ul>"
        
        channel_details_html = ""
        for channel, details in report['detailed_channel_metrics'].items():
            risk_level = report.get('burnout_assessment', {}).get(channel, {}).get('risk_level', 'low')
            alert_class = f"alert-{risk_level}"
            
            channel_details_html += f"""
            <div class="channel-details {alert_class}">
                <h3>{channel}</h3>
                <p><strong>Average Sentiment:</strong> {details['summary_stats']['avg_daily_sentiment']:.3f}</p>
                <p><strong>Average Engagement:</strong> {details['summary_stats']['avg_engagement_score']:.3f}</p>
                <p><strong>Daily Messages:</strong> {details['summary_stats']['avg_daily_messages']:.1f}</p>
                <p><strong>Risk Level:</strong> {risk_level.upper()}</p>
            </div>
            """
        
        # Fill template
        html_content = html_template.format(
            generated_at=metadata['generated_at'],
            start_date=metadata['report_period']['start'],
            end_date=metadata['report_period']['end'],
            executive_summary=executive_html,
            insights=insights_html,
            recommendations=recommendations_html,
            channel_details=channel_details_html
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)