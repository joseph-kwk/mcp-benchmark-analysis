# MCP Benchmark Analysis - Senior Project

**Author**: Joseph Kasongo  
**Institution**: Southwestern College  
**Course**: Senior Project and Seminar  
**Semester**: Spring 2026  

## Project Overview

Large language models (LLMs) progressively depend on external tools such as databases, APIs, and productivity systems to perform complex, real world tasks. This trend introduces an N×M integration challenge in which each model must be manually connected to each tool, resulting in duplicated engineering effort, inconsistent performance, and limited cross system interoperability. Emerging standardization efforts, such as the Model Context Protocol (MCP), aim to mitigate these issues by providing a unified communication layer for connecting models with tools and contextual data sources. Despite growing interest, there is limited empirical evidence comparing MCP's performance to traditional function calling pipelines. This project addresses that gap through a comprehensive benchmarking study of MCP in practical tool integration scenarios.

## Research Questions

The research focuses on three central questions:

1. **Interoperability**: To what extent does MCP improve interoperability across heterogeneous tools and LLMs?
2. **Performance**: How does MCP influence latency and throughput relative to direct function calling?
3. **Reliability**: What effect does MCP have on task accuracy and reliability within agent based workflows?

## Methodology

To investigate these questions, we develop a controlled experimental framework that evaluates MCP based integrations against conventional approaches across tasks such as:
- Structured data retrieval
- Task automation  
- Multi step reasoning

**Key Metrics**:
- Response time
- Error rates
- Integration complexity
- Scalability as the number of tools increases

## Current Implementation - AgriAdvisor MCP Server

This repository contains the initial MCP server implementation used for benchmarking, featuring agricultural advisory services with calculator tools for testing.

### Features

#### Agricultural Tools
- `get_field_status(field_id)` - Get moisture and health status of fields
- `calculate_area(length, width)` - Calculate field area

#### Calculator Tools (For Benchmarking)
- `add(a, b)` - Add two numbers  
- `subtract(a, b)` - Subtract two numbers
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide two numbers (with zero-division protection)

#### Resources
- Safety policy for tractor operation

### Running the Server

1. Install dependencies:
   ```bash
   pip install fastmcp mcp
   ```

2. Start the MCP server:
   ```bash
   python server.py
   ```

3. Connect using MCP Inspector with configuration:
   - **Command**: `python`
   - **Arguments**: `server.py`

### Testing Framework

The calculator tools provide a controlled environment for performance benchmarking:

1. **Basic Operations**: Measure response times for arithmetic operations
2. **Error Handling**: Test fault tolerance with edge cases
3. **Complexity Analysis**: Compare MCP overhead vs direct function calls

#### Example Test Cases
- `add(10, 5)` → "10 + 5 = 15"
- `multiply(7, 8)` → "7 × 8 = 56"
- `divide(10, 0)` → "Error: Cannot divide by zero!"
- `calculate_area(100, 50)` → "Area of 100 × 50 field = 5000 square units"

## Expected Outcomes

The findings of this study will:
- Inform best practices for AI agent architecture
- Offer actionable guidance for developers evaluating MCP adoption
- Provide rigorous, data-driven comparison of integration approaches
- Contribute to the development of more scalable, interoperable, and efficient tool-augmented LLM systems

## Project Structure

```
├── server.py          # Main MCP server implementation
├── main.py            # Testing utilities
├── pyproject.toml     # Project dependencies
└── README.md          # Project documentation
```

## Future Work

1. Implement comprehensive benchmarking suite
2. Add performance monitoring and metrics collection
3. Compare against traditional function calling approaches
4. Scale to multiple tool integrations
5. Analyze cross-LLM compatibility