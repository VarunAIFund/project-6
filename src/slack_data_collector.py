import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

class SlackDataCollector:
    def __init__(self, token: str, rate_limit_delay: float = 1.0):
        self.client = WebClient(token=token)
        self.rate_limit_delay = rate_limit_delay
        self.logger = logging.getLogger(__name__)
        
    def get_channels(self, channel_names: List[str]) -> Dict[str, str]:
        try:
            response = self.client.conversations_list(types="public_channel,private_channel")
            channels = {}
            
            for channel in response["channels"]:
                channel_name = f"#{channel['name']}"
                if channel_name in channel_names:
                    channels[channel_name] = channel["id"]
            
            # Handle private channels that may not appear in conversations_list
            # Try to find missing channels by testing direct access
            missing_channels = [name for name in channel_names if name not in channels]
            if missing_channels:
                self.logger.info(f"Trying direct lookup for missing channels: {missing_channels}")
                
                # Try private channels specifically
                try:
                    priv_response = self.client.conversations_list(types="private_channel", limit=100)
                    for channel in priv_response["channels"]:
                        channel_name = f"#{channel['name']}"
                        if channel_name in missing_channels:
                            channels[channel_name] = channel["id"]
                            self.logger.info(f"Found private channel: {channel_name}")
                except SlackApiError as e:
                    self.logger.warning(f"Could not fetch private channels: {e}")
            
            time.sleep(self.rate_limit_delay)
            return channels
        except SlackApiError as e:
            self.logger.error(f"Error fetching channels: {e}")
            return {}
    
    def get_channel_history(self, channel_id: str, days_back: int = 7) -> List[Dict[str, Any]]:
        oldest_timestamp = (datetime.now() - timedelta(days=days_back)).timestamp()
        messages = []
        
        try:
            cursor = None
            while True:
                response = self.client.conversations_history(
                    channel=channel_id,
                    oldest=str(oldest_timestamp),
                    cursor=cursor,
                    limit=200
                )
                
                batch_messages = response.get("messages", [])
                
                # Filter out bot messages and system notifications
                filtered_messages = [
                    msg for msg in batch_messages 
                    if not msg.get("bot_id") and 
                       msg.get("type") == "message" and 
                       msg.get("subtype") is None and
                       msg.get("text", "").strip()
                ]
                
                messages.extend(filtered_messages)
                
                if not response.get("has_more", False):
                    break
                    
                cursor = response.get("response_metadata", {}).get("next_cursor")
                time.sleep(self.rate_limit_delay)
            
            return messages
        except SlackApiError as e:
            self.logger.error(f"Error fetching channel history for {channel_id}: {e}")
            return []
    
    def get_message_reactions(self, channel_id: str, timestamp: str) -> List[Dict[str, Any]]:
        try:
            response = self.client.reactions_get(
                channel=channel_id,
                timestamp=timestamp,
                full=True
            )
            time.sleep(self.rate_limit_delay)
            return response.get("message", {}).get("reactions", [])
        except SlackApiError as e:
            self.logger.error(f"Error fetching reactions: {e}")
            return []
    
    def collect_channel_data(self, channel_names: List[str], days_back: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        channels = self.get_channels(channel_names)
        channel_data = {}
        
        for channel_name, channel_id in channels.items():
            self.logger.info(f"Collecting data from {channel_name}")
            messages = self.get_channel_history(channel_id, days_back)
            
            # Enrich messages with reaction data
            for message in messages:
                if "reactions" not in message:
                    reactions = self.get_message_reactions(channel_id, message["ts"])
                    message["reactions"] = reactions
            
            channel_data[channel_name] = messages
            self.logger.info(f"Collected {len(messages)} messages from {channel_name}")
        
        return channel_data
    
    def test_connection(self) -> bool:
        try:
            response = self.client.auth_test()
            self.logger.info(f"Connected as: {response['user']}")
            return True
        except SlackApiError as e:
            self.logger.error(f"Connection test failed: {e}")
            return False