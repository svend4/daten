# Collect test data
mkdir -p test_data/sgb_ix
# Download 50 SGB-IX documents (laws, decisions, applications)

# Run bulk import
python scripts/bulk_import.py test_data/sgb_ix/

# Verify results
python scripts/verify_import.py