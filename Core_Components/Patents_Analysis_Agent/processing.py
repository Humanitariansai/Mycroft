import pandas as pd
import ast

# -------- CONFIG ----------
INPUT_FILE = "patents.csv"
OUTPUT_FILE = "processed_patents.csv"

AI_KEYWORDS = ["artificial intelligence", "neural", "machine learning", "deep learning", "ai"]
AI_CPC_PREFIXES = ["G06N", "G06F17", "G06F18"]  
# ---------------------------

def safe_eval(s):
    """Safely eval JSON-like strings stored in CSV."""
    try:
        return ast.literal_eval(s)
    except Exception:
        return []

def extract_org(assignee_field):
    assignees = safe_eval(assignee_field)
    if assignees and isinstance(assignees, list):
        return assignees[0].get("assignee_organization")
    return None

def extract_inventors(inventor_field):
    inventors = safe_eval(inventor_field)
    if inventors and isinstance(inventors, list):
        return "; ".join(
            f"{inv.get('inventor_name_first','')} {inv.get('inventor_name_last','')}".strip()
            for inv in inventors
        )
    return None

def extract_cpc(cpc_field):
    cpcs = safe_eval(cpc_field)
    if cpcs and isinstance(cpcs, list):
        return "; ".join(c["cpc_class_id"] for c in cpcs if "cpc_class_id" in c)
    return None

def extract_wipo(wipo_field):
    wipos = safe_eval(wipo_field)
    if wipos and isinstance(wipos, list):
        return "; ".join(w["wipo_field_id"] for w in wipos if "wipo_field_id" in w)
    return None

def is_ai_related(title, cpc_field):
    title_lower = str(title).lower()
    if any(kw in title_lower for kw in AI_KEYWORDS):
        return True
    cpcs = safe_eval(cpc_field)
    for c in cpcs:
        if any(c["cpc_class_id"].startswith(pref) for pref in AI_CPC_PREFIXES):
            return True
    return False

def process_csv(input_file, output_file):
    df = pd.read_csv(input_file)

    processed_df = pd.DataFrame({
        "patent_id": df["patent_id"],
        "patent_title": df["patent_title"],
        "patent_date": df["patent_date"],
        "organization": df["assignees"].apply(extract_org),
        "inventors": df["inventors"].apply(extract_inventors),
        "cpc_classes": df["cpc_current"].apply(extract_cpc),
        "wipo_fields": df["wipo"].apply(extract_wipo),
    })

    processed_df["is_ai"] = df.apply(
        lambda row: is_ai_related(row["patent_title"], row["cpc_current"]), axis=1
    )

    processed_df.to_csv(output_file, index=False)
    print(f"Processed dataset saved as {output_file}")
    return processed_df

if __name__ == "__main__":
    process_csv(INPUT_FILE, OUTPUT_FILE)
