# Setup test database
createdb ios_test
psql ios_test -c "CREATE USER ios_user WITH PASSWORD 'ios_password';"
psql ios_test -c "GRANT ALL PRIVILEGES ON DATABASE ios_test TO ios_user;"

# Run tests
pytest tests/integration/test_document_pipeline.py -v -s

# Expected output:
# test_complete_document_pipeline PASSED
# test_entity_extraction PASSED
# test_classification_accuracy PASSED