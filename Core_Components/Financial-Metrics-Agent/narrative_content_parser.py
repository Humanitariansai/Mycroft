#!/usr/bin/env python3
"""
SEC Filing Narrative Content Parser
This script extracts narrative content from SEC filings by parsing the HTML sections.
It identifies and extracts text from key narrative sections like MD&A, Risk Factors, etc.
"""

import re
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime

class SECNarrativeParser:
    def __init__(self):
        # Common section patterns for different filing types
        self.section_patterns = {
            '10-K': {
                'business': r'item\s+1[\.\s\-]+business',
                'risk_factors': r'item\s+1a[\.\s\-]+risk\s+factors',
                'properties': r'item\s+2[\.\s\-]+properties',
                'legal_proceedings': r'item\s+3[\.\s\-]+legal\s+proceedings',
                'controls_procedures': r'item\s+4[\.\s\-]+controls\s+and\s+procedures',
                'market_risk': r'item\s+7a[\.\s\-]+market\s+risk',
                'md_a': r'item\s+7[\.\s\-]+management[\'\u2019]?s\s+discussion\s+and\s+analysis',
                'financial_statements': r'item\s+8[\.\s\-]+financial\s+statements',
                'controls_internal': r'item\s+9a[\.\s\-]+controls\s+and\s+procedures',
                'directors_officers': r'item\s+10[\.\s\-]+directors',
                'executive_compensation': r'item\s+11[\.\s\-]+executive\s+compensation',
                'security_ownership': r'item\s+12[\.\s\-]+security\s+ownership',
                'certain_relationships': r'item\s+13[\.\s\-]+certain\s+relationships',
                'principal_accountant': r'item\s+14[\.\s\-]+principal\s+accountant',
                'exhibits': r'item\s+15[\.\s\-]+exhibits'
            },
            '10-Q': {
                'financial_statements': r'part\s+i[\.\s\-]+item\s+1[\.\s\-]+financial\s+statements',
                'md_a': r'part\s+i[\.\s\-]+item\s+2[\.\s\-]+management[\'\u2019]?s\s+discussion\s+and\s+analysis',
                'market_risk': r'part\s+i[\.\s\-]+item\s+3[\.\s\-]+market\s+risk',
                'controls_procedures': r'part\s+i[\.\s\-]+item\s+4[\.\s\-]+controls\s+and\s+procedures',
                'legal_proceedings': r'part\s+ii[\.\s\-]+item\s+1[\.\s\-]+legal\s+proceedings',
                'risk_factors': r'part\s+ii[\.\s\-]+item\s+1a[\.\s\-]+risk\s+factors',
                'unregistered_sales': r'part\s+ii[\.\s\-]+item\s+2[\.\s\-]+unregistered\s+sales',
                'defaults': r'part\s+ii[\.\s\-]+item\s+3[\.\s\-]+defaults',
                'mine_safety': r'part\s+ii[\.\s\-]+item\s+4[\.\s\-]+mine\s+safety',
                'other_information': r'part\s+ii[\.\s\-]+item\s+5[\.\s\-]+other\s+information',
                'exhibits': r'part\s+ii[\.\s\-]+item\s+6[\.\s\-]+exhibits'
            },
            '8-K': {
                'business_combinations': r'item\s+1\.01[\.\s\-]+entry\s+into\s+a\s+material\s+definitive\s+agreement',
                'completion_acquisition': r'item\s+2\.01[\.\s\-]+completion\s+of\s+acquisition',
                'creation_direct_financial': r'item\s+2\.02[\.\s\-]+results\s+of\s+operations',
                'material_agreements': r'item\s+1\.01[\.\s\-]+entry\s+into.*agreement',
                'departure_directors': r'item\s+5\.02[\.\s\-]+departure\s+of\s+directors',
                'other_events': r'item\s+8\.01[\.\s\-]+other\s+events',
                'financial_statements': r'item\s+9\.01[\.\s\-]+financial\s+statements'
            },
            'DEF 14A': {
                'executive_compensation': r'executive\s+compensation',
                'director_compensation': r'director\s+compensation',
                'security_ownership': r'security\s+ownership',
                'audit_committee': r'audit\s+committee',
                'proposal': r'proposal\s+\d+',
                'board_matters': r'corporate\s+governance'
            },
            'SC 13G': {
                'general_statement': r'general\s+statement',
                'identity_statement': r'identity\s+and\s+background',
                'source_funds': r'source\s+and\s+amount\s+of\s+funds',
                'purpose_transaction': r'purpose\s+of\s+transaction'
            }
        }
        
        # Noise patterns to remove
        self.noise_patterns = [
            r'table\s+of\s+contents',
            r'page\s+\d+',
            r'^\s*\d+\s*$',  # Page numbers
            r'^\s*-+\s*$',   # Dashes
            r'^\s*=+\s*$',   # Equal signs
            r'\*+',          # Asterisks
        ]
    
    def extract_html_sections(self, filing_content: str) -> List[str]:
        """
        Extract HTML document sections from SEC filing content
        """
        # SEC filings often contain multiple documents separated by specific markers
        html_sections = []
        
        # Look for HTML document boundaries
        html_doc_pattern = r'<HTML>.*?</HTML>'
        html_matches = re.findall(html_doc_pattern, filing_content, re.DOTALL | re.IGNORECASE)
        
        if html_matches:
            html_sections = html_matches
        else:
            # If no HTML tags found, look for document boundaries
            doc_pattern = r'<DOCUMENT>.*?</DOCUMENT>'
            doc_matches = re.findall(doc_pattern, filing_content, re.DOTALL | re.IGNORECASE)
            
            # Filter for HTML documents
            for doc in doc_matches:
                if re.search(r'<TYPE>.*?HTML', doc, re.IGNORECASE):
                    html_sections.append(doc)
        
        return html_sections
    
    def clean_html_content(self, html_content: str) -> str:
        """
        Clean and extract text from HTML content
        """
        try:
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'meta', 'link']):
                element.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace and formatting
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize line breaks
            text = re.sub(r'\t', ' ', text)           # Replace tabs with spaces
            text = re.sub(r' +', ' ', text)          # Multiple spaces to single
            
            # Remove common noise patterns
            for pattern in self.noise_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
            
            return text.strip()
            
        except Exception as e:
            print(f"Error cleaning HTML content: {e}")
            return ""
    
    def find_section_boundaries(self, text: str, form_type: str) -> Dict[str, Tuple[int, int]]:
        """
        Find the start and end positions of different sections in the text
        """
        sections = {}
        patterns = self.section_patterns.get(form_type, {})
        
        # If no specific patterns for this form type, try generic patterns
        if not patterns:
            patterns = self._get_generic_patterns(text)
        
        # Find all section starts
        section_starts = []
        for section_name, pattern in patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                section_starts.append((match.start(), section_name))
        
        # If we didn't find any matches with our patterns, try a more generic approach
        if not section_starts:
            section_starts = self._find_generic_sections(text)
        
        # Sort by position
        section_starts.sort(key=lambda x: x[0])
        
        # Determine section boundaries
        for i, (start_pos, section_name) in enumerate(section_starts):
            if i + 1 < len(section_starts):
                end_pos = section_starts[i + 1][0]
            else:
                end_pos = len(text)
            
            sections[section_name] = (start_pos, end_pos)
        
        return sections
    
    def _get_generic_patterns(self, text: str) -> Dict[str, str]:
        """
        Generate generic patterns based on what we find in the text
        """
        patterns = {}
        
        # Look for common patterns in the text
        common_sections = [
            ('business', r'business'),
            ('risk_factors', r'risk\s+factors?'),
            ('md_a', r'management[\'\u2019]?s\s+discussion'),
            ('financial_statements', r'financial\s+statements?'),
            ('legal_proceedings', r'legal\s+proceedings?'),
            ('executive_compensation', r'executive\s+compensation'),
            ('directors', r'directors?'),
            ('other_events', r'other\s+events?'),
        ]
        
        for section_name, base_pattern in common_sections:
            # Try different formats
            full_patterns = [
                rf'item\s+\d+[a-z]*[\.\s\-]+{base_pattern}',
                rf'part\s+[iv]+[\.\s\-]+item\s+\d+[\.\s\-]+{base_pattern}',
                rf'{base_pattern}',  # Just the section name
            ]
            
            for pattern in full_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    patterns[section_name] = pattern
                    break
        
        return patterns
    
    def _find_generic_sections(self, text: str) -> List[Tuple[int, str]]:
        """
        Find sections using a more generic approach
        """
        section_starts = []
        
        # Look for lines that start with ITEM or PART
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Match patterns like "ITEM 1. Business", "PART I - ITEM 2", etc.
            item_match = re.match(r'^item\s+(\d+[a-z]*[\.\s]+.*)', line_clean, re.IGNORECASE)
            part_match = re.match(r'^part\s+[iv]+.*item\s+(\d+[a-z]*[\.\s]+.*)', line_clean, re.IGNORECASE)
            
            if item_match or part_match:
                # Find position in original text
                pos = text.find(line)
                if pos != -1:
                    section_name = f"section_{len(section_starts)+1}"
                    section_starts.append((pos, section_name))
        
        return section_starts
    
    def extract_section_content(self, text: str, section_name: str, start_pos: int, end_pos: int) -> str:
        """
        Extract and clean content from a specific section
        """
        section_text = text[start_pos:end_pos]
        
        # Remove section header (first few lines)
        lines = section_text.split('\n')
        
        # Skip the first few lines which usually contain the section title
        content_lines = []
        header_skipped = False
        
        for line in lines:
            line = line.strip()
            if not header_skipped and len(line) > 0:
                # Skip lines that look like headers
                if not re.match(r'^(item|part)\s+\d+', line, re.IGNORECASE):
                    content_lines.append(line)
                    header_skipped = True
                continue
            elif header_skipped:
                content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        # Additional cleaning
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 consecutive newlines
        
        return content
    
    def parse_filing_narrative(self, filing_content: str, form_type: str) -> Dict:
        """
        Main method to parse narrative content from a filing
        """
        result = {
            'form_type': form_type,
            'parsing_timestamp': datetime.now().isoformat(),
            'sections': {},
            'metadata': {
                'total_characters': 0,
                'sections_found': 0,
                'html_sections_count': 0
            }
        }
        
        # Extract HTML sections
        html_sections = self.extract_html_sections(filing_content)
        result['metadata']['html_sections_count'] = len(html_sections)
        
        if not html_sections:
            print("No HTML sections found in the filing")
            return result
        
        # Process each HTML section (usually there's just one main document)
        for i, html_section in enumerate(html_sections):
            print(f"Processing HTML section {i + 1}/{len(html_sections)}")
            
            # Clean HTML and extract text
            clean_text = self.clean_html_content(html_section)
            
            if not clean_text:
                continue
            
            # Find section boundaries
            section_boundaries = self.find_section_boundaries(clean_text, form_type)
            
            # Extract each section's content
            for section_name, (start_pos, end_pos) in section_boundaries.items():
                section_content = self.extract_section_content(
                    clean_text, section_name, start_pos, end_pos
                )
                
                if section_content and len(section_content) > 100:  # Filter very short sections
                    result['sections'][section_name] = {
                        'content': section_content,
                        'character_count': len(section_content),
                        'word_count': len(section_content.split()),
                        'position_in_document': start_pos
                    }
                    
                    result['metadata']['total_characters'] += len(section_content)
                    result['metadata']['sections_found'] += 1
        
        return result
    
    def parse_filing_file(self, file_path: str) -> Optional[Dict]:
        """
        Parse narrative content from a filing file
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        # Extract form type from filename
        filename = os.path.basename(file_path)
        form_type = self.extract_form_type_from_filename(filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            print(f"Parsing narrative content from {filename}")
            return self.parse_filing_narrative(content, form_type)
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def extract_form_type_from_filename(self, filename: str) -> str:
        """
        Extract form type from filename
        """
        # Common patterns: TICKER_10-K_DATE.txt, TICKER_10-Q_DATE.txt, etc.
        # Handle patterns like AAPL_8-K_A_DATE.txt and AAPL_DEF 14A_DATE.txt
        form_match = re.search(r'_([0-9A-Z\-\s\/]+?)_\d{4}-\d{2}-\d{2}', filename)
        if form_match:
            form_type = form_match.group(1).replace('_', '/').strip()
            # Handle special cases
            if form_type.endswith('/A'):
                form_type = form_type[:-2] + '/A'  # Convert "8-K/A" format
            return form_type
        
        # Fallback to common form types
        filename_upper = filename.upper()
        if 'DEF 14A' in filename_upper or 'DEF_14A' in filename_upper:
            return 'DEF 14A'
        elif 'SC 13G' in filename_upper or 'SC_13G' in filename_upper:
            return 'SC 13G'
        elif '8-K_A' in filename_upper:
            return '8-K/A'
        elif '10-K' in filename_upper:
            return '10-K'
        elif '10-Q' in filename_upper:
            return '10-Q'
        elif '8-K' in filename_upper:
            return '8-K'
        
        return 'UNKNOWN'
    
    def batch_parse_directory(self, directory_path: str, output_file: str = None) -> Dict:
        """
        Parse all SEC filing files in a directory
        """
        if not os.path.isdir(directory_path):
            print(f"Directory not found: {directory_path}")
            return {}
        
        results = {}
        
        # Find all .txt files (SEC filings)
        filing_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
        
        if not filing_files:
            print("No .txt files found in directory")
            return {}
        
        print(f"Found {len(filing_files)} filing files to process")
        
        for filename in filing_files:
            file_path = os.path.join(directory_path, filename)
            
            print(f"\nProcessing: {filename}")
            result = self.parse_filing_file(file_path)
            
            if result:
                results[filename] = result
                print(f"  - Found {result['metadata']['sections_found']} sections")
                print(f"  - Total characters: {result['metadata']['total_characters']:,}")
            else:
                print(f"  - Failed to parse")
        
        # Save results if output file specified
        if output_file:
            self.save_results(results, output_file)
        
        return results
    
    def debug_filing_content(self, filing_content: str, form_type: str, max_preview_chars: int = 2000) -> Dict:
        """
        Debug method to inspect filing content and identify why sections aren't being found
        """
        debug_info = {
            'form_type': form_type,
            'total_content_length': len(filing_content),
            'html_sections': [],
            'cleaned_text_preview': '',
            'potential_section_headers': [],
            'pattern_matches': {}
        }
        
        # Extract HTML sections
        html_sections = self.extract_html_sections(filing_content)
        debug_info['html_sections'] = [len(section) for section in html_sections]
        
        if html_sections:
            # Take the largest HTML section for analysis
            main_section = max(html_sections, key=len)
            
            # Clean the content
            clean_text = self.clean_html_content(main_section)
            debug_info['cleaned_text_preview'] = clean_text[:max_preview_chars]
            
            # Look for potential section headers (lines that start with "ITEM" or "PART")
            lines = clean_text.split('\n')
            potential_headers = []
            
            for i, line in enumerate(lines[:200]):  # Check first 200 lines
                line_clean = line.strip()
                if re.match(r'^(item|part)\s+\d+', line_clean, re.IGNORECASE):
                    potential_headers.append(f"Line {i}: {line_clean[:100]}")
            
            debug_info['potential_section_headers'] = potential_headers
            
            # Test our patterns against the text
            patterns = self.section_patterns.get(form_type, {})
            for section_name, pattern in patterns.items():
                matches = list(re.finditer(pattern, clean_text, re.IGNORECASE | re.MULTILINE))
                if matches:
                    debug_info['pattern_matches'][section_name] = [
                        f"Position {m.start()}: {clean_text[m.start():m.end()+50]}" 
                        for m in matches[:3]
                    ]
        
        return debug_info
    
    def debug_filing_file(self, file_path: str) -> Optional[Dict]:
        """
        Debug a single filing file
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        filename = os.path.basename(file_path)
        form_type = self.extract_form_type_from_filename(filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return self.debug_filing_content(content, form_type)
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
        """
        Save parsing results to JSON file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {output_file}")
            
            # Print summary
            total_files = len(results)
            total_sections = sum(r['metadata']['sections_found'] for r in results.values())
            total_chars = sum(r['metadata']['total_characters'] for r in results.values())
            
            print(f"\nSummary:")
            print(f"  Files processed: {total_files}")
            print(f"  Total sections extracted: {total_sections}")
            print(f"  Total characters: {total_chars:,}")
            
        except Exception as e:
            print(f"Error saving results: {e}")

    def save_results(self, results: Dict, output_file: str):
        """
        Save parsing results to JSON file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {output_file}")
            
            # Print summary
            total_files = len(results)
            total_sections = sum(r['metadata']['sections_found'] for r in results.values())
            total_chars = sum(r['metadata']['total_characters'] for r in results.values())
            
            print(f"\nSummary:")
            print(f"  Files processed: {total_files}")
            print(f"  Total sections extracted: {total_sections}")
            print(f"  Total characters: {total_chars:,}")
            
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    parser = SECNarrativeParser()
    
    print("SEC Filing Narrative Content Parser")
    print("=" * 40)
    
    choice = input("\nChoose an option:\n1. Parse single file\n2. Parse directory\n3. Debug single file\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "3":
        file_path = input("Enter path to SEC filing file for debugging: ").strip()
        
        debug_info = parser.debug_filing_file(file_path)
        
        if debug_info:
            print(f"\n{'='*60}")
            print("DEBUG INFORMATION")
            print('='*60)
            print(f"Form Type: {debug_info['form_type']}")
            print(f"Total Content Length: {debug_info['total_content_length']:,} characters")
            print(f"HTML Sections Found: {len(debug_info['html_sections'])} (sizes: {debug_info['html_sections']})")
            
            print(f"\nPotential Section Headers Found:")
            if debug_info['potential_section_headers']:
                for header in debug_info['potential_section_headers'][:10]:
                    print(f"  {header}")
            else:
                print("  None found")
            
            print(f"\nPattern Matches:")
            if debug_info['pattern_matches']:
                for section, matches in debug_info['pattern_matches'].items():
                    print(f"  {section}:")
                    for match in matches:
                        print(f"    {match}")
            else:
                print("  No pattern matches found")
            
            print(f"\nCleaned Text Preview (first 2000 chars):")
            print("-" * 50)
            print(debug_info['cleaned_text_preview'])
            print("-" * 50)
            
            # Try parsing again after showing debug info
            print(f"\nAttempting to parse with enhanced detection...")
            result = parser.parse_filing_file(file_path)
            if result and result['metadata']['sections_found'] > 0:
                print(f"SUCCESS! Found {result['metadata']['sections_found']} sections")
            else:
                print("Still no sections found. The patterns may need adjustment.")
    
    elif choice == "1":
        file_path = input("Enter path to SEC filing file: ").strip()
        
        result = parser.parse_filing_file(file_path)
        
        if result:
            print(f"\nParsing completed!")
            print(f"Form Type: {result['form_type']}")
            print(f"Sections found: {result['metadata']['sections_found']}")
            print(f"Total characters: {result['metadata']['total_characters']:,}")
            
            print(f"\nSections extracted:")
            for section_name, section_data in result['sections'].items():
                print(f"  - {section_name}: {section_data['character_count']:,} chars, {section_data['word_count']} words")
            
            # Save individual result
            output_file = file_path.replace('.txt', '_narrative.json')
            parser.save_results({os.path.basename(file_path): result}, output_file)
            
            # Show preview of first section
            if result['sections']:
                first_section = list(result['sections'].keys())[0]
                first_content = result['sections'][first_section]['content']
                print(f"\nPreview of '{first_section}' (first 300 characters):")
                print("-" * 50)
                print(first_content[:300] + "...")
                print("-" * 50)
    
    elif choice == "2":
        directory_path = input("Enter directory path containing SEC filing files: ").strip()
        output_file = input("Enter output JSON file name (or press Enter for default): ").strip()
        
        if not output_file:
            output_file = "sec_narrative_analysis.json"
        
        results = parser.batch_parse_directory(directory_path, output_file)
        
        if results:
            print(f"\nBatch processing completed!")
            print(f"Processed {len(results)} files")
            
            # Show section distribution
            section_counts = {}
            for result in results.values():
                for section_name in result['sections'].keys():
                    section_counts[section_name] = section_counts.get(section_name, 0) + 1
            
            print(f"\nMost common sections found:")
            for section, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {section}: {count} filings")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()