"""
Platform compatibility features for LLM Context Exporter.

This module provides functionality for handling platform format changes,
unknown versions, feature detection, and installation verification.
"""

import os
import subprocess
import shutil
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.core import ParsedExport, UniversalContextPack


logger = logging.getLogger(__name__)


class CompatibilityLevel(Enum):
    """Compatibility levels for format versions."""
    FULLY_SUPPORTED = "fully_supported"
    BACKWARD_COMPATIBLE = "backward_compatible"
    LIMITED_SUPPORT = "limited_support"
    UNSUPPORTED = "unsupported"


@dataclass
class FormatDiagnostic:
    """Diagnostic information about format detection."""
    detected_version: str
    confidence: float  # 0.0 to 1.0
    compatibility_level: CompatibilityLevel
    issues: List[str]
    suggestions: List[str]
    fallback_version: Optional[str] = None


@dataclass
class PlatformFeature:
    """Information about a platform-specific feature."""
    name: str
    platform: str
    supported_in_target: bool
    description: str
    workaround: Optional[str] = None


@dataclass
class UnsupportedDataLog:
    """Log entry for unsupported data types."""
    data_type: str
    location: str  # Where in the export this was found
    reason: str
    sample_data: Optional[str] = None  # Truncated sample for debugging
    count: int = 1


class CompatibilityManager:
    """
    Manages platform compatibility features including format detection,
    version fallback, and feature flagging.
    """
    
    def __init__(self):
        self.unsupported_data_log: List[UnsupportedDataLog] = []
        self.platform_features: Dict[str, List[PlatformFeature]] = {}
        self._initialize_known_features()
    
    def _initialize_known_features(self):
        """Initialize known platform-specific features."""
        # ChatGPT-specific features that may not transfer
        chatgpt_features = [
            PlatformFeature(
                name="Web Browsing",
                platform="chatgpt",
                supported_in_target=False,
                description="ChatGPT's ability to browse the web for current information",
                workaround="Mention that you previously used web browsing for research"
            ),
            PlatformFeature(
                name="Plugin Usage",
                platform="chatgpt",
                supported_in_target=False,
                description="ChatGPT plugins for specific tasks",
                workaround="Describe the plugin functionality in your context"
            ),
            PlatformFeature(
                name="Code Interpreter",
                platform="chatgpt",
                supported_in_target=False,
                description="ChatGPT's code execution environment",
                workaround="Include code examples and expected outputs in context"
            ),
            PlatformFeature(
                name="DALL-E Integration",
                platform="chatgpt",
                supported_in_target=False,
                description="Image generation capabilities",
                workaround="Describe image requirements and preferences in text"
            ),
            PlatformFeature(
                name="File Uploads",
                platform="chatgpt",
                supported_in_target=False,
                description="Ability to analyze uploaded files",
                workaround="Include file contents or summaries in context text"
            )
        ]
        
        self.platform_features["chatgpt"] = chatgpt_features
    
    def detect_format_with_diagnostics(self, file_path: str, parser_class) -> FormatDiagnostic:
        """
        Detect format version with detailed diagnostics.
        
        Args:
            file_path: Path to the export file
            parser_class: Parser class to use for detection
            
        Returns:
            FormatDiagnostic with detailed information
        """
        try:
            parser = parser_class()
            detected_version = parser.detect_format_version(file_path)
            supported_versions = parser.get_supported_versions()
            
            # Determine compatibility level
            if detected_version in supported_versions:
                if detected_version == "unknown":
                    compatibility_level = CompatibilityLevel.LIMITED_SUPPORT
                    confidence = 0.5
                else:
                    compatibility_level = CompatibilityLevel.FULLY_SUPPORTED
                    confidence = 1.0
            else:
                # Try to find a compatible fallback
                fallback_version = self._find_fallback_version(detected_version, supported_versions)
                if fallback_version:
                    compatibility_level = CompatibilityLevel.BACKWARD_COMPATIBLE
                    confidence = 0.7
                else:
                    compatibility_level = CompatibilityLevel.UNSUPPORTED
                    confidence = 0.0
            
            # Generate diagnostic information
            issues = []
            suggestions = []
            
            if compatibility_level == CompatibilityLevel.LIMITED_SUPPORT:
                issues.append("Format version could not be determined")
                suggestions.append("File may be from a newer ChatGPT export format")
                suggestions.append("Try updating the tool or contact support")
            
            elif compatibility_level == CompatibilityLevel.BACKWARD_COMPATIBLE:
                issues.append(f"Format version {detected_version} not directly supported")
                suggestions.append(f"Will attempt parsing with {fallback_version} compatibility")
                suggestions.append("Some features may not be available")
            
            elif compatibility_level == CompatibilityLevel.UNSUPPORTED:
                issues.append(f"Format version {detected_version} is not supported")
                suggestions.append("This export format is too old or too new")
                suggestions.append("Try exporting again or use a different export format")
            
            # Add file structure diagnostics
            structure_issues = self._analyze_file_structure(file_path)
            issues.extend(structure_issues)
            
            return FormatDiagnostic(
                detected_version=detected_version,
                confidence=confidence,
                compatibility_level=compatibility_level,
                issues=issues,
                suggestions=suggestions,
                fallback_version=fallback_version if compatibility_level == CompatibilityLevel.BACKWARD_COMPATIBLE else None
            )
            
        except Exception as e:
            return FormatDiagnostic(
                detected_version="error",
                confidence=0.0,
                compatibility_level=CompatibilityLevel.UNSUPPORTED,
                issues=[f"Failed to analyze file: {str(e)}"],
                suggestions=[
                    "Check that the file is a valid ChatGPT export",
                    "Ensure the file is not corrupted",
                    "Try extracting ZIP files before processing"
                ]
            )
    
    def _find_fallback_version(self, detected_version: str, supported_versions: List[str]) -> Optional[str]:
        """Find a compatible fallback version for backward compatibility."""
        if detected_version == "unknown":
            # For unknown versions, try the most recent supported version
            if supported_versions:
                # Remove "unknown" from the list and get the latest
                known_versions = [v for v in supported_versions if v != "unknown"]
                if known_versions:
                    return max(known_versions)  # Assumes version strings are sortable
        
        # For specific versions, try to find the closest older supported version
        # This is a simple heuristic - could be improved with proper version parsing
        try:
            if detected_version.count('-') == 2:  # Date format like "2024-06-01"
                year, month, day = detected_version.split('-')
                detected_date = (int(year), int(month), int(day))
                
                best_fallback = None
                best_date = None
                
                for version in supported_versions:
                    if version == "unknown":
                        continue
                    try:
                        v_year, v_month, v_day = version.split('-')
                        v_date = (int(v_year), int(v_month), int(v_day))
                        
                        # Find the newest version that's older than or equal to detected
                        if v_date <= detected_date:
                            if best_date is None or v_date > best_date:
                                best_fallback = version
                                best_date = v_date
                    except (ValueError, AttributeError):
                        continue
                
                # If no older version found, try the oldest supported version
                if best_fallback is None:
                    known_versions = [v for v in supported_versions if v != "unknown"]
                    if known_versions:
                        return min(known_versions)
                
                return best_fallback
        except (ValueError, AttributeError):
            pass
        
        # If no smart fallback found, return the first supported version
        known_versions = [v for v in supported_versions if v != "unknown"]
        return known_versions[0] if known_versions else None
    
    def _analyze_file_structure(self, file_path: str) -> List[str]:
        """Analyze file structure for diagnostic information."""
        issues = []
        
        try:
            file_size = os.path.getsize(file_path)
            
            # Check file size
            if file_size == 0:
                issues.append("File is empty")
            elif file_size > 1024 * 1024 * 1024:  # 1GB
                issues.append("File is very large (>1GB) - processing may be slow")
            
            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if ext not in ['.json', '.zip']:
                issues.append(f"Unexpected file extension: {ext}")
            
            # Try to peek at file content
            with open(file_path, 'rb') as f:
                header = f.read(100)
                
                # Check for ZIP signature
                if header.startswith(b'PK'):
                    if ext != '.zip':
                        issues.append("File appears to be ZIP but has wrong extension")
                
                # Check for JSON start
                elif header.strip().startswith(b'{') or header.strip().startswith(b'['):
                    if ext != '.json':
                        issues.append("File appears to be JSON but has wrong extension")
                
                # Check for binary data
                elif b'\x00' in header:
                    issues.append("File contains binary data - may be corrupted")
                
        except Exception as e:
            issues.append(f"Could not analyze file structure: {str(e)}")
        
        return issues
    
    def attempt_fallback_parsing(self, file_path: str, parser_class, fallback_version: str) -> Optional[ParsedExport]:
        """
        Attempt to parse with fallback version compatibility.
        
        Args:
            file_path: Path to the export file
            parser_class: Parser class to use
            fallback_version: Version to use for fallback parsing
            
        Returns:
            ParsedExport if successful, None if failed
        """
        try:
            parser = parser_class()
            
            # Temporarily override version detection to use fallback
            original_detect = parser.detect_format_version
            parser.detect_format_version = lambda path: fallback_version
            
            try:
                result = parser.parse_export(file_path)
                logger.info(f"Successfully parsed with fallback version {fallback_version}")
                return result
            finally:
                # Restore original method
                parser.detect_format_version = original_detect
                
        except Exception as e:
            logger.warning(f"Fallback parsing with version {fallback_version} failed: {str(e)}")
            return None
    
    def identify_platform_features(self, parsed_export: ParsedExport) -> List[PlatformFeature]:
        """
        Identify platform-specific features that may not transfer.
        
        Args:
            parsed_export: Parsed export data
            
        Returns:
            List of identified platform features
        """
        identified_features = []
        
        # Analyze conversations for platform-specific features
        for conversation in parsed_export.conversations:
            for message in conversation.messages:
                content = message.content.lower()
                
                # Check for web browsing indicators
                if any(indicator in content for indicator in [
                    "browsed", "searched the web", "found online", "according to my search",
                    "based on current information", "from the web"
                ]):
                    feature = next((f for f in self.platform_features["chatgpt"] 
                                  if f.name == "Web Browsing"), None)
                    if feature and feature not in identified_features:
                        identified_features.append(feature)
                
                # Check for plugin usage
                if any(indicator in content for indicator in [
                    "using the", "plugin", "tool:", "executed code", "ran the"
                ]):
                    # Could be plugin or code interpreter
                    if "code" in content or "python" in content or "execute" in content:
                        feature = next((f for f in self.platform_features["chatgpt"] 
                                      if f.name == "Code Interpreter"), None)
                    else:
                        feature = next((f for f in self.platform_features["chatgpt"] 
                                      if f.name == "Plugin Usage"), None)
                    
                    if feature and feature not in identified_features:
                        identified_features.append(feature)
                
                # Check for image generation
                if any(indicator in content for indicator in [
                    "generated an image", "created an image", "dall-e", "image generation"
                ]):
                    feature = next((f for f in self.platform_features["chatgpt"] 
                                  if f.name == "DALL-E Integration"), None)
                    if feature and feature not in identified_features:
                        identified_features.append(feature)
                
                # Check for file uploads
                if any(indicator in content for indicator in [
                    "uploaded file", "analyze this file", "document you provided",
                    "in the file you shared"
                ]):
                    feature = next((f for f in self.platform_features["chatgpt"] 
                                  if f.name == "File Uploads"), None)
                    if feature and feature not in identified_features:
                        identified_features.append(feature)
        
        return identified_features
    
    def log_unsupported_data(self, data_type: str, location: str, reason: str, 
                           sample_data: Optional[str] = None):
        """
        Log unsupported data types encountered during processing.
        
        Args:
            data_type: Type of unsupported data
            location: Where in the export this was found
            reason: Why it's unsupported
            sample_data: Optional sample for debugging (will be truncated)
        """
        # Check if we already have a log entry for this type/location
        existing_entry = None
        for entry in self.unsupported_data_log:
            if entry.data_type == data_type and entry.location == location:
                existing_entry = entry
                break
        
        if existing_entry:
            existing_entry.count += 1
        else:
            # Truncate sample data for privacy and storage
            truncated_sample = None
            if sample_data:
                truncated_sample = sample_data[:100] + "..." if len(sample_data) > 100 else sample_data
            
            self.unsupported_data_log.append(UnsupportedDataLog(
                data_type=data_type,
                location=location,
                reason=reason,
                sample_data=truncated_sample
            ))
        
        logger.warning(f"Unsupported data type '{data_type}' at {location}: {reason}")
    
    def get_unsupported_data_summary(self) -> Dict[str, Any]:
        """Get a summary of all unsupported data encountered."""
        if not self.unsupported_data_log:
            return {"total_types": 0, "entries": []}
        
        return {
            "total_types": len(self.unsupported_data_log),
            "total_occurrences": sum(entry.count for entry in self.unsupported_data_log),
            "entries": [
                {
                    "data_type": entry.data_type,
                    "location": entry.location,
                    "reason": entry.reason,
                    "count": entry.count,
                    "sample": entry.sample_data
                }
                for entry in self.unsupported_data_log
            ]
        }
    
    def verify_ollama_installation(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify Ollama installation and provide guidance if not found.
        
        Returns:
            Tuple of (is_installed, status_info)
        """
        status_info = {
            "ollama_found": False,
            "ollama_running": False,
            "qwen_available": False,
            "version": None,
            "issues": [],
            "suggestions": []
        }
        
        # Check if Ollama binary is available
        if shutil.which("ollama") is None:
            status_info["issues"].append("Ollama not found in PATH")
            status_info["suggestions"].extend([
                "Visit https://ollama.ai to download and install Ollama",
                "Make sure Ollama is added to your system PATH",
                "Restart your terminal after installation"
            ])
            return False, status_info
        
        status_info["ollama_found"] = True
        
        # Check Ollama version
        try:
            result = subprocess.run(
                ["ollama", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                status_info["version"] = result.stdout.strip()
            else:
                status_info["issues"].append("Could not get Ollama version")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            status_info["issues"].append("Ollama command failed")
        
        # Check if Ollama is running by trying to list models
        try:
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            if result.returncode == 0:
                status_info["ollama_running"] = True
                
                # Check if Qwen model is available
                if "qwen" in result.stdout.lower():
                    status_info["qwen_available"] = True
                else:
                    status_info["issues"].append("Qwen model not found")
                    status_info["suggestions"].append("Run: ollama pull qwen")
            else:
                status_info["issues"].append("Ollama is not running")
                status_info["suggestions"].extend([
                    "Start Ollama service: ollama serve",
                    "Or run Ollama in the background"
                ])
        except subprocess.TimeoutExpired:
            status_info["issues"].append("Ollama command timed out")
            status_info["suggestions"].append("Ollama may be starting up - try again in a moment")
        except (subprocess.CalledProcessError, FileNotFoundError):
            status_info["issues"].append("Could not communicate with Ollama")
            status_info["suggestions"].append("Make sure Ollama is properly installed and running")
        
        # Determine overall status
        is_ready = (status_info["ollama_found"] and 
                   status_info["ollama_running"] and 
                   status_info["qwen_available"])
        
        if not is_ready and not status_info["issues"]:
            status_info["issues"].append("Ollama setup incomplete")
        
        return is_ready, status_info
    
    def generate_compatibility_report(self, parsed_export: ParsedExport, 
                                    target_platform: str) -> Dict[str, Any]:
        """
        Generate a comprehensive compatibility report.
        
        Args:
            parsed_export: Parsed export data
            target_platform: Target platform (gemini, ollama)
            
        Returns:
            Compatibility report dictionary
        """
        # Identify platform features
        platform_features = self.identify_platform_features(parsed_export)
        
        # Get unsupported data summary
        unsupported_summary = self.get_unsupported_data_summary()
        
        # Check target platform requirements
        target_status = {}
        if target_platform == "ollama":
            is_ready, ollama_status = self.verify_ollama_installation()
            target_status = {
                "platform": "ollama",
                "ready": is_ready,
                "details": ollama_status
            }
        elif target_platform == "gemini":
            target_status = {
                "platform": "gemini",
                "ready": True,  # Gemini doesn't require local installation
                "details": {
                    "notes": ["Gemini is cloud-based and doesn't require local setup"]
                }
            }
        
        return {
            "export_info": {
                "format_version": parsed_export.format_version,
                "conversations_count": len(parsed_export.conversations),
                "export_date": parsed_export.export_date.isoformat()
            },
            "platform_features": [
                {
                    "name": feature.name,
                    "platform": feature.platform,
                    "supported_in_target": feature.supported_in_target,
                    "description": feature.description,
                    "workaround": feature.workaround
                }
                for feature in platform_features
            ],
            "unsupported_data": unsupported_summary,
            "target_platform_status": target_status,
            "recommendations": self._generate_recommendations(
                platform_features, unsupported_summary, target_status
            )
        }
    
    def _generate_recommendations(self, platform_features: List[PlatformFeature], 
                                unsupported_summary: Dict[str, Any], 
                                target_status: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on compatibility analysis."""
        recommendations = []
        
        # Platform feature recommendations
        unsupported_features = [f for f in platform_features if not f.supported_in_target]
        if unsupported_features:
            recommendations.append(
                f"Found {len(unsupported_features)} platform-specific features that won't transfer directly"
            )
            for feature in unsupported_features[:3]:  # Show top 3
                if feature.workaround:
                    recommendations.append(f"For {feature.name}: {feature.workaround}")
        
        # Unsupported data recommendations
        if unsupported_summary["total_types"] > 0:
            recommendations.append(
                f"Encountered {unsupported_summary['total_types']} types of unsupported data - "
                "some information may be lost"
            )
        
        # Target platform recommendations
        if not target_status.get("ready", True):
            recommendations.append("Target platform is not ready - see setup instructions")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Export appears compatible with minimal issues")
        
        return recommendations