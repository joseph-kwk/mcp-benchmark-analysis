"""
Multi-Step Task Scenarios for MCP vs Traditional Function Calling Comparison
Defines complex agricultural workflows to test RQ1, RQ2, RQ3

These scenarios are designed to evaluate:
- RQ1: Interoperability across Claude 3.5 and GPT-4o
- RQ2: Latency overhead of MCP protocol 
- RQ3: Task accuracy in multi-step reasoning chains
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class TaskComplexity(Enum):
    SIMPLE = "simple"        # Single tool call
    MODERATE = "moderate"    # 2-3 tool calls with dependencies  
    COMPLEX = "complex"      # 4+ tool calls with conditional logic


@dataclass 
class TaskScenario:
    """Defines a benchmarking task scenario"""
    scenario_id: str
    name: str
    description: str
    complexity: TaskComplexity
    user_prompt: str
    expected_tools: List[str]  # Expected tool call sequence
    expected_steps: int        # Number of tool calls expected
    validation_criteria: Dict[str, Any]  # How to verify correctness


class BenchmarkScenarios:
    """Collection of standardized test scenarios for MCP benchmarking"""
    
    @classmethod
    def get_all_scenarios(cls) -> List[TaskScenario]:
        """Get all defined test scenarios"""
        return [
            # Simple scenarios (single tool call)
            cls.simple_field_check(),
            cls.simple_weather_query(),
            cls.simple_area_calculation(),
            
            # Moderate scenarios (2-3 coordinated calls)
            cls.irrigation_planning(),
            cls.field_comparison(),
            cls.weather_based_recommendation(),
            
            # Complex scenarios (4+ calls with conditional logic)
            cls.comprehensive_field_analysis(),
            cls.multi_field_optimization(),
            cls.harvest_logistics_planning(),
        ]
    
    @classmethod
    def get_by_complexity(cls, complexity: TaskComplexity) -> List[TaskScenario]:
        """Filter scenarios by complexity level"""
        return [s for s in cls.get_all_scenarios() if s.complexity == complexity]
    
    # ═══════════════════════════════════════════════════════════════
    # SIMPLE SCENARIOS (Single tool call - baseline performance)
    # ═══════════════════════════════════════════════════════════════
    
    @classmethod
    def simple_field_check(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="S1",
            name="Single Field Status Check",
            description="Basic field information retrieval",
            complexity=TaskComplexity.SIMPLE,
            user_prompt="What is the current status of Field_A?",
            expected_tools=["get_field_status"],
            expected_steps=1,
            validation_criteria={
                "contains_moisture_pct": True,
                "contains_status": True,
                "correct_field_id": "Field_A"
            }
        )
    
    @classmethod
    def simple_weather_query(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="S2", 
            name="Weather Forecast Request",
            description="Basic weather information retrieval",
            complexity=TaskComplexity.SIMPLE,
            user_prompt="Give me the 3-day weather forecast for my Iowa farm.",
            expected_tools=["get_weather_forecast"],
            expected_steps=1,
            validation_criteria={
                "location_specified": True,
                "forecast_days": 3,
                "contains_precipitation": True
            }
        )
    
    @classmethod  
    def simple_area_calculation(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="S3",
            name="Field Area Calculation",
            description="Basic mathematical computation", 
            complexity=TaskComplexity.SIMPLE,
            user_prompt="Calculate the area of a field that is 200 feet by 150 feet.",
            expected_tools=["calculate_area"],
            expected_steps=1,
            validation_criteria={
                "correct_sq_feet": 30000,
                "contains_acres": True,
                "length_width_preserved": True
            }
        )
    
    # ═══════════════════════════════════════════════════════════════
    # MODERATE SCENARIOS (Multi-step coordination)  
    # ═══════════════════════════════════════════════════════════════
    
    @classmethod
    def irrigation_planning(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="M1",
            name="Smart Irrigation Planning",
            description="Weather-informed irrigation decision making",
            complexity=TaskComplexity.MODERATE,
            user_prompt="""
            I need to decide whether to irrigate Field_B tomorrow. 
            Check the current field status and the weather forecast to make a recommendation.
            """,
            expected_tools=["get_field_status", "get_weather_forecast", "recommend_irrigation"],
            expected_steps=3,
            validation_criteria={
                "field_status_checked": True,
                "weather_considered": True,  
                "irrigation_recommendation": True,
                "reasoning_provided": True
            }
        )
    
    @classmethod
    def field_comparison(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="M2",
            name="Multi-Field Health Comparison", 
            description="Comparative analysis across multiple fields",
            complexity=TaskComplexity.MODERATE,
            user_prompt="""
            Compare the health status of Field_A and Field_C. 
            Which one needs more immediate attention and why?
            """,
            expected_tools=["get_field_status", "get_field_status"],
            expected_steps=2,
            validation_criteria={
                "both_fields_checked": True,
                "comparison_made": True,
                "priority_identified": True,
                "reasoning_sound": True
            }
        )
    
    @classmethod
    def weather_based_recommendation(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="M3",
            name="Weather-Based Field Management",
            description="Conditional recommendations based on forecast",
            complexity=TaskComplexity.MODERATE, 
            user_prompt="""
            Based on the weather forecast for the next 3 days,
            should I adjust irrigation for Field_D? Consider both current field 
            condition and upcoming weather patterns.
            """,
            expected_tools=["get_field_status", "get_weather_forecast", "recommend_irrigation"],
            expected_steps=3,
            validation_criteria={
                "current_status_assessed": True,
                "forecast_analyzed": True,
                "conditional_logic_applied": True,
                "final_recommendation": True
            }
        )
    
    # ═══════════════════════════════════════════════════════════════
    # COMPLEX SCENARIOS (Multi-step with conditional branching)
    # ═══════════════════════════════════════════════════════════════
    
    @classmethod
    def comprehensive_field_analysis(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="C1",
            name="Comprehensive Farm Health Analysis",
            description="Full farm assessment with prioritized action plan",
            complexity=TaskComplexity.COMPLEX,
            user_prompt="""
            I need a comprehensive analysis of my entire farm operation. 
            Check all fields (A through D), get the weather forecast, 
            and create a prioritized action plan for the next week. 
            Include irrigation recommendations and any urgent issues that need attention.
            """,
            expected_tools=[
                "get_field_status", "get_field_status", "get_field_status", "get_field_status",
                "get_weather_forecast", "recommend_irrigation"
            ],
            expected_steps=6,  # Could be more depending on logic
            validation_criteria={
                "all_fields_assessed": True,
                "weather_integrated": True,
                "priority_ranking": True,
                "actionable_plan": True,
                "timeline_specified": True
            }
        )
    
    @classmethod
    def multi_field_optimization(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="C2", 
            name="Multi-Field Irrigation Optimization",
            description="Resource allocation across multiple fields",
            complexity=TaskComplexity.COMPLEX,
            user_prompt="""
            I have limited water resources this week due to equipment maintenance.
            Analyze all my fields and the weather forecast to determine the optimal 
            irrigation strategy. Prioritize which fields get water first and 
            calculate the total water needs. Fields are 100ft x 200ft each.
            """,
            expected_tools=[
                "get_field_status", "get_field_status", "get_field_status", "get_field_status", 
                "get_weather_forecast", "calculate_area", "recommend_irrigation"
            ],
            expected_steps=7,
            validation_criteria={
                "resource_constraint_acknowledged": True,
                "field_prioritization": True,
                "total_water_calculated": True,
                "field_areas_computed": True,
                "optimization_strategy": True
            }
        )
    
    @classmethod
    def harvest_logistics_planning(cls) -> TaskScenario:
        return TaskScenario(
            scenario_id="C3",
            name="Harvest Logistics Coordination", 
            description="Complex multi-factor harvest planning",
            complexity=TaskComplexity.COMPLEX,
            user_prompt="""
            Plan the harvest schedule for my farm. Check field conditions, 
            weather forecast, and calculate field areas for equipment planning.
            Fields with corn should be harvested first if weather permits.
            Create a day-by-day harvest plan considering weather windows.
            """,
            expected_tools=[
                "get_field_status", "get_field_status", "get_field_status", "get_field_status",
                "get_weather_forecast", "calculate_area", "get_crop_schedule" 
            ],
            expected_steps=7,
            validation_criteria={
                "crop_types_identified": True,
                "weather_windows_analyzed": True,
                "harvest_priority_logical": True,
                "daily_schedule_provided": True,
                "equipment_considerations": True
            }
        )


# Utility functions for scenario execution and validation

def validate_scenario_completion(scenario: TaskScenario, 
                                execution_result: Dict[str, Any]) -> Dict[str, bool]:
    """
    Validate whether a scenario was completed correctly
    Returns validation results for each criteria
    """
    validation_results = {}
    
    for criteria, expected in scenario.validation_criteria.items():
        # This is where you'd implement specific validation logic
        # For now, placeholder implementation
        validation_results[criteria] = True  # TODO: Implement actual validation
    
    return validation_results


def generate_scenario_prompts(complexity_filter: TaskComplexity = None) -> List[str]:
    """Generate list of prompts for batch testing"""
    scenarios = BenchmarkScenarios.get_all_scenarios()
    
    if complexity_filter:
        scenarios = [s for s in scenarios if s.complexity == complexity_filter]
    
    return [scenario.user_prompt for scenario in scenarios]


if __name__ == "__main__":
    # Test scenario generation
    print("MCP Benchmarking Test Scenarios")
    print("═" * 50)
    
    all_scenarios = BenchmarkScenarios.get_all_scenarios()
    
    for complexity in TaskComplexity:
        scenarios = BenchmarkScenarios.get_by_complexity(complexity)
        print(f"\n{complexity.value.upper()} SCENARIOS ({len(scenarios)} total):")
        
        for scenario in scenarios:
            print(f"  {scenario.scenario_id}: {scenario.name}")
            print(f"    Expected tools: {len(scenario.expected_tools)} calls")
            print(f"    Validation criteria: {len(scenario.validation_criteria)} checks")
    
    print(f"\nTotal scenarios defined: {len(all_scenarios)}")
    print("Ready for benchmarking framework integration!")