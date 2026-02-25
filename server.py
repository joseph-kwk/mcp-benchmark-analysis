from fastmcp import FastMCP

# 1. Initialize the MCP Server
# We name it "AgriAdvisor"
mcp = FastMCP("AgriAdvisor")

# 2. Create a "Tool" (An Action)
@mcp.tool()
def get_field_status(field_id: str) -> str:
    """Provides the current moisture and health status of a specific field."""
    # In the future, this will query a real database.
    # For now, it's a deterministic mock response for your demo.
    data = {
        "Field_A": "Moisture: 12% | Status: Needs Irrigation",
        "Field_B": "Moisture: 28% | Status: Healthy",
    }
    return data.get(field_id, "Field not found.")

# Calculator Tools for Testing
@mcp.tool()
def add(a: float, b: float) -> str:
    """Adds two numbers together."""
    result = a + b
    return f"{a} + {b} = {result}"

@mcp.tool()
def subtract(a: float, b: float) -> str:
    """Subtracts the second number from the first."""
    result = a - b
    return f"{a} - {b} = {result}"

@mcp.tool()
def multiply(a: float, b: float) -> str:
    """Multiplies two numbers."""
    result = a * b
    return f"{a} × {b} = {result}"

@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divides the first number by the second."""
    if b == 0:
        return "Error: Cannot divide by zero!"
    result = a / b
    return f"{a} ÷ {b} = {result}"

@mcp.tool()
def calculate_area(length: float, width: float) -> str:
    """Calculates the area of a rectangle (useful for field calculations)."""
    area = length * width
    return f"Area of {length} × {width} field = {area} square units"

# 3. Create a "Resource" (Data)
@mcp.resource("agri://handbook/safety")
def get_safety_policy() -> str:
    """Returns the safety policy for tractor operation."""
    return "Safety Rule #1: Always wear a seatbelt when operating machinery."

if __name__ == "__main__":
    mcp.run()
