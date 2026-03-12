from iis_parser import IISLogParser

def test_parser():
    print("Testing parser...")
    parser = IISLogParser('sample_iis.log')
    df = parser.parse()
    
    print(f"Loaded {len(df)} rows.")
    assert len(df) == 12, f"Expected 12 rows, got {len(df)}"
    
    print("Testing filtering by IP (10.0.0.1)...")
    filtered = parser.filter_data({'c-ip': '10.0.0.1'})
    print(f"Found {len(filtered)} rows.")
    assert len(filtered) == 6, f"Expected 6, got {len(filtered)}"
    
    print("Testing filtering by Status (200)...")
    filtered = parser.filter_data({'sc-status': '200'})
    print(f"Found {len(filtered)} rows.")
    assert len(filtered) == 8, f"Expected 8, got {len(filtered)}"
    
    print("Testing filtering by Device-Type (Mobile)...")
    filtered = parser.filter_data({'Device-Type': 'mobile'})
    print(f"Found {len(filtered)} rows.")
    assert len(filtered) == 2, f"Expected 2, got {len(filtered)}"
    
    stats = parser.get_summary_stats()
    print("Summary Stats:", stats)
    assert stats['Total Requests'] == 12
    
    print("All tests passed!")

if __name__ == '__main__':
    test_parser()
