# 📋 راهنمای کامل Unit Tests

## 📁 ساختار فایل‌ها

```
trading_ai_system/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Fixtures و Configuration
│   ├── test_core.py                   # Test Core Module
│   ├── test_data.py                   # Test Data Module
│   ├── test_features.py               # Test Features Module
│   ├── test_models.py                 # Test Models Module
│   ├── test_strategy.py               # Test Strategy Module
│   ├── test_risk.py                   # Test Risk Module
│   ├── test_integration.py            # Integration Tests
│   └── test_performance.py            # Performance Tests
│
├── pytest.ini                         # Pytest Configuration
├── setup.py / pyproject.toml
└── README.md
```

---

## 🚀 نصب Pytest و Dependencies

### 1. نصب با pip:

```bash
# نصب Pytest و Extensions
pip install pytest==7.4.0
pip install pytest-cov==4.1.0
pip install pytest-timeout==2.1.0
pip install pytest-xdist==3.3.0
pip install pytest-mock==3.11.1
pip install pytest-asyncio==0.21.0

# یا استفاده از requirements-dev.txt:
pip install -r requirements-dev.txt
```

### 2. فایل `requirements-dev.txt`:

```txt
# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-timeout==2.1.0
pytest-xdist==3.3.0
pytest-mock==3.11.1
pytest-asyncio==0.21.0

# Code Quality
black==23.7.0
flake8==6.0.0
isort==5.12.0
mypy==1.4.0

# Documentation
pytest-html==3.2.0
```

### 3. نصب:

```bash
pip install -r requirements-dev.txt
```

---

## 🏃 نحوه اجرای تست‌ها

### 1️⃣ اجرای تمام تست‌ها:

```bash
pytest
```

**خروجی:**
```
tests/test_core.py::TestCoreModuleConfig::test_config_creation_with_defaults PASSED
tests/test_data.py::TestDataFetcher::test_fetch_returns_valid_ohlcv PASSED
...
======================== 150 passed in 25.32s ========================
```

### 2️⃣ اجرای تست‌های خاص:

```bash
# تست‌های یک فایل
pytest tests/test_data.py

# تست‌های یک کلاس
pytest tests/test_data.py::TestDataFetcher

# تست خاص
pytest tests/test_data.py::TestDataFetcher::test_fetch_returns_valid_ohlcv
```

### 3️⃣ اجرای تست‌ها با Coverage:

```bash
# Coverage Report
pytest --cov=trading_ai_system --cov-report=html

# Output: htmlcov/index.html
```

### 4️⃣ اجرای تست‌های سریع (بدون slow tests):

```bash
pytest -m "not slow"
```

### 5️⃣ اجرای تست‌های Integration:

```bash
pytest -m integration
```

### 6️⃣ اجرای تست‌های Parallel:

```bash
# نیاز: pip install pytest-xdist
pytest -n auto
```

### 7️⃣ اجرای تست‌ها با Verbose:

```bash
pytest -vv
```

### 8️⃣ اجرای تست‌ها با Debug:

```bash
# متوقف بر اولین failure
pytest -x

# متوقف بر 3 failure
pytest --maxfail=3

# Debug Mode (PDB)
pytest --pdb
```

### 9️⃣ اجرای تست‌های خاص با Pattern:

```bash
# تمام تست‌های شامل "data"
pytest -k "data"

# تمام تست‌های شامل "data" یا "feature"
pytest -k "data or feature"

# تمام تست‌های شامل "data" اما نه "cache"
pytest -k "data and not cache"
```

### 🔟 اجرای تست‌ها با Output نشان‌دهنده محلی متغیرها:

```bash
pytest -l
```

---

## 📊 Markers (نشانگر‌ها)

### تعریف Markers:

```python
@pytest.mark.slow
def test_large_dataset_processing():
    """تست بزرگ."""
    pass

@pytest.mark.integration
def test_data_to_strategy_pipeline():
    """تست یکپارچگی."""
    pass

@pytest.mark.performance
def test_model_prediction_speed():
    """تست Performance."""
    pass

@pytest.mark.security
def test_api_key_validation():
    """تست Security."""
    pass
```

### اجرای با Markers:

```bash
# تمام Slow Tests
pytest -m slow

# تمام Integration Tests
pytest -m integration

# بدون Slow Tests
pytest -m "not slow"

# Slow یا Integration
pytest -m "slow or integration"
```

---

## 📈 Coverage Analysis

### 1. تولید Coverage Report:

```bash
pytest --cov=trading_ai_system --cov-report=html --cov-report=term
```

### 2. خواندن Report:

```
htmlcov/index.html
```

### 3. Coverage Targets:

```
Target: 85%+
- Core Module: 95%+
- Data Module: 90%+
- Features Module: 85%+
- Models Module: 80%+
- Strategy Module: 80%+
- Risk Module: 85%+
```

---

## 🔧 Writing Your Own Tests

### Template سادگی:

```python
# tests/test_my_module.py

import pytest
from trading_ai_system.my_module import MyClass


class TestMyClass:
    """تست‌های MyClass."""
    
    def test_initialization(self):
        """تست initialization."""
        obj = MyClass(param='value')
        assert obj.param == 'value'
    
    def test_method_returns_expected_value(self):
        """تست method."""
        obj = MyClass()
        result = obj.my_method(10)
        assert result == 20
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """تست عملیات کند."""
        pass
    
    @pytest.mark.integration
    def test_integration(self, sample_data):
        """تست یکپارچگی."""
        pass
```

### استفاده از Fixtures:

```python
@pytest.fixture
def sample_data():
    """تولید داده نمونه."""
    return {'key': 'value'}

def test_with_fixture(sample_data):
    """تست با fixture."""
    assert sample_data['key'] == 'value'
```

### Testing Exceptions:

```python
def test_raises_exception():
    """تست Exception."""
    from trading_ai_system.core import ConfigError
    
    with pytest.raises(ConfigError):
        raise ConfigError("Invalid config")
```

### Mocking:

```python
from unittest.mock import Mock, patch

@patch('trading_ai_system.data.fetch_data')
def test_with_mock(mock_fetch):
    """تست با Mock."""
    mock_fetch.return_value = {'price': 1.1}
    
    result = my_function()
    
    assert result == expected
    mock_fetch.assert_called_once()
```

---

## 📋 Checklist قبل از Commit

- [ ] تمام تست‌ها PASS می‌شوند
- [ ] Coverage > 85%
- [ ] کد به Black Format متطابق است
- [ ] Linting Errors وجود ندارند
- [ ] New Tests برای New Code نوشته شده است

---

## 🐛 Troubleshooting

### ImportError: No module named

```bash
# اطمینان حاصل کنید که در ROOT directory هستید
cd trading_ai_system_refactored

# نصب در Development Mode
pip install -e .
```

### Fixture not found

```bash
# اطمینان حاصل کنید conftest.py در tests/ است
# یا در parent directory
```

### Tests too slow

```bash
# اجرای parallel
pytest -n auto

# یا skip slow tests
pytest -m "not slow"
```

### Memory Error

```bash
# اجرای تست‌های individual
pytest tests/test_data.py::TestDataFetcher::test_fetch
```

---

## 📚 Best Practices

### 1. Naming Convention:

```python
# ✅ خوب
def test_data_fetcher_returns_valid_ohlcv():
    pass

# ❌ بد
def test_fetcher():
    pass
```

### 2. Test Isolation:

```python
# هر تست باید مستقل باشد
# از fixtures و cleanup استفاده کنید
```

### 3. Single Responsibility:

```python
# هر تست تنها یک چیز را تست کند
def test_model_training():
    model = LGBModel()
    model.train(X, y)
    assert model.is_trained
```

### 4. Meaningful Assertions:

```python
# ✅ خوب
assert model.accuracy > 0.85, "Model accuracy should be > 85%"

# ❌ بد
assert model.accuracy
```

### 5. Use Fixtures:

```python
# ✅ خوب
def test_with_fixture(sample_ohlcv):
    features = engineer.calculate(sample_ohlcv)

# ❌ بد
def test_without_fixture():
    ohlcv = fetch_data()
    features = engineer.calculate(ohlcv)
```

---

## 🎓 مثال‌های عملی

### مثال 1: تست Data Module

```python
# tests/test_data.py

class TestDataFetcher:
    def test_fetch_returns_dataframe(self, mock_broker):
        """تست بازیابی داده."""
        fetcher = DataFetcher(broker=mock_broker)
        data = fetcher.fetch("EURUSD", "2023-01-01", "2023-01-31")
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert all(col in data.columns for col in ['open', 'high', 'low', 'close'])
```

### مثال 2: تست Features Module

```python
# tests/test_features.py

class TestFeatureEngineer:
    def test_rsi_calculation(self, sample_ohlcv):
        """تست محاسبه RSI."""
        engineer = FeatureEngineer()
        features = engineer.calculate(sample_ohlcv)
        
        assert 'rsi' in features.columns
        assert (0 <= features['rsi']).all()
        assert (features['rsi'] <= 100).all()
```

### مثال 3: تست Risk Module

```python
# tests/test_risk.py

class TestPositionSizing:
    def test_kelly_sizing(self):
        """تست Kelly Criterion."""
        sizer = PositionSizer(method='kelly')
        
        size = sizer.calculate(
            capital=10000,
            win_rate=0.55,
            avg_win=100,
            avg_loss=80
        )
        
        assert 0 < size <= 0.25
```

---

## 🔄 CI/CD Integration

### GitHub Actions:

```yaml
# .github/workflows/tests.yml

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
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=trading_ai_system
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 📞 Support & Resources

- Pytest Docs: https://docs.pytest.org/
- Coverage Docs: https://coverage.readthedocs.io/
- Mock Docs: https://docs.python.org/3/library/unittest.mock.html

---

**نسخه**: 0.79.0  
**تاریخ**: تیر 1405  
**نویسنده**: Hamed
