# youtube_extractor.py
import os
import pandas as pd
import re
from datetime import datetime, timedelta
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import nltk
from nltk.corpus import stopwords

# Load environment variables
load_dotenv()

# Download NLTK resources if needed
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class YouTubeExtractor:
    def __init__(self, api_key=None):
        # Use API key from environment variable if not provided
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YouTube API key is required. Set YOUTUBE_API_KEY in .env file")
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.stop_words = set(stopwords.words('english'))
        
        # Category keywords
        self.categories = {
            'fashion': ['fashion', 'style', 'outfit', 'clothes', 'model'],
            'food': ['food', 'cook', 'recipe', 'eat', 'chef', 'delicious'],
            'travel': ['travel', 'trip', 'journey', 'adventure', 'destination'],
            'fitness': ['fitness', 'workout', 'gym', 'exercise', 'training'],
            'tech': ['tech', 'technology', 'gadget', 'digital', 'coding', 'programming'],
            'gaming': ['game', 'gaming', 'gamer', 'playstation', 'xbox', 'nintendo'],
            'lifestyle': ['lifestyle', 'life', 'daily', 'family', 'home']
        }
    
    def extract_profile_data(self, channel_ids):
        """Extract data from multiple YouTube channels"""
        all_channels_data = []
        
        for channel_id in channel_ids:
            print(f"Extracting data for YouTube channel: {channel_id}")
            try:
                channel_data = self._get_profile_data_by_id(channel_id)
                if channel_data:
                    all_channels_data.append(channel_data)
                time.sleep(1)  # To avoid rate limits
            except Exception as e:
                print(f"Error extracting data for {channel_id}: {e}")
        
        return pd.DataFrame(all_channels_data)
    
    def extract_channel(self, channel_id_or_name):
        """Extract data for a single YouTube channel (wrapper for extract_profile_data)"""
        print(f"Processing YouTube channel: {channel_id_or_name}")
        
        # If this looks like a username instead of a channel ID, try to get the channel ID
        if not channel_id_or_name.startswith('UC'):
            try:
                # Search for the channel
                search_response = self.youtube.search().list(
                    q=channel_id_or_name,
                    type='channel',
                    part='id',
                    maxResults=1
                ).execute()
                
                if search_response.get('items'):
                    channel_id = search_response['items'][0]['id']['channelId']
                    print(f"Found channel ID for {channel_id_or_name}: {channel_id}")
                else:
                    print(f"Could not find channel ID for: {channel_id_or_name}")
                    return
            except Exception as e:
                print(f"Error searching for channel {channel_id_or_name}: {e}")
                return
        else:
            channel_id = channel_id_or_name
        
        # Process this single channel using existing method
        try:
            channel_data = self._get_profile_data_by_id(channel_id)
            if channel_data:
                # Add to the class's data collection
                self.channels_data = self.channels_data if hasattr(self, 'channels_data') else []
                self.channels_data.append(channel_data)
        except Exception as e:
            print(f"Error extracting data for {channel_id}: {e}")
    
    def _get_profile_data_by_id(self, channel_id):
        """Extract data for a single YouTube channel by ID"""
        # Get channel statistics and info
        channel_response = self.youtube.channels().list(
            part="snippet,statistics,contentDetails,brandingSettings",
            id=channel_id
        ).execute()
        
        if not channel_response['items']:
            print(f"No channel found for ID: {channel_id}")
            return None
        
        channel = channel_response['items'][0]
        snippet = channel['snippet']
        statistics = channel['statistics']
        
        # Get basic profile info
        profile_info = {
            'platform': 'YouTube',
            'name': snippet['title'],
            'username': channel_id,
            'bio': snippet['description'],
            'profile_link': f"https://www.youtube.com/channel/{channel_id}",
            'followers': int(statistics.get('subscriberCount', 0)),
            'following': 'N/A',
            'posts_count': int(statistics.get('videoCount', 0)),
        }
        
        # Audience data (not directly available without Analytics API)
        profile_info.update({
            'top_geographies': 'N/A (requires Analytics API)',
            'gender_ratio': 'N/A (requires Analytics API)',
            'language': snippet.get('defaultLanguage', 'N/A'),
        })
        
        # Get recent videos for engagement stats
        try:
            playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']
            videos_response = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=10
            ).execute()
            
            video_ids = [item['contentDetails']['videoId'] for item in videos_response.get('items', [])]
            
            if video_ids:
                # Get statistics for each video
                videos_stats_response = self.youtube.videos().list(
                    part="statistics,snippet,contentDetails",  # Added contentDetails for duration
                    id=','.join(video_ids)
                ).execute()
                
                likes = []
                comments = []
                views = []
                titles = []
                descriptions = []
                published_dates = []
                video_details = []
                
                # Track video types (similar to Instagram media distribution)
                video_types = {
                    'short': 0,  # Under 1 minute
                    'medium': 0, # 1-10 minutes
                    'long': 0    # Over 10 minutes
                }
                
                for item in videos_stats_response.get('items', []):
                    stats = item['statistics']
                    snippet = item['snippet']
                    content_details = item.get('contentDetails', {})
                    
                    # Get like and comment counts
                    like_count = int(stats.get('likeCount', 0))
                    comment_count = int(stats.get('commentCount', 0))
                    view_count = int(stats.get('viewCount', 0))
                    
                    # Parse duration to seconds
                    duration = content_details.get('duration', 'PT0S')
                    duration_seconds = self._parse_duration(duration)
                    
                    # Categorize video length
                    if duration_seconds < 60:
                        video_types['short'] += 1
                    elif duration_seconds < 600:
                        video_types['medium'] += 1
                    else:
                        video_types['long'] += 1
                    
                    # Add to lists for averages
                    likes.append(like_count)
                    comments.append(comment_count)
                    views.append(view_count)
                    titles.append(snippet.get('title', ''))
                    descriptions.append(snippet.get('description', ''))
                    published_dates.append(snippet.get('publishedAt', ''))
                    
                    # Store detailed video data
                    video_details.append({
                        'video_id': item['id'],
                        'title': snippet.get('title', ''),
                        'published_at': snippet.get('publishedAt', ''),
                        'like_count': like_count,
                        'comment_count': comment_count,
                        'view_count': view_count,
                        'duration': duration,
                        'duration_seconds': duration_seconds
                    })
                
                # Calculate average engagement
                profile_info.update({
                    'avg_likes': sum(likes) / len(likes) if likes else 0,
                    'avg_comments': sum(comments) / len(comments) if comments else 0,
                    'avg_views': sum(views) / len(views) if views else 0,
                    'max_likes': max(likes) if likes else 0,
                    'max_comments': max(comments) if comments else 0,
                    'max_views': max(views) if views else 0,
                    'total_likes': sum(likes) if likes else 0,
                    'total_comments': sum(comments) if comments else 0,
                    'total_views': sum(views) if likes else 0,
                })
                
                # Add video distribution (similar to Instagram media distribution)
                total_videos = len(video_details)
                if total_videos > 0:
                    profile_info['video_distribution'] = {
                        'short_percentage': (video_types['short'] / total_videos) * 100,
                        'medium_percentage': (video_types['medium'] / total_videos) * 100,
                        'long_percentage': (video_types['long'] / total_videos) * 100
                    }
                
                # Calculate engagement rates
                if profile_info['followers'] > 0:
                    profile_info['engagement_rate'] = ((profile_info['avg_likes'] + profile_info['avg_comments']) / 
                                                  profile_info['followers'] * 100)
                    profile_info['view_engagement_rate'] = (profile_info['avg_views'] / 
                                                      profile_info['followers'] * 100)
                else:
                    profile_info['engagement_rate'] = 0
                    profile_info['view_engagement_rate'] = 0
                
                # Store recent videos
                profile_info['recent_videos'] = video_details
                
                # Calculate posting frequency
                if published_dates and len(published_dates) >= 2:
                    dates = [datetime.strptime(date.split('T')[0], '%Y-%m-%d') for date in published_dates]
                    dates.sort()
                    oldest_date = dates[0]
                    newest_date = dates[-1]
                    days_diff = (newest_date - oldest_date).days or 1
                    videos_per_day = len(dates) / days_diff if days_diff > 0 else len(dates)
                    profile_info['posting_frequency'] = videos_per_day * 7  # videos per week
                else:
                    profile_info['posting_frequency'] = 0
                
                # Detect content category
                all_text = snippet.get('description', '').lower() + " " + " ".join(titles) + " " + " ".join(descriptions)
                profile_info['category'] = self._detect_category(all_text)
                
                # Estimate follower growth
                profile_info['estimated_weekly_growth'] = round(profile_info['followers'] * 0.01)  # 1% estimate
            else:
                # Default values if no videos
                self._set_default_values(profile_info, snippet)
        except Exception as e:
            print(f"Error getting videos data: {e}")
            self._set_default_values(profile_info, snippet)
        
        return profile_info
    
    def _set_default_values(self, profile_info, snippet):
        """Set default values when video data is unavailable"""
        profile_info.update({
            'avg_likes': 0,
            'avg_comments': 0,
            'avg_views': 0,
            'engagement_rate': 0,
            'posting_frequency': 0,
            'category': self._detect_category(snippet.get('description', '').lower()),
            'estimated_weekly_growth': 0
        })
    
    def _detect_category(self, text):
        """Detect content category based on keywords"""
        text = re.sub(r'[^\w\s]', '', text)
        words = text.lower().split()
        
        category_scores = {category: 0 for category in self.categories}
        
        for word in words:
            for category, keywords in self.categories.items():
                if word in keywords:
                    category_scores[category] += 1
        
        if max(category_scores.values(), default=0) > 0:
            return max(category_scores, key=category_scores.get)
        else:
            return "other"
    
    def save_data(self, file_path):
        """Save extracted channels data to a JSON file"""
        import json
        try:
            # Make sure we have channels_data attribute
            if not hasattr(self, 'channels_data'):
                self.channels_data = []
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.channels_data, f, indent=4, ensure_ascii=False)
            print(f"Saved YouTube data to {file_path}")
        except Exception as e:
            print(f"Error saving YouTube data: {e}")

    def _parse_duration(self, duration_str):
        """Parse ISO 8601 duration to seconds"""
        if not duration_str or not duration_str.startswith('PT'):
            return 0
        
        seconds = 0
        # Remove PT prefix
        duration = duration_str[2:]
        
        # Parse hours
        if 'H' in duration:
            hours, duration = duration.split('H')
            seconds += int(hours) * 3600
        
        # Parse minutes
        if 'M' in duration:
            minutes, duration = duration.split('M')
            seconds += int(minutes) * 60
        
        # Parse seconds
        if 'S' in duration:
            s = duration.split('S')[0]
            seconds += int(s)
        
        return seconds

if __name__ == "__main__":
    # Example usage
    try:
        extractor = YouTubeExtractor()
        sample_channels = [
            "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast
            "UCsBjURrPoezykLs9EqgamOA",  # Fireship
            "UC8butISFwT-Wl7EV0hUK0BQ"   # freeCodeCamp
        ]
        df = extractor.extract_profile_data(sample_channels)
        df.to_csv("youtube_data.csv", index=False)
        print("Data saved to youtube_data.csv")
    except ValueError as e:
        print(f"Error: {e}")