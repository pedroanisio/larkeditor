"""API routes for grammar parsing operations."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from ..models.requests import ParseRequest, GrammarValidationRequest
from ..models.responses import ParseResult, GrammarValidationResult
from ..core.parser import get_parser
from ..core.config import get_logger

router = APIRouter()
logger = get_logger("api.parsing")


@router.post("/parse", response_model=ParseResult)
async def parse_grammar(request: ParseRequest) -> ParseResult:
    """Parse text using provided grammar."""
    logger.info(f"Parse request: grammar({len(request.grammar)} chars), text({len(request.text)} chars)")
    logger.debug(f"Parse settings: {request.settings}")
    
    parser = get_parser()
    
    try:
        result = await parser.parse_async(
            grammar=request.grammar,
            text=request.text,
            parse_settings=request.settings,
            use_cache=True
        )
        
        logger.info(f"Parse completed successfully: status={result.status}, time={result.parse_time:.3f}s")
        return result
        
    except Exception as e:
        logger.error(f"Parse failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Parse failed: {str(e)}")


@router.post("/validate", response_model=GrammarValidationResult)
async def validate_grammar(request: GrammarValidationRequest) -> GrammarValidationResult:
    """Validate grammar syntax without parsing text."""
    logger.info(f"Grammar validation request: grammar({len(request.grammar)} chars)")
    logger.debug(f"Validation settings: {request.settings}")
    
    parser = get_parser()
    
    try:
        result = await parser.validate_grammar(
            grammar=request.grammar,
            parse_settings=request.settings
        )
        
        logger.info(f"Grammar validation completed: valid={result.is_valid}, rules={result.rule_count}, terminals={result.terminal_count}")
        if not result.is_valid:
            logger.warning(f"Grammar validation failed with {len(result.errors)} errors")
            
        return result
        
    except Exception as e:
        logger.error(f"Grammar validation failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/stats")
async def get_parser_stats() -> Dict[str, Any]:
    """Get parser statistics and performance metrics."""
    logger.debug("Parser stats requested")
    parser = get_parser()
    stats = parser.get_stats()
    logger.debug(f"Returning parser stats: {stats}")
    return stats


@router.post("/clear-cache")
async def clear_parse_cache(background_tasks: BackgroundTasks):
    """Clear the parser cache."""
    logger.info("Cache clear requested")
    parser = get_parser()
    background_tasks.add_task(parser.clear_cache)
    return {"message": "Cache clear scheduled"}


@router.post("/cleanup")
async def cleanup_parsers(background_tasks: BackgroundTasks):
    """Clean up unused parsers."""
    logger.info("Parser cleanup requested")
    parser = get_parser()
    background_tasks.add_task(parser.cleanup_parsers)
    return {"message": "Parser cleanup scheduled"}