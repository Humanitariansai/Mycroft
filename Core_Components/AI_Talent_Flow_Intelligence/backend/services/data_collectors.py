"""
Data collection services for talent intelligence gathering.
Implements ethical, compliant data collection from public sources.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import requests
import json
from dataclasses import dataclass
import time
import hashlib
import os

# GitHub API
import github
from github import Github

# Data processing
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

# Internal imports
from models.schemas import TalentProfile, CompanyProfile, TalentMovement, TalentMovementType


logger = logging.getLogger(__name__)


@dataclass
class CollectionConfig:
    """Configuration for data collection operations"""
    rate_limit_delay: float = 1.0  # seconds between requests
    max_retries: int = 3
    timeout: int = 30
    respect_robots_txt: bool = True
    user_agent: str = "Mycroft-TalentIntel/1.0 (Educational Research)"


class GitHubTalentCollector:
    """Collects talent intelligence from GitHub public data"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.client = Github(self.github_token) if self.github_token else None
        self.config = CollectionConfig()
        
    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Get public GitHub user profile data"""
        if not self.client:
            logger.warning("No GitHub token provided, using anonymous access")
            return await self._get_anonymous_profile(username)
        
        try:
            user = self.client.get_user(username)
            
            # Get user basic info
            profile_data = {
                'username': user.login,
                'name': user.name,
                'company': user.company,
                'location': user.location,
                'bio': user.bio,
                'blog': user.blog,
                'email': user.email,
                'followers': user.followers,
                'following': user.following,
                'public_repos': user.public_repos,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            }
            
            # Get recent activity
            profile_data['recent_activity'] = await self._get_recent_activity(user)
            
            # Get language and technology analysis
            profile_data['tech_profile'] = await self._analyze_tech_profile(user)
            
            # Get collaboration network
            profile_data['collaborations'] = await self._get_collaborations(user)
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error collecting GitHub profile for {username}: {e}")
            return {}
    
    async def _get_anonymous_profile(self, username: str) -> Dict[str, Any]:
        """Get basic profile data without authentication"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, headers={'User-Agent': self.config.user_agent})
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"GitHub API returned {response.status_code} for {username}")
                return {}
                
        except Exception as e:
            logger.error(f"Error in anonymous GitHub collection for {username}: {e}")
            return {}
    
    async def _get_recent_activity(self, user) -> Dict[str, Any]:
        """Analyze recent GitHub activity patterns"""
        try:
            repos = list(user.get_repos())[:20]  # Last 20 repos
            
            activity_data = {
                'total_commits': 0,
                'recent_commits': 0,
                'active_repos': 0,
                'languages_used': set(),
                'last_activity': None,
            }
            
            cutoff_date = datetime.now() - timedelta(days=90)
            
            for repo in repos:
                if repo.updated_at and repo.updated_at > cutoff_date:
                    activity_data['active_repos'] += 1
                    
                    # Get commit activity (sample)
                    try:
                        commits = list(repo.get_commits(since=cutoff_date))[:10]
                        activity_data['recent_commits'] += len(commits)
                        
                        if commits and (not activity_data['last_activity'] or 
                                      commits[0].commit.author.date > activity_data['last_activity']):
                            activity_data['last_activity'] = commits[0].commit.author.date
                            
                    except Exception:
                        pass  # Skip if we can't access commits
                
                # Collect languages
                if repo.language:
                    activity_data['languages_used'].add(repo.language)
            
            activity_data['languages_used'] = list(activity_data['languages_used'])
            if activity_data['last_activity']:
                activity_data['last_activity'] = activity_data['last_activity'].isoformat()
            
            return activity_data
            
        except Exception as e:
            logger.error(f"Error analyzing recent activity: {e}")
            return {}
    
    async def _analyze_tech_profile(self, user) -> Dict[str, Any]:
        """Analyze technical profile and expertise"""
        try:
            repos = list(user.get_repos())
            
            tech_profile = {
                'primary_languages': {},
                'framework_experience': set(),
                'ai_ml_experience': False,
                'open_source_contributions': 0,
                'repository_quality_score': 0.0,
            }
            
            total_size = 0
            for repo in repos:
                if repo.language:
                    tech_profile['primary_languages'][repo.language] = \
                        tech_profile['primary_languages'].get(repo.language, 0) + (repo.size or 0)
                    total_size += repo.size or 0
                
                # Check for AI/ML indicators
                repo_name = (repo.name or '').lower()
                repo_desc = (repo.description or '').lower()
                ai_keywords = ['ai', 'ml', 'machine learning', 'neural', 'tensorflow', 'pytorch', 'opencv']
                
                if any(keyword in repo_name + ' ' + repo_desc for keyword in ai_keywords):
                    tech_profile['ai_ml_experience'] = True
                
                # Quality indicators
                if repo.stargazers_count and repo.stargazers_count > 0:
                    tech_profile['open_source_contributions'] += repo.stargazers_count
                    tech_profile['repository_quality_score'] += min(repo.stargazers_count / 100, 1.0)
            
            # Normalize language percentages
            if total_size > 0:
                for lang in tech_profile['primary_languages']:
                    tech_profile['primary_languages'][lang] = \
                        tech_profile['primary_languages'][lang] / total_size
            
            tech_profile['framework_experience'] = list(tech_profile['framework_experience'])
            
            return tech_profile
            
        except Exception as e:
            logger.error(f"Error analyzing tech profile: {e}")
            return {}
    
    async def _get_collaborations(self, user) -> List[Dict[str, Any]]:
        """Find collaboration patterns and networks"""
        try:
            collaborations = []
            repos = list(user.get_repos())[:10]  # Sample recent repos
            
            for repo in repos:
                try:
                    contributors = list(repo.get_contributors())
                    if len(contributors) > 1:  # Multi-contributor repo
                        for contributor in contributors[:5]:  # Top 5 contributors
                            if contributor.login != user.login:
                                collab_data = {
                                    'collaborator': contributor.login,
                                    'repository': repo.name,
                                    'contributions': contributor.contributions,
                                    'repo_stars': repo.stargazers_count,
                                }
                                collaborations.append(collab_data)
                except Exception:
                    continue  # Skip repos we can't access
            
            return collaborations[:20]  # Return top 20 collaborations
            
        except Exception as e:
            logger.error(f"Error finding collaborations: {e}")
            return []


class LinkedInTalentCollector:
    """Collects publicly available LinkedIn data (educational/research purposes only)"""
    
    def __init__(self):
        self.config = CollectionConfig()
        # Note: This is a placeholder for educational demonstration
        # Real implementation would need proper LinkedIn API partnership
        
    async def get_public_profile_data(self, profile_url: str) -> Dict[str, Any]:
        """
        Placeholder for LinkedIn public data collection
        In production, this would use official LinkedIn APIs with proper authentication
        """
        logger.info(f"LinkedIn data collection for {profile_url} - EDUCATIONAL PLACEHOLDER")
        
        # Simulated profile data for demonstration
        return {
            'name': 'Sample AI Researcher',
            'current_company': 'TechCorp AI',
            'current_role': 'Senior ML Engineer',
            'location': 'San Francisco, CA',
            'experience': [
                {
                    'company': 'TechCorp AI',
                    'role': 'Senior ML Engineer', 
                    'duration': '2022-Present',
                    'description': 'Leading computer vision research team'
                },
                {
                    'company': 'Previous Corp',
                    'role': 'ML Engineer',
                    'duration': '2020-2022',
                    'description': 'Developed NLP models for enterprise'
                }
            ],
            'skills': ['Machine Learning', 'Python', 'TensorFlow', 'Computer Vision'],
            'education': [
                {
                    'institution': 'Stanford University',
                    'degree': 'PhD Computer Science',
                    'year': '2020'
                }
            ],
            'data_source': 'simulated',
            'collection_note': 'Educational demonstration - not real data'
        }


class AcademicDataCollector:
    """Collects academic publication and research data"""
    
    def __init__(self):
        self.config = CollectionConfig()
        
    async def get_researcher_publications(self, researcher_name: str, 
                                        affiliation: Optional[str] = None) -> Dict[str, Any]:
        """Collect academic publication data using public APIs"""
        try:
            # Use arXiv API for demonstration
            arxiv_data = await self._query_arxiv(researcher_name)
            
            # Could integrate with other sources like:
            # - Google Scholar API
            # - Semantic Scholar API  
            # - PubMed for medical AI research
            
            return {
                'researcher': researcher_name,
                'affiliation': affiliation,
                'publications': arxiv_data,
                'total_papers': len(arxiv_data),
                'recent_activity': self._analyze_publication_activity(arxiv_data),
                'collaboration_network': self._extract_coauthors(arxiv_data),
            }
            
        except Exception as e:
            logger.error(f"Error collecting academic data for {researcher_name}: {e}")
            return {}
    
    async def _query_arxiv(self, author_name: str) -> List[Dict[str, Any]]:
        """Query arXiv for researcher's publications"""
        try:
            import urllib.parse
            import xml.etree.ElementTree as ET
            
            # arXiv API query
            query = f'au:"{author_name}"'
            url = f'http://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&max_results=50'
            
            await asyncio.sleep(self.config.rate_limit_delay)  # Rate limiting
            
            response = requests.get(url, headers={'User-Agent': self.config.user_agent})
            
            if response.status_code == 200:
                return self._parse_arxiv_response(response.text)
            else:
                logger.warning(f"arXiv API returned {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error querying arXiv: {e}")
            return []
    
    def _parse_arxiv_response(self, xml_text: str) -> List[Dict[str, Any]]:
        """Parse arXiv XML response"""
        try:
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(xml_text)
            papers = []
            
            # Parse each entry
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                paper = {
                    'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                    'authors': [author.find('{http://www.w3.org/2005/Atom}name').text 
                              for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                    'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
                    'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
                    'link': entry.find('{http://www.w3.org/2005/Atom}id').text,
                }
                
                # Extract categories
                categories = []
                for category in entry.findall('{http://www.w3.org/2005/Atom}category'):
                    categories.append(category.get('term'))
                paper['categories'] = categories
                
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error parsing arXiv response: {e}")
            return []
    
    def _analyze_publication_activity(self, publications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze publication patterns and activity"""
        if not publications:
            return {}
        
        try:
            # Parse publication dates
            dates = []
            for pub in publications:
                try:
                    date_str = pub.get('published', '')
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dates.append(date)
                except:
                    continue
            
            if not dates:
                return {}
            
            # Calculate activity metrics
            now = datetime.now().replace(tzinfo=dates[0].tzinfo)
            recent_cutoff = now - timedelta(days=365)  # Last year
            
            recent_papers = [d for d in dates if d > recent_cutoff]
            
            return {
                'total_publications': len(dates),
                'recent_publications': len(recent_papers),
                'publication_frequency': len(recent_papers) / 12,  # per month
                'first_publication': min(dates).isoformat() if dates else None,
                'last_publication': max(dates).isoformat() if dates else None,
                'active_researcher': len(recent_papers) > 0,
            }
            
        except Exception as e:
            logger.error(f"Error analyzing publication activity: {e}")
            return {}
    
    def _extract_coauthors(self, publications: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract collaboration network from coauthors"""
        coauthor_counts = {}
        
        for pub in publications:
            authors = pub.get('authors', [])
            for author in authors:
                if author not in coauthor_counts:
                    coauthor_counts[author] = 0
                coauthor_counts[author] += 1
        
        # Sort by collaboration frequency
        return dict(sorted(coauthor_counts.items(), key=lambda x: x[1], reverse=True)[:20])


class TalentMovementDetector:
    """Detects and analyzes talent movements across companies"""
    
    def __init__(self):
        self.github_collector = GitHubTalentCollector()
        self.linkedin_collector = LinkedInTalentCollector()
        self.academic_collector = AcademicDataCollector()
        
    async def detect_profile_changes(self, talent_profile: TalentProfile) -> Optional[TalentMovement]:
        """Detect if a talent profile has changed companies or roles"""
        try:
            current_data = {}
            
            # Collect current data from all sources
            if talent_profile.github_username:
                github_data = await self.github_collector.get_user_profile(talent_profile.github_username)
                current_data['github'] = github_data
            
            if talent_profile.linkedin_url:
                linkedin_data = await self.linkedin_collector.get_public_profile_data(talent_profile.linkedin_url)
                current_data['linkedin'] = linkedin_data
            
            # Compare with stored profile
            movement = self._analyze_profile_differences(talent_profile, current_data)
            
            return movement
            
        except Exception as e:
            logger.error(f"Error detecting profile changes for {talent_profile.name}: {e}")
            return None
    
    def _analyze_profile_differences(self, stored_profile: TalentProfile, 
                                   current_data: Dict[str, Any]) -> Optional[TalentMovement]:
        """Compare stored vs current profile data to detect movements"""
        try:
            # Check for company changes
            current_company = None
            
            if 'linkedin' in current_data:
                current_company = current_data['linkedin'].get('current_company')
            elif 'github' in current_data:
                current_company = current_data['github'].get('company')
            
            if current_company and current_company != stored_profile.current_company:
                # Movement detected!
                movement = TalentMovement(
                    id=f"movement_{stored_profile.id}_{int(datetime.now().timestamp())}",
                    talent_id=stored_profile.id,
                    talent_name=stored_profile.name,
                    movement_type=TalentMovementType.JOB_CHANGE,
                    from_company=stored_profile.current_company,
                    to_company=current_company,
                    from_role=stored_profile.current_role,
                    to_role=current_data.get('linkedin', {}).get('current_role', 'Unknown'),
                    movement_date=datetime.now(),
                    expected_impact='moderate',  # Default, would be calculated
                    confidence_score=0.8,  # Based on data source reliability
                    strategic_importance=stored_profile.influence_score,
                    detection_source='automated_profile_monitoring',
                    detection_confidence=0.8,
                )
                
                return movement
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing profile differences: {e}")
            return None


class CompanyTalentTracker:
    """Tracks talent changes at the company level"""
    
    def __init__(self):
        self.movement_detector = TalentMovementDetector()
        
    async def analyze_company_talent_flow(self, company: CompanyProfile) -> Dict[str, Any]:
        """Analyze overall talent flow for a company"""
        try:
            # This would integrate with a database of tracked talent
            # For now, return simulated analysis
            
            return {
                'company_id': company.id,
                'company_name': company.name,
                'analysis_date': datetime.now().isoformat(),
                'talent_flow_metrics': {
                    'net_talent_flow': 5,  # +5 high-quality hires vs exits
                    'hiring_velocity': 12,  # 12 new hires this quarter
                    'retention_rate': 0.94,  # 94% retention rate
                    'quality_score': 0.78,  # Quality of new hires
                },
                'recent_movements': {
                    'key_hires': [],  # Would be populated from database
                    'notable_exits': [],
                    'internal_promotions': [],
                },
                'competitive_intelligence': {
                    'talent_sources': {},  # Where they're hiring from
                    'talent_destinations': {},  # Where people are going
                    'skill_gaps': [],
                },
                'investment_implications': {
                    'talent_momentum': 'positive',
                    'innovation_potential': 'high',
                    'execution_risk': 'low',
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing company talent flow: {e}")
            return {}


# Example usage and testing functions
async def test_data_collection():
    """Test the data collection pipeline"""
    print("Testing AI Talent Flow Intelligence Data Collection")
    
    # Test GitHub collection
    github_collector = GitHubTalentCollector()
    profile_data = await github_collector.get_user_profile("octocat")  # GitHub mascot
    print(f"GitHub profile data: {json.dumps(profile_data, indent=2, default=str)}")
    
    # Test academic collection
    academic_collector = AcademicDataCollector()
    academic_data = await academic_collector.get_researcher_publications("Geoffrey Hinton")
    print(f"Academic data: {json.dumps(academic_data, indent=2, default=str)}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_data_collection())