from fastmcp import FastMCP
from datetime import datetime

# 1. Initialize the MCP Server
mcp = FastMCP("AgriAdvisor")

# ─────────────────────────────────────────────
# AGRICULTURAL TOOLS
# ─────────────────────────────────────────────

@mcp.tool()
def get_field_status(field_id: str) -> dict:
    """Provides the current moisture and health status of a specific field."""
    data = {
        "Field_A": {"field_id": "Field_A", "moisture_pct": 12, "status": "Needs Irrigation", "crop": "corn"},
        "Field_B": {"field_id": "Field_B", "moisture_pct": 28, "status": "Healthy",          "crop": "wheat"},
        "Field_C": {"field_id": "Field_C", "moisture_pct": 8,  "status": "Critical",          "crop": "soybean"},
        "Field_D": {"field_id": "Field_D", "moisture_pct": 45, "status": "Healthy",           "crop": "corn"},
    }
    return data.get(field_id, {"error": f"Field '{field_id}' not found."})


@mcp.tool()
def get_weather_forecast(location: str, days: int = 3) -> dict:
    """Get a simulated weather forecast for a farm location (1–5 days)."""
    days = max(1, min(days, 5))  # clamp to 1–5
    forecasts = [
        {"day": 1, "condition": "Sunny",   "temp_high_f": 78, "precip_chance_pct": 10},
        {"day": 2, "condition": "Cloudy",  "temp_high_f": 72, "precip_chance_pct": 40},
        {"day": 3, "condition": "Rain",    "temp_high_f": 65, "precip_chance_pct": 80},
        {"day": 4, "condition": "Sunny",   "temp_high_f": 70, "precip_chance_pct": 5},
        {"day": 5, "condition": "Windy",   "temp_high_f": 68, "precip_chance_pct": 20},
    ]
    return {"location": location, "forecast": forecasts[:days]}


@mcp.tool()
def recommend_irrigation(field_id: str, moisture_pct: float) -> dict:
    """Recommend an irrigation action based on current soil moisture level."""
    if moisture_pct < 15:
        action, gallons_per_acre = "irrigate_immediately", 600
    elif moisture_pct < 30:
        action, gallons_per_acre = "irrigate_soon",        300
    elif moisture_pct < 50:
        action, gallons_per_acre = "monitor",              0
    else:
        action, gallons_per_acre = "no_action_needed",     0
    return {
        "field_id":         field_id,
        "moisture_pct":     moisture_pct,
        "action":           action,
        "gallons_per_acre": gallons_per_acre,
    }


@mcp.tool()
def log_sensor_reading(field_id: str, sensor_type: str, value: float) -> dict:
    """Log a sensor reading (moisture, temperature, pH, etc.) for a field."""
    valid_sensors = {"moisture", "temperature", "ph", "nitrogen", "humidity"}
    if sensor_type.lower() not in valid_sensors:
        return {"error": f"Unknown sensor type '{sensor_type}'. Valid: {sorted(valid_sensors)}"}
    return {
        "logged":      True,
        "field_id":    field_id,
        "sensor_type": sensor_type.lower(),
        "value":       value,
        "timestamp":   datetime.utcnow().isoformat() + "Z",
    }


@mcp.tool()
def get_crop_schedule(crop: str) -> dict:
    """Return the planting and harvest schedule for a given crop."""
    schedules = {
        "corn":    {"plant_month": "April",  "harvest_month": "September", "days_to_maturity": 90},
        "wheat":   {"plant_month": "October","harvest_month": "June",      "days_to_maturity": 240},
        "soybean": {"plant_month": "May",    "harvest_month": "October",   "days_to_maturity": 100},
        "cotton":  {"plant_month": "April",  "harvest_month": "October",   "days_to_maturity": 150},
    }
    info = schedules.get(crop.lower())
    if not info:
        return {"error": f"Crop '{crop}' not found. Available: {sorted(schedules.keys())}"}
    return {"crop": crop.lower(), **info}


@mcp.tool()
def calculate_area(length: float, width: float) -> dict:
    """Calculate the area of a rectangular field in acres and square feet."""
    sq_feet = length * width
    acres   = round(sq_feet / 43560, 4)
    return {
        "length_ft":  length,
        "width_ft":   width,
        "sq_feet":    sq_feet,
        "acres":      acres,
    }


# ─────────────────────────────────────────────
# CALCULATOR TOOLS  (standardized benchmarking)
# ─────────────────────────────────────────────

@mcp.tool()
def add(a: float, b: float) -> dict:
    """Add two numbers."""
    return {"operation": "add", "a": a, "b": b, "result": a + b}

@mcp.tool()
def subtract(a: float, b: float) -> dict:
    """Subtract b from a."""
    return {"operation": "subtract", "a": a, "b": b, "result": a - b}

@mcp.tool()
def multiply(a: float, b: float) -> dict:
    """Multiply two numbers."""
    return {"operation": "multiply", "a": a, "b": b, "result": a * b}

@mcp.tool()
def divide(a: float, b: float) -> dict:
    """Divide a by b. Returns an error if b is zero."""
    if b == 0:
        return {"operation": "divide", "a": a, "b": b, "error": "Division by zero."}
    return {"operation": "divide", "a": a, "b": b, "result": round(a / b, 6)}


# ─────────────────────────────────────────────
# RESOURCES  (read-only reference data)
# ─────────────────────────────────────────────

@mcp.resource("agri://handbook/safety")
def get_safety_policy() -> str:
    """Returns the safety policy for tractor operation."""
    return (
        "Safety Rule #1: Always wear a seatbelt when operating machinery.\n"
        "Safety Rule #2: Never operate equipment under the influence of substances.\n"
        "Safety Rule #3: Inspect equipment before each use.\n"
        "Safety Rule #4: Keep bystanders at least 50 feet from operating machinery."
    )

@mcp.resource("agri://handbook/crops")
def get_crop_list() -> str:
    """Returns the list of supported crops in this system."""
    return "Supported crops: corn, wheat, soybean, cotton."


if __name__ == "__main__":
    mcp.run()