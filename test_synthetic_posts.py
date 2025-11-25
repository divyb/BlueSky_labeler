#!/usr/bin/env python3
"""
Test Script for Synthetic Posts Analysis
=========================================
Tests the Community Safety Alert Labeler on synthetic posts dataset
with harmful content detection.
"""

import pandas as pd
import json
import time
from collections import Counter, defaultdict
import sys
import os

# Import the labeler
sys.path.append('/home/claude')
from policy_proposal_labeler import AutomatedLabeler

def analyze_synthetic_posts(input_file: str = '/mnt/user-data/uploads/synthetic_posts.csv'):
    """
    Analyze synthetic posts with the Community Safety Alert Labeler
    """
    print("=" * 70)
    print("COMMUNITY SAFETY ALERT LABELER - SYNTHETIC POSTS ANALYSIS")
    print("=" * 70)
    
    # Load synthetic posts
    df = pd.read_csv(input_file)
    print(f"\n📊 Dataset Overview:")
    print(f"  • Total posts: {len(df)}")
    
    # Get post types distribution
    if 'Post Type' in df.columns:
        type_counts = df['Post Type'].value_counts()
        print(f"\n📁 Post Types in Dataset:")
        for post_type, count in type_counts.items():
            print(f"  • {post_type}: {count}")
    
    # Initialize labeler
    print(f"\n🔧 Initializing Community Safety Alert Labeler...")
    labeler = AutomatedLabeler()
    
    # Process all posts
    results = []
    label_counter = Counter()
    type_labels = defaultdict(lambda: defaultdict(int))
    processing_times = []
    
    print(f"\n🔍 Processing {len(df)} posts...")
    print("-" * 50)
    
    for idx, row in df.iterrows():
        # Get post content
        text = str(row['Post Content']) if pd.notna(row['Post Content']) else ""
        post_type = row.get('Post Type', 'Unknown')
        
        # Skip if no text
        if not text or text == 'nan':
            continue
            
        # Process with labeler
        start_time = time.time()
        labels = labeler.moderate_post(text)
        processing_time = (time.time() - start_time) * 1000
        processing_times.append(processing_time)
        
        # Store results
        result = {
            'id': idx + 1,
            'post_type': post_type,
            'text': text[:100] + '...' if len(text) > 100 else text,
            'labels': labels,
            'processing_time_ms': processing_time
        }
        results.append(result)
        
        # Count labels
        for label in labels:
            label_counter[label] += 1
            type_labels[post_type][label] += 1
        
        # Progress indicator
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(df)} posts...")
    
    print(f"\n✅ Processing complete!")
    print("-" * 50)
    
    # Analysis Results
    print(f"\n📊 LABELING RESULTS:")
    print(f"\n  Total posts processed: {len(results)}")
    print(f"  Posts with labels: {sum(1 for r in results if r['labels'])}")
    print(f"  Posts without labels: {sum(1 for r in results if not r['labels'])}")
    
    # Label distribution
    if label_counter:
        print(f"\n🏷️  Label Distribution:")
        for label, count in label_counter.most_common():
            percentage = (count / len(results)) * 100
            print(f"  • {label}: {count} posts ({percentage:.1f}%)")
    else:
        print(f"\n⚠️  No labels were applied to any posts")
    
    # Analysis by post type
    print(f"\n📁 Labels by Post Type:")
    for post_type in sorted(type_labels.keys()):
        type_posts = [r for r in results if r['post_type'] == post_type]
        labeled_posts = [r for r in type_posts if r['labels']]
        
        print(f"\n  {post_type}: {len(labeled_posts)}/{len(type_posts)} labeled ({len(labeled_posts)/len(type_posts)*100:.1f}%)")
        
        if type_labels[post_type]:
            for label, count in type_labels[post_type].items():
                print(f"    • {label}: {count}")
        else:
            print(f"    • No labels applied")
    
    # Posts with multiple labels
    multi_label_posts = [r for r in results if len(r['labels']) > 1]
    if multi_label_posts:
        print(f"\n🔀 Posts with Multiple Labels: {len(multi_label_posts)}")
        for post in multi_label_posts[:5]:
            print(f"  • Post {post['id']}: {post['labels']}")
            print(f"    Text: {post['text']}")
    
    # Performance metrics
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)
        
        print(f"\n⚡ Performance Metrics:")
        print(f"  • Average processing time: {avg_time:.2f} ms")
        print(f"  • Max processing time: {max_time:.2f} ms")
        print(f"  • Min processing time: {min_time:.2f} ms")
        print(f"  • Posts per second: {1000/avg_time:.0f}")
    
    # Effectiveness Analysis
    print(f"\n🎯 Effectiveness Analysis:")
    
    # Check harmful content detection
    harmful_types = ['Anti-Immigrant', 'Anti-immigrant', 'anti-immigrant']
    harmful_posts = [r for r in results if r['post_type'] in harmful_types]
    if harmful_posts:
        harmful_labeled = [r for r in harmful_posts if r['labels']]
        detection_rate = len(harmful_labeled) / len(harmful_posts) * 100
        print(f"  • Harmful content detection rate: {detection_rate:.1f}% ({len(harmful_labeled)}/{len(harmful_posts)})")
        
        # Most common labels for harmful content
        harmful_labels = Counter()
        for post in harmful_labeled:
            for label in post['labels']:
                harmful_labels[label] += 1
        
        if harmful_labels:
            print(f"\n  Most common labels for harmful content:")
            for label, count in harmful_labels.most_common(3):
                print(f"    • {label}: {count} times")
    
    # Sample posts by label
    print(f"\n📝 Sample Posts by Label Category:")
    
    for label in label_counter.keys():
        print(f"\n  {label.upper()}:")
        labeled_posts = [r for r in results if label in r['labels']][:3]
        for i, post in enumerate(labeled_posts, 1):
            print(f"    {i}. [{post['post_type']}] {post['text']}")
    
    # Unlabeled harmful content (potential misses)
    if harmful_posts:
        unlabeled_harmful = [r for r in harmful_posts if not r['labels']]
        if unlabeled_harmful:
            print(f"\n❓ Sample Harmful Posts NOT Labeled (potential false negatives):")
            for post in unlabeled_harmful[:5]:
                print(f"  • Post {post['id']}: {post['text']}")
    
    # Export results
    print(f"\n💾 Exporting results...")
    
    # Save to CSV
    results_df = pd.DataFrame(results)
    output_csv = '/mnt/user-data/outputs/synthetic_posts_results.csv'
    results_df.to_csv(output_csv, index=False)
    print(f"  ✓ Results saved to: {output_csv}")
    
    # Save analysis to JSON
    analysis = {
        'summary': {
            'total_posts': len(results),
            'posts_with_labels': sum(1 for r in results if r['labels']),
            'posts_without_labels': sum(1 for r in results if not r['labels']),
            'label_distribution': dict(label_counter),
            'detection_rate': detection_rate if harmful_posts else 0
        },
        'performance': {
            'avg_processing_time_ms': avg_time if processing_times else 0,
            'max_processing_time_ms': max_time if processing_times else 0,
            'min_processing_time_ms': min_time if processing_times else 0
        },
        'by_type': {
            post_type: {
                'total': len([r for r in results if r['post_type'] == post_type]),
                'labeled': len([r for r in results if r['post_type'] == post_type and r['labels']]),
                'labels': dict(type_labels[post_type])
            }
            for post_type in type_labels.keys()
        }
    }
    
    output_json = '/mnt/user-data/outputs/synthetic_posts_analysis.json'
    with open(output_json, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"  ✓ Analysis saved to: {output_json}")
    
    # Final summary
    print(f"\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if harmful_posts:
        print(f"\n🔴 Critical Finding:")
        print(f"  The labeler detected {detection_rate:.1f}% of harmful content")
        print(f"  Main detection mechanism: {harmful_labels.most_common(1)[0][0] if harmful_labels else 'None'}")
    
    print(f"\n📌 Key Takeaways:")
    print(f"  1. Processing speed: {1000/avg_time if processing_times else 0:.0f} posts/second")
    print(f"  2. Most common label: {label_counter.most_common(1)[0][0] if label_counter else 'None'}")
    print(f"  3. Coverage: {sum(1 for r in results if r['labels'])/len(results)*100:.1f}% of posts labeled")
    
    return results, analysis

def main():
    """Main execution"""
    try:
        # Run analysis
        results, analysis = analyze_synthetic_posts()
        
        print("\n✅ ANALYSIS COMPLETE")
        print("\n📁 Output files generated:")
        print("  • /mnt/user-data/outputs/synthetic_posts_results.csv")
        print("  • /mnt/user-data/outputs/synthetic_posts_analysis.json")
        
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())