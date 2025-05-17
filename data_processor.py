import pandas as pd
import json
import re
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import os
import math

class DataProcessor:
    def __init__(self):
        self.instagram_data = None
        self.youtube_data = None
        self.combined_data = None
        
        # Category keywords for classification
        self.category_keywords = {
            'fashion': ['fashion', 'style', 'outfit', 'clothing', 'model', 'beauty'],
            'tech': ['tech', 'technology', 'coding', 'programming', 'gadget', 'software'],
            'food': ['food', 'recipe', 'cooking', 'chef', 'cuisine', 'baking'],
            'fitness': ['fitness', 'workout', 'gym', 'exercise', 'health', 'training'],
            'travel': ['travel', 'destination', 'adventure', 'journey', 'explore'],
            'gaming': ['game', 'gaming', 'gamer', 'streamer', 'esports', 'playstation'],
            'education': ['education', 'learn', 'school', 'college', 'university'],
            'entertainment': ['entertainment', 'fun', 'comedy', 'funny', 'humor'],
            'music': ['music', 'song', 'artist', 'band', 'singer', 'musician']
        }
    
    def load_instagram_data(self, file_path):
        """Load Instagram data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.instagram_data = json.load(f)
            print(f"Loaded Instagram data: {len(self.instagram_data)} profiles")
        except Exception as e:
            print(f"Error loading Instagram data: {e}")
    
    def load_youtube_data(self, file_path):
        """Load YouTube data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.youtube_data = json.load(f)
            print(f"Loaded YouTube data: {len(self.youtube_data)} profiles")
        except Exception as e:
            print(f"Error loading YouTube data: {e}")
    
    def detect_category(self, text):
        """Detect category based on keywords in text"""
        if not text or not isinstance(text, str):
            return "unknown"
            
        text = text.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            category_scores[category] = score
        
        # Get the category with highest score
        if max(category_scores.values()) > 0:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        else:
            return "other"
    
    def calculate_engagement_rate(self, avg_engagement, followers):
        """Calculate engagement rate as (likes + comments) / followers * 100"""
        if followers and followers > 0:
            return (avg_engagement / followers) * 100
        return 0
    
    def enrich_data(self):
        """Enrich data with additional calculations and insights"""
        if not self.instagram_data and not self.youtube_data:
            print("No data to enrich. Please load data first.")
            return
        
        combined = []
        
        # Process Instagram data
        if self.instagram_data:
            for profile in self.instagram_data:
                # Calculate engagement metrics
                avg_likes = profile.get('avg_likes', 0)
                avg_comments = profile.get('avg_comments', 0)
                followers = profile.get('followers', 0)
                
                # Calculate engagement rate
                engagement_rate = self.calculate_engagement_rate(avg_likes + avg_comments, followers)
                
                # Detect category
                bio = profile.get('bio', '')
                category = self.detect_category(bio)
                
                # Add enriched data
                enriched_profile = profile.copy()
                enriched_profile.update({
                    'platform': 'Instagram',
                    'engagement_rate': round(engagement_rate, 2),
                    'category': category,
                    'total_avg_engagement': avg_likes + avg_comments
                })
                
                combined.append(enriched_profile)
        
        # Process YouTube data
        if self.youtube_data:
            for profile in self.youtube_data:
                # Calculate engagement metrics
                avg_likes = profile.get('avg_likes', 0)
                avg_comments = profile.get('avg_comments', 0)
                subscribers = profile.get('followers', 0)  # Use 'followers' directly here
                
                # Calculate engagement rate
                engagement_rate = self.calculate_engagement_rate(avg_likes + avg_comments, subscribers)
                
                # Detect category
                description = profile.get('bio', '')
                category = self.detect_category(description)
                
                # Add enriched data
                enriched_profile = profile.copy()
                enriched_profile.update({
                    'platform': 'YouTube',
                    'engagement_rate': round(engagement_rate, 2),
                    'category': category,
                    'total_avg_engagement': avg_likes + avg_comments
                })
                
                combined.append(enriched_profile)
        
        # Create pandas DataFrame for easier manipulation
        self.combined_data = pd.DataFrame(combined)
        print(f"Enriched {len(self.combined_data)} profiles")
    
    def save_to_csv(self, file_path):
        """Save combined data to CSV file with all fields from both platforms"""
        if self.combined_data is None:
            print("No data to save. Please enrich data first.")
            return
        
        try:
            # Sort by platform and then by followers (descending)
            sorted_df = self.combined_data.sort_values(by=['platform', 'followers'], ascending=[True, False])
            
            # Define column order to include all fields from both platforms
            column_order = [
                # Platform identifier
                'platform',
                
                # Basic profile info
                'username', 
                'name',
                'bio', 
                'profile_link',
                
                # Audience metrics
                'followers',
                'following',
                'posts_count',
                'is_private',  # Instagram specific
                
                # Engagement metrics
                'avg_likes',
                'avg_comments',
                'avg_views',  # YouTube specific
                'engagement_rate',
                'posting_frequency',
                
                # Content categorization
                'category',
                
                # Growth and demographics
                'estimated_weekly_growth',
                'top_geographies',
                'gender_ratio',
                'language'
            ]
            
            # Filter to only include columns that exist in the dataframe
            available_columns = [col for col in column_order if col in sorted_df.columns]
            
            # Rearrange columns and fill missing values with "N/A"
            sorted_df = sorted_df[available_columns].fillna("N/A")
            
            # Save to CSV
            sorted_df.to_csv(file_path, index=False)
            print(f"Saved combined data to {file_path}")
            
            # Create a summary CSV with key metrics
            summary_file = file_path.replace('.csv', '_summary.csv')
            summary_columns = ['platform', 'username', 'name', 'followers', 'engagement_rate', 'category', 'posting_frequency']
            summary_available = [col for col in summary_columns if col in sorted_df.columns]
            summary_df = sorted_df[summary_available].copy()
            summary_df.to_csv(summary_file, index=False)
            print(f"Created summary metrics file at {summary_file}")
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")
    
    def save_to_json(self, file_path):
        """Save combined data to JSON file"""
        if self.combined_data is None:
            print("No data to save. Please enrich data first.")
            return
        
        try:
            # Convert DataFrame to dict records
            json_data = self.combined_data.to_dict(orient='records')
            
            # Clean NaN values
            clean_json_data = self._clean_nan_values(json_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(clean_json_data, f, indent=4, ensure_ascii=False)
            print(f"Saved combined data to {file_path}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")
    
    def generate_analytics_report(self, file_path):
        """Generate a comprehensive analytics report in Markdown format"""
        if self.combined_data is None:
            print("No data to analyze. Please enrich data first.")
            return
        
        import matplotlib.pyplot as plt
        import seaborn as sns
        import os
        
        # Create directory for charts
        charts_dir = os.path.dirname(file_path) + "/charts"
        os.makedirs(charts_dir, exist_ok=True)
        
        # Get data by platform
        ig_data = self.combined_data[self.combined_data['platform'] == 'Instagram']
        yt_data = self.combined_data[self.combined_data['platform'] == 'YouTube']
        
        report = []
        report.append("# Social Media Creator Analytics Report\n")
        report.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n")
        
        # Executive Summary
        report.append("## Executive Summary\n")
        total_profiles = len(self.combined_data)
        total_followers = self.combined_data['followers'].sum()
        avg_engagement = self.combined_data['engagement_rate'].mean()
        
        report.append(f"This report analyzes **{total_profiles}** creator profiles across Instagram and YouTube with a ")
        report.append(f"combined audience of **{total_followers:,}** followers. ")
        report.append(f"The average engagement rate across all profiles is **{avg_engagement:.2f}%**.\n")
        
        # Create platform comparison chart
        plt.figure(figsize=(10, 6))
        platform_data = self.combined_data.groupby('platform').agg({
            'followers': 'sum',
            'engagement_rate': 'mean',
            'posting_frequency': 'mean'
        }).reset_index()
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Followers by platform
        sns.barplot(x='platform', y='followers', data=platform_data, ax=axes[0])
        axes[0].set_title('Total Followers')
        axes[0].set_ylabel('Followers')
        
        # Engagement rate by platform
        sns.barplot(x='platform', y='engagement_rate', data=platform_data, ax=axes[1])
        axes[1].set_title('Avg. Engagement Rate (%)')
        axes[1].set_ylabel('Engagement Rate (%)')
        
        # Posting frequency by platform
        sns.barplot(x='platform', y='posting_frequency', data=platform_data, ax=axes[2])
        axes[2].set_title('Avg. Posts per Week')
        axes[2].set_ylabel('Posts per Week')
        
        plt.tight_layout()
        platform_chart_path = f"{charts_dir}/platform_comparison.png"
        plt.savefig(platform_chart_path)
        plt.close()
        
        report.append("## Platform Comparison\n")
        report.append(f"![Platform Comparison](charts/platform_comparison.png)\n")
        
        if not ig_data.empty:
            ig_avg_engagement = ig_data['engagement_rate'].mean()
            report.append(f"**Instagram creators** average an engagement rate of {ig_avg_engagement:.2f}% ")
            report.append(f"and post approximately {ig_data['posting_frequency'].mean():.1f} times per week.\n")
        
        if not yt_data.empty:
            yt_avg_engagement = yt_data['engagement_rate'].mean()
            report.append(f"**YouTube creators** average an engagement rate of {yt_avg_engagement:.2f}% ")
            report.append(f"and post approximately {yt_data['posting_frequency'].mean():.1f} videos per week.\n")
        
        # Top Performers
        report.append("## Top Performers\n")
        
        # Top by followers
        top_followers = self.combined_data.sort_values('followers', ascending=False).head(5)
        report.append("### Top 5 Creators by Followers\n")
        report.append("| Creator | Platform | Followers | Engagement Rate |\n")
        report.append("|---------|----------|-----------|----------------|\n")
        
        for _, row in top_followers.iterrows():
            report.append(f"| {row['name']} | {row['platform']} | {row['followers']:,} | {row['engagement_rate']:.2f}% |\n")
        
        report.append("\n")
        
        # Top by engagement
        top_engagement = self.combined_data.sort_values('engagement_rate', ascending=False).head(5)
        report.append("### Top 5 Creators by Engagement Rate\n")
        report.append("| Creator | Platform | Engagement Rate | Followers |\n")
        report.append("|---------|----------|----------------|----------|\n")
        
        for _, row in top_engagement.iterrows():
            report.append(f"| {row['name']} | {row['platform']} | {row['engagement_rate']:.2f}% | {row['followers']:,} |\n")
        
        report.append("\n")
        
        # Category Distribution
        report.append("## Content Category Analysis\n")
        
        # Create category chart
        plt.figure(figsize=(12, 6))
        category_counts = self.combined_data['category'].value_counts()
        
        plt.figure(figsize=(10, 6))
        sns.countplot(y='category', data=self.combined_data, order=category_counts.index)
        plt.title('Content Categories')
        plt.xlabel('Number of Creators')
        plt.ylabel('Category')
        plt.tight_layout()
        
        category_chart_path = f"{charts_dir}/category_distribution.png"
        plt.savefig(category_chart_path)
        plt.close()
        
        report.append(f"![Category Distribution](charts/category_distribution.png)\n")
        
        # Category insights
        top_category = category_counts.index[0] if not category_counts.empty else "N/A"
        report.append(f"The most common content category is **{top_category}** with {category_counts.iloc[0]} creators. ")
        
        # Compare engagement by category
        category_engagement = self.combined_data.groupby('category')['engagement_rate'].mean().sort_values(ascending=False)
        best_category = category_engagement.index[0] if not category_engagement.empty else "N/A"
        
        report.append(f"The **{best_category}** category has the highest average engagement rate ")
        report.append(f"at {category_engagement.iloc[0]:.2f}%.\n")
        
        # Create engagement by category chart
        plt.figure(figsize=(12, 6))
        sns.barplot(x='engagement_rate', y='category', 
                    data=self.combined_data, 
                    order=category_engagement.index)
        plt.title('Average Engagement Rate by Category')
        plt.xlabel('Engagement Rate (%)')
        plt.ylabel('Category')
        plt.tight_layout()
        
        category_engagement_path = f"{charts_dir}/category_engagement.png"
        plt.savefig(category_engagement_path)
        plt.close()
        
        report.append(f"![Engagement by Category](charts/category_engagement.png)\n")
        
        # Correlation Analysis
        report.append("## Relationship Between Followers and Engagement\n")
        
        # Create scatter plot
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=self.combined_data, x='followers', y='engagement_rate', hue='platform')
        plt.title('Engagement Rate vs. Followers')
        plt.xlabel('Followers (log scale)')
        plt.ylabel('Engagement Rate (%)')
        plt.xscale('log')
        plt.tight_layout()
        
        follower_engagement_path = f"{charts_dir}/follower_engagement.png"
        plt.savefig(follower_engagement_path)
        plt.close()
        
        report.append(f"![Followers vs Engagement](charts/follower_engagement.png)\n")
        
        # Calculate correlation
        correlation = self.combined_data[['followers', 'engagement_rate']].corr().iloc[0, 1]
        
        if correlation < -0.3:
            report.append("There is a **negative correlation** between follower count and engagement rate. ")
            report.append("Creators with smaller audiences tend to have higher engagement rates, ")
            report.append("likely due to more intimate community connections.\n")
        elif correlation > 0.3:
            report.append("There is a **positive correlation** between follower count and engagement rate. ")
            report.append("More popular creators tend to generate higher engagement, ")
            report.append("suggesting quality content that scales well with audience size.\n")
        else:
            report.append("There is **little correlation** between follower count and engagement rate. ")
            report.append("Engagement appears to be driven by factors other than audience size, ")
            report.append("such as content quality, posting consistency, and niche appeal.\n")
        
        # Recommendations Section
        report.append("## Recommendations\n")
        
        report.append("Based on the analysis, we recommend:\n\n")
        
        # Generate dynamic recommendations
        if ig_data.empty or yt_data.empty:
            report.append("1. **Expand platform presence**: Consider adding creators from additional platforms ")
            report.append("to diversify your creator portfolio.\n")
        
        # Recommend focusing on high-engagement categories
        if not category_engagement.empty:
            top_categories = category_engagement.head(2).index.tolist()
            report.append(f"2. **Focus on high-engagement categories**: The {' and '.join(top_categories)} ")
            report.append("categories show the highest engagement rates. Consider adding more creators ")
            report.append("from these categories.\n")
        
        # Posting frequency recommendation
        high_engagement_profiles = self.combined_data.sort_values('engagement_rate', ascending=False).head(5)
        optimal_frequency = high_engagement_profiles['posting_frequency'].mean()
        
        report.append(f"3. **Optimize posting frequency**: Top-performing creators post approximately ")
        report.append(f"{optimal_frequency:.1f} times per week. Consider this benchmark when planning content calendars.\n")
        
        report.append("4. **Balance follower size with engagement**: While large follower counts provide reach, ")
        report.append("creators with moderate follower counts but higher engagement rates often provide ")
        report.append("better ROI for partnerships and campaigns.\n")
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(''.join(report))
        
        print(f"Generated analytics report at {file_path}")
    
    def save_platform_specific_csv(self, output_dir):
        """Save separate CSV files for each platform"""
        if self.combined_data is None:
            print("No data to save. Please enrich data first.")
            return
        
        try:
            # Split by platform
            instagram_df = self.combined_data[self.combined_data['platform'] == 'Instagram']
            youtube_df = self.combined_data[self.combined_data['platform'] == 'YouTube']
            
            # Save separate files
            instagram_path = os.path.join(output_dir, "instagram_metrics.csv")
            youtube_path = os.path.join(output_dir, "youtube_metrics.csv")
            
            instagram_df.to_csv(instagram_path, index=False)
            youtube_df.to_csv(youtube_path, index=False)
            
            print(f"Saved platform-specific CSV files in {output_dir}")
        except Exception as e:
            print(f"Error saving platform-specific CSVs: {e}")
    
    def _clean_nan_values(self, data):
        """Replace NaN values with appropriate defaults before JSON conversion"""
        cleaned_data = []
        
        for item in data:
            clean_item = {}
            for key, value in item.items():
                # Handle different types of NaN values
                if isinstance(value, float) and math.isnan(value):
                    if key in ['avg_views', 'max_views', 'total_views', 'engagement_rate', 'view_engagement_rate']:
                        clean_item[key] = 0
                    elif key in ['is_private', 'is_verified']:
                        clean_item[key] = False
                    else:
                        clean_item[key] = None
                elif isinstance(value, dict):
                    # Clean NaN values in nested dictionaries
                    clean_nested = {}
                    for k, v in value.items():
                        if isinstance(v, float) and math.isnan(v):
                            clean_nested[k] = 0
                        else:
                            clean_nested[k] = v
                    clean_item[key] = clean_nested
                else:
                    clean_item[key] = value
            
            # Handle platform-specific fields
            if item.get('platform') == 'Instagram':
                if 'video_distribution' not in clean_item or clean_item['video_distribution'] is None:
                    clean_item['video_distribution'] = {}
                if 'recent_videos' not in clean_item or clean_item['recent_videos'] is None:
                    clean_item['recent_videos'] = []
                    
            elif item.get('platform') == 'YouTube':
                if 'media_distribution' not in clean_item or clean_item['media_distribution'] is None:
                    clean_item['media_distribution'] = {}
                if 'recent_posts' not in clean_item or clean_item['recent_posts'] is None:
                    clean_item['recent_posts'] = []
            
            cleaned_data.append(clean_item)
        
        return cleaned_data
