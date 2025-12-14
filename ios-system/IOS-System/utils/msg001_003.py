def classify_document(doc):
    # Извлечь признаки
    features = extract_features(doc)
    
    # Определить домен (SGB, медицина, техника)
    domain = predict_domain(features)
    
    # Определить тип (закон, письмо, отчёт)
    doc_type = predict_type(features)
    
    # Определить тематические теги
    tags = extract_tags(doc, domain)
    
    # Найти связанные документы
    related = find_related(doc, domain)
    
    return {
        'domain': domain,
        'type': doc_type,
        'tags': tags,
        'related': related,
        'suggested_path': f"/{domain}/{doc_type}/{tags[0]}"
    }