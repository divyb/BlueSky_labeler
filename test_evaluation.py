#!/usr/bin/env python3
"""
Testing and Evaluation Script for Community Safety Alert Labeler
================================================================
This script tests the policy proposal labeler and generates evaluation metrics.
"""

import json
import time
import sys
import os
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# Import the labeler
from policy_proposal_labeler import AutomatedLabeler

class LabelerEvaluator:
    """Comprehensive evaluation system for the labeler"""
    
    def __init__(self, labeler: AutomatedLabeler, test_data_path: str):
        """
        Initialize evaluator
        
        Args:
            labeler: The labeler instance to test
            test_data_path: Path to CSV with test data
        """
        self.labeler = labeler
        self.test_data = pd.read_csv(test_data_path)
        self.results = []
        self.metrics = {}
        
    def run_evaluation(self) -> Dict:
        """Run complete evaluation suite"""
        print("=" * 60)
        print("COMMUNITY SAFETY ALERT LABELER - EVALUATION")
        print("=" * 60)
        print(f"Testing on {len(self.test_data)} posts...")
        print()
        
        # Run tests
        self._test_all_posts()
        
        # Calculate metrics
        self._calculate_metrics()
        
        # Performance analysis
        self._analyze_performance()
        
        # Category analysis
        self._analyze_by_category()
        
        # Error analysis
        self._analyze_errors()
        
        # Generate report
        self._generate_report()
        
        return self.metrics
    
    def _test_all_posts(self):
        """Test labeler on all posts in dataset"""
        for idx, row in self.test_data.iterrows():
            start_time = time.time()
            
            # Get expected labels
            expected = eval(row['Expected_Labels']) if isinstance(row['Expected_Labels'], str) else row['Expected_Labels']
            
            # Run labeler
            predicted = self.labeler.moderate_post(row['Text'])
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Store results
            self.results.append({
                'id': row['URL'],
                'text': row['Text'],
                'expected': expected,
                'predicted': predicted,
                'category': row['Category'],
                'processing_time_ms': processing_time,
                'correct': set(predicted) == set(expected)
            })
            
            # Progress indicator
            if (idx + 1) % 25 == 0:
                print(f"Processed {idx + 1}/{len(self.test_data)} posts...")
    
    def _calculate_metrics(self):
        """Calculate comprehensive metrics"""
        # Initialize counters
        true_positives = defaultdict(int)
        false_positives = defaultdict(int)
        true_negatives = defaultdict(int)
        false_negatives = defaultdict(int)
        
        # Get all possible labels
        all_labels = set()
        for r in self.results:
            all_labels.update(r['expected'])
            all_labels.update(r['predicted'])
        
        # Calculate per-label metrics
        for result in self.results:
            expected_set = set(result['expected'])
            predicted_set = set(result['predicted'])
            
            for label in all_labels:
                if label in expected_set and label in predicted_set:
                    true_positives[label] += 1
                elif label in predicted_set and label not in expected_set:
                    false_positives[label] += 1
                elif label not in predicted_set and label not in expected_set:
                    true_negatives[label] += 1
                elif label in expected_set and label not in predicted_set:
                    false_negatives[label] += 1
        
        # Calculate metrics for each label
        label_metrics = {}
        for label in all_labels:
            tp = true_positives[label]
            fp = false_positives[label]
            tn = true_negatives[label]
            fn = false_negatives[label]
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
            
            label_metrics[label] = {
                'true_positives': tp,
                'false_positives': fp,
                'true_negatives': tn,
                'false_negatives': fn,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'accuracy': accuracy
            }
        
        # Overall accuracy
        correct_predictions = sum(1 for r in self.results if r['correct'])
        overall_accuracy = correct_predictions / len(self.results)
        
        # Average processing time
        avg_processing_time = np.mean([r['processing_time_ms'] for r in self.results])
        
        self.metrics = {
            'overall_accuracy': overall_accuracy,
            'correct_predictions': correct_predictions,
            'total_predictions': len(self.results),
            'label_metrics': label_metrics,
            'avg_processing_time_ms': avg_processing_time,
            'max_processing_time_ms': max(r['processing_time_ms'] for r in self.results),
            'min_processing_time_ms': min(r['processing_time_ms'] for r in self.results)
        }
    
    def _analyze_performance(self):
        """Analyze performance characteristics"""
        processing_times = [r['processing_time_ms'] for r in self.results]
        
        self.metrics['performance'] = {
            'median_time_ms': np.median(processing_times),
            'std_time_ms': np.std(processing_times),
            '95th_percentile_ms': np.percentile(processing_times, 95),
            '99th_percentile_ms': np.percentile(processing_times, 99)
        }
    
    def _analyze_by_category(self):
        """Analyze performance by post category"""
        category_results = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for result in self.results:
            category = result['category']
            category_results[category]['total'] += 1
            if result['correct']:
                category_results[category]['correct'] += 1
        
        category_accuracy = {}
        for category, counts in category_results.items():
            accuracy = counts['correct'] / counts['total'] if counts['total'] > 0 else 0
            category_accuracy[category] = {
                'accuracy': accuracy,
                'correct': counts['correct'],
                'total': counts['total']
            }
        
        self.metrics['category_accuracy'] = category_accuracy
    
    def _analyze_errors(self):
        """Analyze common error patterns"""
        errors = []
        
        for result in self.results:
            if not result['correct']:
                expected_set = set(result['expected'])
                predicted_set = set(result['predicted'])
                
                errors.append({
                    'id': result['id'],
                    'text_snippet': result['text'][:100] + '...' if len(result['text']) > 100 else result['text'],
                    'expected': result['expected'],
                    'predicted': result['predicted'],
                    'missing_labels': list(expected_set - predicted_set),
                    'extra_labels': list(predicted_set - expected_set),
                    'category': result['category']
                })
        
        # Find common error patterns
        missing_label_counts = Counter()
        extra_label_counts = Counter()
        
        for error in errors:
            for label in error['missing_labels']:
                missing_label_counts[label] += 1
            for label in error['extra_labels']:
                extra_label_counts[label] += 1
        
        self.metrics['error_analysis'] = {
            'total_errors': len(errors),
            'error_rate': len(errors) / len(self.results),
            'most_missed_labels': dict(missing_label_counts.most_common(5)),
            'most_over_applied_labels': dict(extra_label_counts.most_common(5)),
            'sample_errors': errors[:10]  # First 10 errors as examples
        }
    
    def _generate_report(self):
        """Generate comprehensive evaluation report"""
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        
        # Overall metrics
        print(f"\n[OVERALL METRICS]")
        print(f"  - Overall Accuracy: {self.metrics['overall_accuracy']:.2%}")
        print(f"  - Correct Predictions: {self.metrics['correct_predictions']}/{self.metrics['total_predictions']}")
        print(f"  - Average Processing Time: {self.metrics['avg_processing_time_ms']:.2f} ms")
        print(f"  - Max Processing Time: {self.metrics['max_processing_time_ms']:.2f} ms")
        
        # Per-label metrics
        print(f"\n[PER-LABEL METRICS]")
        for label, metrics in self.metrics['label_metrics'].items():
            print(f"\n  {label}:")
            print(f"    - Precision: {metrics['precision']:.2%}")
            print(f"    - Recall: {metrics['recall']:.2%}")
            print(f"    - F1 Score: {metrics['f1_score']:.2%}")
            print(f"    - TP:{metrics['true_positives']} FP:{metrics['false_positives']} TN:{metrics['true_negatives']} FN:{metrics['false_negatives']}")
        
        # Performance analysis
        print(f"\n[PERFORMANCE ANALYSIS]")
        print(f"  - Median Processing Time: {self.metrics['performance']['median_time_ms']:.2f} ms")
        print(f"  - 95th Percentile: {self.metrics['performance']['95th_percentile_ms']:.2f} ms")
        print(f"  - 99th Percentile: {self.metrics['performance']['99th_percentile_ms']:.2f} ms")
        
        # Category accuracy
        print(f"\n[ACCURACY BY CATEGORY]")
        sorted_categories = sorted(self.metrics['category_accuracy'].items(), 
                                 key=lambda x: x[1]['accuracy'], reverse=True)
        for category, stats in sorted_categories[:10]:
            print(f"  - {category}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})")
        
        # Error analysis
        print(f"\n[ERROR ANALYSIS]")
        print(f"  • Total Errors: {self.metrics['error_analysis']['total_errors']}")
        print(f"  • Error Rate: {self.metrics['error_analysis']['error_rate']:.2%}")
        
        if self.metrics['error_analysis']['most_missed_labels']:
            print(f"\n  Most Frequently Missed Labels:")
            for label, count in self.metrics['error_analysis']['most_missed_labels'].items():
                print(f"    - {label}: {count} times")
        
        if self.metrics['error_analysis']['most_over_applied_labels']:
            print(f"\n  Most Frequently Over-Applied Labels:")
            for label, count in self.metrics['error_analysis']['most_over_applied_labels'].items():
                print(f"    - {label}: {count} times")
        
        # Sample errors
        if self.metrics['error_analysis']['sample_errors']:
            print(f"\n  Sample Errors (first 3):")
            for i, error in enumerate(self.metrics['error_analysis']['sample_errors'][:3], 1):
                print(f"\n    Error {i}:")
                print(f"      Text: {error['text_snippet']}")
                print(f"      Expected: {error['expected']}")
                print(f"      Predicted: {error['predicted']}")
        
        print("\n" + "=" * 60)
        print("EVALUATION COMPLETE")
        print("=" * 60)
    
    def export_results(self, output_path: str = "evaluation_results.json"):
        """Export detailed results to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metrics': self.metrics,
                'detailed_results': self.results[:50]  # First 50 for review
            }, f, indent=2, default=str)
        print(f"\n[EXPORT] Detailed results exported to: {output_path}")


def main():
    """Main execution function"""
    # Initialize labeler (without Bluesky client for testing)
    labeler = AutomatedLabeler()
    
    # Initialize evaluator
    evaluator = LabelerEvaluator(labeler, 'data.csv')
    
    # Run evaluation
    metrics = evaluator.run_evaluation()
    
    # Export results
    evaluator.export_results()
    
    # Return success
    return 0


if __name__ == "__main__":
    sys.exit(main())