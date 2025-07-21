import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

class DataStorage:
    def __init__(self, db_path: str, retention_days: int = 30):
        self.db_path = Path(db_path)
        self.retention_days = retention_days
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    message_count INTEGER NOT NULL,
                    avg_sentiment REAL NOT NULL,
                    sentiment_std REAL DEFAULT 0.0,
                    emoji_count INTEGER DEFAULT 0,
                    reaction_count INTEGER DEFAULT 0,
                    active_hours_count INTEGER DEFAULT 0,
                    active_hours TEXT DEFAULT '',
                    thread_participation REAL DEFAULT 0.0,
                    engagement_score REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, channel_name)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sentiment_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    sentiment_trend TEXT NOT NULL,
                    sentiment_change REAL DEFAULT 0.0,
                    engagement_trend TEXT NOT NULL,
                    engagement_change REAL DEFAULT 0.0,
                    message_trend TEXT NOT NULL,
                    message_change REAL DEFAULT 0.0,
                    recent_avg_sentiment REAL DEFAULT 0.0,
                    recent_avg_engagement REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, channel_name)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS burnout_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    consecutive_negative_days INTEGER DEFAULT 0,
                    warning_indicators TEXT DEFAULT '',
                    recommendations TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, channel_name)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS activity_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    peak_hour INTEGER DEFAULT 12,
                    peak_day TEXT DEFAULT 'Monday',
                    hourly_distribution TEXT DEFAULT '{}',
                    daily_distribution TEXT DEFAULT '{}',
                    total_messages INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS engagement_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_channels_monitored INTEGER NOT NULL,
                    total_messages_analyzed INTEGER NOT NULL,
                    overall_avg_sentiment REAL NOT NULL,
                    overall_avg_engagement REAL NOT NULL,
                    sentiment_distribution TEXT DEFAULT '{}',
                    most_active_channel TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            ''')
            
            # Create indexes for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_daily_metrics_channel ON daily_metrics(channel_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_burnout_alerts_date ON burnout_alerts(date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_burnout_alerts_risk ON burnout_alerts(risk_level)')
            
            conn.commit()
    
    def store_daily_metrics(self, date: str, daily_metrics: Dict[str, Dict]):
        with sqlite3.connect(self.db_path) as conn:
            for channel_name, channel_data in daily_metrics.items():
                for day_date, metrics in channel_data.items():
                    try:
                        conn.execute('''
                            INSERT OR REPLACE INTO daily_metrics 
                            (date, channel_name, message_count, avg_sentiment, sentiment_std,
                             emoji_count, reaction_count, active_hours_count, active_hours,
                             thread_participation, engagement_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            day_date,
                            channel_name,
                            metrics['message_count'],
                            metrics['avg_sentiment'],
                            metrics['sentiment_std'],
                            metrics['emoji_count'],
                            metrics['reaction_count'],
                            metrics['active_hours_count'],
                            json.dumps(metrics['active_hours']),
                            metrics['thread_participation'],
                            metrics['engagement_score']
                        ))
                    except Exception as e:
                        self.logger.error(f"Error storing daily metrics for {channel_name} on {day_date}: {e}")
            
            conn.commit()
    
    def store_sentiment_trends(self, date: str, trends: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            for channel_name, trend_data in trends.items():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO sentiment_trends 
                        (date, channel_name, sentiment_trend, sentiment_change,
                         engagement_trend, engagement_change, message_trend, message_change,
                         recent_avg_sentiment, recent_avg_engagement)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date,
                        channel_name,
                        trend_data.get('sentiment_trend', 'stable'),
                        trend_data.get('sentiment_change', 0.0),
                        trend_data.get('engagement_trend', 'stable'),
                        trend_data.get('engagement_change', 0.0),
                        trend_data.get('message_trend', 'stable'),
                        trend_data.get('message_change', 0.0),
                        trend_data.get('recent_avg_sentiment', 0.0),
                        trend_data.get('recent_avg_engagement', 0.0)
                    ))
                except Exception as e:
                    self.logger.error(f"Error storing sentiment trends for {channel_name}: {e}")
            
            conn.commit()
    
    def store_burnout_alerts(self, date: str, alerts: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            for channel_name, alert_data in alerts.items():
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO burnout_alerts 
                        (date, channel_name, risk_level, risk_score, consecutive_negative_days,
                         warning_indicators, recommendations)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date,
                        channel_name,
                        alert_data.get('risk_level', 'low'),
                        alert_data.get('risk_score', 0.0),
                        alert_data.get('consecutive_negative_days', 0),
                        json.dumps(alert_data.get('warning_indicators', [])),
                        json.dumps(alert_data.get('recommendations', []))
                    ))
                except Exception as e:
                    self.logger.error(f"Error storing burnout alerts for {channel_name}: {e}")
            
            conn.commit()
    
    def store_activity_patterns(self, date: str, patterns: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO activity_patterns 
                    (date, peak_hour, peak_day, hourly_distribution, daily_distribution, total_messages)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    date,
                    patterns.get('peak_hour', 12),
                    patterns.get('peak_day', 'Monday'),
                    json.dumps(patterns.get('hourly_distribution', {})),
                    json.dumps(patterns.get('daily_distribution', {})),
                    patterns.get('total_messages', 0)
                ))
                conn.commit()
            except Exception as e:
                self.logger.error(f"Error storing activity patterns: {e}")
    
    def store_engagement_summary(self, date: str, summary: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO engagement_summary 
                    (date, total_channels_monitored, total_messages_analyzed,
                     overall_avg_sentiment, overall_avg_engagement, sentiment_distribution,
                     most_active_channel)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date,
                    summary.get('total_channels_monitored', 0),
                    summary.get('total_messages_analyzed', 0),
                    summary.get('overall_avg_sentiment', 0.0),
                    summary.get('overall_avg_engagement', 0.0),
                    json.dumps(summary.get('sentiment_distribution', {})),
                    summary.get('most_active_channel', '')
                ))
                conn.commit()
            except Exception as e:
                self.logger.error(f"Error storing engagement summary: {e}")
    
    def get_daily_metrics(self, channel_name: str = None, days_back: int = 7) -> Dict[str, Any]:
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT * FROM daily_metrics 
            WHERE date >= ?
        '''
        params = [start_date]
        
        if channel_name:
            query += ' AND channel_name = ?'
            params.append(channel_name)
        
        query += ' ORDER BY date DESC, channel_name'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # Convert to nested dict structure
        result = {}
        for row in rows:
            channel = row['channel_name']
            date = row['date']
            
            if channel not in result:
                result[channel] = {}
            
            result[channel][date] = {
                'message_count': row['message_count'],
                'avg_sentiment': row['avg_sentiment'],
                'sentiment_std': row['sentiment_std'],
                'emoji_count': row['emoji_count'],
                'reaction_count': row['reaction_count'],
                'active_hours_count': row['active_hours_count'],
                'active_hours': json.loads(row['active_hours'] or '[]'),
                'thread_participation': row['thread_participation'],
                'engagement_score': row['engagement_score']
            }
        
        return result
    
    def get_burnout_history(self, channel_name: str = None, days_back: int = 30) -> List[Dict[str, Any]]:
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT * FROM burnout_alerts 
            WHERE date >= ? AND risk_level != 'low'
        '''
        params = [start_date]
        
        if channel_name:
            query += ' AND channel_name = ?'
            params.append(channel_name)
        
        query += ' ORDER BY date DESC, risk_score DESC'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'date': row['date'],
                'channel_name': row['channel_name'],
                'risk_level': row['risk_level'],
                'risk_score': row['risk_score'],
                'consecutive_negative_days': row['consecutive_negative_days'],
                'warning_indicators': json.loads(row['warning_indicators'] or '[]'),
                'recommendations': json.loads(row['recommendations'] or '[]')
            })
        
        return result
    
    def get_sentiment_trends_history(self, channel_name: str = None, days_back: int = 14) -> Dict[str, List[Dict[str, Any]]]:
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        query = '''
            SELECT * FROM sentiment_trends 
            WHERE date >= ?
        '''
        params = [start_date]
        
        if channel_name:
            query += ' AND channel_name = ?'
            params.append(channel_name)
        
        query += ' ORDER BY date DESC, channel_name'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        result = {}
        for row in rows:
            channel = row['channel_name']
            
            if channel not in result:
                result[channel] = []
            
            result[channel].append({
                'date': row['date'],
                'sentiment_trend': row['sentiment_trend'],
                'sentiment_change': row['sentiment_change'],
                'engagement_trend': row['engagement_trend'],
                'engagement_change': row['engagement_change'],
                'recent_avg_sentiment': row['recent_avg_sentiment'],
                'recent_avg_engagement': row['recent_avg_engagement']
            })
        
        return result
    
    def get_database_stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Count records in each table
            tables = ['daily_metrics', 'sentiment_trends', 'burnout_alerts', 'activity_patterns', 'engagement_summary']
            
            for table in tables:
                cursor = conn.execute(f'SELECT COUNT(*) FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Date ranges
            cursor = conn.execute('SELECT MIN(date), MAX(date) FROM daily_metrics')
            min_date, max_date = cursor.fetchone()
            stats['data_date_range'] = {'start': min_date, 'end': max_date}
            
            # Channel count
            cursor = conn.execute('SELECT COUNT(DISTINCT channel_name) FROM daily_metrics')
            stats['unique_channels'] = cursor.fetchone()[0]
            
            # Database size
            stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        
        return stats
    
    def cleanup_old_data(self) -> int:
        cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).strftime('%Y-%m-%d')
        deleted_count = 0
        
        tables = ['daily_metrics', 'sentiment_trends', 'burnout_alerts', 'activity_patterns', 'engagement_summary']
        
        with sqlite3.connect(self.db_path) as conn:
            for table in tables:
                cursor = conn.execute(f'DELETE FROM {table} WHERE date < ?', (cutoff_date,))
                deleted_count += cursor.rowcount
                self.logger.info(f"Cleaned up {cursor.rowcount} old records from {table}")
            
            # Vacuum to reclaim space
            conn.execute('VACUUM')
            conn.commit()
        
        self.logger.info(f"Cleanup completed: removed {deleted_count} old records")
        return deleted_count
    
    def export_data(self, output_path: str, format_type: str = 'json', days_back: int = 30):
        output_path = Path(output_path)
        
        # Get all data
        daily_metrics = self.get_daily_metrics(days_back=days_back)
        burnout_history = self.get_burnout_history(days_back=days_back)
        trends_history = self.get_sentiment_trends_history(days_back=days_back)
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'days_back': days_back,
            'daily_metrics': daily_metrics,
            'burnout_history': burnout_history,
            'sentiment_trends_history': trends_history,
            'database_stats': self.get_database_stats()
        }
        
        if format_type == 'json':
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        self.logger.info(f"Data exported to {output_path}")
    
    def close(self):
        pass