#!/usr/bin/env python3
"""
MODULE 1: FIXED SEARCH ENGINE - Based on earlier working version
Enhanced with input validation for security
"""
import json
import re
import html
import logging
from datetime import datetime

DATA_FILE = "/media/data/webapps/f250_ai_manual/data/indexes/all_manuals_combined.json"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedSearch:
    def __init__(self):
        self.data = self.load_data()
        self.last_results = []
        self.last_query = ""
        self.security_log = []
        
        # Compile regex patterns for efficiency
        self.allowed_chars_pattern = re.compile(r'^[A-Za-z0-9\s\.,\'\"\-\!\?\(\)\:\;]+$')
        self.quote_pattern = re.compile(r'"([^"]+)"')  # For exact phrase detection
    
    def load_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Data file not found: {DATA_FILE}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data file: {e}")
            return None
    
    def validate_and_sanitize_query(self, query):
        """
        Validate and sanitize search query to prevent injection attacks.
        Returns: (is_valid, sanitized_query, validation_notes)
        """
        if not query or not isinstance(query, str):
            logger.warning("Empty or non-string query received")
            return False, "", "Invalid input type"
        
        # Trim whitespace
        query = query.strip()
        if not query:
            logger.warning("Empty query after trimming")
            return False, "", "Empty query"
        
        # Check length (prevent DoS via very long queries)
        if len(query) > 200:
            logger.warning(f"Query too long: {len(query)} characters")
            return False, "", "Query too long (max 200 characters)"
        
        # HTML escape to prevent XSS if query is displayed anywhere
        query = html.escape(query)
        
        # Allowlist validation: only allow reasonable search characters
        if not self.allowed_chars_pattern.match(query):
            # Log security event with details (but truncate for safety)
            truncated_query = query[:100] + "..." if len(query) > 100 else query
            logger.warning(f"Security: Invalid characters in query: '{truncated_query}'")
            
            # Record in security log
            self.security_log.append({
                'query': truncated_query,
                'reason': 'Invalid characters',
                'timestamp': datetime.now().isoformat()[:-7]  # Remove microseconds
            })
            
            return False, "", "Invalid characters in query. Use only letters, numbers, and basic punctuation."
        
        # Additional security: Check for suspicious patterns
        suspicious_patterns = [
            r'<script', r'javascript:', r'onload=', r'onerror=',
            r';', r'--', r'\/\*', r'\*\/',  # SQL comment patterns
            r'\.\.\/', r'\.\.\\',  # Directory traversal
            r'\|\|', r'&&',  # Command injection patterns
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Security: Suspicious pattern detected in query: {pattern}")
                self.security_log.append({
                    'query': query[:100] if len(query) > 100 else query,
                    'reason': f'Suspicious pattern: {pattern}',
                    'timestamp': datetime.now().isoformat()[:-7]
                })
                return False, "", "Suspicious query pattern detected"
        
        return True, query, "Valid query"
    
    def weighted_search(self, query):
        """
        WEIGHTED SEARCH with exact phrase support and security validation.
        - Doesn't require ALL words
        - Scores based on word matches
        - Prioritizes pages with more matches
        - Supports exact phrases in quotes: "fuel filter"
        """
        # Validate the query BEFORE processing
        is_valid, clean_query, validation_msg = self.validate_and_sanitize_query(query)
        if not is_valid:
            logger.info(f"Rejected invalid query: '{query[:50]}...' - {validation_msg}")
            return []
        
        original_query = clean_query
        query = clean_query.strip()
        self.last_query = original_query
        
        if not self.data:
            logger.error("No data loaded for search")
            return []
        
        logger.info(f"Searching for: '{original_query}'")
        
        # Detect exact phrase search (text in quotes)
        exact_phrase = None
        phrase_match = self.quote_pattern.search(query)
        if phrase_match:
            exact_phrase = phrase_match.group(1).lower()
            # Validate the phrase content as well
            phrase_is_valid, _, _ = self.validate_and_sanitize_query(exact_phrase)
            if not phrase_is_valid:
                logger.warning(f"Invalid phrase in quotes: '{exact_phrase}'")
                exact_phrase = None
            else:
                # Remove quotes from query for additional word matching
                query = self.quote_pattern.sub('', query).strip()
        
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        if not query_words and not exact_phrase:
            logger.info("Query too short or meaningless")
            return []
        
        results = []
        
        for entry in self.data.get('entries', []):
            text = entry.get('text', '').lower()
            
            if len(text) < 50:
                continue
            
            # Initialize score
            score = 0
            
            # A. WORD MATCH SCORING (if we have query_words)
            if query_words:
                word_matches = sum(1 for word in query_words if word in text)
                
                if word_matches == 0 and not exact_phrase:
                    continue  # Skip pages with no matches
                
                # 1. Base score for each word match
                score += word_matches * 10
                
                # 2. Bonus for having ALL words
                if word_matches == len(query_words):
                    score += 50
                
                # 3. Bonus for word proximity
                if word_matches > 1:
                    positions = []
                    for word in query_words:
                        if word in text:
                            pos = text.find(word)
                            if pos != -1:
                                positions.append(pos)
                    
                    if len(positions) > 1:
                        positions.sort()
                        distances = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
                        if distances:
                            avg_distance = sum(distances) / len(distances)
                            
                            if avg_distance < 100:
                                score += 30
                            elif avg_distance < 500:
                                score += 10
            else:
                word_matches = 0
            
            # B. EXACT PHRASE SCORING (higher priority)
            if exact_phrase:
                if exact_phrase in text:
                    # Major boost for exact phrase match
                    score += 100
                    # Additional bonus for multiple occurrences
                    occurrences = text.count(exact_phrase)
                    score += occurrences * 20
                elif not query_words:
                    # If ONLY phrase search and no match, skip this page
                    continue
            
            # C. TECHNICAL CONTENT BONUS
            if any(term in text for term in ['torque', 'specification', 'procedure', 'installation']):
                score += 5
            
            # D. SPECS BONUS
            if re.search(r'\d+\.?\d*\s*(nm|lb|ft|psi|mm|in|°|deg)', text, re.IGNORECASE):
                score += 20
            
            # Get context (prioritize phrase context if available)
            if exact_phrase and exact_phrase in text:
                # Find phrase for context
                pos = text.find(exact_phrase)
                if pos != -1:
                    start = max(0, pos - 80)
                    end = min(len(text), pos + len(exact_phrase) + 120)
                    context = entry['text'][start:end]
                    if start > 0:
                        context = "..." + context
                    if end < len(entry['text']):
                        context = context + "..."
                else:
                    context = self.get_context(entry['text'], query_words)
            else:
                context = self.get_context(entry['text'], query_words)
            
            results.append({
                'manual': entry['manual'],
                'page': entry['page'],
                'score': score,
                'context': context,
                'full_text': entry['text'],
                'word_count': entry.get('word_count', 0),
                'matches': word_matches + (1 if exact_phrase and exact_phrase in text else 0),
                'total_words': len(query_words) + (1 if exact_phrase else 0)
            })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Filter out very low scores (adjust threshold for phrase-only searches)
        min_score = 5 if exact_phrase and not query_words else 10
        filtered_results = [r for r in results if r['score'] >= min_score]
        
        logger.info(f"Found {len(filtered_results)} relevant pages")
        
        self.last_results = filtered_results
        return filtered_results
    
    def get_context(self, text, query_words):
        """Get readable context - SIMPLE version like earlier"""
        text_lower = text.lower()
        
        # Find first occurrence of any query word
        first_pos = len(text)
        for word in query_words:
            pos = text_lower.find(word)
            if pos != -1 and pos < first_pos:
                first_pos = pos
        
        if first_pos < len(text):
            start = max(0, first_pos - 80)
            end = min(len(text), first_pos + 120)
            context = text[start:end]
            
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."
            
            return context
        
        return text[:200] + "..."
    
    def get_security_log(self, limit=10):
        """Get recent security events"""
        return self.security_log[-limit:] if self.security_log else []
    
    def show_results(self, results):
        """Show results like earlier working version"""
        if not results:
            print(f"\n❌ No good results found for '{self.last_query}'")
            print(f"\n💡 Try simpler search:")
            print(f"   • 'wheel torque' instead of 'wheel lug torque specs'")
            print(f"   • 'lug nut' instead of 'wheel lug nut'")
            print(f"   • 'torque specification'")
            return 0
        
        print(f"\n📚 SEARCH RESULTS for '{self.last_query}':")
        print("=" * 80)
        
        for i, result in enumerate(results[:8], 1):  # Show first 8 like earlier
            # Show match info
            match_info = f"({result['matches']}/{result['total_words']} words)"
            
            print(f"\n{i}. {result['manual'][:50]}...")
            print(f"   Page {result['page']} | Score: {result['score']} {match_info}")
            print(f"   {result['context']}")
        
        print("\n" + "=" * 80)
        return len(results)
    
    def run_interactive(self):
        """Interactive search like earlier"""
        print("\n🚛 F250 MANUAL SEARCH")
        print("=" * 60)
        print("Tips: Use 2-3 words for best results")
        print("Type 'quit' to exit")
        print("=" * 60)
        
        while True:
            query = input("\n🔍 Search for: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            results = self.weighted_search(query)
            num_results = self.show_results(results)
            
            if num_results > 0:
                print(f"\n✅ Found {num_results} results. Options:")
                print("   1. View a result in detail")
                print("   2. New search")
                print("   3. Quit")
                
                while True:
                    choice = input("\nSelect (1-3): ").strip()
                    
                    if choice == '1':
                        try:
                            result_num = int(input(f"Which result (1-{min(8, num_results)})? ").strip())
                            if 1 <= result_num <= min(8, num_results):
                                selected = results[result_num - 1]
                                print(f"\n🎯 Selected: {selected['manual']} - Page {selected['page']}")
                                print(f"\n📖 PAGE PREVIEW:")
                                print("-" * 60)
                                # Show cleaned text
                                text = selected['full_text']
                                # Clean up all-caps
                                lines = text.split('\n')
                                for line in lines[:10]:  # First 10 lines
                                    if line.strip():
                                        print(f"  {line[:80]}")
                                print("-" * 60)
                                
                                print(f"\n💡 Next: Would open manual to page {selected['page']}")
                                print("     (Module 2 will handle this)")
                                
                                input("\nPress Enter to continue...")
                                break  # Go back to search options
                            else:
                                print(f"❌ Please enter 1-{min(8, num_results)}")
                        except ValueError:
                            print("❌ Please enter a number")
                    
                    elif choice == '2':
                        break  # New search
                    
                    elif choice == '3':
                        print("👋 Goodbye!")
                        return
                    
                    else:
                        print("❌ Please enter 1, 2, or 3")

def main():
    search = FixedSearch()
    search.run_interactive()

if __name__ == "__main__":
    main()
