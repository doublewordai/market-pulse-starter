#!/usr/bin/env python3
"""
Simple example demonstrating the natural language news search feature.
Run this script to see the system in action.
"""

from mypythonlibrary.dataloader import CSVLoader
from mypythonlibrary import search_and_summarize

def example_1_basic_search():
    """Example 1: Basic fuzzy matching and record retrieval"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Fuzzy Company Matching")
    print("="*80)
    
    loader = CSVLoader()
    
    print("\nTesting fuzzy matching for company names:")
    typos = ["aple", "tesla", "microSoft", "NVDA", "amzn", "alpha"]
    
    for typo in typos:
        matched = loader.fuzzy_match_company(typo)
        print(f"  Input: '{typo:12}' -> Matched: '{matched}'")


def example_2_parse_prompt():
    """Example 2: Parse natural language prompt into filters"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Natural Language Prompt Parsing")
    print("="*80)
    
    loader = CSVLoader()
    
    test_prompts = [
        "Show me Apple news",
        "Find headlines about Tesla from July",
        "What's new with Microsoft?",
        "NVIDIA AI announcements",
    ]
    
    print("\nParsing natural language prompts:")
    for prompt in test_prompts:
        print(f"\n  Prompt: '{prompt}'")
        filters = loader.parse_natural_language_prompt(prompt)
        print(f"  Extracted filters: {filters}")


def example_3_search_records():
    """Example 3: Search and retrieve raw records"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Search for Matching Records")
    print("="*80)
    
    loader = CSVLoader()
    
    prompt = "Apple news from July 13"
    print(f"\nSearching for: '{prompt}'")
    
    records = loader.run_with_natural_language(prompt)
    
    print(f"Found {len(records)} matching records:\n")
    
    for i, record in enumerate(records[:3], 1):  # Show first 3
        print(f"Record {i}:")
        print(f"  Company:  {record.get('company')}")
        print(f"  Date:     {record.get('date')}")
        print(f"  Headline: {record.get('headline')[:60]}...")
        print(f"  Source:   {record.get('source')}")
        print()


def example_4_full_pipeline():
    """Example 4: Full pipeline - search and get AI summary"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Full Pipeline with AI Summarization")
    print("="*80)
    
    print("\nRunning full pipeline (NL prompt -> AI parsing -> filtering -> AI summary)")
    print("This will take 5-10 seconds...\n")
    
    prompt = "News about Apple and AI from July 2026"
    print(f"User prompt: '{prompt}'")
    
    try:
        result = search_and_summarize(prompt)
        print("\nAI-Generated Summary:")
        print("-"*80)
        print(result)
    except Exception as e:
        print(f"Note: API error (expected in demo): {e}")
        print("(Set OPENAI_API_KEY or DOUBLEWORD_API_KEY to enable summarization)")


def example_5_data_overview():
    """Example 5: Show data overview"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Data Overview")
    print("="*80)
    
    loader = CSVLoader()
    
    print(f"\nDataset Statistics:")
    print(f"  Total articles: {len(loader.df)}")
    print(f"  Columns: {list(loader.df.columns)}")
    print(f"\nCompanies in dataset:")
    for company in loader.df['company'].unique():
        count = len(loader.df[loader.df['company'] == company])
        print(f"  - {company}: {count} articles")
    
    print(f"\nDate range:")
    dates = loader.df['date'].unique()
    print(f"  From: {sorted(dates)[0]}")
    print(f"  To:   {sorted(dates)[-1]}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("NATURAL LANGUAGE NEWS SEARCH - EXAMPLES")
    print("="*80)
    
    # Run all examples
    example_1_basic_search()
    example_2_parse_prompt()
    example_3_search_records()
    example_5_data_overview()
    example_4_full_pipeline()
    
    print("\n" + "="*80)
    print("Examples complete! Check NATURAL_LANGUAGE_GUIDE.md for more details.")
    print("="*80 + "\n")
