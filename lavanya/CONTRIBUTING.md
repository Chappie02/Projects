# Contributing to Speaker Isolation System

Thank you for your interest in contributing to the Real-Time Speaker Isolation & Identification system! We welcome contributions from the community.

## 🤝 How to Contribute

### Reporting Issues

1. **Check existing issues** first to avoid duplicates
2. **Use the issue template** with all required information
3. **Provide detailed reproduction steps**
4. **Include system information** (OS, Python version, etc.)
5. **Attach relevant logs** and error messages

### Suggesting Features

1. **Check the roadmap** to see if it's already planned
2. **Open a feature request** with detailed description
3. **Explain the use case** and expected behavior
4. **Consider implementation complexity**

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- Git
- Docker (optional, for containerized development)

### Local Development

```bash
# Clone your fork
git clone https://github.com/yourusername/speaker-isolation-system.git
cd speaker-isolation-system

# Add upstream remote
git remote add upstream https://github.com/originalowner/speaker-isolation-system.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

### Docker Development

```bash
# Build development image
docker-compose -f docker-compose.dev.yml up --build

# Run tests in container
docker-compose exec speaker-isolation pytest
```

## 📝 Coding Standards

### Python Style

- **PEP 8 compliance** with 88-character line limit
- **Type hints** for all function parameters and return values
- **Docstrings** following Google style
- **Meaningful variable names** and comments

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Check style with Flake8
flake8 src/ tests/

# Type checking with MyPy
mypy src/
```

### Example Code Style

```python
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExampleClass:
    """Example class demonstrating coding standards.
    
    This class shows the expected style for:
    - Type hints
    - Docstrings
    - Error handling
    - Logging
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        """Initialize the example class.
        
        Args:
            param1: Description of first parameter
            param2: Optional second parameter with default value
            
        Raises:
            ValueError: If param1 is empty
        """
        if not param1:
            raise ValueError("param1 cannot be empty")
        
        self.param1 = param1
        self.param2 = param2 or 0
        
        logger.info(f"Initialized ExampleClass with param1={param1}")
    
    def process_data(self, data: List[Dict[str, Any]]) -> List[str]:
        """Process input data and return results.
        
        Args:
            data: List of dictionaries containing data to process
            
        Returns:
            List of processed results as strings
            
        Raises:
            ProcessingError: If data processing fails
        """
        try:
            results = []
            for item in data:
                # Process each item
                result = self._process_item(item)
                results.append(result)
            
            logger.debug(f"Processed {len(data)} items")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process data: {e}")
            raise ProcessingError(f"Data processing failed: {e}") from e
    
    def _process_item(self, item: Dict[str, Any]) -> str:
        """Process a single item (private method).
        
        Args:
            item: Dictionary containing item data
            
        Returns:
            Processed item as string
        """
        return str(item.get("value", "default"))
```

## 🧪 Testing

### Writing Tests

- **Test coverage** should be >80% for new code
- **Unit tests** for individual functions and methods
- **Integration tests** for component interactions
- **Mock external dependencies** (APIs, file system, etc.)

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from src.example_module import ExampleClass


class TestExampleClass:
    """Test suite for ExampleClass."""
    
    def test_initialization_success(self):
        """Test successful initialization."""
        obj = ExampleClass("test_param")
        assert obj.param1 == "test_param"
        assert obj.param2 == 0
    
    def test_initialization_with_optional_param(self):
        """Test initialization with optional parameter."""
        obj = ExampleClass("test", 42)
        assert obj.param1 == "test"
        assert obj.param2 == 42
    
    def test_initialization_empty_param_raises_error(self):
        """Test that empty param1 raises ValueError."""
        with pytest.raises(ValueError, match="param1 cannot be empty"):
            ExampleClass("")
    
    @patch('src.example_module.logger')
    def test_process_data_success(self, mock_logger):
        """Test successful data processing."""
        obj = ExampleClass("test")
        data = [{"value": "test1"}, {"value": "test2"}]
        
        results = obj.process_data(data)
        
        assert results == ["test1", "test2"]
        mock_logger.debug.assert_called_once()
    
    def test_process_data_empty_list(self):
        """Test processing empty data list."""
        obj = ExampleClass("test")
        results = obj.process_data([])
        assert results == []
    
    @patch('src.example_module.logger')
    def test_process_data_error_handling(self, mock_logger):
        """Test error handling in data processing."""
        obj = ExampleClass("test")
        
        # Mock _process_item to raise exception
        with patch.object(obj, '_process_item', side_effect=Exception("Processing error")):
            with pytest.raises(ProcessingError):
                obj.process_data([{"value": "test"}])
            
            mock_logger.error.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_example.py -v

# Run tests matching pattern
pytest -k "test_initialization" -v

# Run tests with debugging
pytest --pdb
```

## 📚 Documentation

### Code Documentation

- **Module docstrings** describing the module's purpose
- **Class docstrings** with usage examples
- **Function docstrings** with Args, Returns, and Raises sections
- **Inline comments** for complex logic

### API Documentation

- **Update README.md** for new features
- **Add examples** for new functionality
- **Update API reference** for new endpoints
- **Include type information** in documentation

### Example Documentation

```python
def separate_speakers(audio_data: np.ndarray, 
                     sample_rate: int = 16000,
                     max_speakers: int = 4) -> List[np.ndarray]:
    """Separate overlapping speakers in audio data.
    
    This function uses a pretrained Sepformer model to separate
    overlapping speakers in audio data. It returns a list of
    separated audio streams, one for each detected speaker.
    
    Args:
        audio_data: Input audio data as numpy array
        sample_rate: Audio sample rate in Hz (default: 16000)
        max_speakers: Maximum number of speakers to separate (default: 4)
        
    Returns:
        List of numpy arrays, each containing separated audio for one speaker
        
    Raises:
        ValueError: If audio_data is empty or invalid
        ModelError: If the separation model fails to load
        
    Example:
        >>> import numpy as np
        >>> audio = np.random.randn(16000)  # 1 second of audio
        >>> separated = separate_speakers(audio, sample_rate=16000)
        >>> print(f"Separated into {len(separated)} speakers")
        Separated into 2 speakers
    """
    # Implementation here...
```

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure tests pass**: `pytest`
2. **Check code style**: `black src/ && flake8 src/`
3. **Update documentation** if needed
4. **Add changelog entry** for significant changes

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or documented if necessary)

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks** must pass (tests, linting)
2. **Code review** by maintainers
3. **Documentation review** if applicable
4. **Testing verification** by maintainers
5. **Approval and merge**

## 🏷️ Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release notes
- [ ] Tag release
- [ ] Update Docker images

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat (if available)
- **Email**: dev@speakerisolation.com

### Code of Conduct

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) in all interactions.

## 🎯 Areas for Contribution

### High Priority

- **Performance optimization** for real-time processing
- **Additional language support** for transcription
- **Mobile app development** (iOS/Android)
- **Cloud deployment** guides and scripts

### Medium Priority

- **Advanced diarization** features
- **Custom model training** interfaces
- **Enhanced web UI** components
- **Additional audio formats** support

### Low Priority

- **Documentation improvements**
- **Test coverage** increases
- **Code refactoring** and cleanup
- **Translation** of documentation

## 🏆 Recognition

Contributors will be:
- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes**
- **Given credit** in documentation
- **Invited** to maintainer team (for significant contributions)

Thank you for contributing to make this project better! 🚀
