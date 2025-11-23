#!/usr/bin/env python3
"""
Evaluation Script for Actual Bluesky Posts
===========================================
This script runs the labeler on actual posts from Bluesky and generates statistics.
"""

import json
import time
import sys
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict

# Import the labeler
from policy_proposal_labeler import AutomatedLabeler

class ActualPostsEvaluator:
    """Evaluator for actual posts without expected labels"""
    
    def __init__(self, labeler: AutomatedLabeler, test_data_path: str):
        """
        Initialize evaluator
        
        Args:
            labeler: The labeler instance to test
            test_data_path: Path to CSV with actual posts
        """
        self.labeler = labeler
        self.test_data = pd.read_csv(test_data_path)
        self.results = []
        self.metrics = {}
        
    def run_evaluation(self) -> Dict:
        """Run complete evaluation suite"""
        print("=" * 60)
        print("COMMUNITY SAFETY ALERT LABELER - ACTUAL POSTS EVALUATION")
        print("=" * 60)
        print(f"Testing on {len(self.test_data)} actual posts...")
        print()
        
        # Run tests
        self._test_all_posts()
        
        # Calculate metrics
        self._calculate_metrics()
        
        # Performance analysis
        self._analyze_performance()
        
        # Category analysis
        self._analyze_by_category()
        
        # Label distribution analysis
        self._analyze_label_distribution()
        
        # Generate report
        self._generate_report()
        
        return self.metrics
    
    def _test_all_posts(self):
        """Test labeler on all posts in dataset"""
        for idx, row in self.test_data.iterrows():
            start_time = time.time()
            
            # Get post text
            text = str(row['text']) if pd.notna(row['text']) else ""
            
            # Skip if text is empty or unavailable
            if not text or text.lower() == "this post requires authentication to view.":
                self.results.append({
                    'id': row.get('id', idx),
                    'text': text,
                    'predicted': [],
                    'category': row.get('category', 'Unknown'),
                    'type': row.get('type', 'Unknown'),
                    'ice_related': row.get('label_ice_related', 0),
                    'processing_time_ms': 0,
                    'skipped': True
                })
                continue
            
            # Run labeler (pass text directly since it doesn't start with http)
            predicted = self.labeler.moderate_post(text)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Store results
            self.results.append({
                'id': row.get('id', idx),
                'text': text[:200] + '...' if len(text) > 200 else text,  # Truncate for storage
                'predicted': predicted,
                'category': row.get('category', 'Unknown'),
                'type': row.get('type', 'Unknown'),
                'ice_related': row.get('label_ice_related', 0),
                'processing_time_ms': processing_time,
                'skipped': False
            })
            
            # Progress indicator
            if (idx + 1) % 25 == 0:
                print(f"Processed {idx + 1}/{len(self.test_data)} posts...")
    
    def _calculate_metrics(self):
        """Calculate comprehensive metrics"""
        # Filter out skipped posts
        valid_results = [r for r in self.results if not r.get('skipped', False)]
        
        if not valid_results:
            self.metrics = {'error': 'No valid posts to analyze'}
            return
        
        # Label frequency
        label_counts = Counter()
        for result in valid_results:
            for label in result['predicted']:
                label_counts[label] += 1
        
        # Posts with labels vs without
        posts_with_labels = sum(1 for r in valid_results if r['predicted'])
        posts_without_labels = len(valid_results) - posts_with_labels
        
        # Average labels per post
        total_labels = sum(len(r['predicted']) for r in valid_results)
        avg_labels_per_post = total_labels / len(valid_results) if valid_results else 0
        
        # Average processing time
        avg_processing_time = np.mean([r['processing_time_ms'] for r in valid_results])
        
        self.metrics = {
            'total_posts': len(self.test_data),
            'valid_posts': len(valid_results),
            'skipped_posts': len(self.results) - len(valid_results),
            'posts_with_labels': posts_with_labels,
            'posts_without_labels': posts_without_labels,
            'label_distribution': dict(label_counts),
            'total_labels_applied': total_labels,
            'avg_labels_per_post': avg_labels_per_post,
            'avg_processing_time_ms': avg_processing_time,
            'max_processing_time_ms': max(r['processing_time_ms'] for r in valid_results),
            'min_processing_time_ms': min(r['processing_time_ms'] for r in valid_results)
        }
    
    def _analyze_performance(self):
        """Analyze performance characteristics"""
        valid_results = [r for r in self.results if not r.get('skipped', False)]
        if not valid_results:
            return
            
        processing_times = [r['processing_time_ms'] for r in valid_results]
        
        self.metrics['performance'] = {
            'median_time_ms': np.median(processing_times),
            'std_time_ms': np.std(processing_times),
            '95th_percentile_ms': np.percentile(processing_times, 95),
            '99th_percentile_ms': np.percentile(processing_times, 99)
        }
    
    def _analyze_by_category(self):
        """Analyze performance by post category"""
        valid_results = [r for r in self.results if not r.get('skipped', False)]
        if not valid_results:
            return
            
        category_stats = defaultdict(lambda: {'total': 0, 'with_labels': 0, 'labels': Counter()})
        
        for result in valid_results:
            category = result['category']
            category_stats[category]['total'] += 1
            if result['predicted']:
                category_stats[category]['with_labels'] += 1
            for label in result['predicted']:
                category_stats[category]['labels'][label] += 1
        
        category_analysis = {}
        for category, stats in category_stats.items():
            category_analysis[category] = {
                'total_posts': stats['total'],
                'posts_with_labels': stats['with_labels'],
                'label_rate': stats['with_labels'] / stats['total'] if stats['total'] > 0 else 0,
                'label_distribution': dict(stats['labels'])
            }
        
        self.metrics['category_analysis'] = category_analysis
    
    def _analyze_label_distribution(self):
        """Analyze label combinations"""
        valid_results = [r for r in self.results if not r.get('skipped', False)]
        if not valid_results:
            return
            
        # Label combinations
        label_combinations = Counter()
        for result in valid_results:
            if result['predicted']:
                combo = tuple(sorted(result['predicted']))
                label_combinations[combo] += 1
            else:
                label_combinations[('no-labels',)] += 1
        
        self.metrics['label_combinations'] = {
            str(k): v for k, v in label_combinations.most_common(10)
        }
    
    def _generate_report(self):
        """Generate comprehensive evaluation report"""
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS - ACTUAL POSTS")
        print("=" * 60)
        
        # Overall metrics
        print(f"\n[OVERALL METRICS]")
        print(f"  - Total Posts: {self.metrics['total_posts']}")
        print(f"  - Valid Posts: {self.metrics['valid_posts']}")
        print(f"  - Skipped Posts: {self.metrics['skipped_posts']}")
        print(f"  - Posts with Labels: {self.metrics['posts_with_labels']} ({self.metrics['posts_with_labels']/self.metrics['valid_posts']*100:.1f}%)")
        print(f"  - Posts without Labels: {self.metrics['posts_without_labels']} ({self.metrics['posts_without_labels']/self.metrics['valid_posts']*100:.1f}%)")
        print(f"  - Total Labels Applied: {self.metrics['total_labels_applied']}")
        print(f"  - Average Labels per Post: {self.metrics['avg_labels_per_post']:.2f}")
        print(f"  - Average Processing Time: {self.metrics['avg_processing_time_ms']:.2f} ms")
        
        # Label distribution
        print(f"\n[LABEL DISTRIBUTION]")
        for label, count in sorted(self.metrics['label_distribution'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / self.metrics['valid_posts'] * 100
            print(f"  - {label}: {count} posts ({percentage:.1f}%)")
        
        # Performance analysis
        if 'performance' in self.metrics:
            print(f"\n[PERFORMANCE ANALYSIS]")
            print(f"  - Median Processing Time: {self.metrics['performance']['median_time_ms']:.2f} ms")
            print(f"  - 95th Percentile: {self.metrics['performance']['95th_percentile_ms']:.2f} ms")
            print(f"  - 99th Percentile: {self.metrics['performance']['99th_percentile_ms']:.2f} ms")
        
        # Category analysis
        if 'category_analysis' in self.metrics:
            print(f"\n[LABEL RATE BY CATEGORY]")
            sorted_categories = sorted(self.metrics['category_analysis'].items(), 
                                     key=lambda x: x[1]['label_rate'], reverse=True)
            for category, stats in sorted_categories[:10]:
                print(f"  - {category}: {stats['label_rate']:.1%} ({stats['posts_with_labels']}/{stats['total_posts']})")
        
        # Label combinations
        if 'label_combinations' in self.metrics:
            print(f"\n[TOP LABEL COMBINATIONS]")
            for combo, count in list(self.metrics['label_combinations'].items())[:5]:
                print(f"  - {combo}: {count} posts")
        
        print("\n" + "=" * 60)
        print("EVALUATION COMPLETE")
        print("=" * 60)
    
    def export_results(self, output_path: str = "evaluation_results_actual.json"):
        """Export detailed results to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metrics': self.metrics,
                'sample_results': self.results[:50]  # First 50 for review
            }, f, indent=2, default=str)
        print(f"\n[EXPORT] Detailed results exported to: {output_path}")


def main():
    """Main execution function"""
    # Initialize labeler (without Bluesky client for testing)
    labeler = AutomatedLabeler()
    
    # Initialize evaluator
    evaluator = ActualPostsEvaluator(labeler, 'data_actual_posts.csv')
    
    # Run evaluation
    metrics = evaluator.run_evaluation()
    
    # Export results
    evaluator.export_results()
    
    return metrics


if __name__ == "__main__":
    metrics = main()
    sys.exit(0)

