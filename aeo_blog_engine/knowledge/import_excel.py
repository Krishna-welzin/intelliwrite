import os
import argparse
import pandas as pd
from pathlib import Path

def clean_filename(name):
    """Sanitize brand name for folder creation."""
    return "".join([c if c.isalnum() else "_" for c in name]).strip()

def import_brand_data(excel_path):
    print(f"Reading data from: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Normalize column names to lowercase for easier matching
    df.columns = [c.lower().strip() for c in df.columns]
    print(f"Found columns: {list(df.columns)}")

    # Map expected fields to likely column names
    # Adjust these keys based on your actual Excel headers
    col_map = {
        "name": ["company_name", "company name", "brand", "company"],
        "url": ["url", "website", "link"],
        "industry": ["industry", "sector", "niche"],
        "analysis": ["analysis_data", "analysis data", "analysis", "brand analysis"],
        "competitors": ["competitors", "competition"],
        "prompts": ["prompts", "brand prompts"]
    }

    base_docs_dir = Path(os.path.dirname(__file__)) / "docs"

    for index, row in df.iterrows():
        # Find brand name
        brand_name = None
        for col in col_map["name"]:
            if col in df.columns:
                brand_name = row[col]
                break
        
        if not brand_name or pd.isna(brand_name):
            print(f"Skipping row {index}: No brand name found.")
            continue

        safe_name = clean_filename(str(brand_name))
        brand_dir = base_docs_dir / safe_name
        brand_dir.mkdir(parents=True, exist_ok=True)

        print(f"Processing brand: {brand_name}")

        # Construct Markdown content
        md_content = f"# Brand Profile: {brand_name}\n\n"
        
        # URL
        for col in col_map["url"]:
            if col in df.columns and not pd.isna(row[col]):
                md_content += f"**Website:** {row[col]}\n\n"
                break
        
        # Industry
        for col in col_map["industry"]:
            if col in df.columns and not pd.isna(row[col]):
                md_content += f"**Industry:** {row[col]}\n\n"
                break

        md_content += "---\n\n"

        # Analysis
        for col in col_map["analysis"]:
            if col in df.columns and not pd.isna(row[col]):
                md_content += f"## Brand Analysis\n\n{row[col]}\n\n"
                break

        # Competitors
        for col in col_map["competitors"]:
            if col in df.columns and not pd.isna(row[col]):
                md_content += f"## Competitors\n\n{row[col]}\n\n"
                break

        # Prompts
        for col in col_map["prompts"]:
            if col in df.columns and not pd.isna(row[col]):
                md_content += f"## System Prompts / Guidelines\n\n{row[col]}\n\n"
                break

        # Write to file
        output_file = brand_dir / "profile.md"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"Saved profile to: {output_file}")
        except Exception as e:
            print(f"Failed to write file for {brand_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import brand data from Excel to Knowledge Base.")
    parser.add_argument("file_path", help="Path to the .xlsx file containing brand data.")
    args = parser.parse_args()

    import_brand_data(args.file_path)
