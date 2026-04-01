"""
Metrics Collection Framework for MCP vs Traditional Function Calling Benchmarking
Implements RQ1, RQ2, RQ3 measurement infrastructure with statistical analysis

This module provides:
- Performance metrics collection (RQ2: Latency)  
- Interoperability assessment (RQ1: Cross-LLM compatibility)
- Accuracy measurement (RQ3: Task completion reliability)
- Statistical analysis and reporting
"""

import time
import json
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import csv


@dataclass
class PerformanceMetrics:
    """RQ2: Latency and throughput measurements"""
    protocol_type: str          # "mcp" or "traditional"
    scenario_id: str           # Test scenario identifier
    iteration: int             # Test iteration number
    total_latency_ms: float    # End-to-end response time
    protocol_overhead_ms: float # Protocol-specific overhead
    token_count: int           # Approximate token usage  
    tools_called: int          # Number of tool invocations
    timestamp: str             # When the test was run
    
    @property
    def latency_per_tool(self) -> float:
        """Average latency per tool call"""
        return self.total_latency_ms / max(1, self.tools_called)


@dataclass 
class InteroperabilityMetrics:
    """RQ1: Cross-LLM compatibility measurements"""
    protocol_type: str         # "mcp" or "traditional"
    llm_provider: str         # "claude_3.5" or "gpt4o"
    scenario_id: str          # Test scenario
    code_changes_required: int # Lines of code needed to port (0 = perfect compatibility)
    setup_complexity: int     # Setup steps required (1-10 scale)
    config_changes: int       # Configuration modifications needed
    compatibility_score: float # Overall compatibility (0-1 scale)
    notes: str                # Qualitative observations


@dataclass
class AccuracyMetrics:
    """RQ3: Task completion and correctness measurements"""
    protocol_type: str         # "mcp" or "traditional" 
    llm_provider: str         # Model used
    scenario_id: str          # Test scenario
    iteration: int            # Test iteration
    task_completed: bool      # Successfully finished the task
    correct_tool_selection: bool # Selected appropriate tools
    parameter_accuracy: float  # Correct parameter usage (0-1)
    result_correctness: float  # Final result accuracy (0-1)
    hallucination_detected: bool # False tool calls or data
    error_recovery: bool      # Recovered from errors gracefully
    validation_scores: Dict[str, bool] # Scenario-specific validation results


@dataclass
class BenchmarkSession:
    """Container for a complete benchmarking run"""
    session_id: str
    start_time: str
    end_time: Optional[str]
    protocol_type: str
    llm_provider: str
    iterations_per_scenario: int
    scenarios_tested: List[str]
    performance_results: List[PerformanceMetrics]
    interop_results: List[InteroperabilityMetrics]  
    accuracy_results: List[AccuracyMetrics]


class MetricsCollector:
    """Central metrics collection and analysis system"""
    
    def __init__(self, results_dir: Path = None):
        self.results_dir = results_dir or Path("benchmark/results")
        self.results_dir.mkdir(exist_ok=True)
        self.current_session: Optional[BenchmarkSession] = None
    
    def start_session(self, protocol_type: str, llm_provider: str, 
                     iterations: int = 100) -> str:
        """Start a new benchmarking session"""
        session_id = f"{protocol_type}_{llm_provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = BenchmarkSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            end_time=None,
            protocol_type=protocol_type,
            llm_provider=llm_provider,
            iterations_per_scenario=iterations,
            scenarios_tested=[],
            performance_results=[],
            interop_results=[],
            accuracy_results=[]
        )
        
        print(f"Started benchmarking session: {session_id}")
        return session_id
    
    def record_performance(self, scenario_id: str, iteration: int,
                          total_latency_ms: float, protocol_overhead_ms: float,
                          token_count: int, tools_called: int) -> PerformanceMetrics:
        """Record performance metrics for RQ2 analysis"""
        
        metrics = PerformanceMetrics(
            protocol_type=self.current_session.protocol_type,
            scenario_id=scenario_id,
            iteration=iteration,
            total_latency_ms=total_latency_ms,
            protocol_overhead_ms=protocol_overhead_ms,
            token_count=token_count,
            tools_called=tools_called,
            timestamp=datetime.now().isoformat()
        )
        
        self.current_session.performance_results.append(metrics)
        return metrics
    
    def record_interoperability(self, scenario_id: str, code_changes: int,
                               setup_complexity: int, config_changes: int,
                               notes: str = "") -> InteroperabilityMetrics:
        """Record interoperability metrics for RQ1 analysis"""
        
        # Calculate compatibility score (higher is better)
        compatibility_score = 1.0 - (
            (code_changes * 0.4) + 
            (setup_complexity * 0.1) + 
            (config_changes * 0.05)
        )
        compatibility_score = max(0.0, min(1.0, compatibility_score))
        
        metrics = InteroperabilityMetrics(
            protocol_type=self.current_session.protocol_type,
            llm_provider=self.current_session.llm_provider,
            scenario_id=scenario_id,
            code_changes_required=code_changes,
            setup_complexity=setup_complexity,
            config_changes=config_changes,
            compatibility_score=compatibility_score,
            notes=notes
        )
        
        self.current_session.interop_results.append(metrics)
        return metrics
    
    def record_accuracy(self, scenario_id: str, iteration: int,
                       task_completed: bool, correct_tools: bool,
                       param_accuracy: float, result_correctness: float,
                       hallucination: bool, error_recovery: bool,
                       validation_scores: Dict[str, bool]) -> AccuracyMetrics:
        """Record accuracy metrics for RQ3 analysis"""
        
        metrics = AccuracyMetrics(
            protocol_type=self.current_session.protocol_type,
            llm_provider=self.current_session.llm_provider,
            scenario_id=scenario_id,
            iteration=iteration,
            task_completed=task_completed,
            correct_tool_selection=correct_tools,
            parameter_accuracy=param_accuracy,
            result_correctness=result_correctness,
            hallucination_detected=hallucination,
            error_recovery=error_recovery,
            validation_scores=validation_scores
        )
        
        self.current_session.accuracy_results.append(metrics)
        return metrics
    
    def end_session(self) -> BenchmarkSession:
        """Finalize current session and save results"""
        if not self.current_session:
            raise ValueError("No active session to end")
        
        self.current_session.end_time = datetime.now().isoformat()
        self._save_session_results()
        
        completed_session = self.current_session
        self.current_session = None
        
        return completed_session
    
    def _save_session_results(self):
        """Save session results to CSV files"""
        session = self.current_session
        base_filename = f"{session.session_id}"
        
        # Save performance metrics  
        perf_file = self.results_dir / f"{base_filename}_performance.csv"
        with open(perf_file, 'w', newline='') as f:
            if session.performance_results:
                writer = csv.DictWriter(f, fieldnames=list(asdict(session.performance_results[0]).keys()))
                writer.writeheader()
                for result in session.performance_results:
                    writer.writerow(asdict(result))
        
        # Save interoperability metrics
        interop_file = self.results_dir / f"{base_filename}_interoperability.csv"  
        with open(interop_file, 'w', newline='') as f:
            if session.interop_results:
                writer = csv.DictWriter(f, fieldnames=list(asdict(session.interop_results[0]).keys()))
                writer.writeheader()
                for result in session.interop_results:
                    writer.writerow(asdict(result))
        
        # Save accuracy metrics
        accuracy_file = self.results_dir / f"{base_filename}_accuracy.csv"
        with open(accuracy_file, 'w', newline='') as f:
            if session.accuracy_results:
                # Handle nested validation_scores dict
                fieldnames = [f for f in asdict(session.accuracy_results[0]).keys() if f != 'validation_scores']
                fieldnames.append('validation_scores_json')
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in session.accuracy_results:
                    row = asdict(result)
                    row['validation_scores_json'] = json.dumps(row.pop('validation_scores'))
                    writer.writerow(row)
        
        print(f"Session results saved to {self.results_dir}")


class StatisticalAnalyzer:
    """Statistical analysis of benchmark results for research conclusions"""
    
    def __init__(self, results_dir: Path = None):
        self.results_dir = results_dir or Path("benchmark/results")
    
    def analyze_rq2_latency(self, mcp_results: List[PerformanceMetrics], 
                           traditional_results: List[PerformanceMetrics]) -> Dict[str, Any]:
        """
        RQ2: Statistical analysis of latency differences between MCP and traditional
        Returns significance tests, effect sizes, and confidence intervals
        """
        
        mcp_latencies = [r.total_latency_ms for r in mcp_results]
        trad_latencies = [r.total_latency_ms for r in traditional_results]
        
        # Descriptive statistics
        mcp_stats = {
            'mean': statistics.mean(mcp_latencies),
            'std': statistics.stdev(mcp_latencies),
            'median': statistics.median(mcp_latencies),
            'count': len(mcp_latencies)
        }
        
        trad_stats = {
            'mean': statistics.mean(trad_latencies), 
            'std': statistics.stdev(trad_latencies),
            'median': statistics.median(trad_latencies),
            'count': len(trad_latencies)
        }
        
        # Calculate protocol overhead
        overhead_pct = ((mcp_stats['mean'] - trad_stats['mean']) / trad_stats['mean']) * 100
        
        return {
            'mcp_latency_stats': mcp_stats,
            'traditional_latency_stats': trad_stats,
            'protocol_overhead_pct': overhead_pct,
            'mean_difference_ms': mcp_stats['mean'] - trad_stats['mean'],
            # TODO: Add t-test, confidence intervals, effect size calculations
        }
    
    def analyze_rq1_interoperability(self, results: List[InteroperabilityMetrics]) -> Dict[str, Any]:
        """
        RQ1: Analysis of cross-LLM compatibility scores
        """
        
        mcp_results = [r for r in results if r.protocol_type == "mcp"]
        trad_results = [r for r in results if r.protocol_type == "traditional"]
        
        analysis = {}
        
        if mcp_results:
            mcp_scores = [r.compatibility_score for r in mcp_results]
            analysis['mcp_compatibility'] = {
                'mean_score': statistics.mean(mcp_scores),
                'std': statistics.stdev(mcp_scores) if len(mcp_scores) > 1 else 0,
                'perfect_compatibility_rate': sum(1 for s in mcp_scores if s >= 0.95) / len(mcp_scores)
            }
        
        if trad_results:
            trad_scores = [r.compatibility_score for r in trad_results]
            analysis['traditional_compatibility'] = {
                'mean_score': statistics.mean(trad_scores),
                'std': statistics.stdev(trad_scores) if len(trad_scores) > 1 else 0,
                'perfect_compatibility_rate': sum(1 for s in trad_scores if s >= 0.95) / len(trad_scores)
            }
        
        return analysis
    
    def analyze_rq3_accuracy(self, results: List[AccuracyMetrics]) -> Dict[str, Any]:
        """
        RQ3: Analysis of task completion accuracy and reliability
        """
        
        mcp_results = [r for r in results if r.protocol_type == "mcp"]
        trad_results = [r for r in results if r.protocol_type == "traditional"]
        
        def calculate_accuracy_stats(result_set):
            if not result_set:
                return {}
                
            return {
                'task_completion_rate': sum(1 for r in result_set if r.task_completed) / len(result_set),
                'tool_selection_accuracy': sum(1 for r in result_set if r.correct_tool_selection) / len(result_set),
                'parameter_accuracy_avg': statistics.mean([r.parameter_accuracy for r in result_set]),
                'result_correctness_avg': statistics.mean([r.result_correctness for r in result_set]),
                'hallucination_rate': sum(1 for r in result_set if r.hallucination_detected) / len(result_set),
                'error_recovery_rate': sum(1 for r in result_set if r.error_recovery) / len(result_set),
                'sample_size': len(result_set)
            }
        
        return {
            'mcp_accuracy': calculate_accuracy_stats(mcp_results),
            'traditional_accuracy': calculate_accuracy_stats(trad_results)
        }
    
    def generate_summary_report(self, session_files: List[str]) -> str:
        """Generate comprehensive analysis report from multiple sessions"""
        
        # TODO: Load and combine multiple CSV files
        # TODO: Perform cross-session statistical analysis
        # TODO: Generate research conclusions
        
        report = f"""
        MCP vs Traditional Function Calling - Benchmarking Results
        ========================================================
        
        Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        RQ1: Interoperability Analysis
        - MCP provides X% better cross-LLM compatibility
        - Code changes required: MCP avg vs Traditional avg
        
        RQ2: Performance Analysis  
        - Protocol overhead: X.X% latency increase
        - Statistical significance: p < 0.05 (or not significant)
        
        RQ3: Accuracy Analysis
        - Task completion rates: MCP X.X% vs Traditional X.X%
        - Tool selection accuracy comparison
        
        Conclusions and Recommendations:
        - [Research findings based on statistical analysis]
        """
        
        return report


if __name__ == "__main__":
    # Test metrics collection system
    print("Testing MCP Benchmarking Metrics Collection")
    print("=" * 50)
    
    # Create test collector
    collector = MetricsCollector()
    
    # Simulate a benchmarking session
    session_id = collector.start_session(protocol_type="mcp", llm_provider="claude_3.5")
    
    # Record some test metrics
    collector.record_performance("S1", 1, 150.5, 25.0, 100, 1)
    collector.record_performance("S1", 2, 145.2, 22.5, 98, 1)
    
    collector.record_interoperability("S1", code_changes=0, setup_complexity=2, 
                                     config_changes=1, notes="Zero code changes required")
    
    collector.record_accuracy("S1", 1, task_completed=True, correct_tools=True,
                             param_accuracy=1.0, result_correctness=0.95,
                             hallucination=False, error_recovery=True,
                             validation_scores={"contains_moisture_pct": True})
    
    # End session and save
    session = collector.end_session()
    
    print(f"Test session completed: {session.session_id}")
    print(f"Performance results: {len(session.performance_results)}")
    print(f"Interoperability results: {len(session.interop_results)}")
    print(f"Accuracy results: {len(session.accuracy_results)}")
    
    print("\nMetrics collection framework ready for benchmarking!")
    print("Next steps:")
    print("1. Integrate with MCP server and traditional baseline")
    print("2. Add actual LLM provider connections") 
    print("3. Implement automated test runner")
    print("4. Add statistical significance testing")