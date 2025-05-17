# Social Media Metadata Extraction Pipeline

This project extracts and analyzes metadata from Instagram and YouTube creator profiles, enriching the data with engagement metrics, category detection, and audience analytics.

## Features

- Extract metadata from Instagram creator profiles using Instaloader
- Extract metadata from YouTube channels using the YouTube Data API v3
- Combine and enrich data with engagement rates, category detection, and more
- Generate structured output in CSV and JSON formats
- Create an analytics report with key insights and visualizations

## Project Structure

- `instagram_extractor.py` - Script for extracting data from Instagram profiles
- `youtube_extractor.py` - Script for extracting data from YouTube channels
- `data_processor.py` - Combines and enriches data from both platforms
- `main.py` - Main script to run the entire pipeline
- `app.py` - Script to run on streamlit server 
- `requirements.txt` - Dependencies list
- `output/` - Directory where output files are saved

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/23f1000965/scrap_users_data_yt_and_ig.git
   cd scrap_users_data_yt_and_ig
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up YouTube API credentials:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the YouTube Data API v3
   - Create API credentials (OAuth client ID or API key)
   - Save your API key in a `.env` file as `YOUTUBE_API_KEY=your_api_key_here`

## Usage

Run the pipeline with default settings:

```
python main.py
```
```
streamlit run app.py

````
Customize extraction with command line arguments:

```
python main.py --ig_usernames natgeo,nasa,instagram --yt_channels mkbhd,pewdiepie,tseries --output_dir output --format both
```

### Command Line Options

- `--ig_usernames`: Comma-separated list of Instagram usernames to extract
- `--yt_channels`: Comma-separated list of YouTube channel IDs or usernames
- `--output_dir`: Directory to save output files (default: output)
- `--format`: Output format - csv, json, or both (default: both)

## Output Files

The pipeline generates the following files:

- `instagram_data.json`: Raw Instagram data
- `youtube_data.json`: Raw YouTube data
- `metadata.csv`: Combined and enriched data in CSV format
- `metadata.json`: Combined and enriched data in JSON format
- `analytics_report.md`: Markdown report with summary analytics and insights

## Data Fields

Each creator profile includes:

### Basic Info
- Name
- Username/Channel ID
- Bio/Description
- Profile/Channel Link

### Audience Data
- Followers/Subscribers
- Top geographies (when available)
- Gender ratio (when available)
- Language

### Engagement Stats
- Average likes per post/video
- Average comments per post/video
- Average views per video (YouTube only)
- Engagement rate calculation
- Posting frequency (posts per week)

### Enriched Data
- Category detection based on content keywords
- Follower growth estimation
- Comparative platform metrics

## Limitations

- Instagram data extraction is limited to public profiles and available data
- YouTube API has daily quota limits
- Audience demographics are estimates and may not be fully accurate
- Category detection is keyword-based and may not always be precise
