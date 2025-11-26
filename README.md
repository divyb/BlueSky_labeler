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

## 📐 Scoring Model

Each post is analyzed by multiple detection layers. Each layer generates a numeric score based on matched patterns. The final label decision is made by comparing combined scores against thresholds.

### Keyword Score Calculation
- Each primary ICE term matched (ice, raid, detained, custody, etc.): **+8 points**
- Each high-severity term matched (died in custody, brutal, warrantless): **+15 points**
- Each Spanish term matched (redada, migra, deportación): **+10 points**
- Each amplifier matched (breaking, urgent, confirmed): **+4 points**
- Bonus if primary terms + amplifiers found together: **+8 points**
- Bonus if high-severity + any other match: **+10 points**

### Location Score Calculation
- Each street address detected: **+20 points**
- GPS coordinates detected: **+30 points**
- Each sensitive place mentioned (school, church, hospital): **+15 points**
- Each temporal marker (now, today, urgent): **+3 points**

### Media Score Calculation
- Each unverified URL: **+10 points**
- Each suspicious platform URL (Telegram, Parler, etc.): **+15 points**

### Escalation Score Calculation
- Each panic phrase (spread this, share now): **+8 points**
- Each mobilization phrase (gather at, resist): **+10 points**
- Each fear phrase (they are coming, stay away): **+7 points**
- Each news concern phrase (taken into custody, found dead): **+6 points**
- Violence terms detected: **+25 points**
- ALL CAPS words: **+2 points each** (max 10)
- Excessive exclamation marks (3+): **up to +8 points**

### Final Label Decision

**For `community-alert` label:**
```
Total = escalation_score + (keyword_score × 0.8)
If Total ≥ 10 → apply label
OR if keyword_score alone ≥ 15 → apply label (direct detection fallback)
```

**For `sensitive-location` label:**
```
If location_score ≥ 12 → apply label
```

**For `unverified-media` label:**
```
If media_score ≥ 8 → apply label
```

---
## Data 
We tested out labler in 3 iterations, each iterations uses differnt type of data. 
The reason why we decides to use 3 different types of data is because people may spam using llm generated post to spam bluesky, we are trying to see if the labler can label these posts properly

`Iteration 1 `: using just synthetic data  (210 posts)
   - data collection process : generated using LLM, such as DeepSeek

`Iteration 2` : using actual post data (106 posts)
   -  data collection process : we collect the posts by looking through BlueSky platform

`Iteration 3` : using both synthetic and actual post data (316 posts in total)
   - we take all the actual post from bluesky, and combined with some synthetic ones.- - 66.45 % sythetic, 33.55 % actual post from BlueSky

---

## 📊 Performance Metrics

### Iteration 1: Test Dataset (150 posts)

| Metric | Value |
|--------|-------|
| **Overall Accuracy** | 53.33% |
| **Average Processing Time** | 0.06 ms |
| **95th Percentile Time** | 0.08 ms |

### Per-Label Performance (Iteration 1):

| Label | Precision | Recall | F1 Score |
|-------|-----------|---------|----------|
| `sensitive-location` | 64.52% | 50.00% | 56.34% |
| `community-alert` | 68.00% | 39.53% | 50.00% |
| `unverified-media` | 71.43% | 25.00% | 37.04% |

### Iteration 2: Actual Posts from Bluesky (106 posts)

Based on testing with 106 actual posts collected from Bluesky:

| Metric | Value |
|--------|-------|
| **Total Posts** | 106 |
| **Valid Posts** | 103 |
| **Posts with Labels** | 19 (18.4%) |
| **Posts without Labels** | 84 (81.6%) |
| **Average Processing Time** | 0.20 ms |
| **95th Percentile Time** | 0.30 ms |
| **Median Processing Time** | 0.15 ms |

### Label Distribution (Iteration 2):

| Label | Count | Percentage |
|-------|-------|------------|
| `community-alert` | 16 | 15.5% |
| `sensitive-location` | 3 | 2.9% |
| `unverified-media` | 0 | 0.0% |

### Label Rate by Category (Iteration 2):

| Category | Label Rate | Posts with Labels |
|----------|------------|-------------------|
| News; ICE Raid Report | 100.0% | 2/2 |
| Fear-mongering; ICE Raid Report | 100.0% | 1/1 |
| News; Legal Case | 66.7% | 2/3 |
| News; ICE Raid Report; Legal Case | 50.0% | 1/2 |
| ICE Raid Report; Legal Case | 33.3% | 1/3 |
| Legal Case | 28.6% | 2/7 |
| News | 27.3% | 3/11 |
| News; Political Commentary | 25.0% | 1/4 |
| Political Commentary | 25.0% | 2/8 |
| General ICE Content | 10.8% | 4/37 |

**Key Observations:**
- The labeler applied labels to 18.4% of actual posts, showing conservative labeling behavior
- `community-alert` was the most frequently applied label (15.5% of posts)
- Categories with "ICE Raid Report" had the highest label rates, indicating effective detection of location-specific threats
- No `unverified-media` labels were applied, suggesting actual posts may not contain suspicious links or the detection threshold may need adjustment
- Processing time remains fast (0.20 ms average), suitable for real-time moderation

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

## 👨‍💻 Developer Documentation

This section provides comprehensive documentation for developers who want to use, modify, or extend the labeler codebase.

### 📄 `policy_proposal_labeler.py` - Core Implementation

The main labeler implementation consists of several classes working together to analyze content and apply labels.

#### Class: `AutomatedLabeler`

The primary class that orchestrates the labeling process.

**Initialization:**
```python
labeler = AutomatedLabeler(client=None, input_dir=None)
```

**Parameters:**
- `client` (optional): Authenticated Bluesky `Client` object from `atproto`. If `None`, the labeler runs in test mode.
- `input_dir` (optional): Directory path for input files (currently unused, reserved for future features).

**Key Methods:**

1. **`moderate_post(url: str) -> List[str]`**
   - Main entry point for moderation
   - Accepts either a Bluesky post URL or raw text (for testing)
   - Returns a list of label strings (e.g., `['sensitive-location', 'community-alert']`)
   - Example:
     ```python
     labels = labeler.moderate_post("https://bsky.app/profile/user/post/123")
     # or for testing:
     labels = labeler.moderate_post("ICE raid at 123 Main St. RIGHT NOW!")
     ```

**Configuration Thresholds:**

The labeler uses three configurable thresholds (defined in `__init__`):

```python
self.LOCATION_THRESHOLD = 15   # Minimum score for 'sensitive-location' label
self.MEDIA_THRESHOLD = 10      # Minimum score for 'unverified-media' label  
self.ESCALATION_THRESHOLD = 15 # Minimum score for 'community-alert' label
```

**To modify thresholds:**
1. Edit the values in `AutomatedLabeler.__init__()` (lines 71-73)
2. Lower values = more sensitive (more labels applied)
3. Higher values = less sensitive (fewer labels applied)

**Internal Architecture:**

The labeler uses a 5-layer analysis system:

1. **KeywordDetector**: Identifies immigration/enforcement keywords in multiple languages
2. **LocationAnalyzer**: Detects addresses, coordinates, sensitive places, and temporal markers
3. **MediaChecker**: Analyzes URLs and embeds for verification status
4. **EscalationScanner**: Detects panic language, mobilization phrases, and violent content
5. **LanguageProcessor**: Identifies multi-language content and evasion tactics

#### Class: `KeywordDetector`

Detects relevant keywords and phrases.

**Customization:**

To add new keywords, modify the lists in `__init__()`:

```python
# Primary English keywords (line 208)
self.primary_terms = ['ice', 'immigration', 'raid', ...]

# Spanish keywords (line 217)
self.spanish_terms = ['redada', 'migra', ...]

# Trust & Safety keywords (line 224)
self.ts_words = ['moderate', 'moderation', ...]

# Context amplifiers (line 237)
self.amplifiers = ['confirmed', 'verified', 'breaking', ...]
```

**Scoring:**
- Primary/Spanish terms: 10 points each
- Amplifiers: 3 points each
- Combination bonus: +10 if both primary terms and amplifiers present

#### Class: `LocationAnalyzer`

Detects location-specific information.

**Customization:**

1. **Sensitive Places** (line 310): Add locations that should trigger alerts
   ```python
   self.sensitive_places = ['school', 'church', 'hospital', ...]
   ```

2. **Address Pattern** (line 317): Regex pattern for street addresses
   - Modify if you need to support different address formats

3. **Time Patterns** (line 328): Regex patterns for temporal markers
   - Add patterns for specific time formats you want to detect

**Scoring:**
- Addresses: 20 points each
- Coordinates: 30 points (one-time)
- Sensitive places: 15 points each
- Temporal markers: 3 points each

#### Class: `MediaChecker`

Analyzes URLs and media embeds.

**Customization:**

1. **Verified Domains** (line 377): Add trusted news sources
   ```python
   self.verified_domains = ['reuters.com', 'apnews.com', ...]
   ```

2. **Suspicious Domains** (line 384): Add suspicious platforms
   ```python
   self.suspicious_domains = ['bit.ly', 'tinyurl.com', ...]
   ```

3. **T&S Domains** (line 392): Add problematic platforms
   ```python
   self.ts_domains = ['4chan.org', '8chan', ...]
   ```

**Scoring:**
- T&S domains: 20 points
- Unverified URLs: 10 points
- Suspicious URLs: +15 points
- Images: 5 points
- Videos: 10 points

#### Class: `EscalationScanner`

Detects panic-inducing and escalatory language.

**Customization:**

1. **Panic Phrases** (line 464): Add phrases that indicate urgency
   ```python
   self.panic_phrases = ['spread this', 'share now', 'urgent', ...]
   ```

2. **Mobilization Phrases** (line 471): Add phrases that call for action
   ```python
   self.mobilization_phrases = ['gather at', 'meet at', 'show up', ...]
   ```

3. **Fear Phrases** (line 477): Add fear-inducing language
   ```python
   self.fear_phrases = ['they are coming', 'be careful', 'stay away', ...]
   ```

4. **Violence Terms** (line 484): Add violent language (high priority)
   ```python
   self.violence_terms = ['kill', 'shoot', 'execute', ...]
   ```

**Scoring:**
- Violence terms: 25 points (high priority, breaks early)
- Panic phrases: 8 points each
- Mobilization phrases: 10 points each
- Fear phrases: 7 points each
- ALL CAPS words: 2 points each (max 10)
- Exclamations: 1 point each (max 8)

#### Class: `LanguageProcessor`

Detects multiple languages and evasion tactics.

**Customization:**

Add new language patterns (line 550):

```python
self.language_patterns = {
    'spanish': re.compile(r'[áéíóúñüÁÉÍÓÚÑÜ]'),
    'chinese': re.compile(r'[\u4e00-\u9fff]'),
    # Add more languages here
    'japanese': re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),
}
```

**Note:** Multi-language detection adds +15 to escalation score (line 173).

#### Extending the Labeler

**Adding a New Label:**

1. Define the label constant (line 40-43):
   ```python
   NEW_LABEL = "new-label-name"
   ```

2. Add detection logic in `_analyze_content()` (line 140):
   ```python
   new_score, new_details = self.new_analyzer.analyze(text)
   analysis['new_score'] = new_score
   ```

3. Add label determination in `_determine_labels()` (line 178):
   ```python
   if analysis['new_score'] >= self.NEW_THRESHOLD:
       labels.append(NEW_LABEL)
   ```

4. Create a new analyzer class following the pattern of existing analyzers.

---

### 📊 CSV Data Files

The project uses several CSV files for testing and data management.

#### `data.csv` - Test Dataset

**Purpose:** Comprehensive test dataset with expected labels for evaluation.

**Schema:**
```csv
URL,Text,Expected_Labels,Category
```

**Columns:**
- `URL`: Test identifier (e.g., "test_1")
- `Text`: Post content to analyze
- `Expected_Labels`: JSON array string of expected labels (e.g., `"['sensitive-location', 'community-alert']"`)
- `Category`: Human-readable category description

**Usage:**
```python
import pandas as pd
df = pd.read_csv('data.csv')
# Process each row
for idx, row in df.iterrows():
    text = row['Text']
    expected = eval(row['Expected_Labels'])  # Convert string to list
    labels = labeler.moderate_post(text)
    # Compare labels with expected
```

**Adding Test Cases:**

1. Open `data.csv` in a text editor or spreadsheet
2. Add a new row with:
   - Unique test ID in `URL` column
   - Test text in `Text` column
   - Expected labels as JSON array string in `Expected_Labels`
   - Category description in `Category` column
3. Example:
   ```csv
   test_151,"New test case here",['community-alert'],"Test category"
   ```

#### `data_actual_posts.csv` - Real Bluesky Posts

**Purpose:** Actual posts collected from Bluesky for real-world evaluation.

**Schema:**
```csv
id,type,category,text,url,label_ice_related
```

**Columns:**
- `id`: Unique post identifier
- `type`: Post type classification
- `category`: Category tags (semicolon-separated)
- `text`: Post content (may be truncated or require authentication)
- `url`: Bluesky post URL
- `label_ice_related`: Binary flag (0 or 1) indicating ICE-related content

**Usage:**
```python
import pandas as pd
df = pd.read_csv('data_actual_posts.csv')

# Filter valid posts
valid_posts = df[df['text'].notna() & 
                 (df['text'] != "this post requires authentication to view.")]

# Process posts
for idx, row in valid_posts.iterrows():
    labels = labeler.moderate_post(row['text'])
    print(f"Post {row['id']}: {labels}")
```

**Note:** Some posts may have empty text or require authentication. The test script handles these cases automatically.

#### Other CSV Files

- **`synthetic_posts.csv`**: Generated test posts (if present)
- **`test-data/input-posts-*.csv`**: Category-specific test datasets
- **`labeler-inputs/*.csv`**: Configuration files for keywords, domains, etc.

**Creating Custom Test Data:**

1. Create a new CSV file with appropriate columns
2. Follow the schema of `data.csv` or `data_actual_posts.csv`
3. Use the test scripts with your custom file:
   ```python
   evaluator = ActualPostsEvaluator(labeler, 'your_custom_data.csv')
   metrics = evaluator.run_evaluation()
   ```

---

### 🧪 `test_actual_posts.py` - Testing Framework

A comprehensive testing framework for evaluating the labeler on actual posts without ground truth labels.

#### Class: `ActualPostsEvaluator`

**Initialization:**
```python
from test_actual_posts import ActualPostsEvaluator
from policy_proposal_labeler import AutomatedLabeler

labeler = AutomatedLabeler()
evaluator = ActualPostsEvaluator(labeler, 'data_actual_posts.csv')
```

**Parameters:**
- `labeler`: An instance of `AutomatedLabeler`
- `test_data_path`: Path to CSV file with posts to test

#### Key Methods:

1. **`run_evaluation() -> Dict`**
   - Runs complete evaluation suite
   - Returns metrics dictionary
   - Prints comprehensive report to console
   ```python
   metrics = evaluator.run_evaluation()
   ```

2. **`export_results(output_path: str = "evaluation_results_actual.json")`**
   - Exports detailed results to JSON
   - Includes metrics and sample results
   ```python
   evaluator.export_results('my_results.json')
   ```

#### Metrics Generated:

The evaluator calculates:

- **Overall Metrics:**
  - Total/valid/skipped posts
  - Posts with/without labels
  - Label distribution
  - Processing time statistics

- **Performance Analysis:**
  - Median, mean, std dev processing times
  - Percentiles (95th, 99th)

- **Category Analysis:**
  - Label rate by category
  - Label distribution per category

- **Label Combinations:**
  - Most common label combinations
  - Frequency of each combination

#### Customizing the Evaluator:

**Adding New Metrics:**

1. Add calculation in `_calculate_metrics()`:
   ```python
   def _calculate_metrics(self):
       # ... existing code ...
       self.metrics['custom_metric'] = your_calculation()
   ```

2. Add reporting in `_generate_report()`:
   ```python
   def _generate_report(self):
       # ... existing code ...
       print(f"Custom Metric: {self.metrics['custom_metric']}")
   ```

**Filtering Posts:**

Modify `_test_all_posts()` to add custom filters:

```python
def _test_all_posts(self):
    for idx, row in self.test_data.iterrows():
        # Add custom filter
        if row['category'] == 'SkipThisCategory':
            continue
        # ... rest of method ...
```

**Custom Analysis:**

Add new analysis methods following the pattern:

```python
def _analyze_custom_feature(self):
    """Your custom analysis"""
    valid_results = [r for r in self.results if not r.get('skipped', False)]
    # Your analysis logic
    self.metrics['custom_analysis'] = results
```

Then call it in `run_evaluation()`.

#### Running Tests:

**Command Line:**
```bash
python test_actual_posts.py
```

**Programmatic:**
```python
from test_actual_posts import main
metrics = main()
```

**With Custom Data:**
```python
from test_actual_posts import ActualPostsEvaluator
from policy_proposal_labeler import AutomatedLabeler

labeler = AutomatedLabeler()
evaluator = ActualPostsEvaluator(labeler, 'custom_data.csv')
metrics = evaluator.run_evaluation()
evaluator.export_results('custom_results.json')
```

#### Output Format:

**Console Output:**
- Formatted tables and statistics
- Category breakdowns
- Performance metrics

**JSON Export:**
```json
{
  "metrics": {
    "total_posts": 106,
    "valid_posts": 103,
    "posts_with_labels": 19,
    "label_distribution": {...},
    "performance": {...},
    "category_analysis": {...}
  },
  "sample_results": [...]
}
```

---

### 🔧 Common Customization Tasks

#### Adjusting Sensitivity

**Make labeler more sensitive (more labels):**
```python
# In AutomatedLabeler.__init__()
self.LOCATION_THRESHOLD = 10   # Lower threshold
self.MEDIA_THRESHOLD = 5
self.ESCALATION_THRESHOLD = 10
```

**Make labeler less sensitive (fewer labels):**
```python
self.LOCATION_THRESHOLD = 25   # Higher threshold
self.MEDIA_THRESHOLD = 20
self.ESCALATION_THRESHOLD = 25
```

#### Adding Language Support

1. Add keywords to `KeywordDetector`:
   ```python
   self.french_terms = ['raide', 'immigration', ...]
   ```

2. Add pattern to `LanguageProcessor`:
   ```python
   'french': re.compile(r'[àâäéèêëïîôùûüÿç]')
   ```

3. Compile pattern in `_compile_patterns()`:
   ```python
   french = '|'.join(re.escape(term) for term in self.french_terms)
   self.patterns['french'] = re.compile(r'\b(' + french + r')\b', re.IGNORECASE)
   ```

#### Adding New Detection Rules

1. Create a new analyzer class (or extend existing):
   ```python
   class CustomAnalyzer:
       def analyze(self, text: str) -> Tuple[int, Dict]:
           score = 0
           details = {}
           # Your detection logic
           return score, details
   ```

2. Initialize in `AutomatedLabeler.__init__()`:
   ```python
   self.custom_analyzer = CustomAnalyzer()
   ```

3. Use in `_analyze_content()`:
   ```python
   custom_score, custom_details = self.custom_analyzer.analyze(text)
   analysis['custom_score'] = custom_score
   ```

4. Apply in `_determine_labels()`:
   ```python
   if analysis['custom_score'] >= self.CUSTOM_THRESHOLD:
       labels.append(CUSTOM_LABEL)
   ```

#### Debugging

**Enable verbose output:**
```python
# Add to AutomatedLabeler.moderate_post()
print(f"Analysis for {url}:")
print(json.dumps(analysis, indent=2))
print(f"Labels: {labels}")
```

**Test individual analyzers:**
```python
from policy_proposal_labeler import KeywordDetector

detector = KeywordDetector()
score, details = detector.analyze("ICE raid at Main St")
print(f"Score: {score}, Details: {details}")
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
