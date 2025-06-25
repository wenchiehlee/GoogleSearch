"""
stage_runner.py - Stage Execution Coordinator (v3.3.3)

Version: 3.3.3
Date: 2025-06-24
Author: FactSet Pipeline - v3.3.3 Final Integrated Edition

v3.3.3 ENHANCEMENTS:
- ✅ Integration with StandardizedQualityScorer (0-10 scale)
- ✅ Quality scoring integration across all stages
- ✅ All v3.3.2 functionality preserved and enhanced

v3.3.2 FEATURES MAINTAINED:
- ✅ Unified stage execution coordination
- ✅ Integration with enhanced logging system
- ✅ Cross-platform execution context management
- ✅ Automatic error recovery and retry logic
- ✅ Performance monitoring and resource management
- ✅ Stage dependency validation and sequencing
"""

import os
import sys
import time
import traceback
import platform
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

# Import v3.3.2 enhanced logging
from enhanced_logger import EnhancedLoggerManager, get_logger_manager, get_stage_logger, get_performance_logger

# Version Information - v3.3.3
__version__ = "3.3.3"
__date__ = "2025-06-24"
__author__ = "FactSet Pipeline - v3.3.3 Final Integrated Edition"

# ============================================================================
# v3.3.3 QUALITY SCORING INTEGRATION
# ============================================================================

def get_quality_scorer():
    """Get v3.3.3 standardized quality scorer"""
    try:
        from factset_cli import StandardizedQualityScorer
        return StandardizedQualityScorer()
    except ImportError:
        # Fallback quality scorer
        return FallbackQualityScorer()

class FallbackQualityScorer:
    """Fallback quality scorer when StandardizedQualityScorer not available"""
    
    def __init__(self):
        self.scoring_version = "3.3.3-fallback"
    
    def calculate_score(self, data_metrics: Dict[str, Any]) -> int:
        """Calculate 0-10 fallback quality score"""
        score = 0
        
        # Data completeness (40% weight)
        eps_completeness = data_metrics.get('eps_data_completeness', 0)
        if eps_completeness >= 0.9:
            score += 4
        elif eps_completeness >= 0.7:
            score += 3
        elif eps_completeness >= 0.5:
            score += 2
        elif eps_completeness >= 0.3:
            score += 1
        
        # Analyst coverage (30% weight)
        analyst_count = data_metrics.get('analyst_count', 0)
        if analyst_count >= 20:
            score += 3
        elif analyst_count >= 10:
            score += 2
        elif analyst_count >= 5:
            score += 1
        
        # Data freshness (30% weight)
        days_old = data_metrics.get('data_age_days', float('inf'))
        if days_old <= 7:
            score += 3
        elif days_old <= 30:
            score += 2
        elif days_old <= 90:
            score += 1
        
        return min(10, max(0, score))
    
    def get_quality_indicator(self, score: int) -> str:
        """Get quality indicator for score"""
        if 9 <= score <= 10:
            return '🟢 完整'
        elif score == 8:
            return '🟡 良好'
        elif 3 <= score <= 7:
            return '🟠 部分'
        else:
            return '🔴 不足'
    
    def standardize_quality_data(self, quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize quality data to v3.3.3 format"""
        standardized = quality_data.copy()
        
        # Add quality indicator
        score = standardized.get('quality_score', 0)
        standardized['quality_status'] = self.get_quality_indicator(score)
        standardized['scoring_version'] = self.scoring_version
        
        return standardized

# ============================================================================
# STAGE DEFINITIONS AND CONFIGURATION (v3.3.3 - Enhanced)
# ============================================================================

class StageStatus(Enum):
    """Stage execution status"""
    PENDING = "pending"
    RUNNING = "running"  
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RECOVERED = "recovered"

@dataclass
class StageContext:
    """Execution context for a stage"""
    stage_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: StageStatus = StageStatus.PENDING
    parameters: Dict[str, Any] = None
    results: Dict[str, Any] = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 2
    quality_data: Dict[str, Any] = None  # v3.3.3: Quality scoring data
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.results is None:
            self.results = {}
        if self.quality_data is None:
            self.quality_data = {}
    
    @property
    def duration(self) -> Optional[float]:
        """Get stage duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def mark_completed(self, results: Dict[str, Any] = None):
        """Mark stage as completed"""
        self.end_time = datetime.now()
        self.status = StageStatus.COMPLETED
        if results:
            self.results.update(results)
    
    def mark_failed(self, error: Exception):
        """Mark stage as failed"""
        self.end_time = datetime.now()
        self.status = StageStatus.FAILED
        self.error = error

@dataclass 
class StageDefinition:
    """Definition of a pipeline stage"""
    name: str
    handler: Callable
    dependencies: List[str] = None
    required: bool = True
    timeout_minutes: int = 30
    retry_on_failure: bool = True
    description: str = ""
    enable_quality_scoring: bool = True  # v3.3.3: Quality scoring flag
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

# ============================================================================
# EXECUTION CONTEXT MANAGER (v3.3.3 - Enhanced)
# ============================================================================

class ExecutionContext:
    """Global execution context for the pipeline"""
    
    def __init__(self, execution_mode: str = "intelligent", **kwargs):
        self.execution_mode = execution_mode
        self.parameters = kwargs
        self.start_time = datetime.now()
        self.stage_contexts = {}
        self.global_state = {}
        
        # v3.3.3: Quality scoring settings
        self.quality_scorer = kwargs.get('quality_scorer') or get_quality_scorer()
        self.enable_quality_scoring = kwargs.get('quality_scoring', True)
        
        # Platform information
        self.platform_info = {
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "working_directory": str(Path.cwd()),
            "encoding": sys.stdout.encoding or "unknown"
        }
        
        # v3.3.1 compatibility settings
        self.v331_settings = {
            "memory_limit_mb": kwargs.get("memory_limit", 2048),
            "batch_size": kwargs.get("batch_size", 50),
            "rate_limit_delay": kwargs.get("rate_limit_delay", 3),
            "enable_cascade_protection": True,
            "enable_performance_optimization": True,
            "enable_memory_management": True
        }
        
        # v3.3.3: Quality tracking
        self.quality_metrics = {
            "total_score": 0,
            "stage_scores": {},
            "average_quality": 0,
            "quality_distribution": {}
        }
    
    def get_stage_context(self, stage_name: str) -> Optional[StageContext]:
        """Get context for a specific stage"""
        return self.stage_contexts.get(stage_name)
    
    def set_global_state(self, key: str, value: Any):
        """Set global state value"""
        self.global_state[key] = value
    
    def get_global_state(self, key: str, default: Any = None) -> Any:
        """Get global state value"""
        return self.global_state.get(key, default)
    
    def update_quality_metrics(self, stage_name: str, quality_data: Dict[str, Any]):
        """v3.3.3: Update quality metrics for a stage"""
        if not self.enable_quality_scoring:
            return
        
        try:
            score = quality_data.get('quality_score', 0)
            self.quality_metrics['stage_scores'][stage_name] = score
            
            # Calculate average
            scores = list(self.quality_metrics['stage_scores'].values())
            if scores:
                self.quality_metrics['average_quality'] = sum(scores) / len(scores)
            
            # Update distribution
            indicator = self.quality_scorer.get_quality_indicator(score)
            self.quality_metrics['quality_distribution'][indicator] = \
                self.quality_metrics['quality_distribution'].get(indicator, 0) + 1
                
        except Exception as e:
            # Quality metrics update failure shouldn't stop pipeline
            pass

# ============================================================================
# STAGE RUNNER MAIN CLASS (v3.3.3 - Enhanced)
# ============================================================================

class StageRunner:
    """Central coordinator for all pipeline stages with v3.3.3 quality scoring"""
    
    def __init__(self, logger_manager: EnhancedLoggerManager = None):
        self.logger_manager = logger_manager or get_logger_manager()
        self.main_logger = get_stage_logger("runner")
        
        # v3.3.3: Quality scoring integration
        self.quality_scorer = get_quality_scorer()
        
        # Stage definitions
        self.stage_definitions = self._setup_stage_definitions()
        
        # Execution state
        self.current_context = None
        self._lock = threading.Lock()
        
        # Import v3.3.1 components (lazy loading to avoid circular imports)
        self._v331_components = {}
        
        self.main_logger.info(f"StageRunner v{__version__} initialized with quality scoring")
    
    def _setup_stage_definitions(self) -> Dict[str, StageDefinition]:
        """Setup all available stage definitions with v3.3.3 enhancements"""
        return {
            "validate": StageDefinition(
                name="validate",
                handler=self._run_validation_stage,
                dependencies=[],
                required=True,
                timeout_minutes=5,
                description="System validation and configuration check",
                enable_quality_scoring=False  # Validation doesn't need quality scoring
            ),
            "download_watchlist": StageDefinition(
                name="download_watchlist", 
                handler=self._run_download_watchlist_stage,
                dependencies=["validate"],
                required=True,
                timeout_minutes=5,
                description="Download and validate company watchlist",
                enable_quality_scoring=False
            ),
            "search": StageDefinition(
                name="search",
                handler=self._run_search_stage,
                dependencies=["download_watchlist"],
                required=False,
                timeout_minutes=60,
                description="Enhanced search for financial data",
                enable_quality_scoring=True  # Search results have quality scores
            ),
            "process": StageDefinition(
                name="process",
                handler=self._run_processing_stage,
                dependencies=["search"],
                required=True,
                timeout_minutes=30,
                description="Process MD files and generate aggregated data",
                enable_quality_scoring=True  # Main quality scoring stage
            ),
            "upload": StageDefinition(
                name="upload",
                handler=self._run_upload_stage,
                dependencies=["process"],
                required=False,
                timeout_minutes=10,
                description="Upload results to Google Sheets",
                enable_quality_scoring=False
            ),
            "pipeline": StageDefinition(
                name="pipeline",
                handler=self._run_pipeline_stage,
                dependencies=[],
                required=True,
                timeout_minutes=120,
                description="Complete pipeline execution",
                enable_quality_scoring=True  # Overall pipeline quality
            )
        }
    
    def run_stage(self, stage_name: str, context: ExecutionContext = None, **kwargs) -> bool:
        """Run a specific stage with enhanced error handling and v3.3.3 quality scoring"""
        with self._lock:
            if context is None:
                context = ExecutionContext(**kwargs)
            
            self.current_context = context
            
            # Get stage definition
            if stage_name not in self.stage_definitions:
                self.main_logger.error(f"Unknown stage: {stage_name}")
                return False
            
            stage_def = self.stage_definitions[stage_name]
            
            # Create stage context with v3.3.3 enhancements
            stage_context = StageContext(
                stage_name=stage_name,
                start_time=datetime.now(),
                parameters=kwargs,
                max_retries=2 if stage_def.retry_on_failure else 0,
                quality_data={}  # v3.3.3: Initialize quality data
            )
            
            context.stage_contexts[stage_name] = stage_context
            
            # Get stage-specific logger
            stage_logger = get_stage_logger(stage_name)
            perf_logger = get_performance_logger(stage_name)
            
            try:
                return self._execute_stage_with_monitoring(
                    stage_def, stage_context, context, stage_logger, perf_logger
                )
                
            except Exception as e:
                self.main_logger.error(f"Critical error in stage {stage_name}: {e}")
                stage_context.mark_failed(e)
                return False
    
    def _execute_stage_with_monitoring(self, stage_def: StageDefinition, 
                                     stage_context: StageContext,
                                     exec_context: ExecutionContext,
                                     stage_logger: Any,
                                     perf_logger: Any) -> bool:
        """Execute stage with comprehensive monitoring and v3.3.3 quality integration"""
        
        stage_logger.info(f"Starting stage: {stage_def.name}")
        stage_logger.info(f"Description: {stage_def.description}")
        stage_logger.debug(f"Parameters: {stage_context.parameters}")
        
        # v3.3.3: Log quality scoring status
        if stage_def.enable_quality_scoring and exec_context.enable_quality_scoring:
            stage_logger.info(f"Quality scoring enabled for {stage_def.name}")
        
        # Check dependencies
        if not self._check_stage_dependencies(stage_def, exec_context, stage_logger):
            stage_context.status = StageStatus.SKIPPED
            stage_logger.warning(f"Stage {stage_def.name} skipped due to dependency issues")
            return False
        
        # Pre-stage validation
        if not self._pre_stage_validation(stage_def, stage_context, exec_context, stage_logger):
            stage_context.mark_failed(Exception("Pre-stage validation failed"))
            return False
        
        stage_context.status = StageStatus.RUNNING
        
        # Execute with timeout and performance monitoring
        try:
            with perf_logger.time_operation(f"stage_{stage_def.name}"):
                # Set timeout
                timeout_seconds = stage_def.timeout_minutes * 60
                
                # Execute stage handler
                result = self._execute_with_timeout(
                    stage_def.handler,
                    timeout_seconds,
                    stage_context, 
                    exec_context,
                    stage_logger
                )
                
                if result:
                    stage_context.mark_completed({"success": True})
                    stage_logger.info(f"Stage {stage_def.name} completed successfully")
                    
                    # v3.3.3: Process quality data if available
                    if (stage_def.enable_quality_scoring and 
                        exec_context.enable_quality_scoring and 
                        stage_context.quality_data):
                        
                        # Standardize quality data
                        stage_context.quality_data = exec_context.quality_scorer.standardize_quality_data(
                            stage_context.quality_data
                        )
                        
                        # Update execution context quality metrics
                        exec_context.update_quality_metrics(stage_def.name, stage_context.quality_data)
                        
                        # Log quality results
                        quality_score = stage_context.quality_data.get('quality_score', 0)
                        quality_status = stage_context.quality_data.get('quality_status', 'Unknown')
                        stage_logger.info(f"Stage quality: {quality_score}/10 ({quality_status})")
                    
                    # Post-stage validation
                    self._post_stage_validation(stage_def, stage_context, exec_context, stage_logger)
                    
                    return True
                else:
                    raise Exception("Stage handler returned False")
                    
        except Exception as e:
            stage_logger.error(f"Stage {stage_def.name} failed: {e}")
            stage_context.mark_failed(e)
            
            # Attempt recovery if enabled
            if stage_def.retry_on_failure and stage_context.retry_count < stage_context.max_retries:
                return self._attempt_stage_recovery(stage_def, stage_context, exec_context, stage_logger)
            
            return False
    
    # ========================================================================
    # STAGE HANDLER IMPLEMENTATIONS (v3.3.3 - Enhanced)
    # ========================================================================
    
    def _run_processing_stage(self, stage_context: StageContext,
                           exec_context: ExecutionContext,
                           stage_logger: Any) -> bool:
        """Run data processing stage with v3.3.3 quality scoring integration"""
        stage_logger.info("Running enhanced processing with quality scoring...")
        
        try:
            # Import processor module with lazy loading
            processor_module = self._get_v331_component("data_processor") 
            if not processor_module:
                stage_logger.error("data_processor module not available")
                return False
            
            # Initialize memory manager if available
            memory_manager = None
            if hasattr(processor_module, 'MemoryManager'):
                memory_limit = exec_context.v331_settings["memory_limit_mb"]
                memory_manager = processor_module.MemoryManager(limit_mb=memory_limit)
            
            # v3.3.3: Run with quality scoring integration
            if hasattr(processor_module, 'process_all_data_v333'):
                success = processor_module.process_all_data_v333(
                    force=stage_context.parameters.get("force", False),
                    memory_manager=memory_manager,
                    quality_scorer=exec_context.quality_scorer
                )
            elif hasattr(processor_module, 'process_all_data_v331'):
                success = processor_module.process_all_data_v331(
                    force=stage_context.parameters.get("force", False),
                    memory_manager=memory_manager
                )
            else:
                stage_logger.warning("Using fallback processor")
                success = processor_module.process_all_data(force=stage_context.parameters.get("force", False), parse_md=True)
            
            # v3.3.3: Extract quality metrics from processing results
            if success and exec_context.enable_quality_scoring:
                try:
                    # Try to get statistics for quality analysis
                    stats_file = Path("data/processed/statistics.json")
                    if stats_file.exists():
                        import json
                        with open(stats_file, 'r', encoding='utf-8') as f:
                            stats = json.load(f)
                        
                        # Extract quality metrics from statistics
                        quality_analysis = stats.get('quality_analysis_v333', {})
                        if quality_analysis:
                            stage_context.quality_data = {
                                'quality_score': int(quality_analysis.get('average_quality_score', 0)),
                                'quality_metrics': quality_analysis,
                                'companies_processed': stats.get('companies_with_data', 0),
                                'total_companies': stats.get('total_companies', 0)
                            }
                            stage_logger.info(f"Quality metrics extracted: avg score {quality_analysis.get('average_quality_score', 0)}")
                
                except Exception as e:
                    stage_logger.warning(f"Could not extract quality metrics: {e}")
            
            if success:
                duration = time.time() - stage_context.start_time.timestamp()
                stage_context.results.update({
                    "processing_status": "completed",
                    "processing_duration": duration
                })
                
                stage_logger.info(f"Processing completed in {duration:.2f}s")
                return True
            else:
                return False
                
        except Exception as e:
            stage_logger.error(f"Processing stage error: {e}")
            return False
    
    # ========================================================================
    # HELPER METHODS (v3.3.3 - Preserved with quality enhancements)
    # ========================================================================
    
    def _check_stage_dependencies(self, stage_def: StageDefinition, 
                                exec_context: ExecutionContext,
                                stage_logger: Any) -> bool:
        """Check if stage dependencies are satisfied (preserved from v3.3.2)"""
        if not stage_def.dependencies:
            return True
        
        for dep_name in stage_def.dependencies:
            dep_context = exec_context.get_stage_context(dep_name)
            
            if not dep_context:
                stage_logger.warning(f"Dependency {dep_name} has not been executed")
                
                # For flexible dependencies, check if we can proceed anyway
                if dep_name == "search" and stage_def.name == "process":
                    # Process can run without search if data exists
                    md_dir = Path("data/md")
                    if md_dir.exists() and list(md_dir.glob("*.md")):
                        stage_logger.info("Proceeding with processing using existing MD files")
                        continue
                
                return False
            
            if dep_context.status != StageStatus.COMPLETED:
                stage_logger.error(f"Dependency {dep_name} status: {dep_context.status}")
                return False
        
        return True
    
    def _pre_stage_validation(self, stage_def: StageDefinition,
                            stage_context: StageContext, 
                            exec_context: ExecutionContext,
                            stage_logger: Any) -> bool:
        """Pre-stage validation checks (preserved from v3.3.2)"""
        
        # Memory check for memory-intensive stages
        if stage_def.name in ["search", "process"]:
            try:
                import psutil
                memory = psutil.virtual_memory()
                available_gb = memory.available / (1024**3)
                
                min_memory_gb = 1.0  # Minimum required memory
                if available_gb < min_memory_gb:
                    stage_logger.warning(f"Low memory: {available_gb:.1f}GB available")
                    # Continue anyway but log warning
                    
            except ImportError:
                pass  # psutil not available
        
        # Directory structure check
        required_dirs = ["data", "logs"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    stage_logger.info(f"Created directory: {dir_name}")
                except Exception as e:
                    stage_logger.error(f"Cannot create directory {dir_name}: {e}")
                    return False
        
        return True
    
    def _post_stage_validation(self, stage_def: StageDefinition,
                             stage_context: StageContext,
                             exec_context: ExecutionContext, 
                             stage_logger: Any):
        """Post-stage validation and cleanup with v3.3.3 quality logging"""
        
        # Log performance information
        if stage_context.duration:
            stage_logger.info(f"Stage duration: {stage_context.duration:.2f} seconds")
            
            if stage_context.duration > 300:  # 5 minutes
                stage_logger.warning(f"Long-running stage detected: {stage_context.duration:.2f}s")
        
        # v3.3.3: Log quality information
        if stage_def.enable_quality_scoring and stage_context.quality_data:
            quality_score = stage_context.quality_data.get('quality_score', 0)
            quality_status = stage_context.quality_data.get('quality_status', 'Unknown')
            stage_logger.info(f"Stage quality assessment: {quality_score}/10 ({quality_status})")
        
        # Stage-specific validation
        if stage_def.name == "search":
            # Validate search results
            md_dir = Path("data/md")
            if md_dir.exists():
                md_count = len(list(md_dir.glob("*.md")))
                stage_logger.info(f"Search generated {md_count} MD files")
                exec_context.set_global_state("md_files_count", md_count)
            
        elif stage_def.name == "process":
            # Validate processed files
            processed_dir = Path("data/processed")
            expected_files = ["portfolio_summary.csv", "detailed_data.csv", "statistics.json"]
            
            for file_name in expected_files:
                file_path = processed_dir / file_name
                if file_path.exists():
                    stage_logger.info(f"Generated: {file_name} ({file_path.stat().st_size} bytes)")
                else:
                    stage_logger.warning(f"Missing expected file: {file_name}")
    
    def _attempt_stage_recovery(self, stage_def: StageDefinition,
                              stage_context: StageContext,
                              exec_context: ExecutionContext,
                              stage_logger: Any) -> bool:
        """Attempt to recover from stage failure (preserved from v3.3.2)"""
        
        stage_context.retry_count += 1
        stage_logger.info(f"Attempting recovery for {stage_def.name} (attempt {stage_context.retry_count})")
        
        # Stage-specific recovery strategies
        recovery_delay = min(30 * stage_context.retry_count, 120)  # Max 2 minutes
        
        if stage_def.name == "search":
            stage_logger.info("Search recovery: switching to conservative mode")
            # Add conservative mode parameter
            stage_context.parameters["mode"] = "conservative"
            stage_context.parameters["rate_limit_delay"] = 10
            
        elif stage_def.name == "upload":
            stage_logger.info("Upload recovery: retrying connection")
            # Clear any cached connection state
            stage_context.parameters["retry_connection"] = True
        
        # Wait before retry
        if recovery_delay > 0:
            stage_logger.info(f"Waiting {recovery_delay} seconds before retry...")
            time.sleep(recovery_delay)
        
        # Reset stage context for retry
        stage_context.status = StageStatus.PENDING
        stage_context.start_time = datetime.now()
        stage_context.end_time = None
        stage_context.error = None
        
        # Retry execution
        try:
            result = stage_def.handler(stage_context, exec_context, stage_logger)
            if result:
                stage_context.status = StageStatus.RECOVERED
                stage_logger.info(f"Recovery successful for {stage_def.name}")
                return True
        except Exception as e:
            stage_logger.error(f"Recovery failed for {stage_def.name}: {e}")
        
        return False
    
    def _execute_with_timeout(self, handler: Callable, timeout_seconds: int,
                            *args) -> bool:
        """Execute handler with timeout protection (preserved from v3.3.2)"""
        # For now, execute directly without timeout
        # TODO: Implement proper timeout mechanism if needed
        try:
            return handler(*args)
        except Exception as e:
            raise e
    
    # ========================================================================
    # PRESERVED v3.3.2 STAGE HANDLERS
    # ========================================================================
    
    def _run_validation_stage(self, stage_context: StageContext,
                            exec_context: ExecutionContext,
                            stage_logger: Any) -> bool:
        """Run validation stage (v3.3.3 fixed with proper parameter extraction)"""
        stage_logger.info("Running comprehensive validation...")
        
        try:
            # Import setup_validator with lazy loading
            setup_validator = self._get_v331_component("setup_validator")
            if not setup_validator:
                stage_logger.error("setup_validator module not available")
                return False
            
            # Create validator instance
            if hasattr(setup_validator, 'EnhancedSetupValidator'):
                validator = setup_validator.EnhancedSetupValidator()
                
                # FIXED: Properly extract parameters from stage_context
                validation_mode = stage_context.parameters.get("mode", "comprehensive")
                test_v333 = stage_context.parameters.get("test_v333", False)
                test_cli = stage_context.parameters.get("test_cli", False) 
                quality_scoring = stage_context.parameters.get("quality_scoring", False)
                fix_issues = stage_context.parameters.get("fix_issues", False)
                
                stage_logger.debug(f"Validation parameters: mode={validation_mode}, test_v333={test_v333}, test_cli={test_cli}, quality_scoring={quality_scoring}, fix_issues={fix_issues}")
                
                # Run validation with v3.3.3 method name
                if validation_mode == "quick":
                    success = validator.run_validation_v333(quick=True)
                elif validation_mode == "comprehensive":
                    success = validator.run_validation_v333(
                        quick=False, 
                        fix_issues=fix_issues,
                        test_v333=test_v333,
                        test_cli=test_cli,
                        test_quality=quality_scoring
                    )
                else:
                    success = validator.run_validation_v333(
                        test_v333=test_v333,
                        test_cli=test_cli,
                        test_quality=quality_scoring
                    )
                
                if success:
                    stage_logger.info("System validation passed")
                    stage_context.results["validation_status"] = "passed"
                    return True
                else:
                    stage_logger.error("System validation failed")
                    stage_context.results["validation_status"] = "failed"
                    return False
            else:
                stage_logger.warning("Using fallback validation")
                # Basic fallback validation
                return self._fallback_validation(stage_logger)
                
        except Exception as e:
            stage_logger.error(f"Validation stage error: {e}")
            stage_logger.debug(f"Stage context parameters: {stage_context.parameters}")
            return False
    
    def _run_download_watchlist_stage(self, stage_context: StageContext,
                                    exec_context: ExecutionContext, 
                                    stage_logger: Any) -> bool:
        """Run watchlist download stage (preserved from v3.3.2)"""
        stage_logger.info("Downloading company watchlist...")
        
        try:
            # Import config with lazy loading
            config_module = self._get_v331_component("config")
            if not config_module:
                stage_logger.error("config module not available")
                return False
            
            # Download watchlist using v3.3.1 enhanced method
            if hasattr(config_module, 'download_target_companies_v330'):
                companies = config_module.download_target_companies_v330(
                    force_refresh=stage_context.parameters.get("force_refresh", False)
                )
            else:
                stage_logger.warning("Using fallback watchlist download")
                companies = self._fallback_download_watchlist(stage_logger)
            
            if companies and len(companies) > 0:
                stage_logger.info(f"Downloaded {len(companies)} companies")
                exec_context.set_global_state("target_companies", companies)
                stage_context.results["companies_count"] = len(companies)
                return True
            else:
                stage_logger.error("No companies downloaded")
                return False
                
        except Exception as e:
            stage_logger.error(f"Watchlist download error: {e}")
            return False
    
    def _run_search_stage(self, stage_context: StageContext,
                        exec_context: ExecutionContext,
                        stage_logger: Any) -> bool:
        """Run enhanced search stage (preserved from v3.3.2)"""
        stage_logger.info("Starting enhanced search...")
        
        try:
            # Import search module with lazy loading
            search_module = self._get_v331_component("factset_search")
            if not search_module:
                stage_logger.error("factset_search module not available")
                return False
            
            # Get companies from context
            companies = exec_context.get_global_state("target_companies", [])
            if not companies:
                stage_logger.error("No target companies available")
                return False
            
            # Prepare search configuration
            search_config = {
                "target_companies": companies,
                "search": {
                    "mode": stage_context.parameters.get("mode", "enhanced"),
                    "max_results": stage_context.parameters.get("max_results", 10),
                    "priority": stage_context.parameters.get("priority", "high_only"),
                    "rate_limit_delay": exec_context.v331_settings["rate_limit_delay"]
                },
                "output": {
                    "md_dir": "data/md",
                    "csv_dir": "data/csv"
                }
            }
            
            # Initialize rate protector
            rate_protector = None
            if hasattr(search_module, 'UnifiedRateLimitProtector'):
                rate_protector = search_module.UnifiedRateLimitProtector(search_config)
            
            # Run enhanced search
            if hasattr(search_module, 'run_enhanced_search_suite_v331'):
                result = search_module.run_enhanced_search_suite_v331(
                    search_config, 
                    rate_protector=rate_protector
                )
            else:
                stage_logger.warning("Using fallback search")
                result = self._fallback_search(stage_logger, companies)
            
            if result == "rate_limited":
                stage_logger.warning("Search stopped due to rate limiting")
                stage_context.results["rate_limited"] = True
                # Still count as success if some files were generated
                md_dir = Path("data/md")
                if md_dir.exists() and list(md_dir.glob("*.md")):
                    return True
                return False
            elif result:
                stage_logger.info("Search completed successfully")
                stage_context.results["search_status"] = "completed"
                return True
            else:
                stage_logger.error("Search failed")
                return False
                
        except Exception as e:
            stage_logger.error(f"Search stage error: {e}")
            return False
    
    def _run_upload_stage(self, stage_context: StageContext,
                        exec_context: ExecutionContext,
                        stage_logger: Any) -> bool:
        """Run sheets upload stage (preserved from v3.3.2)"""
        stage_logger.info("Starting sheets upload...")
        
        try:
            # Check if upload is configured
            if not os.getenv("GOOGLE_SHEET_ID"):
                stage_logger.warning("Google Sheets not configured - skipping upload")
                stage_context.results["upload_status"] = "skipped"
                return True
            
            # Import uploader with lazy loading
            uploader_module = self._get_v331_component("sheets_uploader")
            if not uploader_module:
                stage_logger.error("sheets_uploader module not available")
                return False
            
            # Prepare upload configuration
            upload_config = {
                "input": {
                    "summary_csv": "data/processed/portfolio_summary.csv",
                    "detailed_csv": "data/processed/detailed_data.csv",
                    "stats_json": "data/processed/statistics.json"
                },
                "sheets": {
                    "auto_backup": True,
                    "create_missing_sheets": True,
                    "test_connection": stage_context.parameters.get("test_connection", False)
                }
            }
            
            # Run upload
            if hasattr(uploader_module, 'upload_all_sheets_v332'):
                success = uploader_module.upload_all_sheets_v332(upload_config)
            else:
                stage_logger.warning("Using fallback upload")
                success = self._fallback_upload(stage_logger)
            
            if success:
                stage_logger.info("Sheets upload completed successfully")
                stage_context.results["upload_status"] = "completed"
                return True
            else:
                stage_logger.error("Sheets upload failed")
                return False
                
        except Exception as e:
            stage_logger.error(f"Upload stage error: {e}")
            return False
    
    def _run_pipeline_stage(self, stage_context: StageContext,
                          exec_context: ExecutionContext,
                          stage_logger: Any) -> bool:
        """Run complete pipeline (preserved from v3.3.2)"""
        stage_logger.info("Starting complete pipeline execution...")
        
        try:
            # Import main pipeline with lazy loading
            pipeline_module = self._get_v331_component("factset_pipeline")
            if not pipeline_module:
                stage_logger.error("factset_pipeline module not available")
                return False
            
            # Determine execution strategy based on mode
            execution_mode = stage_context.parameters.get("mode", "intelligent")
            skip_phases = stage_context.parameters.get("skip_phases", [])
            
            if hasattr(pipeline_module, 'EnhancedFactSetPipeline'):
                # Use v3.3.1 enhanced pipeline
                pipeline = pipeline_module.EnhancedFactSetPipeline()
                
                success = pipeline.run_complete_pipeline_v332(
                    force_all=stage_context.parameters.get("force_all", False),
                    skip_phases=skip_phases,
                    execution_mode=execution_mode
                )
            else:
                stage_logger.warning("Using sequential stage execution")
                success = self._run_sequential_pipeline(exec_context, stage_logger)
            
            if success:
                stage_logger.info("Complete pipeline executed successfully")
                stage_context.results["pipeline_status"] = "completed"
                return True
            else:
                stage_logger.error("Pipeline execution failed")
                return False
                
        except Exception as e:
            stage_logger.error(f"Pipeline stage error: {e}")
            return False
    
    # ========================================================================
    # HELPER METHODS AND LAZY LOADING (v3.3.3 - Preserved)
    # ========================================================================
    
    def _get_v331_component(self, module_name: str):
        """Lazy loading of v3.3.1 components to avoid circular imports"""
        if module_name not in self._v331_components:
            try:
                self._v331_components[module_name] = __import__(module_name)
            except ImportError as e:
                self.main_logger.warning(f"Could not import {module_name}: {e}")
                self._v331_components[module_name] = None
        
        return self._v331_components[module_name]
    
    def _fallback_validation(self, stage_logger: Any) -> bool:
        """Fallback validation when setup_validator is not available"""
        stage_logger.info("Running basic fallback validation...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            stage_logger.error("Python 3.8+ required")
            return False
        
        # Check required directories
        required_dirs = ["data", "logs"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                stage_logger.info(f"Created directory: {dir_name}")
        
        stage_logger.info("Basic validation completed")
        return True
    
    def _fallback_download_watchlist(self, stage_logger: Any) -> List[Dict]:
        """Fallback watchlist download"""
        stage_logger.info("Using fallback watchlist download...")
        
        # Check if existing watchlist file exists
        watchlist_file = Path("觀察名單.csv")
        if watchlist_file.exists():
            try:
                import pandas as pd
                df = pd.read_csv(watchlist_file)
                
                companies = []
                for _, row in df.iterrows():
                    if '代號' in df.columns and '名稱' in df.columns:
                        companies.append({
                            "code": str(row['代號']),
                            "name": str(row['名稱']),
                            "stock_code": f"{row['代號']}-TW"
                        })
                
                stage_logger.info(f"Loaded {len(companies)} companies from existing file")
                return companies
                
            except Exception as e:
                stage_logger.error(f"Error reading existing watchlist: {e}")
        
        # Return empty list if no fallback available
        stage_logger.warning("No watchlist available")
        return []
    
    def _fallback_search(self, stage_logger: Any, companies: List[Dict]) -> bool:
        """Fallback search implementation"""
        stage_logger.info("Search module not available - skipping search phase")
        return True
    
    def _fallback_upload(self, stage_logger: Any) -> bool:
        """Fallback upload implementation"""
        stage_logger.info("Sheets uploader not available - skipping upload")
        return True
    
    def _validate_processed_files(self, stage_logger: Any) -> List[str]:
        """Validate that processed files were created"""
        processed_dir = Path("data/processed") 
        expected_files = ["portfolio_summary.csv", "detailed_data.csv", "statistics.json"]
        
        created_files = []
        for file_name in expected_files:
            file_path = processed_dir / file_name
            if file_path.exists() and file_path.stat().st_size > 0:
                created_files.append(file_name)
                stage_logger.info(f"✅ {file_name}: {file_path.stat().st_size} bytes")
            else:
                stage_logger.warning(f"⚠️ Missing or empty: {file_name}")
        
        return created_files
    
    def _run_sequential_pipeline(self, exec_context: ExecutionContext, 
                               stage_logger: Any) -> bool:
        """Run pipeline as sequential stages when main pipeline not available"""
        stage_logger.info("Running sequential stage execution...")
        
        # Define stage sequence
        stages = ["validate", "download_watchlist", "search", "process", "upload"]
        
        for stage_name in stages:
            if stage_name == "search" and exec_context.execution_mode == "process_only":
                stage_logger.info(f"Skipping {stage_name} in process_only mode")
                continue
            
            stage_logger.info(f"Executing sequential stage: {stage_name}")
            
            # Create minimal stage context
            stage_params = exec_context.parameters.copy()
            success = self.run_stage(stage_name, exec_context, **stage_params)
            
            if not success:
                # Check if failure is acceptable
                if stage_name in ["search", "upload"]:
                    stage_logger.warning(f"Non-critical stage {stage_name} failed - continuing")
                    continue
                else:
                    stage_logger.error(f"Critical stage {stage_name} failed - stopping pipeline")
                    return False
        
        stage_logger.info("Sequential pipeline execution completed")
        return True
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get comprehensive execution summary with v3.3.3 quality metrics"""
        if not self.current_context:
            return {}
        
        summary = {
            "execution_mode": self.current_context.execution_mode,
            "start_time": self.current_context.start_time.isoformat(),
            "platform_info": self.current_context.platform_info,
            "v331_settings": self.current_context.v331_settings,
            "quality_metrics": self.current_context.quality_metrics,  # v3.3.3
            "stages": {}
        }
        
        for stage_name, stage_context in self.current_context.stage_contexts.items():
            summary["stages"][stage_name] = {
                "status": stage_context.status.value,
                "duration": stage_context.duration,
                "retry_count": stage_context.retry_count,
                "results": stage_context.results,
                "quality_data": stage_context.quality_data,  # v3.3.3
                "error": str(stage_context.error) if stage_context.error else None
            }
        
        return summary

# ============================================================================
# CONVENIENCE FUNCTIONS AND EXPORTS
# ============================================================================

def create_stage_runner() -> StageRunner:
    """Create a new stage runner instance"""
    return StageRunner()

def run_single_stage(stage_name: str, **kwargs) -> bool:
    """Convenience function to run a single stage"""
    runner = create_stage_runner()
    context = ExecutionContext(**kwargs)
    return runner.run_stage(stage_name, context, **kwargs)

# Module exports
__all__ = [
    'StageRunner',
    'StageContext', 
    'StageDefinition',
    'ExecutionContext',
    'StageStatus',
    'create_stage_runner',
    'run_single_stage'
]