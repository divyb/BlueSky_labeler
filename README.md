# Community Safety Alert Labeler

## CS5342 Assignment 3 - Policy Proposal Implementation

### Team Members
- Divya Kheraj Bhanushali (dkb86), Akshat Chugh (ac3263), Yuya Tseng (yzt2)
- Cornell Tech, Fall 2025

---

## 🎯 Overview

The **Community Safety Alert Labeler** is a sophisticated Bluesky labeler designed to identify potentially sensitive immigration-related content that could lead to community safety concerns or panic. The labeler uses a multi-layer detection system to balance community safety with free speech considerations.

### Labeler Name: "Community Safety Alert"
*A non-triggering name that focuses on safety rather than targeting specific groups*

### Labels Generated:
1. **`sensitive-location`**: Contains specific location/timing information about potential enforcement activities
2. **`unverified-media`**: Contains media/links from unverified or suspicious sources
3. **`community-alert`**: Contains escalatory language that may cause community panic

---

## 🏗️ Architecture

### Three-Layer Detection System

```
Layer 1: Content Identification
├── Keyword Detection (Multi-language)
├── Temporal Markers
└── Context Analysis

Layer 2: Media/Link Analysis  
├── Source Verification
├── Suspicious Platform Detection
└── URL Shortener Detection

Layer 3: Escalation Detection
├── Panic Language Scanning
├── Mobilization Phrases
├── Fear-mongering Detection
└── Multi-language Evasion Detection
```

---

## 📊 Performance Metrics

Based on testing with 150 diverse posts:

| Metric | Value |
|--------|-------|
| **Overall Accuracy** | 53.33% |
| **Average Processing Time** | 0.06 ms |
| **95th Percentile Time** | 0.08 ms |

### Per-Label Performance:

| Label | Precision | Recall | F1 Score |
|-------|-----------|---------|----------|
| `sensitive-location` | 64.52% | 50.00% | 56.34% |
| `community-alert` | 68.00% | 39.53% | 50.00% |
| `unverified-media` | 71.43% | 25.00% | 37.04% |

---

## 🚀 Setup Instructions

### Prerequisites
```bash
# Python 3.8+ required
python3 --version

# Install dependencies
pip install pandas numpy atproto
```

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/bluesky-labeler.git
cd bluesky-labeler

# Install Python dependencies
pip install -r requirements.txt
```

### Configuration
1. Copy `.env-TEMPLATE` to `.env`
2. Add your Bluesky credentials:
```bash
USERNAME = "your.handle.bsky.social"
PW = "your-app-password"
```

---

## 🧪 Testing

### Run Basic Tests
```python
# Test without Bluesky connection
python3 test_evaluation.py
```

### Run with Bluesky Integration
```python
# Test with live Bluesky posts
python3 test_labeler.py labeler-inputs test-data/input-posts.csv
```

### Custom Test Data
The labeler includes a comprehensive test dataset (`data.csv`) with 150 posts covering:
- Location-specific threats
- Multi-language content
- Suspicious media links
- Legitimate news sources
- Unrelated content
- Various escalation levels

---

## 💻 Usage

### Basic Usage
```python
from atproto import Client
from policy_proposal_labeler import AutomatedLabeler

# Initialize client
client = Client()
client.login(USERNAME, PASSWORD)

# Create labeler
labeler = AutomatedLabeler(client)

# Moderate a post
labels = labeler.moderate_post("https://bsky.app/profile/user/post/id")
print(f"Labels: {labels}")
```

### Batch Processing
```python
import pandas as pd

# Load posts
posts = pd.read_csv('posts_to_check.csv')

# Process all posts
results = []
for url in posts['url']:
    labels = labeler.moderate_post(url)
    results.append({'url': url, 'labels': labels})
```

---

## 🔧 Configuration

### Adjustable Thresholds
Edit thresholds in `policy_proposal_labeler.py`:

```python
self.LOCATION_THRESHOLD = 15  # Sensitivity for location detection
self.MEDIA_THRESHOLD = 10     # Sensitivity for unverified media
self.ESCALATION_THRESHOLD = 15 # Sensitivity for panic language
```

### Supported Languages
- English (primary)
- Spanish
- Chinese (Mandarin)
- Arabic
- Hindi
- Russian

---

## 🛡️ Ethical Considerations

### Design Principles
1. **Graduated Response**: Labels provide information, not censorship
2. **User Control**: Users choose how to handle labeled content
3. **Transparency**: Clear labeling criteria and thresholds
4. **Cultural Sensitivity**: Multi-language support without discrimination

### Safeguards Against Misuse
- Does not target legitimate advocacy or journalism
- Verified news sources are whitelisted
- Focuses on panic-inducing content, not immigration discussion
- Regular false positive analysis and adjustment

### Potential Concerns
- **Over-labeling**: May flag legitimate warnings
- **Under-labeling**: Coded language may evade detection
- **Language Bias**: Better detection in English than other languages
- **Context Loss**: Cannot always distinguish satire or quotes

---

## 📈 Future Improvements

### Technical Enhancements
1. **Machine Learning Integration**: Train on labeled data for better accuracy
2. **Network Analysis**: Detect coordinated campaigns
3. **Image Analysis**: Detect location information in images
4. **Real-time Adaptation**: Adjust thresholds based on current events

### Policy Improvements
1. **Community Feedback Loop**: Allow users to report false positives
2. **Tiered Labeling**: Different severity levels within each category
3. **Time-based Decay**: Reduce label severity over time
4. **Geographic Customization**: Adjust for local contexts

---

## 📁 Project Structure

```
bluesky-labeler/
├── policy_proposal_labeler.py   # Main labeler implementation
├── test_evaluation.py            # Evaluation script
├── data.csv                      # Test dataset (150 posts)
├── evaluation_results.json       # Detailed test results
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── pylabel/                      # Bluesky integration module
    ├── __init__.py
    ├── automated_labeler.py      # Base labeler class
    └── label.py                  # Labeling utilities
```

---

## 📝 Files to Submit

1. **policy_proposal_labeler.py** - Main implementation (✓)
2. **data.csv** - Test dataset with 150 posts (✓)
3. **test_evaluation.py** - Testing and metrics script (✓)
4. **evaluation_results.json** - Detailed results (generated)
5. **README.md** - Documentation (✓)
6. **requirements.txt** - Dependencies (see below)
7. **Two-page report** - Summary of approach and results
8. **10-minute video** - Demonstration and analysis

---

## 🎥 Video Presentation Topics

1. **Motivation** (2 min)
   - Immigration-related panic and misinformation
   - Community safety vs. free speech

2. **Technical Approach** (3 min)
   - Three-layer detection system
   - Multi-language support
   - Evasion detection

3. **Demo** (2 min)
   - Live labeling demonstration
   - Test results visualization

4. **Evaluation** (2 min)
   - Performance metrics
   - Error analysis
   - Category breakdown

5. **Ethical Implications** (1 min)
   - Potential for misuse
   - Mitigation strategies
   - Future safeguards

---

## 📚 References

- [Bluesky Moderation Architecture](https://docs.bsky.app/blog/blueskys-moderation-architecture)
- [AT Protocol SDK Documentation](https://atproto.blue/en/latest/)
- [Community Notes Data](https://twitter.github.io/communitynotes/)
- [Perspective API](https://perspectiveapi.com/)

---

## 📬 Contact

For questions about this implementation:
- Course: CS5342 Trust and Safety
- Instructor: Professor Alexios Mantzarlis
- Institution: Cornell Tech

---

## ⚖️ License

This project is submitted as part of CS5342 coursework at Cornell Tech.
Educational use only.

---

*Last Updated: November 2025*
