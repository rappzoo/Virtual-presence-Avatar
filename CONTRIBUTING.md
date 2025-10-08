# 🤝 Contributing to Avatar Tank

Thank you for your interest in contributing to Avatar Tank! This document provides guidelines and information for contributors.

## 🚀 **Getting Started**

### **Prerequisites**
- Read the [README.md](README.md) and [PREREQUISITES.md](PREREQUISITES.md)
- Set up your development environment
- Familiarize yourself with the codebase

### **Development Setup**
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/avatar-tank.git
cd avatar-tank

# Run the setup script
./setup.sh

# Create a feature branch
git checkout -b feature/your-feature-name
```

## 📝 **How to Contribute**

### **Reporting Issues**
- Use the GitHub issue tracker
- Provide detailed information about the problem
- Include system information and logs
- Use appropriate labels

### **Suggesting Features**
- Open a discussion or issue
- Describe the use case and benefits
- Consider implementation complexity
- Get community feedback

### **Code Contributions**
- Follow the coding standards
- Write tests for new features
- Update documentation
- Ensure backward compatibility

## 🎯 **Areas for Contribution**

### **High Priority**
- **Performance Optimization** - Improve streaming performance
- **Hardware Support** - Add support for new cameras/motors
- **Security Enhancements** - Authentication and encryption
- **Mobile Interface** - Better mobile web experience

### **Medium Priority**
- **Additional TTS Languages** - More voice options
- **Advanced Motor Control** - More movement patterns
- **Recording Features** - Video recording capabilities
- **API Extensions** - Additional endpoints

### **Low Priority**
- **UI Improvements** - Visual enhancements
- **Documentation** - More examples and tutorials
- **Testing** - Additional test coverage
- **Code Cleanup** - Refactoring and optimization

## 📋 **Coding Standards**

### **Python Code**
```python
# Use PEP 8 style guide
# Add type hints where appropriate
# Write docstrings for functions and classes
# Use meaningful variable names

def process_video_stream(stream_url: str, resolution: str) -> bool:
    """
    Process video stream with specified resolution.
    
    Args:
        stream_url: URL of the video stream
        resolution: Target resolution (320p, 480p, 720p)
        
    Returns:
        bool: True if successful, False otherwise
    """
    pass
```

### **JavaScript Code**
```javascript
// Use modern ES6+ features
// Add JSDoc comments
// Use consistent naming conventions
// Handle errors gracefully

/**
 * Initialize VU meter for audio visualization
 * @param {HTMLVideoElement} videoElement - Video element with audio
 * @returns {Promise<boolean>} Success status
 */
async function initVUMeter(videoElement) {
    try {
        // Implementation
        return true;
    } catch (error) {
        console.error('VU meter initialization failed:', error);
        return false;
    }
}
```

### **HTML/CSS**
```html
<!-- Use semantic HTML -->
<!-- Add accessibility attributes -->
<!-- Keep structure clean and organized -->

<main class="avatar-tank-interface" role="main">
    <section class="video-stream" aria-label="Live video feed">
        <video id="vid" controls aria-label="Avatar Tank camera feed">
            Your browser does not support video playback.
        </video>
    </section>
</main>
```

## 🧪 **Testing**

### **Running Tests**
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=modules

# Run specific test file
pytest tests/test_camera.py
```

### **Writing Tests**
```python
# tests/test_camera.py
import pytest
from modules.mediamtx_camera import CameraManager

class TestCameraManager:
    def test_camera_initialization(self):
        """Test camera manager initialization."""
        manager = CameraManager()
        assert manager is not None
        
    def test_resolution_change(self):
        """Test resolution change functionality."""
        manager = CameraManager()
        result = manager.set_resolution("720p")
        assert result is True
```

## 📚 **Documentation**

### **Code Documentation**
- Add docstrings to all functions and classes
- Include parameter and return type information
- Provide usage examples where helpful
- Update README for new features

### **API Documentation**
- Document all API endpoints
- Include request/response examples
- Add error code documentation
- Keep examples up to date

## 🔄 **Pull Request Process**

### **Before Submitting**
1. **Test your changes** - Ensure all tests pass
2. **Update documentation** - Add/update relevant docs
3. **Check formatting** - Use consistent code style
4. **Rebase on main** - Keep your branch up to date

### **Pull Request Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### **Review Process**
1. **Automated checks** - CI/CD pipeline runs
2. **Code review** - Maintainers review changes
3. **Testing** - Manual testing if needed
4. **Approval** - Changes approved and merged

## 🏷️ **Issue Labels**

### **Issue Types**
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `question` - Further information needed

### **Priority Levels**
- `high` - Critical issues
- `medium` - Important issues
- `low` - Nice to have
- `good first issue` - Good for newcomers

### **Status**
- `in progress` - Currently being worked on
- `needs review` - Ready for review
- `blocked` - Waiting for dependencies
- `duplicate` - Already reported

## 🎉 **Recognition**

### **Contributors**
- All contributors are listed in CONTRIBUTORS.md
- Significant contributions get special recognition
- Contributors may be invited to become maintainers

### **Contributor Types**
- **Code Contributors** - Write code and tests
- **Documentation Contributors** - Improve docs
- **Bug Reporters** - Report and help fix bugs
- **Community Helpers** - Help other users

## 📞 **Getting Help**

### **Communication Channels**
- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and ideas
- **Pull Requests** - Code contributions and reviews

### **Response Times**
- **Critical bugs** - Within 24 hours
- **General issues** - Within 3-5 days
- **Feature requests** - Within 1-2 weeks
- **Pull requests** - Within 1 week

## 📜 **Code of Conduct**

### **Our Standards**
- **Be respectful** - Treat everyone with respect
- **Be inclusive** - Welcome newcomers and diverse perspectives
- **Be constructive** - Provide helpful feedback
- **Be patient** - Understand that everyone has different skill levels

### **Unacceptable Behavior**
- Harassment or discrimination
- Trolling or inflammatory comments
- Spam or off-topic discussions
- Any other unprofessional conduct

## 📄 **License**

By contributing to Avatar Tank, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Avatar Tank! 🚀**
