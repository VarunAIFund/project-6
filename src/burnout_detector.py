from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging
from collections import defaultdict

class BurnoutDetector:
    def __init__(self, 
                 burnout_threshold: float = -0.3,
                 consecutive_negative_days: int = 3,
                 engagement_drop_threshold: float = 0.5):
        self.burnout_threshold = burnout_threshold
        self.consecutive_negative_days = consecutive_negative_days
        self.engagement_drop_threshold = engagement_drop_threshold
        self.logger = logging.getLogger(__name__)
    
    def detect_burnout_patterns(self, daily_metrics: Dict[str, Dict], 
                              engagement_trends: Dict[str, Any]) -> Dict[str, Any]:
        burnout_alerts = {}
        
        for channel_name, channel_metrics in daily_metrics.items():
            channel_alerts = self.analyze_channel_burnout(
                channel_name, channel_metrics, engagement_trends.get(channel_name, {})
            )
            
            if channel_alerts['risk_level'] != 'low':
                burnout_alerts[channel_name] = channel_alerts
        
        return burnout_alerts
    
    def analyze_channel_burnout(self, channel_name: str, channel_metrics: Dict, 
                               channel_trends: Dict) -> Dict[str, Any]:
        alerts = {
            'channel': channel_name,
            'risk_level': 'low',
            'risk_score': 0.0,
            'warning_indicators': [],
            'recommendations': [],
            'consecutive_negative_days': 0,
            'sentiment_trend': channel_trends.get('sentiment_trend', 'stable'),
            'engagement_trend': channel_trends.get('engagement_trend', 'stable')
        }
        
        if not channel_metrics:
            return alerts
        
        # Analyze recent sentiment patterns
        recent_days = self.get_recent_days(channel_metrics, 7)
        consecutive_negative = self.count_consecutive_negative_days(recent_days)
        
        alerts['consecutive_negative_days'] = consecutive_negative
        
        # Risk indicators
        risk_score = 0.0
        
        # 1. Consecutive negative sentiment days
        if consecutive_negative >= self.consecutive_negative_days:
            risk_score += 40
            alerts['warning_indicators'].append(
                f"Sustained negative sentiment for {consecutive_negative} consecutive days"
            )
        
        # 2. Sharp sentiment decline
        sentiment_change = channel_trends.get('sentiment_change', 0)
        if sentiment_change < -30:  # 30% decline
            risk_score += 30
            alerts['warning_indicators'].append(
                f"Sharp sentiment decline of {abs(sentiment_change):.1f}%"
            )
        
        # 3. Engagement drop
        engagement_change = channel_trends.get('engagement_change', 0)
        if engagement_change < -50:  # 50% drop
            risk_score += 25
            alerts['warning_indicators'].append(
                f"Significant engagement drop of {abs(engagement_change):.1f}%"
            )
        
        # 4. Very low recent sentiment
        recent_sentiment = channel_trends.get('recent_avg_sentiment', 0)
        if recent_sentiment < self.burnout_threshold:
            risk_score += 20
            alerts['warning_indicators'].append(
                f"Very low average sentiment ({recent_sentiment:.2f})"
            )
        
        # 5. Low message activity
        recent_message_counts = [day['message_count'] for day in recent_days.values()]
        avg_messages = sum(recent_message_counts) / len(recent_message_counts) if recent_message_counts else 0
        if avg_messages < 2:  # Less than 2 messages per day
            risk_score += 15
            alerts['warning_indicators'].append(
                f"Very low messaging activity ({avg_messages:.1f} messages/day)"
            )
        
        # 6. Declining trends
        if channel_trends.get('sentiment_trend') == 'decreasing':
            risk_score += 10
        if channel_trends.get('engagement_trend') == 'decreasing':
            risk_score += 10
        
        alerts['risk_score'] = risk_score
        
        # Determine risk level
        if risk_score >= 70:
            alerts['risk_level'] = 'high'
        elif risk_score >= 40:
            alerts['risk_level'] = 'medium'
        else:
            alerts['risk_level'] = 'low'
        
        # Generate recommendations
        alerts['recommendations'] = self.generate_recommendations(alerts, channel_trends)
        
        return alerts
    
    def get_recent_days(self, channel_metrics: Dict, days: int = 7) -> Dict:
        sorted_dates = sorted(channel_metrics.keys())
        recent_dates = sorted_dates[-days:] if len(sorted_dates) >= days else sorted_dates
        return {date: channel_metrics[date] for date in recent_dates}
    
    def count_consecutive_negative_days(self, recent_days: Dict) -> int:
        if not recent_days:
            return 0
        
        sorted_dates = sorted(recent_days.keys(), reverse=True)  # Most recent first
        consecutive_count = 0
        
        for date in sorted_dates:
            if recent_days[date]['avg_sentiment'] < self.burnout_threshold:
                consecutive_count += 1
            else:
                break
        
        return consecutive_count
    
    def generate_recommendations(self, alerts: Dict, channel_trends: Dict) -> List[str]:
        recommendations = []
        risk_level = alerts['risk_level']
        risk_score = alerts['risk_score']
        
        if risk_level == 'high':
            recommendations.append("🚨 Immediate attention required - schedule team check-in")
            recommendations.append("Consider workload review and redistribution")
            recommendations.append("Implement stress-reduction initiatives")
        
        if risk_level in ['high', 'medium']:
            recommendations.append("Schedule one-on-one meetings with team members")
            recommendations.append("Review recent project demands and deadlines")
            
        if alerts['consecutive_negative_days'] >= 3:
            recommendations.append("Address ongoing concerns causing negative sentiment")
            recommendations.append("Consider team building or morale-boosting activities")
        
        if 'engagement drop' in ' '.join(alerts['warning_indicators']).lower():
            recommendations.append("Investigate causes of reduced team engagement")
            recommendations.append("Consider adjusting meeting schedules or communication methods")
        
        if 'low messaging activity' in ' '.join(alerts['warning_indicators']).lower():
            recommendations.append("Check if team members need additional support or resources")
            recommendations.append("Ensure communication channels are being used effectively")
        
        # Sentiment-specific recommendations
        recent_sentiment = channel_trends.get('recent_avg_sentiment', 0)
        if recent_sentiment < -0.5:
            recommendations.append("Address critical team morale issues immediately")
        elif recent_sentiment < 0:
            recommendations.append("Focus on positive team interactions and recognition")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def get_overall_burnout_assessment(self, burnout_alerts: Dict[str, Any]) -> Dict[str, Any]:
        if not burnout_alerts:
            return {
                'overall_risk_level': 'low',
                'channels_at_risk': 0,
                'high_risk_channels': [],
                'medium_risk_channels': [],
                'total_warnings': 0,
                'summary': "No burnout risks detected across monitored channels."
            }
        
        high_risk_channels = [ch for ch, alert in burnout_alerts.items() if alert['risk_level'] == 'high']
        medium_risk_channels = [ch for ch, alert in burnout_alerts.items() if alert['risk_level'] == 'medium']
        
        total_warnings = sum(len(alert['warning_indicators']) for alert in burnout_alerts.values())
        
        # Determine overall risk
        if high_risk_channels:
            overall_risk = 'high'
        elif len(medium_risk_channels) >= 2:
            overall_risk = 'high'
        elif medium_risk_channels:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        # Generate summary
        if overall_risk == 'high':
            summary = f"⚠️ High burnout risk detected. {len(high_risk_channels)} channels at high risk."
        elif overall_risk == 'medium':
            summary = f"🔶 Moderate burnout risk. {len(medium_risk_channels)} channels need attention."
        else:
            summary = "✅ Low overall burnout risk, but monitor flagged channels."
        
        return {
            'overall_risk_level': overall_risk,
            'channels_at_risk': len(burnout_alerts),
            'high_risk_channels': high_risk_channels,
            'medium_risk_channels': medium_risk_channels,
            'total_warnings': total_warnings,
            'summary': summary,
            'priority_actions': self.get_priority_actions(burnout_alerts)
        }
    
    def get_priority_actions(self, burnout_alerts: Dict[str, Any]) -> List[str]:
        actions = []
        
        # High priority actions for high-risk channels
        high_risk_channels = [ch for ch, alert in burnout_alerts.items() if alert['risk_level'] == 'high']
        if high_risk_channels:
            actions.append(f"Immediately review teams in: {', '.join(high_risk_channels)}")
        
        # Check for specific patterns
        channels_with_consecutive_negative = [
            ch for ch, alert in burnout_alerts.items() 
            if alert['consecutive_negative_days'] >= 3
        ]
        if channels_with_consecutive_negative:
            actions.append(f"Address sustained negativity in: {', '.join(channels_with_consecutive_negative)}")
        
        # Engagement issues
        low_engagement_channels = [
            ch for ch, alert in burnout_alerts.items()
            if any('engagement drop' in warning.lower() for warning in alert['warning_indicators'])
        ]
        if low_engagement_channels:
            actions.append(f"Investigate engagement issues in: {', '.join(low_engagement_channels)}")
        
        return actions[:5]  # Limit to top 5 priority actions