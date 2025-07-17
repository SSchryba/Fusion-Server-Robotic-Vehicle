#!/usr/bin/env python3
"""
AutoFix Server
FastAPI server with /autofix endpoint for self-correcting code generation and validation
"""

import sys
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from utils.api_client import FusionAPIClient
from utils.config_loader import ConfigLoader
from fusion_absorb_with_kb import KnowledgeBaseFusion

logger = logging.getLogger(__name__)

# Pydantic models
class CodeFixRequest(BaseModel):
    """Request model for code fixing"""
    code: str
    language: str = "python"
    context: Optional[str] = None
    fix_type: str = "comprehensive"  # comprehensive, syntax, logic, performance, security
    max_iterations: int = 3

class CodeFixResponse(BaseModel):
    """Response model for code fixing"""
    original_code: str
    fixed_code: str
    explanation: str
    fixes_applied: List[str]
    confidence: float
    error_type: str
    piraz_compatibility: bool
    fix_time: float
    iterations_used: int

class CorrectionLog(BaseModel):
    """Model for correction logging"""
    timestamp: str
    original_code: str
    fixed_code: str
    error_type: str
    confidence: float
    explanation: str
    user_feedback: Optional[str] = None

@dataclass
class CodeAnalysis:
    """Data class for code analysis results"""
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    piraz_compatibility: bool
    error_codes: List[str]
    confidence: float

class AutoFixServer:
    """Main AutoFix server with code correction capabilities"""
    
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.get_fusion_config()
        
        self.api_client = FusionAPIClient(
            host=self.config.host,
            port=self.config.port,
            timeout=self.config.timeout
        )
        
        self.kb_fusion = KnowledgeBaseFusion()
        
        # Load knowledge base
        self.kb_data = self.kb_fusion.load_knowledge_base()
        self.piraz_os = self.kb_data.get('piraz_os', {})
        
        # Correction history
        self.correction_history = []
        
        # Setup FastAPI app
        self.app = FastAPI(
            title="AutoFix Server",
            description="Self-correcting code generation and validation with Piraz OS integration",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Mount static files for frontend
        frontend_path = os.path.join(os.path.dirname(__file__), "autofix_frontend")
        if os.path.exists(frontend_path):
            self.app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        
        self.setup_routes()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Serve main autofix interface"""
            frontend_path = os.path.join(os.path.dirname(__file__), "autofix_frontend/index.html")
            if os.path.exists(frontend_path):
                return FileResponse(frontend_path)
            return {"message": "AutoFix Server", "status": "running", "version": "1.0.0"}
        
        @self.app.post("/autofix", response_model=CodeFixResponse)
        async def autofix_code(request: CodeFixRequest, background_tasks: BackgroundTasks):
            """Main autofix endpoint"""
            try:
                start_time = datetime.now()
                
                # Validate request
                if not request.code.strip():
                    raise HTTPException(status_code=400, detail="Code cannot be empty")
                
                if len(request.code) > 50000:
                    raise HTTPException(status_code=400, detail="Code too long (max 50k characters)")
                
                # Analyze code
                analysis = self.analyze_code(request.code, request.language)
                
                # Generate fix using hybrid model
                fix_result = await self.generate_code_fix(request, analysis)
                
                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds()
                fix_result.fix_time = processing_time
                
                # Log correction in background
                background_tasks.add_task(
                    self.log_correction,
                    request.code,
                    fix_result.fixed_code,
                    fix_result.error_type,
                    fix_result.confidence,
                    fix_result.explanation
                )
                
                logger.info(f"✅ Code fix completed in {processing_time:.2f}s")
                return fix_result
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ AutoFix error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/autofix/history")
        async def get_correction_history(limit: int = 50):
            """Get correction history"""
            return {
                "corrections": self.correction_history[-limit:],
                "total": len(self.correction_history)
            }
        
        @self.app.post("/autofix/feedback")
        async def submit_feedback(correction_id: str, feedback: str, rating: int):
            """Submit user feedback on corrections"""
            try:
                # Find correction by ID and update
                for correction in self.correction_history:
                    if correction.get("id") == correction_id:
                        correction["user_feedback"] = feedback
                        correction["rating"] = rating
                        break
                
                # Update KB with feedback
                self.update_kb_from_feedback(correction_id, feedback, rating)
                
                return {"message": "Feedback submitted successfully"}
                
            except Exception as e:
                logger.error(f"❌ Feedback submission error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/autofix/status")
        async def get_autofix_status():
            """Get AutoFix server status"""
            fusion_status = self.api_client.get_fusion_status()
            kb_summary = self.kb_fusion.get_kb_summary()
            
            return {
                "autofix_server": "running",
                "fusion_connected": fusion_status is not None,
                "kb_version": kb_summary.get("version", "unknown"),
                "kb_last_updated": kb_summary.get("last_updated", "unknown"),
                "corrections_performed": len(self.correction_history),
                "available_models": len(self.api_client.get_available_models()),
                "piraz_error_codes": kb_summary.get("error_codes_count", 0),
                "validation_rules": kb_summary.get("validation_rules_count", 0)
            }
        
        @self.app.post("/autofix/update-kb")
        async def update_knowledge_base():
            """Update knowledge base from recent corrections"""
            try:
                # Get recent corrections for KB update
                recent_corrections = self.correction_history[-100:]  # Last 100 corrections
                
                # Update KB
                success = self.kb_fusion.update_kb_from_corrections(recent_corrections)
                
                if success:
                    # Reload KB data
                    self.kb_data = self.kb_fusion.load_knowledge_base()
                    self.piraz_os = self.kb_data.get('piraz_os', {})
                    
                    return {"message": "Knowledge base updated successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to update knowledge base")
                    
            except Exception as e:
                logger.error(f"❌ KB update error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/autofix/trigger-absorption")
        async def trigger_kb_absorption():
            """Trigger knowledge base enhanced absorption"""
            try:
                result = self.kb_fusion.trigger_kb_absorption()
                
                if result["success"]:
                    return {
                        "message": "Knowledge base absorption triggered successfully",
                        "hybrid_model": result.get("hybrid_model", "unknown"),
                        "kb_version": result.get("kb_version", "unknown")
                    }
                else:
                    raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
                    
            except Exception as e:
                logger.error(f"❌ KB absorption trigger error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def analyze_code(self, code: str, language: str) -> CodeAnalysis:
        """Analyze code for errors and compatibility"""
        errors = []
        warnings = []
        suggestions = []
        error_codes = []
        piraz_compatibility = True
        
        # Check for common Piraz OS patterns
        error_codes_dict = self.piraz_os.get('error_codes', {})
        validation_rules = self.piraz_os.get('code_validation_rules', {})
        
        # Basic syntax and pattern analysis
        if language.lower() == 'python':
            # Check for common Python issues
            if 'import os' in code and 'os.system(' in code:
                warnings.append("Using os.system() - consider subprocess for better security")
            
            if 'except:' in code:
                warnings.append("Bare except clause - specify exception types")
            
            if 'print(' in code and 'logging' not in code:
                suggestions.append("Consider using logging instead of print statements")
        
        # Check against Piraz OS validation rules
        for rule_category, rules in validation_rules.items():
            anti_patterns = rules.get('anti_patterns', [])
            for pattern in anti_patterns:
                if pattern.lower() in code.lower():
                    errors.append(f"Anti-pattern detected: {pattern}")
                    piraz_compatibility = False
        
        # Check for error code patterns
        for error_code, error_info in error_codes_dict.items():
            code_patterns = error_info.get('code_patterns', [])
            for pattern in code_patterns:
                if pattern in code:
                    error_codes.append(error_code)
                    suggestions.append(f"Pattern '{pattern}' may lead to {error_code}")
        
        # Calculate confidence based on analysis
        total_issues = len(errors) + len(warnings)
        confidence = max(0.1, 1.0 - (total_issues * 0.1))
        
        return CodeAnalysis(
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            piraz_compatibility=piraz_compatibility,
            error_codes=error_codes,
            confidence=confidence
        )
    
    async def generate_code_fix(self, request: CodeFixRequest, analysis: CodeAnalysis) -> CodeFixResponse:
        """Generate code fix using hybrid model with KB context"""
        
        # Build context for the hybrid model
        context = self.build_fix_context(request, analysis)
        
        # Create fix prompt
        fix_prompt = self.create_fix_prompt(request.code, request.language, context, analysis)
        
        # Call hybrid model for fix generation
        try:
            # Use the fusion API to get fix from hybrid model
            response = self.api_client.chat_with_model("hybrid-fusion-v1", fix_prompt)
            
            if not response:
                raise Exception("No response from hybrid model")
            
            # Parse response to extract fixed code and explanation
            fixed_code, explanation, fixes_applied = self.parse_fix_response(response)
            
            # Validate the fix
            fix_analysis = self.analyze_code(fixed_code, request.language)
            
            # Determine error type
            error_type = self.determine_error_type(analysis, fix_analysis)
            
            return CodeFixResponse(
                original_code=request.code,
                fixed_code=fixed_code,
                explanation=explanation,
                fixes_applied=fixes_applied,
                confidence=fix_analysis.confidence,
                error_type=error_type,
                piraz_compatibility=fix_analysis.piraz_compatibility,
                fix_time=0.0,  # Will be set by caller
                iterations_used=1
            )
            
        except Exception as e:
            logger.error(f"❌ Code fix generation failed: {e}")
            
            # Return minimal fix response
            return CodeFixResponse(
                original_code=request.code,
                fixed_code=request.code,
                explanation=f"Error generating fix: {str(e)}",
                fixes_applied=[],
                confidence=0.0,
                error_type="generation_error",
                piraz_compatibility=analysis.piraz_compatibility,
                fix_time=0.0,
                iterations_used=0
            )
    
    def build_fix_context(self, request: CodeFixRequest, analysis: CodeAnalysis) -> str:
        """Build context for fix generation"""
        context_parts = []
        
        # Add Piraz OS context
        context_parts.append("PIRAZ OS CONTEXT:")
        context_parts.append(f"- Operating System: Piraz OS v{self.piraz_os.get('version', '1.0.0')}")
        context_parts.append(f"- Target Language: {request.language}")
        context_parts.append(f"- Fix Type: {request.fix_type}")
        
        # Add error codes context
        if analysis.error_codes:
            context_parts.append(f"- Related Error Codes: {', '.join(analysis.error_codes)}")
            
            for error_code in analysis.error_codes:
                error_info = self.piraz_os.get('error_codes', {}).get(error_code, {})
                if error_info:
                    context_parts.append(f"  {error_code}: {error_info.get('description', 'No description')}")
                    fixes = error_info.get('recommended_fixes', [])
                    if fixes:
                        context_parts.append(f"  Recommended fixes: {', '.join(fixes[:3])}")
        
        # Add validation rules context
        validation_rules = self.piraz_os.get('code_validation_rules', {})
        if validation_rules:
            context_parts.append("- Validation Rules:")
            for category, rules in validation_rules.items():
                best_practices = rules.get('best_practices', [])
                if best_practices:
                    context_parts.append(f"  {category}: {', '.join(best_practices[:2])}")
        
        # Add user context
        if request.context:
            context_parts.append(f"- User Context: {request.context}")
        
        return "\n".join(context_parts)
    
    def create_fix_prompt(self, code: str, language: str, context: str, analysis: CodeAnalysis) -> str:
        """Create prompt for code fix generation"""
        prompt_parts = []
        
        prompt_parts.append("You are an expert Piraz OS system programmer with deep knowledge of error handling, service management, and code optimization.")
        prompt_parts.append("")
        prompt_parts.append(context)
        prompt_parts.append("")
        prompt_parts.append("ANALYSIS RESULTS:")
        
        if analysis.errors:
            prompt_parts.append(f"- Errors: {'; '.join(analysis.errors)}")
        
        if analysis.warnings:
            prompt_parts.append(f"- Warnings: {'; '.join(analysis.warnings)}")
        
        if analysis.suggestions:
            prompt_parts.append(f"- Suggestions: {'; '.join(analysis.suggestions)}")
        
        prompt_parts.append(f"- Piraz OS Compatibility: {'Yes' if analysis.piraz_compatibility else 'No'}")
        prompt_parts.append("")
        prompt_parts.append("ORIGINAL CODE:")
        prompt_parts.append("```" + language)
        prompt_parts.append(code)
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("TASK:")
        prompt_parts.append("Fix the code above with the following requirements:")
        prompt_parts.append("1. Maintain original functionality")
        prompt_parts.append("2. Follow Piraz OS best practices")
        prompt_parts.append("3. Fix all identified errors and warnings")
        prompt_parts.append("4. Ensure compatibility with Piraz OS error handling")
        prompt_parts.append("5. Add appropriate error checking and logging")
        prompt_parts.append("")
        prompt_parts.append("RESPONSE FORMAT:")
        prompt_parts.append("FIXED_CODE:")
        prompt_parts.append("```" + language)
        prompt_parts.append("# Your fixed code here")
        prompt_parts.append("```")
        prompt_parts.append("")
        prompt_parts.append("EXPLANATION:")
        prompt_parts.append("Detailed explanation of changes made.")
        prompt_parts.append("")
        prompt_parts.append("FIXES_APPLIED:")
        prompt_parts.append("- List of specific fixes applied")
        
        return "\n".join(prompt_parts)
    
    def parse_fix_response(self, response: str) -> tuple[str, str, List[str]]:
        """Parse fix response from hybrid model"""
        try:
            # Extract fixed code
            fixed_code = ""
            explanation = ""
            fixes_applied = []
            
            lines = response.split('\n')
            current_section = None
            code_lines = []
            explanation_lines = []
            fixes_lines = []
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('FIXED_CODE:'):
                    current_section = 'code'
                    continue
                elif line.startswith('EXPLANATION:'):
                    current_section = 'explanation'
                    continue
                elif line.startswith('FIXES_APPLIED:'):
                    current_section = 'fixes'
                    continue
                
                if current_section == 'code':
                    if line.startswith('```') and line != '```':
                        continue
                    elif line == '```':
                        continue
                    else:
                        code_lines.append(line)
                elif current_section == 'explanation':
                    if line and not line.startswith('FIXES_APPLIED:'):
                        explanation_lines.append(line)
                elif current_section == 'fixes':
                    if line.startswith('- '):
                        fixes_lines.append(line[2:])
                    elif line:
                        fixes_lines.append(line)
            
            fixed_code = '\n'.join(code_lines).strip()
            explanation = '\n'.join(explanation_lines).strip()
            fixes_applied = fixes_lines
            
            # Fallback if parsing fails
            if not fixed_code:
                fixed_code = response
            
            if not explanation:
                explanation = "Code has been analyzed and improved for Piraz OS compatibility."
            
            if not fixes_applied:
                fixes_applied = ["General code improvements applied"]
            
            return fixed_code, explanation, fixes_applied
            
        except Exception as e:
            logger.error(f"❌ Error parsing fix response: {e}")
            return response, "Error parsing response", ["Unknown fixes applied"]
    
    def determine_error_type(self, original_analysis: CodeAnalysis, fix_analysis: CodeAnalysis) -> str:
        """Determine the type of error that was fixed"""
        
        if original_analysis.errors:
            if any('syntax' in error.lower() for error in original_analysis.errors):
                return "syntax_error"
            elif any('logic' in error.lower() for error in original_analysis.errors):
                return "logic_error"
            elif any('security' in error.lower() for error in original_analysis.errors):
                return "security_vulnerability"
            else:
                return "general_error"
        
        if original_analysis.warnings:
            if any('performance' in warning.lower() for warning in original_analysis.warnings):
                return "performance_issue"
            else:
                return "code_quality"
        
        if not original_analysis.piraz_compatibility:
            return "compatibility_issue"
        
        return "optimization"
    
    async def log_correction(self, original_code: str, fixed_code: str, error_type: str, 
                           confidence: float, explanation: str):
        """Log correction for learning and analysis"""
        try:
            correction = {
                "id": f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.correction_history)}",
                "timestamp": datetime.now().isoformat(),
                "original_code": original_code,
                "fixed_code": fixed_code,
                "error_type": error_type,
                "confidence": confidence,
                "explanation": explanation,
                "user_feedback": None,
                "rating": None
            }
            
            self.correction_history.append(correction)
            
            # Keep only last 1000 corrections in memory
            if len(self.correction_history) > 1000:
                self.correction_history = self.correction_history[-1000:]
            
            logger.info(f"📝 Logged correction: {correction['id']}")
            
        except Exception as e:
            logger.error(f"❌ Error logging correction: {e}")
    
    def update_kb_from_feedback(self, correction_id: str, feedback: str, rating: int):
        """Update knowledge base based on user feedback"""
        try:
            # This would update the knowledge base with user feedback
            # For now, just log the feedback
            logger.info(f"📝 User feedback for {correction_id}: {feedback} (rating: {rating})")
            
            # TODO: Implement actual KB update logic based on feedback
            
        except Exception as e:
            logger.error(f"❌ Error updating KB from feedback: {e}")
    
    def run(self, host: str = "0.0.0.0", port: int = 8003):
        """Run the AutoFix server"""
        logger.info(f"🚀 Starting AutoFix server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoFix Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=8003, help='Port number')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = AutoFixServer()
    server.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main() 