#!/usr/bin/env python3
"""
Community Safety Alert Labeler for Bluesky
==========================================
Implementation for CS5342 Assignment 3 Part 2

This labeler identifies potentially sensitive immigration-related content
that could lead to community safety concerns or panic.

Labels:
- sensitive-location: Contains specific location/timing information
- unverified-media: Contains unverified media or suspicious links  
- community-alert: Contains escalatory language that may cause panic
"""

import re
import json
import csv
import os
import time
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
import pandas as pd
import numpy as np

# For Bluesky integration
try:
    from atproto import Client
    from pylabel.label import post_from_url
except ImportError:
    print("Note: Running in test mode without Bluesky integration")
    Client = None
    post_from_url = None

# Label constants
LOCATION_LABEL = "sensitive-location"
MEDIA_LABEL = "unverified-media"
ALERT_LABEL = "community-alert"


class AutomatedLabeler:
    """
    Community Safety Alert Labeler
    Identifies immigration-related content that could pose safety concerns
    """
    
    def __init__(self, client: Client = None, input_dir: str = None):
        """
        Initialize the labeler
        
        Args:
            client: Authenticated Bluesky client (optional for testing)
            input_dir: Directory containing input files (not used for policy labeler)
        """
        self.client = client
        self.input_dir = input_dir
        
        # Initialize detection components
        self.keyword_detector = KeywordDetector()
        self.location_analyzer = LocationAnalyzer()
        self.media_checker = MediaChecker()
        self.escalation_scanner = EscalationScanner()
        self.language_processor = LanguageProcessor()
        
        # Configuration thresholds (adjusted for better accuracy)
        self.LOCATION_THRESHOLD = 15  # Lower to catch more location mentions
        self.MEDIA_THRESHOLD = 10     # Lower to catch suspicious links
        self.ESCALATION_THRESHOLD = 15 # Lower to catch panic language
        
        # Performance tracking
        self.stats = Counter()
        self.cache = {}
        
    def moderate_post(self, url: str) -> List[str]:
        """
        Apply moderation to the post specified by the given url
        
        Args:
            url: Bluesky post URL or test string
            
        Returns:
            List of labels to apply
        """
        labels = []
        
        try:
            # Get post content
            text = self._get_post_text(url)
            embeds = self._get_post_embeds(url)
            
            # Perform analysis
            analysis = self._analyze_content(text, embeds)
            
            # Determine labels
            labels = self._determine_labels(analysis)
            
            # Update statistics
            self.stats['processed'] += 1
            for label in labels:
                self.stats[label] += 1
                
        except Exception as e:
            print(f"Error processing {url}: {e}")
            
        return labels
    
    def _get_post_text(self, url: str) -> str:
        """Extract text from post"""
        if self.client and post_from_url:
            try:
                post = post_from_url(self.client, url)
                if hasattr(post, 'record') and hasattr(post.record, 'text'):
                    return post.record.text
                elif hasattr(post, 'value') and hasattr(post.value, 'text'):
                    return post.value.text
            except:
                pass
        
        # For testing without Bluesky connection
        return url if not url.startswith('http') else ""
    
    def _get_post_embeds(self, url: str) -> List:
        """Extract embeds from post"""
        if self.client and post_from_url:
            try:
                post = post_from_url(self.client, url)
                if hasattr(post, 'record') and hasattr(post.record, 'embed'):
                    return [post.record.embed]
                elif hasattr(post, 'value') and hasattr(post.value, 'embed'):
                    return [post.value.embed]
            except:
                pass
        return []
    
    def _analyze_content(self, text: str, embeds: List) -> Dict[str, Any]:
        """Perform comprehensive content analysis"""
        analysis = {
            'keyword_score': 0,
            'location_score': 0,
            'media_score': 0,
            'escalation_score': 0,
            'details': {}
        }
        
        # Layer 1: Keyword Detection
        kw_score, kw_details = self.keyword_detector.analyze(text)
        analysis['keyword_score'] = kw_score
        analysis['details']['keywords'] = kw_details
        
        # Layer 2: Location Analysis
        loc_score, loc_details = self.location_analyzer.analyze(text)
        analysis['location_score'] = loc_score
        analysis['details']['locations'] = loc_details
        
        # Layer 3: Media Checking
        media_score, media_details = self.media_checker.analyze(text, embeds)
        analysis['media_score'] = media_score
        analysis['details']['media'] = media_details
        
        # Layer 4: Escalation Detection
        esc_score, esc_details = self.escalation_scanner.analyze(text)
        analysis['escalation_score'] = esc_score
        analysis['details']['escalation'] = esc_details
        
        # Layer 5: Language Processing
        lang_details = self.language_processor.analyze(text)
        if lang_details.get('multi_language'):
            analysis['escalation_score'] += 15
        analysis['details']['languages'] = lang_details
        
        return analysis
    
    def _determine_labels(self, analysis: Dict[str, Any]) -> List[str]:
        """Determine which labels to apply based on analysis scores"""
        labels = []
        
        # Check location sensitivity
        if analysis['location_score'] >= self.LOCATION_THRESHOLD:
            labels.append(LOCATION_LABEL)
            
        # Check media verification
        if analysis['media_score'] >= self.MEDIA_THRESHOLD:
            labels.append(MEDIA_LABEL)
            
        # Check escalation level
        total_escalation = analysis['escalation_score'] + (analysis['keyword_score'] * 0.5)
        if total_escalation >= self.ESCALATION_THRESHOLD:
            labels.append(ALERT_LABEL)
            
        return labels


class KeywordDetector:
    """Detects immigration and enforcement related keywords"""
    
    def __init__(self):
        # Primary keywords
        self.primary_terms = [
            'ice', 'immigration', 'raid', 'raids', 'deportation', 
            'detention', 'detain', 'enforcement', 'removal',
            'border patrol', 'cbp', 'dhs', 'ins', 'uscis',
            'undocumented', 'illegal', 'checkpoint', 'sweep',
            'round up', 'operation', 'task force'
        ]
        
        # Spanish terms
        self.spanish_terms = [
            'redada', 'redadas', 'migra', 'migracion', 'deportación',
            'detención', 'frontera', 'patrulla fronteriza',
            'indocumentado', 'punto de control', 'operativo'
        ]
        
        # Context amplifiers
        self.amplifiers = [
            'confirmed', 'verified', 'breaking', 'urgent', 'alert',
            'warning', 'spotted', 'seen', 'reported', 'active'
        ]
        
        # Build regex patterns
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        self.patterns = {}
        
        # Primary pattern
        primary = '|'.join(re.escape(term) for term in self.primary_terms)
        self.patterns['primary'] = re.compile(r'\b(' + primary + r')\b', re.IGNORECASE)
        
        # Spanish pattern  
        spanish = '|'.join(re.escape(term) for term in self.spanish_terms)
        self.patterns['spanish'] = re.compile(r'\b(' + spanish + r')\b', re.IGNORECASE)
        
        # Amplifier pattern
        amps = '|'.join(re.escape(term) for term in self.amplifiers)
        self.patterns['amplifier'] = re.compile(r'\b(' + amps + r')\b', re.IGNORECASE)
        
    def analyze(self, text: str) -> Tuple[int, Dict]:
        """Analyze text for keywords and return score"""
        score = 0
        details = {
            'primary_matches': [],
            'spanish_matches': [],
            'amplifiers': []
        }
        
        # Check primary terms
        primary_matches = self.patterns['primary'].findall(text)
        if primary_matches:
            details['primary_matches'] = primary_matches
            score += len(primary_matches) * 10
            
        # Check Spanish terms
        spanish_matches = self.patterns['spanish'].findall(text)
        if spanish_matches:
            details['spanish_matches'] = spanish_matches
            score += len(spanish_matches) * 10
            
        # Check amplifiers
        amp_matches = self.patterns['amplifier'].findall(text)
        if amp_matches:
            details['amplifiers'] = amp_matches
            score += len(amp_matches) * 3
            
        # Bonus for combinations
        if primary_matches and amp_matches:
            score += 10
            
        return score, details


class LocationAnalyzer:
    """Analyzes location information in posts"""
    
    def __init__(self):
        self.sensitive_places = [
            'school', 'church', 'mosque', 'temple', 'synagogue',
            'hospital', 'clinic', 'shelter', 'sanctuary', 'courthouse',
            'community center', 'library', 'university', 'college'
        ]
        
        # Address pattern
        self.address_pattern = re.compile(
            r'\d+\s+[\w\s]+\s+(street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|way|court|ct|plaza|place|pl)\b',
            re.IGNORECASE
        )
        
        # Coordinate pattern
        self.coord_pattern = re.compile(
            r'[-]?\d{1,3}\.\d+[,\s]+[-]?\d{1,3}\.\d+'
        )
        
        # Time patterns
        self.time_patterns = [
            r'\b(now|right now|immediately|urgent|today|tonight|tomorrow|this morning|this afternoon|this evening)\b',
            r'\b\d{1,2}:\d{2}\s*(am|pm|AM|PM)?\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
        ]
        
    def analyze(self, text: str) -> Tuple[int, Dict]:
        """Analyze text for location information"""
        score = 0
        details = {
            'addresses': [],
            'coordinates': [],
            'sensitive_places': [],
            'temporal_markers': []
        }
        
        # Check for addresses
        addresses = self.address_pattern.findall(text)
        if addresses:
            details['addresses'] = addresses
            score += len(addresses) * 20
            
        # Check for coordinates
        coords = self.coord_pattern.findall(text)
        if coords:
            details['coordinates'] = coords
            score += 30
            
        # Check sensitive places
        text_lower = text.lower()
        for place in self.sensitive_places:
            if place in text_lower:
                details['sensitive_places'].append(place)
                score += 15
                
        # Check temporal markers
        for pattern in self.time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                details['temporal_markers'].extend(matches)
                score += len(matches) * 3
                
        return score, details


class MediaChecker:
    """Checks media and links for verification status"""
    
    def __init__(self):
        self.verified_domains = [
            'reuters.com', 'apnews.com', 'bbc.com', 'npr.org',
            'nytimes.com', 'washingtonpost.com', 'wsj.com',
            'cnn.com', 'foxnews.com', 'nbcnews.com', 'abcnews.com',
            'theguardian.com', 'bloomberg.com', '.gov', '.edu'
        ]
        
        self.suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'short.link', 'ow.ly',
            't.co', 'telegram.', 'whatsapp.', 'signal.',
            'rumble.com', 'bitchute.com', 'gab.com', 'parler.com',
            'truthsocial.com', 'gettr.com'
        ]
        
        # URL pattern
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+', 
            re.IGNORECASE
        )
        
    def analyze(self, text: str, embeds: List) -> Tuple[int, Dict]:
        """Analyze media and links"""
        score = 0
        details = {
            'urls': [],
            'unverified_urls': [],
            'suspicious_urls': [],
            'has_images': False,
            'has_videos': False
        }
        
        # Extract URLs from text
        urls = self.url_pattern.findall(text)
        details['urls'] = urls
        
        for url in urls:
            url_lower = url.lower()
            
            # Check if verified
            is_verified = any(domain in url_lower for domain in self.verified_domains)
            
            if not is_verified:
                details['unverified_urls'].append(url)
                score += 10
                
                # Check if suspicious
                for suspicious in self.suspicious_domains:
                    if suspicious in url_lower:
                        details['suspicious_urls'].append(url)
                        score += 15
                        break
                        
        # Check embeds
        for embed in embeds:
            if embed and hasattr(embed, 'py_type'):
                embed_type = embed.py_type.lower() if hasattr(embed.py_type, 'lower') else str(embed.py_type).lower()
                if 'image' in embed_type:
                    details['has_images'] = True
                    score += 5
                elif 'video' in embed_type:
                    details['has_videos'] = True
                    score += 10
                    
        return score, details


class EscalationScanner:
    """Scans for escalatory and panic-inducing language"""
    
    def __init__(self):
        self.panic_phrases = [
            'spread this', 'share now', 'urgent', 'emergency',
            'everyone needs to know', 'pass it on', 'make this viral',
            'repost', 'boost', 'signal boost', 'please share',
            'breaking', 'happening now', 'confirmed', 'verified'
        ]
        
        self.mobilization_phrases = [
            'gather at', 'meet at', 'show up', 'be there',
            'mobilize', 'organize', 'action needed', 'join us',
            'stand together', 'resist', 'fight back'
        ]
        
        self.fear_phrases = [
            'they are coming', 'be careful', 'stay away',
            'avoid', 'danger', 'warning', 'alert', 'threat',
            'at risk', 'not safe', 'stay inside', 'lock doors'
        ]
        
    def analyze(self, text: str) -> Tuple[int, Dict]:
        """Analyze text for escalatory language"""
        score = 0
        details = {
            'panic_phrases': [],
            'mobilization_phrases': [],
            'fear_phrases': [],
            'all_caps_words': 0,
            'exclamations': 0
        }
        
        text_lower = text.lower()
        
        # Check panic phrases
        for phrase in self.panic_phrases:
            if phrase in text_lower:
                details['panic_phrases'].append(phrase)
                score += 8
                
        # Check mobilization phrases
        for phrase in self.mobilization_phrases:
            if phrase in text_lower:
                details['mobilization_phrases'].append(phrase)
                score += 10
                
        # Check fear phrases
        for phrase in self.fear_phrases:
            if phrase in text_lower:
                details['fear_phrases'].append(phrase)
                score += 7
                
        # Check for ALL CAPS
        caps_words = re.findall(r'\b[A-Z]{4,}\b', text)
        if caps_words:
            details['all_caps_words'] = len(caps_words)
            score += min(len(caps_words) * 2, 10)
            
        # Check exclamations
        exclamation_count = text.count('!')
        if exclamation_count >= 3:
            details['exclamations'] = exclamation_count
            score += min(exclamation_count, 8)
            
        return score, details


class LanguageProcessor:
    """Processes multiple languages and detects evasion"""
    
    def __init__(self):
        # Character set patterns for different languages
        self.language_patterns = {
            'spanish': re.compile(r'[áéíóúñüÁÉÍÓÚÑÜ]'),
            'chinese': re.compile(r'[\u4e00-\u9fff]'),
            'arabic': re.compile(r'[\u0600-\u06ff\u0750-\u077f]'),
            'cyrillic': re.compile(r'[\u0400-\u04ff]'),
            'hindi': re.compile(r'[\u0900-\u097f]')
        }
        
    def analyze(self, text: str) -> Dict:
        """Detect languages and potential evasion tactics"""
        details = {
            'languages_detected': [],
            'multi_language': False,
            'possible_evasion': False
        }
        
        # Detect languages
        for lang, pattern in self.language_patterns.items():
            if pattern.search(text):
                details['languages_detected'].append(lang)
                
        # Check for multiple languages (potential evasion)
        if len(details['languages_detected']) > 1:
            details['multi_language'] = True
            details['possible_evasion'] = True
            
        # Check for character substitution
        if re.search(r'[1|!][cC][3E]|[0o][pP][3E][rR]', text):
            details['possible_evasion'] = True
            
        return details