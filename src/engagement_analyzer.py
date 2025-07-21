#!/usr/bin/env python3

import logging
import sys
from datetime import datetime
from typing import Dict, Any, List
import traceback
from pathlib import Path

from config_manager import ConfigManager
from slack_data_collector import SlackDataCollector
from sentiment_analyzer import SentimentAnalyzer
from engagement_tracker import EngagementTracker
from burnout_detector import BurnoutDetector
from report_generator import ReportGenerator
from data_storage import DataStorage

class EngagementAnalyzer:
    def __init__(self, config_file: str = "config.json"):
        # Initialize configuration
        self.config = ConfigManager(config_file)
        
        # Set up logging
        self.setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Slack Employee Engagement Pulse System")
        
        # Initialize components
        try:
            self.slack_collector = SlackDataCollector(
                token=self.config.get_slack_token(),
                rate_limit_delay=self.config.get_rate_limit_delay()
            )
            
            self.sentiment_analyzer = SentimentAnalyzer()
            self.engagement_tracker = EngagementTracker()
            
            self.burnout_detector = BurnoutDetector(
                burnout_threshold=self.config.get_burnout_threshold(),
                consecutive_negative_days=self.config.get_consecutive_negative_days(),
                engagement_drop_threshold=self.config.get_engagement_drop_threshold()
            )
            
            self.report_generator = ReportGenerator(
                reports_dir=self.config.get_reports_directory()
            )
            
            self.data_storage = DataStorage(
                db_path=self.config.get_database_path(),
                retention_days=self.config.get_database_retention_days()
            )
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def setup_logging(self):
        log_config = self.config.get_logging_config()
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        
        # Create logs directory if specified
        if 'file' in log_config:
            log_file = Path(log_config['file'])
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_config.get('file', 'engagement.log'))
            ] if 'file' in log_config else [logging.StreamHandler(sys.stdout)]
        )
    
    def test_slack_connection(self) -> bool:
        try:
            self.logger.info("Testing Slack API connection...")
            success = self.slack_collector.test_connection()
            if success:
                self.logger.info("✅ Slack API connection successful")
            else:
                self.logger.error("❌ Slack API connection failed")
            return success
        except Exception as e:
            self.logger.error(f"❌ Slack API connection error: {e}")
            return False
    
    def collect_and_analyze_data(self, days_back: int = None) -> Dict[str, Any]:
        if days_back is None:
            days_back = self.config.get_analysis_days()
        
        self.logger.info(f"Starting data collection for {days_back} days")
        
        try:
            # 1. Collect data from Slack
            monitored_channels = self.config.get_monitored_channels()
            self.logger.info(f"Monitoring channels: {monitored_channels}")
            
            channel_data = self.slack_collector.collect_channel_data(
                channel_names=monitored_channels,
                days_back=days_back
            )
            
            if not channel_data:
                self.logger.warning("No data collected from Slack channels")
                return {}
            
            # 2. Analyze sentiment for all messages
            self.logger.info("Analyzing sentiment...")
            for channel_name, messages in channel_data.items():
                for message in messages:
                    if 'text' in message and message['text'].strip():
                        sentiment_data = self.sentiment_analyzer.analyze_message_sentiment(
                            message['text']
                        )
                        message['sentiment'] = sentiment_data
                    
                    # Analyze reactions
                    if 'reactions' in message and message['reactions']:
                        reaction_sentiment = self.sentiment_analyzer.analyze_reaction_sentiment(
                            message['reactions']
                        )
                        if 'sentiment' not in message:
                            message['sentiment'] = {}
                        message['sentiment'].update(reaction_sentiment)
            
            # 3. Calculate engagement metrics
            self.logger.info("Calculating engagement metrics...")
            daily_metrics = self.engagement_tracker.calculate_daily_metrics(channel_data)
            
            # 4. Analyze activity patterns
            self.logger.info("Analyzing activity patterns...")
            activity_patterns = self.engagement_tracker.analyze_peak_activity_patterns(channel_data)
            
            # 5. Calculate engagement trends
            self.logger.info("Calculating engagement trends...")
            engagement_trends = self.engagement_tracker.calculate_engagement_trends(daily_metrics, days_back)
            
            # 6. Generate engagement summary
            engagement_summary = self.engagement_tracker.get_engagement_summary(daily_metrics)
            
            # 7. Detect burnout patterns
            self.logger.info("Detecting burnout patterns...")
            burnout_alerts = self.burnout_detector.detect_burnout_patterns(
                daily_metrics, engagement_trends
            )
            
            # 8. Store data in database
            self.logger.info("Storing data...")
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            self.data_storage.store_daily_metrics(date_str, daily_metrics)
            self.data_storage.store_sentiment_trends(date_str, engagement_trends)
            self.data_storage.store_burnout_alerts(date_str, burnout_alerts)
            self.data_storage.store_activity_patterns(date_str, activity_patterns)
            self.data_storage.store_engagement_summary(date_str, engagement_summary)
            
            # Return analysis results
            return {
                'daily_metrics': daily_metrics,
                'engagement_trends': engagement_trends,
                'burnout_alerts': burnout_alerts,
                'activity_patterns': activity_patterns,
                'engagement_summary': engagement_summary,
                'analysis_metadata': {
                    'analysis_date': date_str,
                    'days_analyzed': days_back,
                    'channels_analyzed': list(channel_data.keys()),
                    'total_messages': sum(len(messages) for messages in channel_data.values())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during data collection and analysis: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def generate_reports(self, analysis_data: Dict[str, Any]) -> List[str]:
        self.logger.info("Generating reports...")
        report_paths = []
        
        try:
            # Generate comprehensive weekly report
            weekly_report = self.report_generator.generate_weekly_report(
                daily_metrics=analysis_data['daily_metrics'],
                engagement_trends=analysis_data['engagement_trends'],
                burnout_alerts=analysis_data['burnout_alerts'],
                activity_patterns=analysis_data['activity_patterns'],
                engagement_summary=analysis_data['engagement_summary']
            )
            
            # Save in configured formats
            report_formats = self.config.get_report_formats()
            
            for format_type in report_formats:
                if format_type in ['json', 'csv', 'html']:
                    report_path = self.report_generator.save_report(weekly_report, format_type)
                    report_paths.append(report_path)
                    self.logger.info(f"Report saved: {report_path}")
            
            return report_paths
            
        except Exception as e:
            self.logger.error(f"Error generating reports: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def print_summary(self, analysis_data: Dict[str, Any]):
        print("\n" + "="*60)
        print("📊 SLACK EMPLOYEE ENGAGEMENT PULSE - SUMMARY")
        print("="*60)
        
        metadata = analysis_data.get('analysis_metadata', {})
        summary = analysis_data.get('engagement_summary', {})
        burnout_alerts = analysis_data.get('burnout_alerts', {})
        
        print(f"📅 Analysis Date: {metadata.get('analysis_date', 'N/A')}")
        print(f"📊 Days Analyzed: {metadata.get('days_analyzed', 'N/A')}")
        print(f"💬 Total Messages: {metadata.get('total_messages', 0)}")
        print(f"📢 Channels: {', '.join(metadata.get('channels_analyzed', []))}")
        
        print(f"\n🎯 Overall Sentiment: {summary.get('overall_avg_sentiment', 0):.3f}")
        print(f"⚡ Overall Engagement: {summary.get('overall_avg_engagement', 0):.3f}")
        
        # Sentiment distribution
        sentiment_dist = summary.get('sentiment_distribution', {})
        print(f"\n📈 Sentiment Breakdown:")
        print(f"  Positive: {sentiment_dist.get('positive', 0):.1f}%")
        print(f"  Neutral:  {sentiment_dist.get('neutral', 0):.1f}%")
        print(f"  Negative: {sentiment_dist.get('negative', 0):.1f}%")
        
        # Burnout alerts
        if burnout_alerts:
            print(f"\n⚠️  BURNOUT ALERTS ({len(burnout_alerts)} channels):")
            for channel, alert in burnout_alerts.items():
                risk_emoji = "🔴" if alert['risk_level'] == 'high' else "🟡"
                print(f"  {risk_emoji} {channel}: {alert['risk_level'].upper()} risk (score: {alert['risk_score']:.1f})")
                
                if alert['warning_indicators']:
                    for indicator in alert['warning_indicators'][:2]:  # Show first 2
                        print(f"    - {indicator}")
        else:
            print(f"\n✅ No burnout risks detected")
        
        print("\n" + "="*60)
    
    def cleanup_old_data(self):
        self.logger.info("Cleaning up old data...")
        try:
            deleted_count = self.data_storage.cleanup_old_data()
            self.logger.info(f"Cleanup completed: {deleted_count} records removed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        return self.data_storage.get_database_stats()
    
    def run_analysis(self, days_back: int = None, generate_reports: bool = True, 
                    print_summary: bool = True, cleanup: bool = True) -> Dict[str, Any]:
        try:
            # Test connection first
            if not self.test_slack_connection():
                raise Exception("Failed to connect to Slack API")
            
            # Run data collection and analysis
            analysis_data = self.collect_and_analyze_data(days_back)
            
            if not analysis_data:
                self.logger.warning("No analysis data generated")
                return {}
            
            # Generate reports
            report_paths = []
            if generate_reports:
                report_paths = self.generate_reports(analysis_data)
            
            # Print summary
            if print_summary:
                self.print_summary(analysis_data)
            
            # Cleanup old data
            if cleanup:
                self.cleanup_old_data()
            
            # Add report paths to result
            analysis_data['report_paths'] = report_paths
            analysis_data['database_stats'] = self.get_database_stats()
            
            self.logger.info("Analysis completed successfully!")
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            self.logger.error(traceback.format_exc())
            raise

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Slack Employee Engagement Pulse Analyzer')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--days', type=int, help='Number of days to analyze (overrides config)')
    parser.add_argument('--no-reports', action='store_true', help='Skip report generation')
    parser.add_argument('--no-summary', action='store_true', help='Skip summary output')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip old data cleanup')
    parser.add_argument('--test-connection', action='store_true', help='Test Slack connection only')
    parser.add_argument('--db-stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    try:
        analyzer = EngagementAnalyzer(args.config)
        
        if args.test_connection:
            success = analyzer.test_slack_connection()
            sys.exit(0 if success else 1)
        
        if args.db_stats:
            stats = analyzer.get_database_stats()
            print("\n📊 Database Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            sys.exit(0)
        
        # Run full analysis
        result = analyzer.run_analysis(
            days_back=args.days,
            generate_reports=not args.no_reports,
            print_summary=not args.no_summary,
            cleanup=not args.no_cleanup
        )
        
        if result and result.get('report_paths'):
            print(f"\n📄 Reports generated:")
            for path in result['report_paths']:
                print(f"  - {path}")
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()