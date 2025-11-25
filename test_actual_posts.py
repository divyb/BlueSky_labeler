#!/usr/bin/env python3
"""
Evaluation Script for Actual Bluesky Posts
===========================================
This script runs the labeler on actual posts from Bluesky and generates statistics.
Includes accuracy and precision metrics using label_ice_related as ground truth.
"""

import json
import time
import sys
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

# Import the labeler
from policy_proposal_labeler import AutomatedLabeler

# Label constants
LOCATION_LABEL = "sensitive-location"
MEDIA_LABEL = "unverified-media"
ALERT_LABEL = "community-alert"

class ActualPostsEvaluator:
    """Evaluator for actual posts with accuracy and precision metrics"""
    
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
        
        # Define category-to-expected-label mappings for more detailed evaluation
        self.category_label_mapping = {
            'ICE Raid Report': [ALERT_LABEL],
            'Fear-mongering': [ALERT_LABEL],
            'Fear-mongering; ICE Raid Report': [LOCATION_LABEL, ALERT_LABEL],
            'News; ICE Raid Report': [ALERT_LABEL],
            'News; ICE Raid Report; Legal Case': [ALERT_LABEL],
            'ICE Raid Report; Legal Case': [ALERT_LABEL],
        }
        
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
        
        # Calculate accuracy and precision metrics
        self._calculate_accuracy_precision()
        
        # Calculate per-label metrics
        self._calculate_per_label_metrics()
        
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
    
    def _calculate_accuracy_precision(self):
        """
        Calculate accuracy and precision using label_ice_related as ground truth.
        
        Ground truth interpretation:
        - ice_related=1: Post SHOULD be labeled (True if ICE-related)
        - ice_related=0: Post should NOT be labeled (False if not ICE-related)
        
        Predictions:
        - predicted labels exist: Positive prediction
        - no predicted labels: Negative prediction
        """
        valid_results = [r for r in self.results if not r.get('skipped', False)]
        if not valid_results:
            return
        
        # Initialize counters
        true_positives = 0   # ICE-related AND has labels (correctly labeled)
        false_positives = 0  # NOT ICE-related BUT has labels (incorrectly labeled)
        true_negatives = 0   # NOT ICE-related AND no labels (correctly no label)
        false_negatives = 0  # ICE-related BUT no labels (missed labeling)
        
        for result in valid_results:
            is_ice_related = result.get('ice_related', 0) == 1
            has_labels = len(result['predicted']) > 0
            
            if is_ice_related and has_labels:
                true_positives += 1
            elif not is_ice_related and has_labels:
                false_positives += 1
            elif not is_ice_related and not has_labels:
                true_negatives += 1
            elif is_ice_related and not has_labels:
                false_negatives += 1
        
        # Calculate metrics
        total = true_positives + false_positives + true_negatives + false_negatives
        
        # Accuracy: (TP + TN) / Total
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0
        
        # Precision: TP / (TP + FP) - of all positive predictions, how many were correct
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        
        # Recall: TP / (TP + FN) - of all actual positives, how many did we catch
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        # F1 Score: harmonic mean of precision and recall
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Specificity: TN / (TN + FP) - of all actual negatives, how many did we correctly identify
        specificity = true_negatives / (true_negatives + false_positives) if (true_negatives + false_positives) > 0 else 0
        
        self.metrics['accuracy_metrics'] = {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'true_negatives': true_negatives,
            'false_negatives': false_negatives,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'specificity': specificity
        }
        
        # Also calculate accuracy based on category-expected labels
        self._calculate_category_based_accuracy(valid_results)
    
    def _calculate_category_based_accuracy(self, valid_results: List[Dict]):
        """
        Calculate accuracy based on category-to-expected-label mapping.
        This provides more granular evaluation for posts with known categories.
        """
        category_metrics = defaultdict(lambda: {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0, 'total': 0})
        
        for result in valid_results:
            category = result.get('category', 'Unknown')
            predicted_labels = set(result['predicted'])
            
            # Get expected labels for this category (if defined)
            expected_labels = set(self.category_label_mapping.get(category, []))
            
            # If category has expected labels, calculate per-category accuracy
            if expected_labels:
                for label in [LOCATION_LABEL, MEDIA_LABEL, ALERT_LABEL]:
                    expected = label in expected_labels
                    predicted = label in predicted_labels
                    
                    if expected and predicted:
                        category_metrics[category]['tp'] += 1
                    elif not expected and predicted:
                        category_metrics[category]['fp'] += 1
                    elif not expected and not predicted:
                        category_metrics[category]['tn'] += 1
                    elif expected and not predicted:
                        category_metrics[category]['fn'] += 1
                
                category_metrics[category]['total'] += 1
        
        # Calculate per-category precision and accuracy
        category_accuracy = {}
        for category, counts in category_metrics.items():
            if counts['total'] > 0:
                total = counts['tp'] + counts['fp'] + counts['tn'] + counts['fn']
                accuracy = (counts['tp'] + counts['tn']) / total if total > 0 else 0
                precision = counts['tp'] / (counts['tp'] + counts['fp']) if (counts['tp'] + counts['fp']) > 0 else 0
                recall = counts['tp'] / (counts['tp'] + counts['fn']) if (counts['tp'] + counts['fn']) > 0 else 0
                
                category_accuracy[category] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'true_positives': counts['tp'],
                    'false_positives': counts['fp'],
                    'true_negatives': counts['tn'],
                    'false_negatives': counts['fn'],
                    'total_posts': counts['total']
                }
        
        self.metrics['category_accuracy_detailed'] = category_accuracy
    
    def _calculate_per_label_metrics(self):
        """
        Calculate precision and recall for each individual label type.
        Uses ICE-related status as baseline for expected behavior.
        """
        valid_results = [r for r in self.results if not r.get('skipped', False)]
        if not valid_results:
            return
        
        all_labels = [LOCATION_LABEL, MEDIA_LABEL, ALERT_LABEL]
        per_label_metrics = {}
        
        for label in all_labels:
            # Count how many times this label was applied
            times_applied = sum(1 for r in valid_results if label in r['predicted'])
            
            # Count how many times this label was applied to ICE-related posts
            times_applied_to_ice = sum(1 for r in valid_results 
                                       if label in r['predicted'] and r.get('ice_related', 0) == 1)
            
            # Count how many times this label was applied to non-ICE posts (potential FP)
            times_applied_to_non_ice = sum(1 for r in valid_results 
                                           if label in r['predicted'] and r.get('ice_related', 0) == 0)
            
            # Count ICE-related posts that could potentially receive this label
            ice_related_posts = sum(1 for r in valid_results if r.get('ice_related', 0) == 1)
            non_ice_posts = sum(1 for r in valid_results if r.get('ice_related', 0) == 0)
            
            # Calculate label-specific precision (applied to ICE / total applied)
            label_precision = times_applied_to_ice / times_applied if times_applied > 0 else 0
            
            # Calculate label-specific recall (applied to ICE / total ICE posts)
            label_recall = times_applied_to_ice / ice_related_posts if ice_related_posts > 0 else 0
            
            # False positive rate for this label
            fp_rate = times_applied_to_non_ice / non_ice_posts if non_ice_posts > 0 else 0
            
            per_label_metrics[label] = {
                'times_applied': times_applied,
                'applied_to_ice_related': times_applied_to_ice,
                'applied_to_non_ice': times_applied_to_non_ice,
                'precision': label_precision,
                'recall': label_recall,
                'false_positive_rate': fp_rate
            }
        
        self.metrics['per_label_metrics'] = per_label_metrics
    
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
        
        # Accuracy and Precision metrics (based on ice_related ground truth)
        if 'accuracy_metrics' in self.metrics:
            am = self.metrics['accuracy_metrics']
            print(f"\n[ACCURACY & PRECISION METRICS]")
            print(f"  (Using 'label_ice_related' as ground truth)")
            print(f"  ┌─────────────────────────────────────────┐")
            print(f"  │  Overall Accuracy:    {am['accuracy']:.2%}            │")
            print(f"  │  Precision:           {am['precision']:.2%}            │")
            print(f"  │  Recall:              {am['recall']:.2%}            │")
            print(f"  │  F1 Score:            {am['f1_score']:.2%}            │")
            print(f"  │  Specificity:         {am['specificity']:.2%}            │")
            print(f"  └─────────────────────────────────────────┘")
            print(f"\n  Confusion Matrix:")
            print(f"                          Predicted")
            print(f"                      Pos        Neg")
            print(f"  Actual  Pos (ICE)   TP={am['true_positives']:<4}    FN={am['false_negatives']:<4}")
            print(f"          Neg         FP={am['false_positives']:<4}    TN={am['true_negatives']:<4}")
        
        # Per-label metrics
        if 'per_label_metrics' in self.metrics:
            print(f"\n[PER-LABEL PRECISION & RECALL]")
            print(f"  {'Label':<22} {'Applied':<10} {'Precision':<12} {'Recall':<12} {'FP Rate':<10}")
            print(f"  {'-'*22} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")
            for label, stats in self.metrics['per_label_metrics'].items():
                print(f"  {label:<22} {stats['times_applied']:<10} {stats['precision']:.2%}        {stats['recall']:.2%}        {stats['false_positive_rate']:.2%}")
        
        # Label distribution
        print(f"\n[LABEL DISTRIBUTION]")
        if self.metrics.get('label_distribution'):
            for label, count in sorted(self.metrics['label_distribution'].items(), key=lambda x: x[1], reverse=True):
                percentage = count / self.metrics['valid_posts'] * 100
                print(f"  - {label}: {count} posts ({percentage:.1f}%)")
        else:
            print(f"  - No labels applied")
        
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
        
        # Category-based detailed accuracy (for categories with expected labels)
        if 'category_accuracy_detailed' in self.metrics and self.metrics['category_accuracy_detailed']:
            print(f"\n[CATEGORY-SPECIFIC ACCURACY]")
            print(f"  (For categories with expected label mappings)")
            for category, stats in self.metrics['category_accuracy_detailed'].items():
                print(f"\n  {category}:")
                print(f"    - Accuracy: {stats['accuracy']:.2%}")
                print(f"    - Precision: {stats['precision']:.2%}")
                print(f"    - Recall: {stats['recall']:.2%}")
                print(f"    - TP: {stats['true_positives']}, FP: {stats['false_positives']}, TN: {stats['true_negatives']}, FN: {stats['false_negatives']}")
        
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
        # Create a summary for easy access
        summary = {
            'overall_accuracy': self.metrics.get('accuracy_metrics', {}).get('accuracy', 0),
            'precision': self.metrics.get('accuracy_metrics', {}).get('precision', 0),
            'recall': self.metrics.get('accuracy_metrics', {}).get('recall', 0),
            'f1_score': self.metrics.get('accuracy_metrics', {}).get('f1_score', 0),
            'total_posts': self.metrics.get('total_posts', 0),
            'posts_labeled': self.metrics.get('posts_with_labels', 0),
            'labeling_rate': self.metrics.get('posts_with_labels', 0) / self.metrics.get('valid_posts', 1)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': summary,
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

