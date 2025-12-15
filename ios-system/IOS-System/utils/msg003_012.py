class ConfidenceScorer:
    """Оценка уверенности в классификации"""
    
    def score(self, classification_result: dict, features: dict) -> float:
        """Вычислить итоговую уверенность"""
        
        scores = []
        
        # 1. Базовая уверенность из классификатора
        base_confidence = classification_result.get('confidence', 0.5)
        scores.append(('base', base_confidence, 0.4))
        
        # 2. Согласованность методов
        if classification_result.get('agreement', False):
            scores.append(('agreement', 1.0, 0.2))
        else:
            scores.append(('agreement', 0.5, 0.2))
        
        # 3. Наличие ключевых признаков
        key_features_score = self.evaluate_key_features(classification_result, features)
        scores.append(('key_features', key_features_score, 0.2))
        
        # 4. Полнота документа
        completeness_score = self.evaluate_completeness(features)
        scores.append(('completeness', completeness_score, 0.1))
        
        # 5. Консистентность с другими документами
        consistency_score = self.evaluate_consistency(classification_result, features)
        scores.append(('consistency', consistency_score, 0.1))
        
        # Взвешенная сумма
        total_score = sum(score * weight for name, score, weight in scores)
        
        return min(1.0, max(0.0, total_score))
    
    def evaluate_key_features(self, classification_result: dict, features: dict) -> float:
        """Оценить наличие ключевых признаков для типа документа"""
        
        doc_type = classification_result.get('document_type')
        
        if doc_type == 'Widerspruch':
            required_features = ['widerspruch', 'bescheid', 'behörden']
        elif doc_type == 'Antrag':
            required_features = ['antrag', 'persönliches budget']
        elif doc_type == 'Bescheid':
            required_features = ['bescheid', 'signature', 'reference_number']
        else:
            return 0.5
        
        # Проверить наличие
        present_count = 0
        for feature in required_features:
            if self.feature_present(feature, features):
                present_count += 1
        
        return present_count / len(required_features)
    
    def feature_present(self, feature_name: str, features: dict) -> bool:
        """Проверить наличие признака"""
        
        # Проверка в текстовых признаках
        text_features = features.get('text_features', {})
        tokens = [t.lower() for t in text_features.get('tokens', [])]
        if feature_name.lower() in ' '.join(tokens):
            return True
        
        # Проверка в структурных признаках
        structure_features = features.get('structure_features', {})
        if feature_name in structure_features and structure_features[feature_name]:
            return True
        
        return False