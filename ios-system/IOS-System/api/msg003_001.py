class FeatureExtractor:
    """Извлечение признаков из документов для классификации"""
    
    def __init__(self, domain_config: dict):
        self.domain_config = domain_config
        self.stopwords = self.load_stopwords()
        self.entity_patterns = self.load_entity_patterns()
        
    def extract_features(self, document: Document) -> dict:
        """Извлечь все признаки документа"""
        
        text = document.get_text()
        
        features = {
            # Текстовые признаки
            'text_features': self.extract_text_features(text),
            
            # Структурные признаки
            'structure_features': self.extract_structure_features(document),
            
            # Сущности
            'entity_features': self.extract_entity_features(text),
            
            # Метаданные
            'metadata_features': self.extract_metadata_features(document),
            
            # Статистические признаки
            'statistical_features': self.extract_statistical_features(text)
        }
        
        return features
    
    def extract_text_features(self, text: str) -> dict:
        """Извлечь текстовые признаки"""
        
        # Токенизация
        tokens = self.tokenize(text)
        
        # Удаление стоп-слов
        filtered_tokens = [t for t in tokens if t.lower() not in self.stopwords]
        
        # N-граммы
        bigrams = self.get_ngrams(filtered_tokens, 2)
        trigrams = self.get_ngrams(filtered_tokens, 3)
        
        # TF-IDF
        tf_idf = self.calculate_tfidf(filtered_tokens)
        
        return {
            'tokens': filtered_tokens,
            'unique_tokens': list(set(filtered_tokens)),
            'bigrams': bigrams,
            'trigrams': trigrams,
            'tf_idf_top_10': sorted(tf_idf.items(), key=lambda x: x[1], reverse=True)[:10],
            'keywords': self.extract_keywords(text)
        }
    
    def extract_structure_features(self, document: Document) -> dict:
        """Извлечь структурные признаки"""
        
        return {
            'has_header': self.detect_header(document),
            'has_footer': self.detect_footer(document),
            'num_sections': self.count_sections(document),
            'num_paragraphs': self.count_paragraphs(document),
            'num_pages': document.page_count,
            'has_signature': self.detect_signature(document),
            'has_date': self.detect_date(document),
            'has_reference_number': self.detect_reference_number(document),
            'document_layout': self.analyze_layout(document)
        }
    
    def extract_entity_features(self, text: str) -> dict:
        """Извлечь признаки на основе сущностей"""
        
        entities = {
            'gesetze': [],      # Законы (SGB-IX, SGB-XII)
            'paragraphen': [],  # Параграфы (§29, §30)
            'behörden': [],     # Органы власти
            'personen': [],     # Персоны
            'datum': [],        # Даты
            'geld': []          # Суммы денег
        }
        
        # Поиск законов
        gesetz_pattern = r'SGB[- ]?([IVX]+)'
        entities['gesetze'] = re.findall(gesetz_pattern, text)
        
        # Поиск параграфов
        paragraph_pattern = r'§\s*(\d+[a-z]?)'
        entities['paragraphen'] = re.findall(paragraph_pattern, text)
        
        # Поиск дат
        date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}'
        entities['datum'] = re.findall(date_pattern, text)
        
        # Поиск сумм
        money_pattern = r'(\d+(?:[.,]\d+)?)\s*(?:€|EUR|Euro)'
        entities['geld'] = re.findall(money_pattern, text)
        
        # Поиск органов власти
        behörden_keywords = ['Sozialamt', 'Landkreis', 'Bezirk', 'Sozialgericht', 'Landessozialgericht']
        for keyword in behörden_keywords:
            if keyword.lower() in text.lower():
                entities['behörden'].append(keyword)
        
        return entities
    
    def extract_metadata_features(self, document: Document) -> dict:
        """Извлечь признаки из метаданных"""
        
        return {
            'file_format': document.format,
            'file_size': document.size,
            'creation_date': document.creation_date,
            'modification_date': document.modification_date,
            'author': document.author if hasattr(document, 'author') else None,
            'title': document.title if hasattr(document, 'title') else None
        }
    
    def extract_statistical_features(self, text: str) -> dict:
        """Извлечь статистические признаки"""
        
        words = text.split()
        sentences = self.split_sentences(text)
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'unique_word_ratio': len(set(words)) / len(words) if words else 0,
            'punctuation_count': sum(1 for c in text if c in '.,;:!?'),
            'capital_letter_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0
        }