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
import math
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import csv
from scipy import stats as scipy_stats


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
        self.results_dir = results_dir or Path(__file__).parent / "results"
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
        self.results_dir = results_dir or Path(__file__).parent / "results"
    
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
        
        # ── Statistical significance (Welch's t-test, no equal-variance assumption) ──
        t_stat, p_value = scipy_stats.ttest_ind(mcp_latencies, trad_latencies, equal_var=False)

        # 95% confidence interval for the mean difference (Welch-Satterthwaite)
        n1, n2 = mcp_stats['count'], trad_stats['count']
        se_diff = math.sqrt(mcp_stats['std'] ** 2 / n1 + trad_stats['std'] ** 2 / n2)
        diff_mean = mcp_stats['mean'] - trad_stats['mean']
        df_w = se_diff ** 4 / (
            (mcp_stats['std'] ** 2 / n1) ** 2 / (n1 - 1)
            + (trad_stats['std'] ** 2 / n2) ** 2 / (n2 - 1)
        )
        t_crit = scipy_stats.t.ppf(0.975, df=df_w)
        ci_diff_95 = (diff_mean - t_crit * se_diff, diff_mean + t_crit * se_diff)

        # 95% CI for each individual mean
        mcp_ci_95  = scipy_stats.t.interval(0.95, df=n1 - 1,
                                             loc=mcp_stats['mean'],
                                             scale=scipy_stats.sem(mcp_latencies))
        trad_ci_95 = scipy_stats.t.interval(0.95, df=n2 - 1,
                                             loc=trad_stats['mean'],
                                             scale=scipy_stats.sem(trad_latencies))

        # Cohen's d effect size
        pooled_std = math.sqrt((mcp_stats['std'] ** 2 + trad_stats['std'] ** 2) / 2)
        cohens_d   = diff_mean / pooled_std if pooled_std > 0 else 0.0
        effect_magnitude = (
            "small"  if abs(cohens_d) < 0.5 else
            "medium" if abs(cohens_d) < 0.8 else "large"
        )

        return {
            'mcp_latency_stats':        mcp_stats,
            'traditional_latency_stats': trad_stats,
            'protocol_overhead_pct':     overhead_pct,
            'mean_difference_ms':        diff_mean,
            # Statistical significance
            't_statistic':              round(t_stat, 4),
            'p_value':                  round(p_value, 6),
            'statistically_significant': p_value < 0.05,
            # Confidence intervals
            'mcp_ci_95':               (round(mcp_ci_95[0], 2),  round(mcp_ci_95[1], 2)),
            'trad_ci_95':              (round(trad_ci_95[0], 2), round(trad_ci_95[1], 2)),
            'diff_ci_95':              (round(ci_diff_95[0], 2), round(ci_diff_95[1], 2)),
            # Effect size
            'cohens_d':                round(cohens_d, 4),
            'effect_magnitude':        effect_magnitude,
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
    
    def generate_summary_report(self, session_files: List[str] = None) -> str:
        """Generate comprehensive analysis report from saved CSV files in results_dir."""

        # ── Discover CSV files ────────────────────────────────────────────────
        search_dir = self.results_dir
        perf_files = sorted(search_dir.glob("*_performance.csv"))
        acc_files  = sorted(search_dir.glob("*_accuracy.csv"))
        interop_files = sorted(search_dir.glob("*_interoperability.csv"))

        if not perf_files:
            return "No result CSVs found in " + str(search_dir) + ". Run the benchmark first."

        # ── Load and combine performance data ─────────────────────────────────
        perf_rows = []
        for f in perf_files:
            with open(f, newline='') as fh:
                perf_rows.extend(list(csv.DictReader(fh)))

        mcp_lat  = [float(r['total_latency_ms']) for r in perf_rows if r['protocol_type'] == 'mcp']
        trad_lat = [float(r['total_latency_ms']) for r in perf_rows if r['protocol_type'] == 'traditional']

        # ── Load accuracy data ────────────────────────────────────────────────
        acc_rows = []
        for f in acc_files:
            with open(f, newline='') as fh:
                acc_rows.extend(list(csv.DictReader(fh)))

        mcp_acc_rate  = (sum(1 for r in acc_rows if r['protocol_type'] == 'mcp' and r['task_completed'] == 'True')
                         / max(1, sum(1 for r in acc_rows if r['protocol_type'] == 'mcp')) * 100)
        trad_acc_rate = (sum(1 for r in acc_rows if r['protocol_type'] == 'traditional' and r['task_completed'] == 'True')
                         / max(1, sum(1 for r in acc_rows if r['protocol_type'] == 'traditional')) * 100)

        # ── Load interoperability data ────────────────────────────────────────
        interop_rows = []
        for f in interop_files:
            with open(f, newline='') as fh:
                interop_rows.extend(list(csv.DictReader(fh)))

        mcp_loc  = [int(r['code_changes_required']) for r in interop_rows if r['protocol_type'] == 'mcp']
        trad_loc = [int(r['code_changes_required']) for r in interop_rows if r['protocol_type'] == 'traditional']

        # ── Statistical significance (latency) ────────────────────────────────
        stat_section = "  Not enough data for statistical tests."
        if len(mcp_lat) >= 2 and len(trad_lat) >= 2:
            lat_analysis = self.analyze_rq2_latency(
                [type('P', (), {'total_latency_ms': v})() for v in mcp_lat],
                [type('P', (), {'total_latency_ms': v})() for v in trad_lat],
            )
            stat_section = (
                f"  Welch's t-test: t={lat_analysis['t_statistic']}, p={lat_analysis['p_value']}"
                f" ({'SIGNIFICANT' if lat_analysis['statistically_significant'] else 'not significant'} at α=0.05)\n"
                f"  Cohen's d: {lat_analysis['cohens_d']} ({lat_analysis['effect_magnitude']} effect)\n"
                f"  95% CI for MCP mean latency:  {lat_analysis['mcp_ci_95']} ms\n"
                f"  95% CI for Trad mean latency: {lat_analysis['trad_ci_95']} ms\n"
                f"  95% CI for difference:        {lat_analysis['diff_ci_95']} ms"
            )

        report = f"""\n"""\
            f"MCP vs Traditional Function Calling — Benchmarking Results\n"\
            f"==========================================================\n"\
            f"Analysis Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"\
            f"Sessions      : {len(perf_files)} performance files, {len(acc_files)} accuracy files\n"\
            f"Total trials  : {len(perf_rows)} performance records, {len(acc_rows)} accuracy records\n\n"\
            f"RQ1 — Interoperability\n"\
            f"  MCP  lines to swap provider: {statistics.mean(mcp_loc)  if mcp_loc  else 'n/a'}\n"\
            f"  Trad lines to swap provider: {statistics.mean(trad_loc) if trad_loc else 'n/a'}\n\n"\
            f"RQ2 — Latency\n"\
            f"  MCP  mean latency : {statistics.mean(mcp_lat):.1f} ms (n={len(mcp_lat)})\n"\
            f"  Trad mean latency : {statistics.mean(trad_lat):.1f} ms (n={len(trad_lat)})\n"\
            f"  Protocol overhead : {((statistics.mean(mcp_lat)-statistics.mean(trad_lat))/statistics.mean(trad_lat)*100):.1f}%\n"\
            f"{stat_section}\n\n"\
            f"RQ3 — Accuracy\n"\
            f"  MCP  task-completion rate: {mcp_acc_rate:.1f}%\n"\
            f"  Trad task-completion rate: {trad_acc_rate:.1f}%\n"
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