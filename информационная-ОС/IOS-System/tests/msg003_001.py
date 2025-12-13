class TrainingModule:
    """Модуль для обучения и улучшения классификатора"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.ml_classifier = MLClassifier(domain)
        self.training_data = []
        
    def collect_training_data(self) -> List[TrainingExample]:
        """Собрать обучающие данные"""
        
        training_examples = []
        
        # 1. Из уже классифицированных документов
        classified_docs = self.domain.get_classified_documents()
        for doc in classified_docs:
            example = TrainingExample(
                text=doc.get_text(),
                label=f"{doc.document_type}|{doc.category}|{doc.subcategory or ''}",
                source='manual_classification'
            )
            training_examples.append(example)
        
        # 2. Из шаблонов
        templates = self.domain.get_templates()
        for template in templates:
            example = TrainingExample(
                text=template.get_text(),
                label=f"{template.document_type}|{template.category}|",
                source='template'
            )
            training_examples.append(example)
        
        # 3. Синтетические данные (аугментация)
        augmented = self.augment_training_data(training_examples)
        training_examples.extend(augmented)
        
        return training_examples
    
    def augment_training_data(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Аугментация обучающих данных"""
        
        augmented = []
        
        for example in examples:
            # Замена синонимов
            synonyms = self.get_synonyms(example.text)
            for synonym_text in synonyms:
                augmented.append(TrainingExample(
                    text=synonym_text,
                    label=example.label,
                    source='augmentation_synonym'
                ))
            
            # Изменение порядка предложений
            shuffled = self.shuffle_sentences(example.text)
            augmented.append(TrainingExample(
                text=shuffled,
                label=example.label,
                source='augmentation_shuffle'
            ))
        
        return augmented
    
    def train_classifier(self):
        """Обучить классификатор"""
        
        # Собрать данные
        training_data = self.collect_training_data()
        
        # Разделить на train/validation
        from sklearn.model_selection import train_test_split
        train_data, val_data = train_test_split(training_data, test_size=0.2, random_state=42)
        
        # Обучить
        self.ml_classifier.train(train_data)
        
        # Оценить качество
        metrics = self.evaluate_classifier(val_data)
        
        return metrics
    
    def evaluate_classifier(self, validation_data: List[TrainingExample]) -> dict:
        """Оценить качество классификатора"""
        
        predictions = []
        true_labels = []
        
        for example in validation_data:
            features = self.extract_features_from_text(example.text)
            result = self.ml_classifier.classify(features)
            
            predicted_label = f"{result['document_type']}|{result['category']}|{result.get('subcategory', '')}"
            predictions.append(predicted_label)
            true_labels.append(example.label)
        
        # Метрики
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
        
        accuracy = accuracy_score(true_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(true_labels, predictions, average='weighted')
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'classification_report': classification_report(true_labels, predictions)
        }
    
    def active_learning_loop(self):
        """Активное обучение - классификатор запрашивает примеры для обучения"""
        
        # Найти неклассифицированные документы
        unclassified = self.domain.get_unclassified_documents()
        
        for doc in unclassified:
            # Попытка классификации
            features = self.extract_features_from_text(doc.get_text())
            result = self.ml_classifier.classify(features)
            
            # Если уверенность низкая - запросить помощь пользователя
            if result['confidence'] < 0.7:
                user_label = self.request_user_classification(doc)
                
                if user_label:
                    # Добавить в обучающую выборку
                    example = TrainingExample(
                        text=doc.get_text(),
                        label=user_label,
                        source='active_learning'
                    )
                    self.training_data.append(example)
                    
                    # Переобучить
                    if len(self.training_data) >= 10:
                        self.train_classifier()
                        self.training_data = []