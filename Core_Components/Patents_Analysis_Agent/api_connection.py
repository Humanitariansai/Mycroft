import os
import sys
import json
import time
import argparse
import requests
import pandas as pd
from urllib.parse import urlencode


def fetch_all_patents(base_url, endpoint, params, api_key, response_key,
                      per_page=100, max_retries=5, sleep_time=2,
                      checkpoint_file="checkpoint.csv", checkpoint_interval=10):
    all_results = []
    page = 1
    total_records = None

    while True:
        params_with_paging = params.copy()
        # Fix: Put pagination params at root level, not in "o" object
        params_with_paging["page"] = page
        params_with_paging["per_page"] = per_page

        # Build URL properly
        url = f"{base_url}/{endpoint.strip('/')}/"
        
        retries = 0
        while retries < max_retries:
            try:
                # Send as form data, not as JSON in query string
                response = requests.post(url, 
                                       data=params_with_paging, 
                                       headers={"X-Api-Key": api_key}, 
                                       timeout=30)
                
                if response.status_code == 200:
                    break
                elif response.status_code == 429:  # Too Many Requests
                    wait = sleep_time * (2 ** retries)
                    print(f"⚠️ Rate limited. Sleeping {wait}s...")
                    time.sleep(wait)
                    retries += 1
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Network error on page {page}: {e}")
                wait = sleep_time * (2 ** retries)
                print(f"Retrying in {wait}s...")
                time.sleep(wait)
                retries += 1

        if retries >= max_retries:
            print(f"❌ Failed after {max_retries} retries. Saving progress and exiting.")
            break

        response_data = response.json()
        
        # Get the actual data key
        data_key = response_key(endpoint)
        data = response_data.get(data_key, [])
        
        # Get total count from response (if available)
        if total_records is None and 'total_patent_count' in response_data:
            total_records = response_data['total_patent_count']
            print(f"📊 Total records to fetch: {total_records}")
        
        if not data:
            print("✅ No more results on this page.")
            break

        # Check for duplicates (same patent_id as previous batch)
        if all_results and len(data) > 0:
            existing_ids = {item.get('patent_id') for item in all_results[-per_page:]}
            new_ids = {item.get('patent_id') for item in data}
            if existing_ids.intersection(new_ids):
                print("⚠️ Duplicate records detected - may have reached end of results")
                break

        all_results.extend(data)
        print(f"✅ Page {page} fetched ({len(data)} records), total so far: {len(all_results)}")
        
        # Check if we have all records
        if total_records and len(all_results) >= total_records:
            print(f"✅ All {total_records} records fetched!")
            break

        # Save checkpoint every N pages
        if page % checkpoint_interval == 0:
            pd.DataFrame(all_results).to_csv(checkpoint_file, index=False)
            print(f"💾 Checkpoint saved at {checkpoint_file} (page {page})")

        page += 1

    # Final save
    if all_results:
        pd.DataFrame(all_results).to_csv(checkpoint_file, index=False)
        print(f"📂 Final results saved at {checkpoint_file} ({len(all_results)} records).")
    
    return pd.DataFrame(all_results)


def main():
    parser = argparse.ArgumentParser(description="Fetch all patents from API with checkpointing")
    parser.add_argument("--base_url", default=os.getenv("PATENT_API_BASE", "https://search.patentsview.org"))
    parser.add_argument("--endpoint", default=os.getenv("PATENT_API_ENDPOINT", "api/v1/patent"))
    parser.add_argument("--api_key", default=os.getenv("PATENT_API_KEY", "xM1ScdAa.06Lz8WKH2U5FLdiqXbRtPIygexgeNP3L"))
    parser.add_argument("--year", default=os.getenv("PATENT_YEAR", "2021"))
    parser.add_argument("--output", default=os.getenv("PATENT_OUTPUT", "patents.csv"))
    parser.add_argument("--checkpoint_interval", type=int, default=10)
    args = parser.parse_args()

    special_keys = {
        "api/v1/ipc": "ipcr",
        "api/v1/wipo": "wipo",
    }

    def response_key(endpoint: str) -> str:
        """
        Given the API endpoint contacted, returns the json key for the data returned by the API.
        """
        endpoint = endpoint.rstrip("/")
        leaf = endpoint.split("/")[-1]
        if leaf in special_keys:
            return special_keys[leaf]
        elif leaf.endswith("s"):
            return leaf + "es"
        else:
            return leaf + "s"

    # Convert the query to JSON string format as expected by PatentsView API
    params = {
        "f": json.dumps(["patent_id", "patent_title", "patent_date", "inventors"]),
        "q": json.dumps({"patent_year": args.year}),
    }

    df = fetch_all_patents(
        args.base_url,
        args.endpoint,
        params,
        args.api_key,
        response_key,
        checkpoint_file=args.output,
        checkpoint_interval=args.checkpoint_interval,
    )

    print(f"✅ Done. {len(df)} records collected.")


if __name__ == "__main__":
    main()