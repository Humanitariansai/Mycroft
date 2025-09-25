#!/usr/bin/env python3
"""
USPTO Patent Bulk Data Downloader and Viewer
Downloads PatentsView bulk data and displays in interactive tables
"""

import requests
import pandas as pd
import zipfile
import os
from pathlib import Path
import io
from urllib.parse import urljoin
from datetime import datetime
import time

class PatentBulkDownloader:
    """Download and process USPTO PatentsView bulk data"""
    
    def __init__(self, data_dir="patent_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.base_url = "https://patentsview.org/download/data-download-tables"
        
        # Available datasets - starting with core ones
        self.datasets = {
            'patent': 'Basic patent information',
            'application': 'Patent application details', 
            'assignee': 'Patent assignee/owner information',
            'cpc_current': 'Current CPC classifications',
            'inventor': 'Inventor information',
            'location': 'Geographic location data'
        }
        
    def get_download_links(self):
        """Get current download links for PatentsView data"""
        # PatentsView direct download URLs (these are the actual current links)
        links = {
            'patent': 'https://s3.amazonaws.com/data.patentsview.org/download/g_patent.tsv.zip',
        }
        return links
    
    def download_dataset(self, dataset_name, force_download=False):
        """Download a specific dataset"""
        if dataset_name not in self.datasets:
            raise ValueError(f"Dataset {dataset_name} not available. Choose from: {list(self.datasets.keys())}")
        
        zip_path = self.data_dir / f"{dataset_name}.tsv.zip"
        tsv_path = self.data_dir / f"{dataset_name}.tsv"
        
        # Skip if already downloaded and not forcing
        if tsv_path.exists() and not force_download:
            print(f"✅ {dataset_name} already downloaded. Use force_download=True to re-download.")
            return tsv_path
        
        print(f"📥 Downloading {dataset_name} dataset...")
        print(f"📋 Description: {self.datasets[dataset_name]}")
        
        links = self.get_download_links()
        url = links[dataset_name]
        
        try:
            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"\r⬇️  Progress: {progress:.1f}% ({downloaded_size / 1024 / 1024:.1f} MB)", end="")
            
            print(f"\n✅ Downloaded {zip_path}")
            
            # Extract the ZIP file
            print("📂 Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.data_dir)
            
            print(f"✅ Extracted to {tsv_path}")
            
            # Clean up ZIP file to save space
            zip_path.unlink()
            
            return tsv_path
            
        except Exception as e:
            print(f"❌ Error downloading {dataset_name}: {str(e)}")
            return None
    
    def load_dataset(self, dataset_name, nrows=None):
        """Load a dataset into pandas DataFrame"""
        tsv_path = self.data_dir / f"{dataset_name}.tsv"
        
        if not tsv_path.exists():
            print(f"Dataset {dataset_name} not found. Downloading...")
            tsv_path = self.download_dataset(dataset_name)
            if not tsv_path:
                return None
        
        print(f"📊 Loading {dataset_name} dataset...")
        try:
            # Load with low_memory=False to avoid dtype warnings on large files
            df = pd.read_csv(tsv_path, sep='\t', low_memory=False, nrows=nrows)
            print(f"✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            print(f"❌ Error loading {dataset_name}: {str(e)}")
            return None
    
    def get_dataset_info(self, dataset_name):
        """Get basic info about a dataset without loading all data"""
        tsv_path = self.data_dir / f"{dataset_name}.tsv"
        
        if not tsv_path.exists():
            return f"Dataset {dataset_name} not downloaded yet."
        
        # Read just the header and a few rows for info
        sample_df = pd.read_csv(tsv_path, sep='\t', nrows=5, low_memory=False)
        
        # Get file size
        file_size = tsv_path.stat().st_size / (1024 * 1024)  # MB
        
        info = {
            'file_size_mb': round(file_size, 2),
            'columns': list(sample_df.columns),
            'sample_data': sample_df
        }
        
        return info

# Initialize the downloader
downloader = PatentBulkDownloader()

print("🚀 USPTO Patent Bulk Data Downloader Ready!")
print("\nAvailable datasets:")
for name, desc in downloader.datasets.items():
    print(f"  📁 {name}: {desc}")

print(f"\n💾 Data will be saved to: {downloader.data_dir.absolute()}")

# Example usage functions for notebook
def download_and_explore_patents(nrows=10000):
    """Download patent dataset and show basic exploration"""
    print("=" * 60)
    print("🔍 EXPLORING PATENT DATASET")
    print("=" * 60)
    
    # Download patent data
    patent_df = downloader.load_dataset('patent', nrows=nrows)
    if patent_df is None:
        return None
    
    print(f"\n📈 Dataset shape: {patent_df.shape}")
    print(f"📅 Data range: {patent_df['date'].min()} to {patent_df['date'].max()}")
    
    print("\n📋 Column names:")
    for i, col in enumerate(patent_df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\n🔍 Sample data:")
    display_cols = ['id', 'type', 'number', 'date', 'title', 'abstract']
    available_cols = [col for col in display_cols if col in patent_df.columns]
    
    return patent_df[available_cols].head(10)

def download_and_explore_assignees(nrows=10000):
    """Download assignee dataset and show company information"""
    print("=" * 60)
    print("🏢 EXPLORING ASSIGNEE DATASET")
    print("=" * 60)
    
    assignee_df = downloader.load_dataset('assignee', nrows=nrows)
    if assignee_df is None:
        return None
    
    print(f"\n📈 Dataset shape: {assignee_df.shape}")
    print("\n📋 Column names:")
    for i, col in enumerate(assignee_df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\n🔍 Sample data:")
    display_cols = ['id', 'type', 'organization', 'first_name', 'last_name']
    available_cols = [col for col in display_cols if col in assignee_df.columns]
    
    return assignee_df[available_cols].head(10)

def find_tech_companies():
    """Find patents from major tech companies"""
    print("=" * 60)
    print("🔍 FINDING TECH COMPANY PATENTS")
    print("=" * 60)
    
    # Load assignee data first
    assignee_df = downloader.load_dataset('assignee', nrows=50000)
    if assignee_df is None:
        return None
    
    # Search for tech companies
    tech_companies = ['Google', 'Microsoft', 'Apple', 'Amazon', 'Meta', 'Netflix', 'Tesla', 'NVIDIA']
    
    tech_assignees = assignee_df[
        assignee_df['organization'].str.contains('|'.join(tech_companies), case=False, na=False)
    ]
    
    print(f"\n🏢 Found {len(tech_assignees)} assignee records from major tech companies")
    print("\n🔝 Top tech company assignees:")
    
    return tech_assignees.groupby('organization').size().sort_values(ascending=False).head(10)

# Quick start examples
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 QUICK START EXAMPLES")
    print("="*80)
    
    print("\n1️⃣  To explore patents:")
    print("   patents = download_and_explore_patents()")
    
    print("\n2️⃣  To explore assignees/companies:")
    print("   assignees = download_and_explore_assignees()")
    
    print("\n3️⃣  To find tech company patents:")
    print("   tech_companies = find_tech_companies()")
    
    print("\n4️⃣  To download specific datasets:")
    print("   downloader.download_dataset('cpc_current')  # Technology classifications")
    print("   downloader.download_dataset('inventor')     # Inventor information")
    
    print("\n5️⃣  To get dataset info without loading:")
    print("   info = downloader.get_dataset_info('patent')")
    
    print("\n💡 TIP: Add nrows parameter to limit data for faster testing:")
    print("   patents = downloader.load_dataset('patent', nrows=1000)")