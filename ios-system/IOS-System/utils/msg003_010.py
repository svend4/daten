class RuleBasedClassifier:
    """Классификация на основе экспертных правил"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.rules = self.load_rules()
        
    def load_rules(self) -> List[ClassificationRule]:
        """Загрузить правила классификации"""
        
        rules = []
        
        # Правило 1: Возражение (Widerspruch)
        rules.append(ClassificationRule(
            name="Widerspruch Detection",
            conditions=[
                KeywordCondition(['widerspruch', 'widerspreche'], min_count=1),
                KeywordCondition(['bescheid'], min_count=1),
                EntityCondition('behörden', min_count=1),
                EntityCondition('datum', min_count=1)
            ],
            result={
                'document_type': 'Widerspruch',
                'category': 'Rechtsmittel',
                'confidence': 0.9
            }
        ))
        
        # Правило 2: Заявление (Antrag)
        rules.append(ClassificationRule(
            name="Antrag Detection",
            conditions=[
                KeywordCondition(['antrag', 'beantrage', 'hiermit beantrage'], min_count=1),
                KeywordCondition(['persönliches budget', 'leistung', 'hilfe'], min_count=1),
                NOT(KeywordCondition(['widerspruch']))
            ],
            result={
                'document_type': 'Antrag',
                'category': 'Anträge',
                'confidence': 0.85
            }
        ))
        
        # Правило 3: Решение ведомства (Bescheid)
        rules.append(ClassificationRule(
            name="Bescheid Detection",
            conditions=[
                KeywordCondition(['bescheid', 'bewilligungsbescheid', 'ablehnungsbescheid'], min_count=1),
                StructureCondition('has_signature', True),
                StructureCondition('has_reference_number', True),
                EntityCondition('behörden', min_count=1)
            ],
            result={
                'document_type': 'Bescheid',
                'category': 'Bescheide',
                'confidence': 0.95
            }
        ))
        
        # Правило 4: Судебное решение (Urteil)
        rules.append(ClassificationRule(
            name="Urteil Detection",
            conditions=[
                KeywordCondition(['urteil', 'im namen des volkes', 'beschluss'], min_count=1),
                KeywordCondition(['sozialgericht', 'landessozialgericht'], min_count=1),
                EntityCondition('paragraphen', min_count=3)
            ],
            result={
                'document_type': 'Urteil',
                'category': 'Gerichtsverfahren',
                'subcategory': 'Urteile',
                'confidence': 0.98
            }
        ))
        
        # Правило 5: Закон (Gesetz)
        rules.append(ClassificationRule(
            name="Gesetz Detection",
            conditions=[
                EntityCondition('gesetze', min_count=1),
                EntityCondition('paragraphen', min_count=10),
                KeywordCondition(['sozialgesetzbuch', 'sgb'], min_count=1),
                StructureCondition('num_sections', min_value=5)
            ],
            result={
                'document_type': 'Gesetz',
                'category': 'Gesetze',
                'confidence': 0.95
            }
        ))
        
        return rules
    
    def classify(self, features: dict) -> dict:
        """Применить правила для классификации"""
        
        matches = []
        
        for rule in self.rules:
            if rule.evaluate(features):
                matches.append({
                    'rule_name': rule.name,
                    **rule.result
                })
        
        if not matches:
            return {
                'document_type': 'Unknown',
                'category': 'Uncategorized',
                'confidence': 0.0
            }
        
        # Вернуть наиболее уверенное совпадение
        best_match = max(matches, key=lambda x: x['confidence'])
        return best_match


class ClassificationRule:
    """Правило классификации"""
    
    def __init__(self, name: str, conditions: List, result: dict):
        self.name = name
        self.conditions = conditions
        self.result = result
        
    def evaluate(self, features: dict) -> bool:
        """Проверить, выполняются ли все условия"""
        return all(condition.check(features) for condition in self.conditions)


class KeywordCondition:
    """Условие на наличие ключевых слов"""
    
    def __init__(self, keywords: List[str], min_count: int = 1):
        self.keywords = [k.lower() for k in keywords]
        self.min_count = min_count
        
    def check(self, features: dict) -> bool:
        text_features = features.get('text_features', {})
        tokens = [t.lower() for t in text_features.get('tokens', [])]
        
        count = sum(1 for keyword in self.keywords if keyword in ' '.join(tokens))
        return count >= self.min_count


class EntityCondition:
    """Условие на наличие сущностей"""
    
    def __init__(self, entity_type: str, min_count: int = 1):
        self.entity_type = entity_type
        self.min_count = min_count
        
    def check(self, features: dict) -> bool:
        entity_features = features.get('entity_features', {})
        entities = entity_features.get(self.entity_type, [])
        return len(entities) >= self.min_count


class StructureCondition:
    """Условие на структурные признаки"""
    
    def __init__(self, feature_name: str, expected_value=None, min_value=None):
        self.feature_name = feature_name
        self.expected_value = expected_value
        self.min_value = min_value
        
    def check(self, features: dict) -> bool:
        structure_features = features.get('structure_features', {})
        value = structure_features.get(self.feature_name)
        
        if self.expected_value is not None:
            return value == self.expected_value
        
        if self.min_value is not None:
            return value >= self.min_value
        
        return False


class NOT:
    """Отрицание условия"""
    
    def __init__(self, condition):
        self.condition = condition
        
    def check(self, features: dict) -> bool:
        return not self.condition.check(features)