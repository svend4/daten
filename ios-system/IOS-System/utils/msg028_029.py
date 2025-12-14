# ⚠️ ПОТЕНЦИАЛЬНАЯ ПРОБЛЕМА
for entity in entities:
    related = kg.get_related_entities(entity.id)
    # Может быть много запросов к графу
    
# ✅ РЕШЕНИЕ: Batch loading
entities_with_related = kg.get_entities_with_relations(entity_ids)