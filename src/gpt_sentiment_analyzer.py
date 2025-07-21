import os
import re
import json
import emoji
import logging
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class GPTSentimentAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.logger = logging.getLogger(__name__)
        
        # Emoji sentiment mapping (fallback for when GPT is unavailable)
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
    
    def analyze_emoji_sentiment_fallback(self, emojis: List[str]) -> float:
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
    
    def analyze_text_sentiment_gpt(self, text: str) -> Dict[str, float]:
        clean_text = self.clean_text_for_analysis(text)
        if not clean_text:
            return {
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'category': 'neutral',
                'reasoning': 'Empty text'
            }
        
        try:
            # Create a detailed prompt for sentiment analysis
            prompt = f"""
Analyze the sentiment of this workplace message and provide a detailed assessment:

Message: "{clean_text}"

Please provide:
1. A sentiment score from -1.0 (very negative) to +1.0 (very positive)
2. A confidence level from 0.0 to 1.0
3. A category: "very_positive", "positive", "neutral", "negative", or "very_negative"
4. Brief reasoning (max 50 words)

Respond in JSON format:
{{
    "sentiment_score": <float>,
    "confidence": <float>,
    "category": "<string>",
    "reasoning": "<string>"
}}

Consider workplace context: team collaboration, project updates, challenges, successes, etc.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing workplace communication sentiment. Provide accurate, nuanced sentiment analysis that considers workplace context and team dynamics."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1  # Low temperature for consistent results
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
                
                # Validate and clean the response
                sentiment_score = max(-1.0, min(1.0, float(result.get('sentiment_score', 0.0))))
                confidence = max(0.0, min(1.0, float(result.get('confidence', 0.5))))
                
                return {
                    'sentiment_score': sentiment_score,
                    'confidence': confidence,
                    'category': result.get('category', 'neutral'),
                    'reasoning': result.get('reasoning', 'GPT analysis'),
                    'gpt_response': response_text
                }
                
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse GPT response: {response_text}")
                # Fallback to simple parsing
                return self.parse_gpt_response_fallback(response_text, clean_text)
                
        except Exception as e:
            self.logger.error(f"GPT sentiment analysis failed: {e}")
            # Fallback to basic sentiment
            return {
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'category': 'neutral',
                'reasoning': f'GPT unavailable: {str(e)[:30]}',
                'error': str(e)
            }
    
    def parse_gpt_response_fallback(self, response_text: str, original_text: str) -> Dict[str, float]:
        # Simple fallback parsing if JSON fails
        sentiment_score = 0.0
        confidence = 0.5
        category = 'neutral'
        
        # Look for key words in response
        response_lower = response_text.lower()
        if 'positive' in response_lower and 'negative' not in response_lower:
            sentiment_score = 0.5
            category = 'positive'
        elif 'negative' in response_lower and 'positive' not in response_lower:
            sentiment_score = -0.5
            category = 'negative'
        elif 'very positive' in response_lower:
            sentiment_score = 0.8
            category = 'very_positive'
        elif 'very negative' in response_lower:
            sentiment_score = -0.8
            category = 'very_negative'
        
        # Try to extract numeric score
        import re
        score_match = re.search(r'[-+]?[0-9]*\.?[0-9]+', response_text)
        if score_match:
            try:
                parsed_score = float(score_match.group())
                if -1.0 <= parsed_score <= 1.0:
                    sentiment_score = parsed_score
            except:
                pass
        
        return {
            'sentiment_score': sentiment_score,
            'confidence': confidence,
            'category': category,
            'reasoning': 'Fallback parsing of GPT response',
            'raw_response': response_text
        }
    
    def analyze_message_sentiment(self, message_text: str) -> Dict[str, float]:
        emojis = self.extract_emojis(message_text)
        emoji_sentiment = self.analyze_emoji_sentiment_fallback(emojis)
        
        # Get GPT analysis
        gpt_analysis = self.analyze_text_sentiment_gpt(message_text)
        text_sentiment = gpt_analysis['sentiment_score']
        
        # Combine text and emoji sentiment
        if emojis:
            # Weight: 70% GPT text analysis, 30% emoji analysis
            combined_sentiment = 0.7 * text_sentiment + 0.3 * emoji_sentiment
        else:
            # No emojis, use GPT analysis only
            combined_sentiment = text_sentiment
        
        # Ensure bounds
        combined_sentiment = max(-1.0, min(1.0, combined_sentiment))
        
        return {
            'overall_sentiment': combined_sentiment,
            'text_sentiment': text_sentiment,
            'emoji_sentiment': emoji_sentiment,
            'emoji_count': len(emojis),
            'gpt_confidence': gpt_analysis.get('confidence', 0.0),
            'gpt_category': gpt_analysis.get('category', 'neutral'),
            'gpt_reasoning': gpt_analysis.get('reasoning', ''),
            'gpt_analysis': gpt_analysis
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