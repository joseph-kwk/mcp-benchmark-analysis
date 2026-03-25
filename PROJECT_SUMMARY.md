# Project Summary: mcp-agri-project

## 📁 **Folder Overview**
**Project Name**: `mcp-agri-project`  
**Location**: `C:\Users\Joseph.Kasongo\OneDrive - Southwestern College\Documents\School Work\Spring 2026\Senior Project and Seminar\mcp-agri-project`  
**Academic Context**: Senior Project and Seminar coursework for Spring 2026 at Southwestern College  
**Author**: Joseph Kasongo  
**Date Created**: March 25, 2026

---

## 🎯 **Project Purpose**
This is a **research project focused on benchmarking the Model Context Protocol (MCP)** against traditional function calling approaches for LLM tool integration. The project addresses the N×M integration challenge where each language model needs to be manually connected to each tool, creating duplication and inconsistency.

### **Research Problem Statement**
Large language models (LLMs) progressively depend on external tools such as databases, APIs, and productivity systems to perform complex, real-world tasks. This trend introduces an N×M integration challenge in which each model must be manually connected to each tool, resulting in:
- Duplicated engineering effort
- Inconsistent performance  
- Limited cross-system interoperability

The Model Context Protocol (MCP) aims to mitigate these issues by providing a unified communication layer for connecting models with tools and contextual data sources.

---

## 📊 **Research Objectives**

The project investigates three key research questions:

### 1. **Interoperability**
*To what extent does MCP improve interoperability across heterogeneous tools and LLMs?*

### 2. **Performance** 
*How does MCP influence latency and throughput relative to direct function calling?*

### 3. **Reliability**
*What effect does MCP have on task accuracy and reliability within agent-based workflows?*

### **Research Methodology**
The project develops a controlled experimental framework that evaluates MCP-based integrations against conventional approaches across tasks such as:
- Structured data retrieval
- Task automation  
- Multi-step reasoning

**Key Performance Metrics**:
- Response time
- Error rates
- Integration complexity
- Scalability as the number of tools increases

---

## 📁 **Complete File Structure**

```
mcp-agri-project/
├── .git/                    # Git version control directory
├── .venv/                   # Python virtual environment (active)
├── .gitignore              # Git ignore rules for Python projects
├── .python-version         # Python version specification (3.13)
├── uv.lock                 # UV package manager lock file
├── pyproject.toml          # Python project configuration
├── README.md               # Project documentation and overview
├── main.py                 # Simple main entry point
├── server.py               # Core MCP server implementation
└── PROJECT_SUMMARY.md      # This summary document
```

---

## 🔧 **Technical Implementation**

### **Dependencies** (from pyproject.toml)
- **fastmcp** (>=2.14.5) - FastMCP framework for server implementation
- **mcp** (>=1.26.0) - Model Context Protocol core library
- **Python** 3.13+ required

### **Core Components**

#### **server.py** - Main MCP Server Implementation
**Server Name**: "AgriAdvisor"

**Agricultural Tools**:
- `get_field_status(field_id: str)` - Returns moisture and health status for specific fields
  - Mock data for Field_A and Field_B
  - Returns "Field not found" for unknown fields
- `calculate_area(length: float, width: float)` - Calculates rectangular field area

**Calculator Tools** (for benchmarking):
- `add(a: float, b: float)` - Adds two numbers together
- `subtract(a: float, b: float)` - Subtracts the second number from the first
- `multiply(a: float, b: float)` - Multiplies two numbers
- `divide(a: float, b: float)` - Divides with zero-division protection

**Resources**:
- Safety policy resource (`agri://handbook/safety`) - Returns tractor operation safety rules

#### **main.py** - Basic Entry Point
Simple hello world functionality for basic testing.

#### **README.md** - Comprehensive Project Documentation
Contains detailed project overview, research questions, methodology, and implementation details.

#### **pyproject.toml** - Project Configuration
Defines project metadata, dependencies, and Python version requirements.

---

## ⚙️ **Development Environment**

### **Python Environment**
- **Version**: Python 3.13
- **Virtual Environment**: Active (.venv directory)
- **Package Manager**: UV (indicated by uv.lock file)
- **Dependency Management**: pyproject.toml

### **Version Control**
- **System**: Git (initialized with .git directory)
- **Ignore Rules**: Standard Python gitignore (excludes __pycache__, *.pyc, build/, dist/, .venv)

### **IDE Context**
- **Editor**: VS Code
- **Current Working Directory**: Project root
- **Virtual Environment**: Activated in terminal

---

## 🔬 **Research Context and Significance**

### **Academic Framework**
This implementation serves as a **controlled experimental framework** to compare MCP-based integrations against conventional approaches. The AgriAdvisor server provides a realistic use case while the calculator tools offer standardized benchmarking capabilities.

### **Experimental Design**
The server includes both:
1. **Domain-specific tools** (agricultural advisory) - for real-world applicability
2. **Generic calculation tools** - for standardized performance measurement

### **Expected Outcomes**
The research aims to provide empirical evidence on:
- MCP's effectiveness in reducing integration complexity
- Performance trade-offs between MCP and direct function calling
- Reliability improvements in multi-tool workflows
- Scalability benefits as tool ecosystems grow

---

## 🎓 **Academic Status**

**Course**: Senior Project and Seminar  
**Institution**: Southwestern College  
**Semester**: Spring 2026  
**Project Phase**: Initial implementation complete  
**Date**: March 25, 2026

### **Project Timeline**
- ✅ **Phase 1**: MCP server implementation (Current)
- 🔄 **Phase 2**: Benchmarking framework development
- 📅 **Phase 3**: Experimental data collection
- 📅 **Phase 4**: Analysis and thesis completion

---

## 🚀 **Next Steps**

1. **Expand tool library** - Add more diverse tools for comprehensive testing
2. **Implement benchmarking framework** - Create automated testing suite
3. **Develop comparison baseline** - Implement traditional function calling equivalent
4. **Design experiments** - Create controlled test scenarios
5. **Data collection** - Execute performance and reliability measurements
6. **Analysis and documentation** - Compile results into final thesis

---

*This summary was generated on March 25, 2026, representing the current state of the mcp-agri-project senior research initiative.*