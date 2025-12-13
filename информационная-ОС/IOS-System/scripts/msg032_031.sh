# Validate import
python scripts/validate_import.py

# Expected output:
# ================================================================================
# DATA VALIDATION REPORT
# ================================================================================
# 
# Total Documents: 3
# 
# Documents by Type:
#   Widerspruch: 1
#   Antrag: 1
#   Bescheid: 1
# 
# Total Entities: 15
# 
# Entities by Type:
#   Paragraph: 8
#   Gesetz: 5
#   Behörde: 2
# 
# ================================================================================
# QUALITY CHECKS
# ================================================================================
# ✓ Documents without classification: 0 (expected <= 0)
# ✓ Documents without entities: 0 (expected <= 0)
# ✓ Low confidence classifications (<0.7): 0 (expected <= 0.3)
# 
# ✓ All quality checks passed!