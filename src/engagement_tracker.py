from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import pandas as pd
import logging
from collections import defaultdict, Counter

class EngagementTracker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_timestamp_info(self, timestamp: str) -> Dict[str, Any]:
        dt = datetime.fromtimestamp(float(timestamp))
        return {
            'datetime': dt,
            'date': dt.date(),
            'hour': dt.hour,
            'day_of_week': dt.weekday(),  # 0=Monday, 6=Sunday
            'day_name': dt.strftime('%A')
        }
    
    def calculate_daily_metrics(self, channel_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict]:
        daily_metrics = defaultdict(lambda: defaultdict(dict))
        
        for channel_name, messages in channel_data.items():
            channel_daily_data = defaultdict(lambda: {
                'message_count': 0,
                'sentiment_scores': [],
                'emoji_counts': 0,
                'reaction_counts': 0,
                'active_hours': set(),
                'response_times': [],
                'thread_messages': 0
            })
            
            for message in messages:
                ts_info = self.extract_timestamp_info(message['ts'])
                date_str = ts_info['date'].strftime('%Y-%m-%d')
                
                # Count messages
                channel_daily_data[date_str]['message_count'] += 1
                
                # Track active hours
                channel_daily_data[date_str]['active_hours'].add(ts_info['hour'])
                
                # Sentiment (if analyzed)
                if 'sentiment' in message:
                    channel_daily_data[date_str]['sentiment_scores'].append(
                        message['sentiment']['overall_sentiment']
                    )
                    channel_daily_data[date_str]['emoji_counts'] += message['sentiment']['emoji_count']
                
                # Reactions
                if 'reactions' in message and message['reactions']:
                    total_reactions = sum(r.get('count', 0) for r in message['reactions'])
                    channel_daily_data[date_str]['reaction_counts'] += total_reactions
                
                # Thread tracking
                if message.get('thread_ts') and message.get('thread_ts') != message.get('ts'):
                    channel_daily_data[date_str]['thread_messages'] += 1
            
            # Calculate averages and final metrics
            for date_str, data in channel_daily_data.items():
                sentiment_scores = data['sentiment_scores']
                daily_metrics[channel_name][date_str] = {
                    'message_count': data['message_count'],
                    'avg_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0,
                    'sentiment_std': pd.Series(sentiment_scores).std() if len(sentiment_scores) > 1 else 0.0,
                    'emoji_count': data['emoji_counts'],
                    'reaction_count': data['reaction_counts'],
                    'active_hours_count': len(data['active_hours']),
                    'active_hours': sorted(list(data['active_hours'])),
                    'thread_participation': data['thread_messages'] / max(data['message_count'], 1),
                    'engagement_score': self.calculate_engagement_score(
                        data['message_count'], 
                        data['reaction_counts'], 
                        data['emoji_counts'],
                        len(data['active_hours'])
                    )
                }
        
        return dict(daily_metrics)
    
    def calculate_engagement_score(self, message_count: int, reaction_count: int, 
                                 emoji_count: int, active_hours: int) -> float:
        # Normalize components
        msg_score = min(message_count / 20, 1.0)  # Cap at 20 messages
        reaction_score = min(reaction_count / 10, 1.0)  # Cap at 10 reactions
        emoji_score = min(emoji_count / 15, 1.0)  # Cap at 15 emojis
        hours_score = active_hours / 24  # Hours spread throughout day
        
        # Weighted combination
        engagement = (
            0.4 * msg_score + 
            0.3 * reaction_score + 
            0.2 * emoji_score + 
            0.1 * hours_score
        )
        
        return round(engagement, 3)
    
    def analyze_peak_activity_patterns(self, channel_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        hourly_activity = defaultdict(int)
        daily_activity = defaultdict(int)
        
        for channel_name, messages in channel_data.items():
            for message in messages:
                ts_info = self.extract_timestamp_info(message['ts'])
                hourly_activity[ts_info['hour']] += 1
                daily_activity[ts_info['day_name']] += 1
        
        peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 12
        peak_day = max(daily_activity.items(), key=lambda x: x[1])[0] if daily_activity else 'Monday'
        
        return {
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'hourly_distribution': dict(hourly_activity),
            'daily_distribution': dict(daily_activity),
            'total_messages': sum(hourly_activity.values())
        }
    
    def calculate_engagement_trends(self, daily_metrics: Dict[str, Dict], days: int = 7) -> Dict[str, Any]:
        trends = {}
        
        for channel_name, channel_metrics in daily_metrics.items():
            if not channel_metrics:
                continue
            
            dates = sorted(channel_metrics.keys())
            recent_dates = dates[-days:] if len(dates) >= days else dates
            
            if len(recent_dates) < 2:
                trends[channel_name] = {
                    'sentiment_trend': 'stable',
                    'engagement_trend': 'stable',
                    'message_trend': 'stable',
                    'trend_strength': 0.0
                }
                continue
            
            # Calculate trends
            sentiment_values = [channel_metrics[date]['avg_sentiment'] for date in recent_dates]
            engagement_values = [channel_metrics[date]['engagement_score'] for date in recent_dates]
            message_values = [channel_metrics[date]['message_count'] for date in recent_dates]
            
            sentiment_trend = self.calculate_trend_direction(sentiment_values)
            engagement_trend = self.calculate_trend_direction(engagement_values)
            message_trend = self.calculate_trend_direction(message_values)
            
            trends[channel_name] = {
                'sentiment_trend': sentiment_trend['direction'],
                'sentiment_change': sentiment_trend['change'],
                'engagement_trend': engagement_trend['direction'],
                'engagement_change': engagement_trend['change'],
                'message_trend': message_trend['direction'],
                'message_change': message_trend['change'],
                'recent_avg_sentiment': sum(sentiment_values) / len(sentiment_values),
                'recent_avg_engagement': sum(engagement_values) / len(engagement_values)
            }
        
        return trends
    
    def calculate_trend_direction(self, values: List[float]) -> Dict[str, Any]:
        if len(values) < 2:
            return {'direction': 'stable', 'change': 0.0}
        
        # Simple linear trend calculation
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Classify trend
        if slope > 0.05:
            direction = 'increasing'
        elif slope < -0.05:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        # Calculate percentage change
        if values[0] != 0:
            change = ((values[-1] - values[0]) / abs(values[0])) * 100
        else:
            change = 0.0
        
        return {
            'direction': direction,
            'change': round(change, 2),
            'slope': round(slope, 4)
        }
    
    def get_engagement_summary(self, daily_metrics: Dict[str, Dict]) -> Dict[str, Any]:
        total_messages = 0
        total_channels = len(daily_metrics)
        sentiment_scores = []
        engagement_scores = []
        
        for channel_name, channel_metrics in daily_metrics.items():
            for date, metrics in channel_metrics.items():
                total_messages += metrics['message_count']
                sentiment_scores.append(metrics['avg_sentiment'])
                engagement_scores.append(metrics['engagement_score'])
        
        return {
            'total_channels_monitored': total_channels,
            'total_messages_analyzed': total_messages,
            'overall_avg_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0,
            'overall_avg_engagement': sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0,
            'sentiment_distribution': self.get_sentiment_distribution(sentiment_scores),
            'most_active_channel': max(daily_metrics.keys(), 
                                     key=lambda ch: sum(m['message_count'] for m in daily_metrics[ch].values())) if daily_metrics else None
        }
    
    def get_sentiment_distribution(self, sentiment_scores: List[float]) -> Dict[str, float]:
        if not sentiment_scores:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
        
        positive = sum(1 for s in sentiment_scores if s > 0.1) / len(sentiment_scores) * 100
        negative = sum(1 for s in sentiment_scores if s < -0.1) / len(sentiment_scores) * 100
        neutral = 100 - positive - negative
        
        return {
            'positive': round(positive, 1),
            'neutral': round(neutral, 1),
            'negative': round(negative, 1)
        }