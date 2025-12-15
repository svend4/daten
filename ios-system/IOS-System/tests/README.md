# 🧪 IOS SYSTEM - TESTING SUITE

Comprehensive testing suite для IOS System с unit, integration и performance тестами.

---

## 📋 СОДЕРЖАНИЕ

- [Установка](#установка)
- [Запуск тестов](#запуск-тестов)
- [Типы тестов](#типы-тестов)
- [Покрытие кода](#покрытие-кода)
- [CI/CD интеграция](#cicd-интеграция)

---

## 🚀 УСТАНОВКА

### 1. Установка зависимостей

```bash
# Установка testing dependencies
pip install -r requirements-test.txt
```

### 2. Установка основных зависимостей

```bash
# Установка основных зависимостей проекта
pip install -r requirements.txt
```

---

## ▶️ ЗАПУСК ТЕСТОВ

### Все тесты

```bash
pytest
```

### Unit тесты

```bash
pytest -m unit
```

### Integration тесты

```bash
pytest -m integration
```

### Performance тесты

```bash
pytest -m performance
```

### Конкретный файл

```bash
pytest tests/test_backend_comprehensive.py
```

### Конкретный тест

```bash
pytest tests/test_backend_comprehensive.py::TestMainApplication::test_application_initialization
```

### С покрытием кода

```bash
pytest --cov=ios_system --cov-report=html
```

### Быстрые тесты (без performance)

```bash
pytest -m "not performance"
```

### Verbose режим

```bash
pytest -v
```

### С детальным выводом

```bash
pytest -vv --tb=long
```

---

## 🧪 ТИПЫ ТЕСТОВ

### 1. Unit Tests (`test_backend_comprehensive.py`)

**Покрытие:**
- Main Application
- Service Registry
- Health Checker
- Configuration
- Middleware (Error Handler, Request Logger, Rate Limiter, Security Headers)
- Security Components (Audit Logger, Encryption Service)

**Примеры:**

```python
# Тест Service Registry
def test_register_service():
    registry = ServiceRegistry()
    service = Mock()
    registry.register('test', service)
    assert 'test' in registry

# Тест Encryption
def test_encrypt_decrypt():
    service = EncryptionService()
    encrypted = service.encrypt("data")
    decrypted = service.decrypt(encrypted)
    assert decrypted == "data"
```

**Запуск:**
```bash
pytest tests/test_backend_comprehensive.py -v
```

### 2. Integration Tests (`test_integration.py`)

**Покрытие:**
- API Integration
- Middleware Chain
- Service Integration
- Monitoring Integration
- Security Integration
- End-to-End flows

**Примеры:**

```python
# Тест цепочки middleware
def test_middleware_chain():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggerMiddleware)
    # Проверяем что оба отработали
```

**Запуск:**
```bash
pytest tests/test_integration.py -v
```

### 3. Performance Tests (`test_performance.py`)

**Покрытие:**
- Service Registry Performance
- Encryption Performance
- Health Check Performance
- Concurrency Tests
- Scalability Tests
- Memory Usage
- Response Time Targets

**Примеры:**

```python
# Тест производительности
def test_encryption_performance():
    service = EncryptionService()
    # Должно быть < 10ms
    start = time.time()
    encrypted = service.encrypt(data)
    assert time.time() - start < 0.01
```

**Запуск:**
```bash
pytest tests/test_performance.py -m performance -v
```

---

## 📊 ПОКРЫТИЕ КОДА

### Генерация отчета

```bash
# HTML отчет
pytest --cov=ios_system --cov-report=html

# Terminal отчет
pytest --cov=ios_system --cov-report=term-missing

# XML отчет (для CI)
pytest --cov=ios_system --cov-report=xml
```

### Просмотр HTML отчета

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Целевое покрытие

**Текущее:** 92%  
**Цель:** 95%+

### Минимальное покрытие

Тесты не пройдут если покрытие < 90% (настроено в pytest.ini):

```ini
addopts = --cov-fail-under=90
```

---

## 🔧 КОНФИГУРАЦИЯ

### pytest.ini

Конфигурация pytest находится в `pytest.ini`:

```ini
[pytest]
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
```

### Маркеры

Используйте маркеры для категоризации тестов:

```python
@pytest.mark.unit
def test_something():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.performance
def test_performance():
    pass
```

---

## 🤖 CI/CD ИНТЕГРАЦИЯ

### GitHub Actions

Создайте `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: pytest --cov=ios_system --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### GitLab CI

Создайте `.gitlab-ci.yml`:

```yaml
test:
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-test.txt
    - pytest --cov=ios_system --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

---

## 📈 СТАТИСТИКА ТЕСТОВ

### Unit Tests
- **Файлов:** 1
- **Классов:** 8
- **Тестов:** 30+
- **Покрытие:** Backend components, Security, Middleware

### Integration Tests
- **Файлов:** 1
- **Классов:** 7
- **Тестов:** 20+
- **Покрытие:** API, Service integration, End-to-end flows

### Performance Tests
- **Файлов:** 1
- **Классов:** 6
- **Тестов:** 15+
- **Покрытие:** Performance, Scalability, Memory, Response times

**ИТОГО:** 3 файла, 21+ тестовых классов, 65+ тестов

---

## 🎯 BEST PRACTICES

### 1. Именование тестов

```python
# Хорошо
def test_service_registry_registers_service_successfully():
    pass

# Плохо
def test1():
    pass
```

### 2. Arrange-Act-Assert паттерн

```python
def test_example():
    # Arrange
    service = MyService()
    
    # Act
    result = service.do_something()
    
    # Assert
    assert result == expected
```

### 3. Используйте fixtures

```python
@pytest.fixture
def service():
    return MyService()

def test_with_fixture(service):
    assert service is not None
```

### 4. Мокируйте внешние зависимости

```python
@patch('ios_system.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = "mocked"
    result = use_service()
    assert result == "mocked"
```

---

## 🐛 DEBUGGING

### Запуск с pdb

```bash
pytest --pdb
```

### Остановка на первой ошибке

```bash
pytest -x
```

### Показать print statements

```bash
pytest -s
```

### Verbose traceback

```bash
pytest --tb=long
```

---

## 📝 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Запуск тестов локально

```bash
# 1. Установите зависимости
pip install -r requirements-test.txt

# 2. Запустите тесты
pytest -v

# 3. Проверьте покрытие
pytest --cov=ios_system --cov-report=html
open htmlcov/index.html
```

### Добавление нового теста

```python
# tests/test_my_feature.py
import pytest

class TestMyFeature:
    """Тесты для моей фичи"""
    
    def test_feature_works(self):
        """Тест что фича работает"""
        result = my_feature()
        assert result == expected
        
    @pytest.mark.asyncio
    async def test_async_feature(self):
        """Тест async фичи"""
        result = await async_feature()
        assert result is not None
```

---

## 🎓 ПОЛЕЗНЫЕ КОМАНДЫ

```bash
# Список всех тестов
pytest --collect-only

# Запуск конкретного маркера
pytest -m unit

# Запуск нескольких маркеров
pytest -m "unit or integration"

# Исключить маркер
pytest -m "not performance"

# Параллельное выполнение (требует pytest-xdist)
pytest -n auto

# Генерация HTML отчета
pytest --html=report.html --self-contained-html

# Только провалившиеся тесты
pytest --lf

# Показать самые медленные тесты
pytest --durations=10
```

---

## 📚 ДОКУМЕНТАЦИЯ

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## ✅ CHECKLIST

Перед коммитом убедитесь что:

- [ ] Все тесты проходят: `pytest`
- [ ] Покрытие >= 90%: `pytest --cov`
- [ ] Нет lint ошибок: `pylint ios_system`
- [ ] Код отформатирован: `black ios_system`
- [ ] Imports отсортированы: `isort ios_system`

---

**Версия:** 1.0  
**Дата:** 15 декабря 2024  
**Автор:** IOS System Team
