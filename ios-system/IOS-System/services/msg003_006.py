class ClassificationEngine:
    """Главный движок классификации документов"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.rule_based_classifier = RuleBasedClassifier(domain)
        self.ml_classifier = MLClassifier(domain)
        self.feature_extractor = FeatureExtractor(domain.config)
        self.confidence_scorer = ConfidenceScorer()
        
    def classify(self, document: Document) -> Classification:
        """Классифицировать документ"""
        
        # 1. Извлечь признаки
        features = self.feature_extractor.extract_features(document)
        
        # 2. Классификация на основе правил
        rule_result = self.rule_based_classifier.classify(features)
        
        # 3. Классификация на основе ML
        ml_result = self.ml_classifier.classify(features)
        
        # 4. Объединить результаты
        combined_result = self.combine_results(rule_result, ml_result)
        
        # 5. Оценить уверенность
        confidence = self.confidence_scorer.score(combined_result, features)
        
        # 6. Создать финальную классификацию
        classification = Classification(
            document_type=combined_result['document_type'],
            category=combined_result['category'],
            subcategory=combined_result.get('subcategory'),
            tags=combined_result.get('tags', []),
            confidence=confidence,
            metadata=combined_result.get('metadata', {})
        )
        
        return classification
    
    def combine_results(self, rule_result: dict, ml_result: dict) -> dict:
        """Объединить результаты классификации"""
        
        # Если оба метода согласны - отлично
        if rule_result['document_type'] == ml_result['document_type']:
            return {
                **rule_result,
                'agreement': True,
                'confidence_boost': 0.2
            }
        
        # Если не согласны - приоритет правилам при высокой уверенности
        if rule_result['confidence'] > 0.8:
            return {
                **rule_result,
                'agreement': False,
                'ml_alternative': ml_result
            }
        
        # Иначе - ML
        return {
            **ml_result,
            'agreement': False,
            'rule_alternative': rule_result
        }