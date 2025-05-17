import os
import argparse
from instagram_extractor import InstagramExtractor
from youtube_extractor import YouTubeExtractor
from data_processor import DataProcessor
import time
import random
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    INSTAGRAM_API_KEY = os.getenv("INSTAGRAM_API_KEY")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    
    parser = argparse.ArgumentParser(description='Social Media Metadata Extraction Pipeline')
    parser.add_argument('--ig_usernames', type=str, help='Output format (only JSON supported)')
    parser.add_argument('--yt_channels', type=str, help='Output format (only JSON supported)')
    parser.add_argument('--output_dir', type=str, default='output', help='Directory to save output files')
    parser.add_argument('--format', type=str, default='json', help='Output format (only JSON supported)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Default creators if none provided
    if args.ig_usernames is None:
        args.ig_usernames = "natgeo"
    
    if args.yt_channels is None:
        args.yt_channels = "tseries"
    
    # Parse usernames/channels into lists
    instagram_usernames = [username.strip() for username in args.ig_usernames.split(',')]
    youtube_channels = [channel.strip() for channel in args.yt_channels.split(',')]
    
    print("=== Social Media Metadata Extraction Pipeline ===")
    
    # Step 1: Extract Instagram data
    print("\n--- Instagram Extraction ---")
    ig_extractor = InstagramExtractor(api_key=INSTAGRAM_API_KEY)  # Pass the API key
    
    # Limit to only 5 profiles
    instagram_usernames = instagram_usernames[:3]
    print(f"Limited to 3 Instagram profiles: {', '.join(instagram_usernames)}")
    
    for username in instagram_usernames:
        print(f"Processing Instagram profile: {username}")
        ig_extractor.extract_profile_data(username)
        # Add longer delay between profiles (5-10 seconds)
        time.sleep(random.uniform(5, 10))
    
    # Save Instagram data
    instagram_data_path = os.path.join(args.output_dir, "instagram_data.json")
    ig_extractor.save_data(instagram_data_path)
    
    # Step 2: Extract YouTube data
    print("\n--- YouTube Extraction ---")
    yt_extractor = YouTubeExtractor(api_key=YOUTUBE_API_KEY)  # Pass the API key
    for channel in youtube_channels:
        print(f"Processing YouTube channel: {channel}")
        yt_extractor.extract_channel(channel)
    
    # Save YouTube data
    youtube_data_path = os.path.join(args.output_dir, "youtube_data.json")
    yt_extractor.save_data(youtube_data_path)
    
    # Step 3: Process and enrich data
    print("\n--- Data Processing and Enrichment ---")
    processor = DataProcessor()
    processor.load_instagram_data(instagram_data_path)
    processor.load_youtube_data(youtube_data_path)
    processor.enrich_data()
    
    # Step 4: Save combined data
    
    if args.format in ['json', 'both']:
        json_path = os.path.join(args.output_dir, "metadata.json")
        processor.save_to_json(json_path)
    
    # Step 5: Generate analytics report
    print("\n--- Generating Analytics Report ---")
    report_path = os.path.join(args.output_dir, "analytics_report.md")
    processor.generate_analytics_report(report_path)
    
    print("\n=== Pipeline Completed Successfully ===")
    print(f"Output files saved to: {os.path.abspath(args.output_dir)}")

if __name__ == "__main__":
    main()