# Import test data
python scripts/bulk_import.py test_data/sgb_ix/

# Expected output:
# Processing: widerspruch_001.txt
#   ✓ Widerspruch (confidence: 0.90)
#   Entities: 5
# Processing: antrag_001.txt
#   ✓ Antrag (confidence: 0.85)
#   Entities: 4
# Processing: bescheid_001.txt
#   ✓ Bescheid (confidence: 0.95)
#   Entities: 6
# 
# ================================================================================
# IMPORT SUMMARY
# ================================================================================
# Total documents: 3
# Successfully imported: 3
# Failed: 0