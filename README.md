# AI Self-Improvement Engine

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An advanced AI-driven system for autonomous code improvement and self-extension. This engine uses a sophisticated role-based architecture with autonomous goal generation, advanced feedback loops, and learning capabilities to continuously improve its own codebase.

## 🚀 Key Features

### **Autonomous System**
- **Autonomous Goal Generation**: Automatically analyzes codebase metrics and generates improvement goals using AST parsing and complexity analysis
- **Enhanced Context Management**: Advanced context system with feedback loops, role metrics, and learning insights
- **Self-Directed Development**: Can operate independently with minimal human intervention

### **Role-Based Architecture**
The engine employs specialized AI roles, each with distinct responsibilities:

- **🔍 GoalGenerationRole**: Performs static code analysis and generates improvement opportunities
- **🎯 ProblemIdentificationRole**: Identifies areas for improvement in the codebase
- **⚡ RefineRole & EnhancedRefineRole**: Generate patches and improvements with advanced feedback integration
- **🧪 TestRole**: Automatically generates and runs comprehensive test suites
- **📋 SelfReviewRole**: Reviews and validates changes for quality and correctness

### **Advanced Learning System**
- **Learning Log**: Persistent memory of improvement cycles and outcomes
- **Feedback Loops**: Inter-role communication and performance tracking
- **Adaptive Behavior**: Roles adjust strategies based on historical performance
- **Insight Capture**: System learns and applies lessons from past experiences

### **Enterprise-Grade Architecture**
- **Plugin System**: Extensible architecture with Python plugin support
- **Configuration-Driven**: Fully configurable via YAML with multiple model backends
- **Snapshot System**: State persistence for resuming interrupted cycles
- **Memory Management**: Structured memory bank with decision logs and progress tracking

## 📊 System Architecture

```
AI Self-Improvement Engine
├── Core Engine (engine.py)
│   ├── Goal Management (goal_manager.py)
│   ├── Context & Feedback Systems (role.py)
│   └── Learning & Adaptation (learning_log.py)
├── Role-Based Processing
│   ├── Goal Generation (AST analysis, metrics)
│   ├── Problem Identification (code analysis)
│   ├── Refinement & Enhancement (patch generation)
│   ├── Testing & Validation (automated test generation)
│   └── Self-Review & Quality Assurance
├── Plugin Architecture
│   └── Python Plugin (extensible for other languages)
└── Memory & Learning
    ├── Structured Memory Bank
    ├── Decision Logging
    └── Progress Tracking
```

## 🛠 Installation

### Prerequisites
- Python 3.8+
- Git

### Quick Start
```bash
# Clone the repository
git clone https://github.com/joerogan7722/AI-self-improvement-engine.git
cd AI-self-improvement-engine

# Install in development mode
pip install -e .

# Install test dependencies
pip install -e ".[test]"
```

### Configuration
1. **Set up environment variables:**
   ```bash
   export GEMINI_API_KEY="your-google-api-key-here"
   ```

2. **Configure the engine:**
   - Edit `config/engine_config.yaml` to customize:
     - Model settings (supports Gemini 2.5 Flash by default)
     - Role configurations
     - Plugin settings
     - Logging preferences

## 🚀 Usage

### Command Line Interface
```bash
# Run the autonomous improvement engine
ai-self-ext-engine run

# Run with specific configuration
ai-self-ext-engine run --config path/to/custom/config.yaml

# Generate goals only (no execution)
ai-self-ext-engine generate-goals

# Review and analyze existing code
ai-self-ext-engine analyze
```

### Programmatic Usage
```python
from ai_self_ext_engine.core.engine import Engine
from ai_self_ext_engine.config import Config

# Initialize with configuration
config = Config.from_file("config/engine_config.yaml")
engine = Engine(config)

# Run autonomous improvement cycle
results = engine.run()

# Access learning insights
insights = engine.context.learning_insights
print(f"Generated {len(insights)} learning insights")
```

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=ai_self_ext_engine

# Run specific test categories
pytest tests/test_goal_manager.py -v
pytest tests/test_simple_module.py -v
```

### Test Structure
- **Unit Tests**: Core functionality testing
- **Integration Tests**: End-to-end workflow validation
- **System Tests**: Autonomous operation validation

## 📁 Project Structure

```
AI-self-improvement-engine/
├── src/ai_self_ext_engine/        # Main package
│   ├── core/                      # Core engine components
│   │   ├── engine.py             # Main engine logic
│   │   ├── role.py               # Enhanced role system with feedback
│   │   └── plugin.py             # Plugin architecture
│   ├── roles/                     # Specialized AI roles
│   │   ├── goal_generation.py    # Autonomous goal generation
│   │   ├── enhanced_refine.py    # Advanced refinement with feedback
│   │   ├── problem_identification.py
│   │   ├── self_review.py
│   │   └── test.py
│   ├── plugins/                   # Language-specific plugins
│   │   └── python/               # Python development plugin
│   ├── tests/                    # Test suite
│   ├── config.py                 # Configuration management
│   ├── goal_manager.py           # Goal lifecycle management
│   ├── learning_log.py           # Learning and adaptation
│   └── model_client.py           # AI model integration
├── config/                       # Configuration files
├── prompts/                      # Role-specific prompts
├── memory/                       # Persistent memory storage
├── docs/                         # Documentation
└── test_autonomous_system.py     # End-to-end system tests
```

## 🔧 Configuration

### Engine Configuration (`config/engine_config.yaml`)
```yaml
engine:
  code_dir: ./src              # Target code directory
  max_cycles: 3               # Maximum improvement cycles
  memory_path: ./memory       # Persistent memory location
  
model:
  api_key_env: GEMINI_API_KEY # Environment variable for API key
  model_name: gemini-2.5-flash # AI model to use

roles:                        # Role configuration
  - module: ai_self_ext_engine.roles.goal_generation
    class: GoalGenerationRole
  # ... additional roles
```

### Memory Structure
The engine maintains structured memory in several components:
- **activeContext.md**: Current development context
- **decisionLog.md**: Historical decisions and rationale
- **progress.md**: Development progress tracking
- **learning_log.jsonl**: Machine learning insights

## 🔬 Advanced Features

### Autonomous Goal Generation
The system analyzes codebase metrics including:
- **Complexity Analysis**: Cyclomatic and cognitive complexity
- **Code Quality Metrics**: Maintainability, readability scores
- **Architecture Analysis**: Design pattern compliance
- **Test Coverage**: Gap identification and improvement suggestions

### Feedback Loop System
- **Inter-Role Communication**: Roles provide feedback to each other
- **Performance Tracking**: Historical effectiveness monitoring
- **Adaptive Strategies**: Learning from success/failure patterns
- **Quality Metrics**: Continuous improvement measurement

### Plugin Architecture
Extensible system supporting:
- **Language-Specific Plugins**: Currently supports Python
- **Custom Analysis Tools**: Integrate external code analysis
- **Model Backends**: Support for different AI models
- **Export Formats**: Various output and reporting options

## 🚧 Development Status

### Recent Enhancements ✅
- Enhanced Context system with feedback loops
- Autonomous goal generation with AST analysis
- Advanced inter-role communication
- Comprehensive test coverage
- Code graph integration for analysis

### Current Development 🔄
- Advanced feedback loops between roles
- Goal dependency analysis and conflict resolution
- Integration with MCP (Model Context Protocol) servers

### Planned Features 🎯
- Multi-language support (JavaScript, Go, Rust)
- Distributed execution across multiple processes
- Advanced learning algorithms
- Integration with popular IDEs
- Real-time collaboration features

## 🤝 Contributing

We welcome contributions! See our contribution guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow code style**: Use `black` and `flake8`
4. **Add tests**: Maintain test coverage
5. **Update documentation**: Keep README and docs current
6. **Submit PR**: With clear description and tests

### Development Setup
```bash
# Install development dependencies
pip install -e ".[test]"

# Run code formatting
black ai_self_ext_engine/ && flake8 ai_self_ext_engine/

# Run full test suite
pytest tests/ -v --cov=ai_self_ext_engine
```

## 📈 Performance & Metrics

- **126+ Symbols Indexed**: Complete codebase analysis
- **34 Files Tracked**: Comprehensive coverage
- **92 Classes, 285 Functions**: Rich object model
- **Autonomous Operation**: Minimal human intervention required
- **Learning Enabled**: Improves over time through experience

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Homepage**: [GitHub Repository](https://github.com/joerogan7722/AI-self-improvement-engine)
- **Issue Tracker**: [GitHub Issues](https://github.com/joerogan7722/AI-self-improvement-engine/issues)
- **Documentation**: See `/docs` directory for detailed documentation

## 📧 Support

For support and questions:
- **Create an issue** on GitHub
- **Check documentation** in `/docs` directory
- **Review test examples** in `/tests` directory

---

*Built with ❤️ and advanced AI technology. This engine represents the cutting edge of autonomous software development.*