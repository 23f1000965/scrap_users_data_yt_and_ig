import streamlit as st
import os
import tempfile
import pandas as pd
import json
import base64
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from io import BytesIO
import time
import random
from functools import lru_cache
from dotenv import load_dotenv

# Page configuration MUST be the first Streamlit command
st.set_page_config(
    page_title="Social Media Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load environment variables from .env file
load_dotenv()

# Access API keys - move the visual feedback to after page config
INSTAGRAM_API_KEY = None
YOUTUBE_API_KEY = None

try:
    # Try to load from Streamlit secrets (for deployed app)
    INSTAGRAM_API_KEY = st.secrets["INSTAGRAM_API_KEY"]
    api_status_ig = "✅ Loaded Instagram API key from Streamlit secrets"
except:
    # Fall back to .env file (for local development)
    INSTAGRAM_API_KEY = os.getenv("INSTAGRAM_API_KEY")
    if INSTAGRAM_API_KEY:
        api_status_ig = "✅ Loaded Instagram API key from .env file"
    else:
        api_status_ig = "❌ Instagram API key not found"

try:
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
    api_status_yt = "✅ Loaded YouTube API key from Streamlit secrets"
except:
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    if YOUTUBE_API_KEY:
        api_status_yt = "✅ Loaded YouTube API key from .env file"
    else:
        api_status_yt = "❌ YouTube API key not found"

# Import your existing extractors and processor
from instagram_extractor import InstagramExtractor
from youtube_extractor import YouTubeExtractor
from data_processor import DataProcessor

# Title and description
st.title("📊 Social Media Analytics Dashboard")
st.markdown("""
Extract detailed analytics from Instagram and YouTube creator profiles. 
Get insights on engagement metrics, audience demographics, and content performance.
""")

# Sidebar for inputs
st.sidebar.header("Configuration")

# Platform selection
platform = st.sidebar.radio(
    "Select Platform",
    ["Instagram", "YouTube", "Both"]
)

# Use default accounts option
use_default = st.sidebar.checkbox("Use default accounts", value=False)

# Add demo mode option
use_demo_data = st.sidebar.checkbox("Use demo data (avoid API limits)", value=True)

# Default accounts
default_instagram = ["natgeo", "nasa", "instagram"]
default_youtube = ["tseries", "MrBeast", "PewDiePie"]

# Username inputs
if platform in ["Instagram", "Both"]:
    st.sidebar.subheader("Instagram Accounts")
    if use_default:
        instagram_accounts = st.sidebar.multiselect(
            "Select Instagram accounts",
            options=default_instagram,
            default=default_instagram[:1]
        )
    else:
        instagram_input = st.sidebar.text_input(
            "Enter Instagram usernames (comma-separated)",
            placeholder="e.g., natgeo, nasa, instagram"
        )
        instagram_accounts = [u.strip() for u in instagram_input.split(",")] if instagram_input else []

if platform in ["YouTube", "Both"]:
    st.sidebar.subheader("YouTube Channels")
    if use_default:
        youtube_channels = st.sidebar.multiselect(
            "Select YouTube channels",
            options=default_youtube,
            default=default_youtube[:1]
        )
    else:
        youtube_input = st.sidebar.text_input(
            "Enter YouTube channel names (comma-separated)",
            placeholder="e.g., tseries, MrBeast, PewDiePie"
        )
        youtube_channels = [c.strip() for c in youtube_input.split(",")] if youtube_input else []

# Analyze button
analyze_button = st.sidebar.button("🔍 Analyze Profiles", type="primary")

# Create temp directory for outputs
output_dir = tempfile.mkdtemp()

# Function to create download link
def get_download_link(file_path, link_text):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
    return href

# Add caching to reduce API calls
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_youtube_data(extractor, channel_id):
    try:
        return extractor.extract_channel(channel_id)
    except Exception as e:
        st.error(f"YouTube API error: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_instagram_data(extractor, username):
    try:
        return extractor.extract_profile_data(username)
    except Exception as e:
        st.error(f"Instagram API error: {str(e)}")
        return None

# Function to run analysis
def run_analysis():
    try:
        with st.spinner("Extracting and analyzing data... This may take a minute"):
            progress = st.progress(0)
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Extract Instagram data
            instagram_data_path = None
            if platform in ["Instagram", "Both"] and instagram_accounts:
                st.write("### Instagram Extraction")
                progress_text = st.empty()
                
                # Initialize Instagram extractor
                ig_extractor = InstagramExtractor(api_key=INSTAGRAM_API_KEY)
                
                for i, username in enumerate(instagram_accounts):
                    try:
                        progress_text.write(f"Processing Instagram profile: {username}")
                        result = ig_extractor.extract_profile_data(username)
                        
                        # Check for rate limit or errors
                        if result is None:
                            st.warning(f"Could not extract data for {username}")
                        else:
                            st.success(f"Successfully extracted data for {username}")
                        
                        progress.progress((i + 1) / len(instagram_accounts) * 0.4)
                    except Exception as e:
                        if "429" in str(e) or "rate limit" in str(e).lower():
                            st.error(f"⚠️ API Rate Limit Reached for Instagram! Please try again later.")
                            return None, None, None
                        else:
                            st.warning(f"Error processing {username}: {str(e)}")
                
                # Save Instagram data
                if ig_extractor.profiles_data:
                    instagram_data_path = os.path.join(output_dir, "instagram_data.json")
                    ig_extractor.save_data(instagram_data_path)
                    st.success(f"✅ Successfully processed {len(ig_extractor.profiles_data)} Instagram profiles")
                else:
                    st.warning("No Instagram data was extracted")
            
            # Step 2: Extract YouTube data
            youtube_data_path = None
            if platform in ["YouTube", "Both"] and youtube_channels:
                st.write("### YouTube Extraction")
                progress_text = st.empty()
                
                # Initialize YouTube extractor
                yt_extractor = YouTubeExtractor(api_key=YOUTUBE_API_KEY)
                
                for i, channel in enumerate(youtube_channels):
                    try:
                        progress_text.write(f"Processing YouTube channel: {channel}")
                        result = yt_extractor.extract_channel(channel)
                        
                        if result is None:
                            st.warning(f"Could not extract data for {channel}")
                        else:
                            st.success(f"Successfully extracted data for {channel}")
                        
                        # More careful rate limit detection
                        if result is None:
                            st.warning(f"No result returned for {channel}")
                        elif isinstance(result, dict) and result.get('error_code') == 429:
                            st.error(f"⚠️ API Rate Limit Reached for YouTube! Please try again later or use a different API key.")
                            return None, None, None
                        
                        progress.progress(0.4 + (i + 1) / len(youtube_channels) * 0.4)
                    except Exception as e:
                        error_message = str(e).lower()
                        
                        # Only trigger for actual rate limit errors
                        if "quotaexceeded" in error_message or ("429" in error_message and "rate limit" in error_message):
                            st.error(f"⚠️ API Rate Limit Reached for YouTube! Please try again later or use a different API key.")
                            return None, None, None
                        else:
                            st.warning(f"Error processing {channel}: {str(e)}")
                            # Continue processing instead of stopping
                
                # Save YouTube data
                youtube_data_path = os.path.join(output_dir, "youtube_data.json")
                yt_extractor.save_data(youtube_data_path)
                progress_text.write("✅ YouTube data extraction complete")
            
            # Step 3: Process and combine data
            processor = DataProcessor()
            
            if instagram_data_path and os.path.exists(instagram_data_path):
                processor.load_instagram_data(instagram_data_path)
            
            if youtube_data_path and os.path.exists(youtube_data_path):
                processor.load_youtube_data(youtube_data_path)
            
            if processor.instagram_data or processor.youtube_data:
                processor.enrich_data()
                progress.progress(0.9)  # 90% progress
                
                # Save combined data
                json_path = os.path.join(output_dir, "metadata.json")
                processor.save_to_json(json_path)
                
                # Generate analytics report
                report_path = os.path.join(output_dir, "analytics_report.md")
                processor.generate_analytics_report(report_path)
                
                progress.progress(1.0)  # 100% complete
                
                if processor.instagram_data:
                    st.success(f"✅ Instagram data loaded: {len(processor.instagram_data)} profiles")
                if processor.youtube_data:
                    st.success(f"✅ YouTube data loaded: {len(processor.youtube_data)} profiles")
                
                if processor.combined_data is None or len(processor.combined_data) == 0:
                    st.error("No data was processed. Check if the DataProcessor.enrich_data() method is working correctly.")
                    # Try to create a minimal valid DataFrame to prevent errors
                    processor.combined_data = pd.DataFrame({
                        'name': ['Test'],
                        'platform': ['Test'],
                        'followers': [0],
                        'engagement_rate': [0],
                        'category': ['Unknown']
                    })
                
                return json_path, report_path, processor.combined_data
            else:
                st.error("No data was extracted. Please check the usernames/channels and try again.")
                return None, None, None
                
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")
        return None, None, None

# Main app flow
if analyze_button:
    if (platform in ["Instagram", "Both"] and not instagram_accounts) or \
       (platform in ["YouTube", "Both"] and not youtube_channels):
        st.error("Please enter at least one username/channel or select 'Use default accounts'")
    else:
        # Run analysis
        json_path, report_path, data_df = run_analysis()
        
        # Check if analysis completed successfully
        if json_path and report_path and data_df is not None:
            # Display success message
            st.success("Analysis complete! 🎉")
            
            # Dashboard tabs
            tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Raw Data", "📝 Report"])
            
            with tab1:
                st.header("Creator Analytics Dashboard")
                
                # Key metrics in cards
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Profiles", f"{len(data_df)}")
                
                with col2:
                    st.metric("Total Followers", f"{data_df['followers'].sum():,}")
                
                with col3:
                    st.metric("Avg. Engagement", f"{data_df['engagement_rate'].mean():.2f}%")
                
                with col4:
                    st.metric("Content Categories", f"{data_df['category'].nunique()}")
                
                # Profile comparison chart
                st.subheader("Profile Comparison")
                fig, ax = plt.subplots(figsize=(10, 6))
                sorted_df = data_df.sort_values('followers', ascending=False)
                
                sns.barplot(x='name', y='followers', hue='platform', data=sorted_df, ax=ax)
                ax.set_title('Followers by Profile')
                ax.set_xlabel('')
                ax.set_ylabel('Followers')
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
                
                # Engagement chart
                st.subheader("Engagement Analysis")
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x='name', y='engagement_rate', hue='platform', data=sorted_df, ax=ax)
                ax.set_title('Engagement Rate by Profile')
                ax.set_xlabel('')
                ax.set_ylabel('Engagement Rate (%)')
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
                
                # Content category analysis if available
                if 'category' in data_df.columns:
                    st.subheader("Content Categories")
                    category_counts = data_df['category'].value_counts().reset_index()
                    category_counts.columns = ['category', 'count']
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x='count', y='category', data=category_counts, ax=ax)
                    ax.set_title('Content Category Distribution')
                    ax.set_xlabel('Number of Profiles')
                    plt.tight_layout()
                    st.pyplot(fig)
                
                # Download section
                st.subheader("Download Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(get_download_link(json_path, "📥 Download JSON Data"), unsafe_allow_html=True)
                
                with col2:
                    st.markdown(get_download_link(report_path, "📥 Download Markdown Report"), unsafe_allow_html=True)
            
            with tab2:
                st.header("Raw Data")
                
                # Display the JSON data
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Pretty display the JSON
                st.json(json_data)
                
                # Display as a dataframe
                st.subheader("Data Table")
                st.dataframe(data_df)
            
            with tab3:
                st.header("Analytics Report")
                
                # Read and display the markdown report
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                st.markdown(report_content)
        else:
            st.info("Please adjust your selection and try again. If you keep hitting rate limits, try again later.")
else:
    # Show welcome information
    st.info("👈 Select platform and enter usernames in the sidebar, then click 'Analyze Profiles'")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Features")
        st.markdown("""
        - Extract data from Instagram and YouTube profiles
        - Calculate engagement metrics and audience insights
        - Generate beautiful visualizations
        - Download comprehensive reports
        - Export raw data in JSON format
        """)
    
    with col2:
        st.subheader("How to Use")
        st.markdown("""
        1. Select platform(s) in the sidebar
        2. Enter usernames or select default accounts
        3. Click "Analyze Profiles" button
        4. View results in the dashboard
        5. Download reports for sharing
        """)

