import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier

class MLClassifier:
    """Классификация на основе машинного обучения"""
    
    def __init__(self, domain: Domain):
        self.domain = domain
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=2
        )
        
        # Ансамбль классификаторов
        self.classifier = VotingClassifier(
            estimators=[
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('nb', MultinomialNB()),
                ('svm', SVC(kernel='linear', probability=True, random_state=42))
            ],
            voting='soft'
        )
        
        self.is_trained = False
        self.label_encoder = {}
        
    def train(self, training_data: List[TrainingExample]):
        """Обучить классификатор"""
        
        # Подготовка данных
        texts = [example.text for example in training_data]
        labels = [example.label for example in training_data]
        
        # Кодирование меток
        unique_labels = list(set(labels))
        self.label_encoder = {label: idx for idx, label in enumerate(unique_labels)}
        encoded_labels = [self.label_encoder[label] for label in labels]
        
        # Векторизация текстов
        X = self.vectorizer.fit_transform(texts)
        y = np.array(encoded_labels)
        
        # Обучение
        self.classifier.fit(X, y)
        self.is_trained = True
        
        # Сохранение модели
        self.save_model()
        
    def classify(self, features: dict) -> dict:
        """Классифицировать на основе признаков"""
        
        if not self.is_trained:
            return {
                'document_type': 'Unknown',
                'category': 'Uncategorized',
                'confidence': 0.0,
                'error': 'Model not trained'
            }
        
        # Подготовка текста из признаков
        text = self.features_to_text(features)
        
        # Векторизация
        X = self.vectorizer.transform([text])
        
        # Предсказание
        prediction = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        
        # Декодирование метки
        reverse_encoder = {idx: label for label, idx in self.label_encoder.items()}
        predicted_label = reverse_encoder[prediction]
        confidence = probabilities[prediction]
        
        # Разбор метки (формат: "document_type|category|subcategory")
        parts = predicted_label.split('|')
        
        return {
            'document_type': parts[0] if len(parts) > 0 else 'Unknown',
            'category': parts[1] if len(parts) > 1 else 'Uncategorized',
            'subcategory': parts[2] if len(parts) > 2 else None,
            'confidence': float(confidence),
            'all_probabilities': {
                reverse_encoder[idx]: float(prob) 
                for idx, prob in enumerate(probabilities)
            }
        }
    
    def features_to_text(self, features: dict) -> str:
        """Преобразовать признаки в текст для классификации"""
        
        parts = []
        
        # Текстовые признаки
        text_features = features.get('text_features', {})
        if 'tokens' in text_features:
            parts.append(' '.join(text_features['tokens']))
        
        # Ключевые слова (с весом)
        if 'keywords' in text_features:
            keywords_repeated = ' '.join([kw] * 3 for kw in text_features['keywords'])
            parts.append(keywords_repeated)
        
        # Сущности
        entity_features = features.get('entity_features', {})
        for entity_type, entities in entity_features.items():
            if entities:
                parts.append(' '.join([f"{entity_type}_{e}" for e in entities]))
        
        return ' '.join(parts)
    
    def save_model(self):
        """Сохранить обученную модель"""
        import joblib
        
        model_path = f"{self.domain.path}/ml-models"
        os.makedirs(model_path, exist_ok=True)
        
        joblib.dump(self.classifier, f"{model_path}/classifier.pkl")
        joblib.dump(self.vectorizer, f"{model_path}/vectorizer.pkl")
        joblib.dump(self.label_encoder, f"{model_path}/label_encoder.pkl")
        
    def load_model(self):
        """Загрузить обученную модель"""
        import joblib
        
        model_path = f"{self.domain.path}/ml-models"
        
        if os.path.exists(f"{model_path}/classifier.pkl"):
            self.classifier = joblib.load(f"{model_path}/classifier.pkl")
            self.vectorizer = joblib.load(f"{model_path}/vectorizer.pkl")
            self.label_encoder = joblib.load(f"{model_path}/label_encoder.pkl")
            self.is_trained = True