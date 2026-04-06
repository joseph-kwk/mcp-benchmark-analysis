from fastmcp import FastMCP
from datetime import datetime, timedelta
import json
import random

# Initialize the Professional Agricultural MCP Server
mcp = FastMCP("AgriPro")

# ═══════════════════════════════════════════════════════════════════
# REAL AGRICULTURAL DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

# Comprehensive field database with realistic agricultural data
FARM_DATABASE = {
    "field_data": {
        "Field_A": {
            "crop": "corn",
            "variety": "Pioneer P1197AM",
            "planted_date": "2026-04-15",
            "area_acres": 47.3,
            "soil_type": "Mollisol - Deep Prairie",
            "irrigation_type": "center_pivot",
            "current_stage": "V8_vegetative"
        },
        "Field_B": {
            "crop": "wheat", 
            "variety": "WB-Grainfield",
            "planted_date": "2025-09-20",
            "area_acres": 62.1,
            "soil_type": "Alfisol - Glacial Till",
            "irrigation_type": "none",
            "current_stage": "grain_filling"
        },
        "Field_C": {
            "crop": "soybean",
            "variety": "Asgrow AG2834",
            "planted_date": "2026-05-10", 
            "area_acres": 38.7,
            "soil_type": "Vertisol - Heavy Clay",
            "irrigation_type": "drip",
            "current_stage": "R3_pod_development"
        },
        "Field_D": {
            "crop": "corn",
            "variety": "DeKalb DKC64-87RIB",
            "planted_date": "2026-04-20",
            "area_acres": 55.2,
            "soil_type": "Mollisol - Deep Prairie", 
            "irrigation_type": "center_pivot",
            "current_stage": "V10_vegetative"
        }
    },
    
    "soil_data": {
        "Field_A": {
            "ph": 6.2,
            "organic_matter_pct": 3.1,
            "nitrogen_ppm": 12,
            "phosphorus_ppm": 45,
            "potassium_ppm": 180,
            "field_capacity_pct": 32,
            "wilting_point_pct": 18,
            "current_moisture_pct": 12,
            "bulk_density": 1.25,
            "infiltration_rate_in_hr": 0.8
        },
        "Field_B": {
            "ph": 7.1,
            "organic_matter_pct": 2.8,
            "nitrogen_ppm": 8,
            "phosphorus_ppm": 38,
            "potassium_ppm": 210,
            "field_capacity_pct": 28,
            "wilting_point_pct": 15,
            "current_moisture_pct": 28,
            "bulk_density": 1.32,
            "infiltration_rate_in_hr": 0.6
        },
        "Field_C": {
            "ph": 5.8,
            "organic_matter_pct": 2.2,
            "nitrogen_ppm": 15,
            "phosphorus_ppm": 22,
            "potassium_ppm": 145,
            "field_capacity_pct": 38,
            "wilting_point_pct": 22,
            "current_moisture_pct": 8,
            "bulk_density": 1.45,
            "infiltration_rate_in_hr": 0.3
        },
        "Field_D": {
            "ph": 6.8,
            "organic_matter_pct": 3.4,
            "nitrogen_ppm": 18,
            "phosphorus_ppm": 52,
            "potassium_ppm": 195,
            "field_capacity_pct": 30,
            "wilting_point_pct": 16,
            "current_moisture_pct": 45,
            "bulk_density": 1.22,
            "infiltration_rate_in_hr": 0.9
        }
    },

    "equipment": {
        "irrigation_systems": {
            "pivot_001": {"field": "Field_A", "status": "operational", "flow_gpm": 850, "last_maintenance": "2026-03-15"},
            "pivot_002": {"field": "Field_D", "status": "operational", "flow_gpm": 920, "last_maintenance": "2026-02-28"},
            "drip_system_c": {"field": "Field_C", "status": "needs_repair", "flow_gpm": 120, "last_maintenance": "2026-01-10"}
        },
        "field_equipment": {
            "combine_001": {"model": "John Deere S780", "status": "available", "fuel_pct": 78, "location": "shop"},
            "tractor_001": {"model": "Case IH Steiger 540", "status": "in_field", "fuel_pct": 45, "location": "Field_B"},
            "sprayer_001": {"model": "Apache AS1240", "status": "available", "fuel_pct": 92, "tank_gallons": 1200}
        }
    }
}

# ═══════════════════════════════════════════════════════════════════
# COMPREHENSIVE SOIL MANAGEMENT SYSTEM
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_detailed_soil_analysis(field_id: str) -> dict:
    """Get comprehensive soil analysis including chemical, physical, and biological properties"""
    if field_id not in FARM_DATABASE["soil_data"]:
        return {"error": f"Field {field_id} not found"}
    
    soil = FARM_DATABASE["soil_data"][field_id]
    field = FARM_DATABASE["field_data"][field_id]
    
    # Calculate derived metrics
    available_water = soil["field_capacity_pct"] - soil["wilting_point_pct"]
    water_deficit = max(0, soil["field_capacity_pct"] - soil["current_moisture_pct"])
    npk_ratio = f"{soil['nitrogen_ppm']}:{soil['phosphorus_ppm']}:{soil['potassium_ppm']}"
    
    return {
        "field_id": field_id,
        "analysis_date": datetime.now().isoformat(),
        "chemical_properties": {
            "ph": soil["ph"],
            "ph_status": "acidic" if soil["ph"] < 6.5 else "neutral" if soil["ph"] < 7.5 else "alkaline",
            "organic_matter_pct": soil["organic_matter_pct"],
            "nutrients": {
                "nitrogen_ppm": soil["nitrogen_ppm"],
                "phosphorus_ppm": soil["phosphorus_ppm"],
                "potassium_ppm": soil["potassium_ppm"],
                "npk_ratio": npk_ratio
            }
        },
        "physical_properties": {
            "bulk_density": soil["bulk_density"],
            "infiltration_rate_in_hr": soil["infiltration_rate_in_hr"],
            "compaction_status": "severe" if soil["bulk_density"] > 1.4 else "moderate" if soil["bulk_density"] > 1.3 else "good"
        },
        "water_status": {
            "current_moisture_pct": soil["current_moisture_pct"], 
            "field_capacity_pct": soil["field_capacity_pct"],
            "wilting_point_pct": soil["wilting_point_pct"],
            "available_water_capacity": available_water,
            "water_deficit_inches": round(water_deficit * 0.12, 2),  # Rough conversion
            "stress_level": "severe" if soil["current_moisture_pct"] < soil["wilting_point_pct"] + 5 else 
                          "moderate" if soil["current_moisture_pct"] < soil["field_capacity_pct"] - 10 else "minimal"
        },
        "recommendations": {
            "lime_needed": soil["ph"] < 6.0,
            "nitrogen_application_needed": soil["nitrogen_ppm"] < 20,
            "irrigation_priority": "critical" if water_deficit > 15 else "monitor" if water_deficit > 8 else "adequate"
        }
    }

@mcp.tool()
def calculate_fertilizer_requirements(field_id: str, target_yield: float) -> dict:
    """Calculate specific fertilizer requirements based on soil test and yield goals"""
    if field_id not in FARM_DATABASE["soil_data"]:
        return {"error": f"Field {field_id} not found"}
    
    soil = FARM_DATABASE["soil_data"][field_id]
    field = FARM_DATABASE["field_data"][field_id]
    
    # Realistic crop nutrient removal rates (per bushel)
    nutrient_removal = {
        "corn": {"N": 1.2, "P": 0.4, "K": 0.3},      # per bushel
        "wheat": {"N": 2.4, "P": 0.9, "K": 0.6},     # per bushel  
        "soybean": {"N": 3.2, "P": 0.8, "K": 1.4}    # per bushel
    }
    
    crop = field["crop"]
    if crop not in nutrient_removal:
        return {"error": f"Nutrient data not available for {crop}"}
    
    # Calculate nutrient needs
    n_removal = target_yield * nutrient_removal[crop]["N"]
    p_removal = target_yield * nutrient_removal[crop]["P"]
    k_removal = target_yield * nutrient_removal[crop]["K"]
    
    # Account for soil availability (simplified)
    n_needed = max(0, n_removal - (soil["nitrogen_ppm"] * 0.05))
    p_needed = max(0, p_removal - (soil["phosphorus_ppm"] * 0.01))
    k_needed = max(0, k_removal - (soil["potassium_ppm"] * 0.01))
    
    # Convert to application rates
    acres = field["area_acres"]
    
    return {
        "field_id": field_id,
        "target_yield": target_yield,
        "crop": crop,
        "field_acres": acres,
        "nutrient_requirements": {
            "nitrogen_lbs_acre": round(n_needed, 1),
            "phosphorus_lbs_acre": round(p_needed, 1),
            "potassium_lbs_acre": round(k_needed, 1),
            "total_nitrogen_lbs": round(n_needed * acres, 0),
            "total_phosphorus_lbs": round(p_needed * acres, 0),
            "total_potassium_lbs": round(k_needed * acres, 0)
        },
        "application_timing": {
            "pre_plant": f"{round(n_needed * 0.3, 1)} lbs N/acre",
            "side_dress": f"{round(n_needed * 0.7, 1)} lbs N/acre",
            "phosphorus_timing": "all_pre_plant",
            "potassium_timing": "all_pre_plant"
        },
        "estimated_cost_per_acre": round((n_needed * 0.45) + (p_needed * 0.68) + (k_needed * 0.42), 2)
    }

# ═══════════════════════════════════════════════════════════════════
# PRECISION IRRIGATION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_irrigation_system_status(field_id: str = None) -> dict:
    """Get current status of irrigation equipment and recent activity"""
    systems = FARM_DATABASE["equipment"]["irrigation_systems"]
    
    if field_id:
        # Find system for specific field
        system_id = None
        for sys_id, sys_data in systems.items():
            if sys_data["field"] == field_id:
                system_id = sys_id
                break
        
        if not system_id:
            return {"error": f"No irrigation system found for {field_id}"}
        
        return {
            "system_id": system_id,
            "field_id": field_id,
            **systems[system_id],
            "maintenance_status": "overdue" if systems[system_id]["last_maintenance"] < "2026-03-01" else "current"
        }
    else:
        # Return all systems
        return {
            "all_systems": {
                sys_id: {**sys_data, "maintenance_overdue": sys_data["last_maintenance"] < "2026-03-01"}
                for sys_id, sys_data in systems.items()
            },
            "systems_operational": sum(1 for sys in systems.values() if sys["status"] == "operational"),
            "systems_need_repair": sum(1 for sys in systems.values() if sys["status"] == "needs_repair")
        }

@mcp.tool()
def calculate_irrigation_schedule(field_id: str, days_ahead: int = 7) -> dict:
    """Calculate optimal irrigation schedule based on weather, soil, and crop needs"""
    if field_id not in FARM_DATABASE["field_data"]:
        return {"error": f"Field {field_id} not found"}
    
    field = FARM_DATABASE["field_data"][field_id]
    soil = FARM_DATABASE["soil_data"][field_id]
    
    # Simulate weather forecast impact
    daily_et = 0.25  # inches/day evapotranspiration (simplified)
    precip_forecast = [0.0, 0.0, 0.8, 0.0, 0.0, 0.3, 0.0]  # 7-day forecast
    
    schedule = []
    current_moisture = soil["current_moisture_pct"]
    
    for day in range(days_ahead):
        # Calculate daily moisture change
        moisture_loss = (daily_et / soil["field_capacity_pct"]) * 100
        moisture_gain = (precip_forecast[day] / soil["field_capacity_pct"]) * 100 * 0.8  # 80% efficiency
        
        current_moisture = current_moisture - moisture_loss + moisture_gain
        current_moisture = max(soil["wilting_point_pct"], min(current_moisture, soil["field_capacity_pct"]))
        
        # Irrigation decision
        trigger_point = soil["wilting_point_pct"] + 8  # Safety margin
        irrigation_needed = current_moisture < trigger_point
        irrigation_amount = 0
        
        if irrigation_needed:
            irrigation_amount = (soil["field_capacity_pct"] * 0.8) - current_moisture  # Refill to 80% FC
            current_moisture += irrigation_amount
        
        schedule.append({
            "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
            "predicted_moisture_pct": round(current_moisture, 1),
            "et_loss_inches": round(daily_et, 2),
            "precip_forecast_inches": precip_forecast[day],
            "irrigation_needed": irrigation_needed,
            "irrigation_amount_inches": round(irrigation_amount * 0.01, 2),
            "irrigation_hours": round((irrigation_amount * field["area_acres"]) / 3.5, 1) if irrigation_needed else 0
        })
    
    return {
        "field_id": field_id,
        "crop": field["crop"],
        "current_stage": field["current_stage"],
        "irrigation_schedule": schedule,
        "total_water_needed": sum(day["irrigation_amount_inches"] for day in schedule),
        "total_irrigation_hours": sum(day["irrigation_hours"] for day in schedule),
        "estimated_cost": round(sum(day["irrigation_hours"] for day in schedule) * 8.50, 2)  # $8.50/hr operation
    }

# ═══════════════════════════════════════════════════════════════════
# ADVANCED WEATHER INTEGRATION
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_agricultural_weather_data(location: str, days: int = 7) -> dict:
    """Get comprehensive agricultural weather data including GDD, ET, and field conditions"""
    base_temp = 50  # Base temperature for corn GDD calculation
    
    # Simulate realistic weather data
    weather_data = []
    for day in range(days):
        date = datetime.now() + timedelta(days=day)
        temp_high = 75 + random.randint(-8, 12)
        temp_low = temp_high - random.randint(15, 25)
        
        # Calculate Growing Degree Days
        avg_temp = (temp_high + temp_low) / 2
        gdd = max(0, avg_temp - base_temp)
        
        # Field condition assessment
        precip = random.choice([0.0, 0.0, 0.0, 0.15, 0.3, 0.6, 1.2])
        wind_speed = random.randint(5, 18)
        humidity = random.randint(45, 85)
        
        field_conditions = "excellent"
        if precip > 0.5:
            field_conditions = "too_wet"
        elif wind_speed > 15:
            field_conditions = "too_windy_spray"  
        elif humidity < 50:
            field_conditions = "low_humidity"
        
        weather_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "temp_high_f": temp_high,
            "temp_low_f": temp_low,
            "precipitation_inches": precip,
            "wind_speed_mph": wind_speed,
            "humidity_pct": humidity,
            "growing_degree_days": round(gdd, 1),
            "evapotranspiration_inches": round(0.2 + (gdd * 0.01), 2),
            "field_conditions": field_conditions,
            "spray_window": wind_speed < 12 and precip == 0.0,
            "harvest_suitable": precip == 0.0 and humidity < 75
        })
    
    return {
        "location": location,
        "forecast_period": f"{days} days",
        "weather_data": weather_data,
        "accumulated_gdd": round(sum(day["growing_degree_days"] for day in weather_data), 1),
        "total_precipitation": round(sum(day["precipitation_inches"] for day in weather_data), 2),
        "spray_days_available": sum(1 for day in weather_data if day["spray_window"]),
        "harvest_days_suitable": sum(1 for day in weather_data if day["harvest_suitable"])
    }

# ═══════════════════════════════════════════════════════════════════  
# CROP HEALTH & PEST MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def assess_crop_health_status(field_id: str) -> dict:
    """Comprehensive crop health assessment including growth stage, stress indicators, and pest pressure"""
    if field_id not in FARM_DATABASE["field_data"]:
        return {"error": f"Field {field_id} not found"}
    
    field = FARM_DATABASE["field_data"][field_id]
    soil = FARM_DATABASE["soil_data"][field_id]
    
    # Calculate days since planting
    plant_date = datetime.strptime(field["planted_date"], "%Y-%m-%d")
    days_since_plant = (datetime.now() - plant_date).days
    
    # Crop-specific assessments
    crop_assessments = {
        "corn": {
            "optimal_population": 32000,
            "current_population": random.randint(29000, 34000),
            "pest_risks": ["corn_rootworm", "armyworm", "corn_borer"],
            "disease_risks": ["gray_leaf_spot", "northern_corn_leaf_blight"],
            "critical_stages": ["V6_rapid_growth", "VT_tasseling", "R1_silking"]
        },
        "wheat": {
            "optimal_population": 1200000,
            "current_population": random.randint(1100000, 1300000), 
            "pest_risks": ["hessian_fly", "aphids", "armyworm"],
            "disease_risks": ["stripe_rust", "fusarium_head_blight"],
            "critical_stages": ["tillering", "jointing", "heading"]
        },
        "soybean": {
            "optimal_population": 140000,
            "current_population": random.randint(125000, 155000),
            "pest_risks": ["soybean_aphid", "spider_mites", "stink_bugs"],
            "disease_risks": ["sudden_death_syndrome", "white_mold"],
            "critical_stages": ["R1_flowering", "R3_pod_development", "R5_seed_filling"]
        }
    }
    
    crop = field["crop"]
    if crop not in crop_assessments:
        return {"error": f"Crop health data not available for {crop}"}
    
    assessment = crop_assessments[crop]
    
    # Calculate stress factors
    water_stress = "severe" if soil["current_moisture_pct"] < soil["wilting_point_pct"] + 5 else \
                  "moderate" if soil["current_moisture_pct"] < soil["field_capacity_pct"] - 10 else "minimal"
    
    nutrient_stress = "high" if soil["nitrogen_ppm"] < 15 else "moderate" if soil["nitrogen_ppm"] < 25 else "low"
    
    # Pest pressure simulation (would be real scouting data)
    pest_pressure = {
        pest: {
            "population_level": random.choice(["low", "moderate", "high", "economic_threshold"]),
            "trend": random.choice(["increasing", "stable", "decreasing"]),
            "treatment_needed": random.choice([True, False])
        }
        for pest in assessment["pest_risks"]
    }
    
    return {
        "field_id": field_id,
        "crop": crop,
        "variety": field["variety"],
        "assessment_date": datetime.now().isoformat(),
        "growth_metrics": {
            "days_since_planting": days_since_plant,
            "current_stage": field["current_stage"],
            "population_plants_acre": assessment["current_population"],
            "population_vs_optimal": round((assessment["current_population"] / assessment["optimal_population"]) * 100, 1)
        },
        "stress_indicators": {
            "water_stress": water_stress,
            "nutrient_stress": nutrient_stress,
            "compaction_stress": "high" if soil["bulk_density"] > 1.4 else "low",
            "overall_stress_level": max([water_stress, nutrient_stress], key=["minimal", "moderate", "severe", "high"].index)
        },
        "pest_disease_status": pest_pressure,
        "recommendations": {
            "immediate_actions": [
                "Monitor water status daily" if water_stress in ["moderate", "severe"] else None,
                "Consider nitrogen application" if nutrient_stress == "high" else None,
                "Scout for pest pressure weekly" if any(p["population_level"] in ["high", "economic_threshold"] for p in pest_pressure.values()) else None
            ],
            "yield_impact_risk": "high" if water_stress == "severe" or nutrient_stress == "high" else "moderate" if water_stress == "moderate" else "low"
        }
    }

# ═══════════════════════════════════════════════════════════════════
# EQUIPMENT & LOGISTICS MANAGEMENT  
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_equipment_availability(operation_type: str, date: str = None) -> dict:
    """Check equipment availability and scheduling for specific agricultural operations"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    equipment = FARM_DATABASE["equipment"]["field_equipment"]
    irrigation = FARM_DATABASE["equipment"]["irrigation_systems"]
    
    operation_requirements = {
        "planting": ["tractor_001"],
        "spraying": ["sprayer_001", "tractor_001"],
        "harvesting": ["combine_001"],
        "cultivation": ["tractor_001"],
        "irrigation": list(irrigation.keys())
    }
    
    if operation_type not in operation_requirements:
        return {"error": f"Unknown operation type: {operation_type}"}
    
    required_equipment = operation_requirements[operation_type]
    availability = {}
    
    # Check each required piece of equipment
    for equip_id in required_equipment:
        if equip_id in equipment:
            equip_data = equipment[equip_id]
            availability[equip_id] = {
                "model": equip_data["model"],
                "status": equip_data["status"],
                "available": equip_data["status"] in ["available", "in_field"],
                "fuel_level": equip_data["fuel_pct"],
                "location": equip_data["location"],
                "fuel_adequate": equip_data["fuel_pct"] > 25,
                "ready_for_operation": equip_data["status"] == "available" and equip_data["fuel_pct"] > 25
            }
        elif equip_id in irrigation:
            irrig_data = irrigation[equip_id]
            availability[equip_id] = {
                "type": "irrigation_system",
                "field": irrig_data["field"],
                "status": irrig_data["status"],
                "available": irrig_data["status"] == "operational",
                "flow_capacity": irrig_data["flow_gpm"],
                "maintenance_current": irrig_data["last_maintenance"] >= "2026-03-01"
            }
    
    # Overall operation feasibility
    all_equipment_ready = all(equip.get("ready_for_operation", equip.get("available", False)) 
                             for equip in availability.values())
    
    return {
        "operation_type": operation_type,
        "scheduled_date": date,
        "equipment_availability": availability,
        "operation_feasible": all_equipment_ready,
        "constraints": [
            f"Equipment {equip_id} not available" 
            for equip_id, data in availability.items() 
            if not data.get("ready_for_operation", data.get("available", False))
        ],
        "estimated_hours_available": 12 if all_equipment_ready else 0,  # Standard field day
        "weather_dependent": operation_type in ["spraying", "harvesting", "planting"]
    }

# ═══════════════════════════════════════════════════════════════════
# FINANCIAL & MARKET INTEGRATION
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def calculate_operation_costs(field_id: str, operation_type: str, area_acres: float = None) -> dict:
    """Calculate detailed costs for agricultural operations including fuel, labor, and materials"""
    if field_id not in FARM_DATABASE["field_data"]:
        return {"error": f"Field {field_id} not found"}
    
    field = FARM_DATABASE["field_data"][field_id]
    acres = area_acres or field["area_acres"]
    
    # Current cost structures (realistic 2026 prices)
    cost_database = {
        "planting": {
            "fuel_per_acre": 1.2,  # gallons
            "labor_hours_per_acre": 0.15,
            "seed_cost_per_acre": {"corn": 125, "wheat": 45, "soybean": 68},
            "equipment_cost_per_acre": 12.50
        },
        "spraying": {
            "fuel_per_acre": 0.3,
            "labor_hours_per_acre": 0.08,
            "chemical_cost_per_acre": {"corn": 85, "wheat": 55, "soybean": 72},
            "equipment_cost_per_acre": 8.25
        },
        "fertilizing": {
            "fuel_per_acre": 0.8,
            "labor_hours_per_acre": 0.12,
            "equipment_cost_per_acre": 15.00
        },
        "harvesting": {
            "fuel_per_acre": 2.1,
            "labor_hours_per_acre": 0.18,
            "equipment_cost_per_acre": 45.00,
            "hauling_cost_per_bushel": 0.15
        },
        "irrigation": {
            "electricity_per_inch": 12.50,  # per acre-inch
            "labor_hours_per_application": 2.0,
            "maintenance_cost_per_acre": 8.00
        }
    }
    
    if operation_type not in cost_database:
        return {"error": f"Cost data not available for {operation_type}"}
    
    costs = cost_database[operation_type]
    fuel_price = 3.85  # $/gallon diesel
    labor_rate = 25.00  # $/hour
    
    # Calculate base costs
    fuel_cost = costs.get("fuel_per_acre", 0) * acres * fuel_price
    labor_cost = costs.get("labor_hours_per_acre", 0) * acres * labor_rate
    equipment_cost = costs.get("equipment_cost_per_acre", 0) * acres
    
    # Material costs (crop/operation specific)
    material_cost = 0
    if "seed_cost_per_acre" in costs and field["crop"] in costs["seed_cost_per_acre"]:
        material_cost = costs["seed_cost_per_acre"][field["crop"]] * acres
    elif "chemical_cost_per_acre" in costs and field["crop"] in costs["chemical_cost_per_acre"]:
        material_cost = costs["chemical_cost_per_acre"][field["crop"]] * acres
    
    total_cost = fuel_cost + labor_cost + equipment_cost + material_cost
    
    return {
        "field_id": field_id,
        "operation": operation_type,
        "area_acres": acres,
        "cost_breakdown": {
            "fuel_cost": round(fuel_cost, 2),
            "labor_cost": round(labor_cost, 2),
            "equipment_cost": round(equipment_cost, 2),
            "material_cost": round(material_cost, 2),
            "total_cost": round(total_cost, 2)
        },
        "per_acre_costs": {
            "fuel_per_acre": round(fuel_cost / acres, 2),
            "labor_per_acre": round(labor_cost / acres, 2),
            "equipment_per_acre": round(equipment_cost / acres, 2),
            "material_per_acre": round(material_cost / acres, 2),
            "total_per_acre": round(total_cost / acres, 2)
        },
        "resource_requirements": {
            "fuel_gallons": costs.get("fuel_per_acre", 0) * acres,
            "labor_hours": costs.get("labor_hours_per_acre", 0) * acres,
            "completion_time_days": max(1, round((costs.get("labor_hours_per_acre", 0) * acres) / 12, 1))
        }
    }

# ═══════════════════════════════════════════════════════════════════
# INTEGRATED DECISION SUPPORT SYSTEM  
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def generate_field_action_plan(field_id: str, time_horizon_days: int = 14) -> dict:
    """Generate comprehensive action plan integrating all field management systems"""
    if field_id not in FARM_DATABASE["field_data"]:
        return {"error": f"Field {field_id} not found"}
    
    # This demonstrates the complex multi-tool integration that MCP should excel at
    # vs traditional approaches where each system would need separate API calls
    
    field = FARM_DATABASE["field_data"][field_id]
    soil = FARM_DATABASE["soil_data"][field_id]
    
    action_plan = {
        "field_id": field_id,
        "plan_date": datetime.now().isoformat(),
        "time_horizon": f"{time_horizon_days} days",
        "current_status": {
            "crop": field["crop"],
            "growth_stage": field["current_stage"], 
            "acres": field["area_acres"],
            "soil_moisture": f"{soil['current_moisture_pct']}%"
        },
        "priority_actions": [],
        "scheduled_operations": []
    }
    
    # Critical irrigation assessment
    if soil["current_moisture_pct"] < soil["wilting_point_pct"] + 5:
        action_plan["priority_actions"].append({
            "priority": "CRITICAL",
            "action": "Emergency irrigation",
            "reason": f"Soil moisture at {soil['current_moisture_pct']}% below critical threshold",
            "timeframe": "Immediate (within 24 hours)",
            "estimated_cost": 450.00,
            "risk_if_delayed": "Severe crop stress, potential yield loss 20-40%"
        })
    
    # Nutrient management
    if soil["nitrogen_ppm"] < 15:
        action_plan["priority_actions"].append({
            "priority": "HIGH",
            "action": "Nitrogen application", 
            "reason": f"Soil nitrogen at {soil['nitrogen_ppm']} ppm below optimal",
            "timeframe": "Within 1 week",
            "estimated_cost": field["area_acres"] * 85.00,
            "risk_if_delayed": "Reduced yield potential, yellowing plants"
        })
    
    # Pest monitoring (simulated)
    action_plan["scheduled_operations"].append({
        "operation": "Pest scouting",
        "frequency": "Weekly",
        "next_due": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "labor_hours": 2.5,
        "cost": 62.50
    })
    
    # Calculate total plan impact
    total_cost = sum(action.get("estimated_cost", 0) for action in action_plan["priority_actions"])
    total_cost += sum(op.get("cost", 0) for op in action_plan["scheduled_operations"])
    
    action_plan["plan_summary"] = {
        "total_estimated_cost": round(total_cost, 2),
        "cost_per_acre": round(total_cost / field["area_acres"], 2),
        "risk_level": "HIGH" if any(a["priority"] == "CRITICAL" for a in action_plan["priority_actions"]) else "MODERATE",
        "yield_impact_potential": "Positive with timely action implementation"
    }
    
    return action_plan

# Basic calculator tools (for standardized benchmarking)
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers - for MCP vs Traditional performance testing"""
    return a + b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers - for MCP vs Traditional performance testing"""
    return a * b

# Agricultural knowledge resources
@mcp.resource("agri://handbook/safety")
def safety_handbook() -> str:
    return """Agricultural Safety Protocols:
    1. Never operate equipment without proper training
    2. Always wear appropriate PPE when handling chemicals
    3. Follow lockout/tagout procedures for maintenance
    4. Check weather conditions before field operations
    5. Maintain safe distances from power lines
    """

@mcp.resource("agri://handbook/emergency") 
def emergency_procedures() -> str:
    return """Agricultural Emergency Procedures:
    CHEMICAL EXPOSURE: Remove contaminated clothing, flush with water, seek medical attention
    EQUIPMENT ACCIDENT: Shut off power, secure area, call emergency services
    SEVERE WEATHER: Move to shelter, monitor weather alerts, postpone operations
    CROP FAILURE: Document damage, contact insurance agent, preserve evidence
    """

if __name__ == "__main__":
    mcp.run()