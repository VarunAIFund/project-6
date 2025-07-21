import re
import emoji
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Tuple
import logging
import os

class SentimentAnalyzer:
    def __init__(self, use_gpt: bool = True):
        self.use_gpt = use_gpt and os.getenv('OPENAI_API_KEY') is not None
        self.vader = SentimentIntensityAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        if self.use_gpt:
            try:
                from gpt_sentiment_analyzer import GPTSentimentAnalyzer
                self.gpt_analyzer = GPTSentimentAnalyzer()
                self.logger.info("Initialized GPT-based sentiment analysis")
            except Exception as e:
                self.logger.warning(f"Failed to initialize GPT analyzer, falling back to VADER: {e}")
                self.use_gpt = False
                self.gpt_analyzer = None
        else:
            self.gpt_analyzer = None
            self.logger.info("Using VADER/TextBlob sentiment analysis (GPT disabled or API key missing)")
        
        # Emoji sentiment mapping
        self.emoji_sentiment = {
            '😊': 0.8, '😀': 0.8, '😃': 0.8, '😄': 0.8, '😁': 0.8,
            '😆': 0.7, '😂': 0.9, '🤣': 0.9, '😇': 0.6, '🙂': 0.5,
            '😉': 0.5, '😋': 0.6, '😎': 0.7, '🤗': 0.8, '🤩': 0.9,
            '😍': 0.9, '🥰': 0.9, '😘': 0.8, '😗': 0.6, '☺️': 0.6,
            '😌': 0.4, '😏': 0.3, '🤔': 0.1, '🙄': -0.3, '😒': -0.4,
            '😔': -0.6, '😞': -0.7, '😟': -0.6, '😢': -0.8, '😭': -0.9,
            '😤': -0.5, '😠': -0.7, '😡': -0.8, '🤬': -0.9, '😰': -0.6,
            '😨': -0.7, '😱': -0.8, '😪': -0.4, '🙃': 0.2, '😶': 0.0,
            '🤐': -0.1, '😐': 0.0, '😑': -0.1, '🤨': -0.2, '🧐': 0.1,
            '🤯': -0.3, '😵': -0.5, '🥴': -0.2, '🤮': -0.8, '🤢': -0.6,
            '🤧': -0.3, '😷': -0.2, '🤒': -0.4, '🤕': -0.5, '👍': 0.6,
            '👎': -0.6, '👏': 0.7, '🙌': 0.8, '👌': 0.5, '✨': 0.6,
            '🎉': 0.9, '🎊': 0.8, '💪': 0.7, '🔥': 0.8, '⭐': 0.6,
            '💯': 0.8, '✅': 0.6, '❌': -0.5, '⚠️': -0.3, '🚨': -0.6,
            '💔': -0.8, '❤️': 0.9, '💕': 0.8, '💖': 0.8, '💗': 0.8,
            '😴': -0.1, '💤': -0.1, '🤤': 0.1, '😻': 0.8, '💀': -0.7
        }
    
    def extract_emojis(self, text: str) -> List[str]:
        return [char for char in text if char in emoji.EMOJI_DATA]
    
    def analyze_emoji_sentiment(self, emojis: List[str]) -> float:
        if not emojis:
            return 0.0
        
        sentiment_scores = [
            self.emoji_sentiment.get(em, 0.0) for em in emojis
        ]
        
        return sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
    
    def clean_text_for_analysis(self, text: str) -> str:
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # Remove user mentions
        text = re.sub(r'<@[UW][A-Z0-9]+(?:\|[^>]+)?>', '', text)
        # Remove channel mentions
        text = re.sub(r'<#[C][A-Z0-9]+(?:\|[^>]+)?>', '', text)
        # Remove special Slack formatting
        text = re.sub(r'<[^>]+>', '', text)
        # Remove excess whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def analyze_text_sentiment_vader(self, text: str) -> Dict[str, float]:
        clean_text = self.clean_text_for_analysis(text)
        if not clean_text:
            return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}
        
        scores = self.vader.polarity_scores(clean_text)
        return scores
    
    def analyze_text_sentiment_textblob(self, text: str) -> Dict[str, float]:
        clean_text = self.clean_text_for_analysis(text)
        if not clean_text:
            return {'polarity': 0.0, 'subjectivity': 0.0}
        
        blob = TextBlob(clean_text)
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    
    def analyze_message_sentiment(self, message_text: str) -> Dict[str, float]:
        if self.use_gpt and self.gpt_analyzer:
            # Use GPT-based analysis
            try:
                gpt_result = self.gpt_analyzer.analyze_message_sentiment(message_text)
                # Add fallback scores for compatibility
                gpt_result.update({
                    'vader_pos': 0.0,
                    'vader_neg': 0.0, 
                    'vader_neu': 1.0,
                    'textblob_polarity': gpt_result['text_sentiment'],
                    'textblob_subjectivity': 0.5,
                    'analysis_method': 'gpt'
                })
                return gpt_result
            except Exception as e:
                self.logger.error(f"GPT analysis failed, falling back to VADER: {e}")
                # Fall through to VADER analysis
        
        # Fallback to VADER/TextBlob analysis
        emojis = self.extract_emojis(message_text)
        emoji_sentiment = self.analyze_emoji_sentiment(emojis)
        
        vader_scores = self.analyze_text_sentiment_vader(message_text)
        textblob_scores = self.analyze_text_sentiment_textblob(message_text)
        
        # Combine scores with weights
        text_weight = 0.6
        emoji_weight = 0.4
        
        combined_sentiment = (
            text_weight * vader_scores['compound'] + 
            emoji_weight * emoji_sentiment
        )
        
        return {
            'overall_sentiment': max(-1.0, min(1.0, combined_sentiment)),
            'text_sentiment': vader_scores['compound'],
            'emoji_sentiment': emoji_sentiment,
            'emoji_count': len(emojis),
            'vader_pos': vader_scores['pos'],
            'vader_neg': vader_scores['neg'],
            'vader_neu': vader_scores['neu'],
            'textblob_polarity': textblob_scores['polarity'],
            'textblob_subjectivity': textblob_scores['subjectivity'],
            'analysis_method': 'vader'
        }
    
    def analyze_reaction_sentiment(self, reactions: List[Dict]) -> Dict[str, float]:
        if not reactions:
            return {'reaction_sentiment': 0.0, 'reaction_count': 0}
        
        total_sentiment = 0.0
        total_count = 0
        
        for reaction in reactions:
            emoji_name = reaction.get('name', '')
            count = reaction.get('count', 0)
            
            # Convert reaction name to emoji if possible
            emoji_char = f":{emoji_name}:"
            try:
                emoji_char = emoji.emojize(emoji_char)
            except:
                pass
            
            sentiment = self.emoji_sentiment.get(emoji_char, 0.3)  # Default positive for reactions
            total_sentiment += sentiment * count
            total_count += count
        
        avg_sentiment = total_sentiment / total_count if total_count > 0 else 0.0
        
        return {
            'reaction_sentiment': avg_sentiment,
            'reaction_count': total_count
        }
    
    def categorize_sentiment(self, sentiment_score: float) -> str:
        if sentiment_score >= 0.5:
            return 'very_positive'
        elif sentiment_score >= 0.1:
            return 'positive'
        elif sentiment_score >= -0.1:
            return 'neutral'
        elif sentiment_score >= -0.5:
            return 'negative'
        else:
            return 'very_negative'