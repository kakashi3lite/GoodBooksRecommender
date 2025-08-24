# 🤝 Contributing to GoodBooks Recommender

Welcome to the GoodBooks Recommender project! We're excited that you're interested in contributing. This guide will help you get started and ensure your contributions align with our project standards.

## 📋 Table of Contents

- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Contribution Types](#-contribution-types)
- [Coding Standards](#-coding-standards)
- [Submission Process](#-submission-process)
- [Review Process](#-review-process)
- [Community Guidelines](#-community-guidelines)

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Docker** and **Docker Compose**
- **Git** with proper configuration
- **Code editor** with Python support (VS Code recommended)

### Quick Setup
```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/GoodBooksRecommender.git
cd GoodBooksRecommender

# 3. Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Set up pre-commit hooks
pre-commit install

# 5. Verify setup
python -m pytest tests/
```

### First Contribution
1. **Read the documentation** - Start with [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
2. **Explore the codebase** - Review the [architecture documentation](docs/ARCHITECTURE.md)
3. **Find an issue** - Look for `good-first-issue` or `help-wanted` labels
4. **Ask questions** - Don't hesitate to ask in issue comments

---

## 🛠️ Development Setup

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Configure your development settings
# Edit .env with your specific configuration
```

### Development Services
```bash
# Start all development services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start only core services for development
docker-compose up -d redis postgres

# Run the application locally
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Setup
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/api/

# Run linting and formatting
pre-commit run --all-files
```

---

## 🎯 Contribution Types

### 🐛 Bug Fixes
- **Small bugs**: Direct PR with fix and tests
- **Complex bugs**: Create issue first, then PR
- **Security bugs**: Use private vulnerability reporting

**Bug Fix Checklist:**
- [ ] Reproducer test case added
- [ ] Root cause identified and documented
- [ ] Fix implements minimal necessary change
- [ ] Regression tests added
- [ ] Documentation updated if needed

### ✨ New Features
- **Minor features**: Create issue for discussion
- **Major features**: RFC (Request for Comments) process
- **Breaking changes**: Requires approval from maintainers

**Feature Development Process:**
1. **Issue Creation**: Describe the feature and use case
2. **Design Discussion**: Architecture and implementation approach
3. **Implementation**: Follow coding standards and best practices
4. **Testing**: Comprehensive test coverage
5. **Documentation**: User and developer documentation
6. **Review**: Code and design review process

### 📚 Documentation
- **Typos/Grammar**: Direct PR welcome
- **New documentation**: Follow documentation standards
- **API documentation**: Must match code implementation

**Documentation Standards:**
- Clear, concise writing
- Practical examples included
- Cross-references to related content
- Regular updates with code changes

### 🧪 Testing
- **Unit tests**: Test individual components
- **Integration tests**: Test component interactions
- **API tests**: Test endpoint functionality
- **Performance tests**: Test scalability and performance

---

## 💻 Coding Standards

### Python Standards
We follow [PEP 8](https://pep8.org/) with additional project-specific guidelines:

#### Import Organization
```python
# Standard library imports
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

# Third-party imports
import fastapi
import redis
from pydantic import BaseModel

# Local application imports
from src.core.config import settings
from src.models.schemas import UserSchema
```

#### Function Documentation
```python
async def get_recommendations(
    user_id: int,
    n_recommendations: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> RecommendationResponse:
    """Generate personalized book recommendations.
    
    Args:
        user_id: Target user identifier
        n_recommendations: Number of recommendations (1-50)
        filters: Optional filtering criteria
        
    Returns:
        RecommendationResponse with books and explanations
        
    Raises:
        UserNotFoundError: If user doesn't exist
        ValidationError: If parameters are invalid
        
    Example:
        >>> response = await get_recommendations(123, 5)
        >>> print(response.books[0].title)
    """
```

#### Error Handling
```python
try:
    result = await process_request(request)
    return result
except ValidationError as e:
    logger.error(f"Validation error: {e}")
    raise HTTPException(
        status_code=422,
        detail={"error": "validation_error", "message": str(e)}
    )
except ServiceError as e:
    logger.error(f"Service error: {e}")
    raise HTTPException(
        status_code=503,
        detail={"error": "service_unavailable", "retry_after": 30}
    )
```

### API Standards
- **RESTful design**: Follow REST principles
- **Consistent naming**: Use clear, descriptive names
- **Proper HTTP status codes**: Use appropriate status codes
- **Comprehensive error handling**: Detailed error responses
- **Input validation**: Pydantic models for all inputs
- **Response formatting**: Consistent response structure

### Security Standards
- **Input validation**: All inputs must be validated
- **Output encoding**: Prevent XSS and injection attacks
- **Authentication**: Proper authentication for protected endpoints
- **Authorization**: Role-based access control
- **Sensitive data**: No secrets in code or logs
- **Dependencies**: Keep dependencies updated

---

## 📬 Submission Process

### Branch Strategy
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b fix/issue-number-description

# For documentation
git checkout -b docs/documentation-update
```

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Examples:**
```
feat(api): add multimodal input processing for false news detection

- Implement text, image, and video input handlers
- Add comprehensive input validation and sanitization
- Include rate limiting for large file uploads

Closes #123

fix(auth): resolve JWT token refresh edge case

- Handle expired refresh tokens gracefully
- Add proper error messages for token refresh failures
- Update token refresh logic to prevent race conditions

Fixes #456

docs(fakenews): add integration examples and quickstart guide

- Create step-by-step integration examples
- Add quickstart guide for developers
- Include API usage examples and best practices

Updates documentation for false news detection system
```

### Pre-submission Checklist
- [ ] **Code Quality**: Follows coding standards
- [ ] **Tests**: All tests pass, new tests added
- [ ] **Documentation**: Updated relevant documentation
- [ ] **Security**: No security vulnerabilities introduced
- [ ] **Performance**: No performance regressions
- [ ] **Breaking Changes**: Properly documented and justified

### Pull Request Process
1. **Create descriptive PR**: Use PR template
2. **Link related issues**: Reference issue numbers
3. **Add appropriate labels**: Feature, bug, documentation, etc.
4. **Request reviews**: Tag relevant maintainers
5. **Address feedback**: Respond to review comments
6. **Update as needed**: Make requested changes

---

## 🔍 Review Process

### Review Criteria
- **Functionality**: Code works as intended
- **Quality**: Clean, readable, maintainable code
- **Testing**: Adequate test coverage
- **Documentation**: Clear documentation and comments
- **Security**: No security vulnerabilities
- **Performance**: No unnecessary performance impact

### Review Timeline
- **Standard PRs**: 48-72 hours for initial review
- **Bug fixes**: 24-48 hours for initial review
- **Security fixes**: 12-24 hours for initial review
- **Documentation**: 24-48 hours for initial review

### Review Process
1. **Automated checks**: CI/CD pipeline validation
2. **Code review**: Technical review by maintainers
3. **Security review**: For security-sensitive changes
4. **Documentation review**: For user-facing changes
5. **Final approval**: Maintainer approval required

---

## 🌟 Community Guidelines

### Code of Conduct
We are committed to providing a welcoming and inclusive environment:
- **Be respectful**: Treat all community members with respect
- **Be inclusive**: Welcome newcomers and diverse perspectives
- **Be collaborative**: Work together towards common goals
- **Be constructive**: Provide helpful feedback and suggestions

### Communication Channels
- **GitHub Issues**: Bug reports, feature requests, discussions
- **Pull Requests**: Code contributions and reviews
- **Discussions**: General questions and community topics
- **Security**: Private vulnerability reporting for security issues

### Getting Help
- **Documentation**: Check [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
- **Issues**: Search existing issues for similar problems
- **Discussions**: Start a discussion for general questions
- **Maintainers**: Tag maintainers for urgent issues

### Recognition
We value all contributions and recognize contributors through:
- **Contributor credits**: Listed in project documentation
- **Release notes**: Contributions highlighted in releases
- **Community recognition**: Public acknowledgment of significant contributions

---

## 📚 Additional Resources

### Development Resources
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Testing Guide](docs/TESTING_GUIDE.md)
- [Security Guide](docs/SECURITY_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

### Learning Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)

### Tools and Setup
- [VS Code Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Pre-commit Hooks](https://pre-commit.com/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [isort Import Sorter](https://pycqa.github.io/isort/)

---

## 📝 Questions?

If you have questions about contributing, please:
1. **Check the documentation** first
2. **Search existing issues** for similar questions
3. **Create a discussion** for general questions
4. **Create an issue** for specific problems

Thank you for contributing to GoodBooks Recommender! 🎉

---

*This contributing guide is maintained by the project maintainers and is updated regularly to reflect current best practices and community needs.*

---
## Quick Commands
```bash
npm test             # Run frontend tests
python -m pytest     # Run backend tests
npm run lint         # Lint frontend
pre-commit run --files <path>  # Lint backend
```

## Issue Triage Labels
Use labels like `bug`, `feature`, `documentation`, `good-first-issue` to help prioritization.

## Commit & PR Conventions
- Commits follow `type(scope): short description`
- Reference issues with `Fixes #123`
- Include test and doc updates with code changes
