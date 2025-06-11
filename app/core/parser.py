"""Async parser service for Lark grammar parsing."""

import asyncio
import hashlib
import time
from typing import Optional, Dict, Any, Union, List
from datetime import datetime

import lark
from lark.exceptions import GrammarError, ParseError, VisitError

from ..models.requests import ParseSettings, ParserType
from ..models.responses import (
    ParseResult, ParseStatus, ParseError as APIParseError, 
    ErrorType, ASTNode, GrammarValidationResult
)
from .config import get_settings, get_logger

settings = get_settings()
logger = get_logger("parser")


class ParseCache:
    """Simple LRU cache for parse results."""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, ParseResult] = {}
        self.access_order: List[str] = []
        self.max_size = max_size
        logger.info(f"Initialized parse cache with max_size={max_size}")
    
    def get_cache_key(self, grammar: str, text: str, parse_settings: ParseSettings) -> str:
        """Generate cache key from inputs."""
        content = f"{grammar}|{text}|{parse_settings.start_rule}|{parse_settings.parser}"
        cache_key = hashlib.md5(content.encode()).hexdigest()
        logger.debug(f"Generated cache key: {cache_key[:8]}... for grammar({len(grammar)} chars), text({len(text)} chars)")
        return cache_key
    
    def get(self, key: str) -> Optional[ParseResult]:
        """Get cached result and update access order."""
        if key in self.cache:
            self.access_order.remove(key)
            self.access_order.append(key)
            logger.debug(f"Cache hit for key: {key[:8]}...")
            return self.cache[key]
        logger.debug(f"Cache miss for key: {key[:8]}...")
        return None
    
    def put(self, key: str, result: ParseResult):
        """Store result in cache with LRU eviction."""
        if key in self.cache:
            self.access_order.remove(key)
            logger.debug(f"Updated existing cache entry: {key[:8]}...")
        elif len(self.cache) >= self.max_size:
            # Evict least recently used
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
            logger.debug(f"Evicted LRU cache entry: {oldest_key[:8]}...")
        
        self.cache[key] = result
        self.access_order.append(key)
        logger.debug(f"Cached result for key: {key[:8]}... (cache size: {len(self.cache)})")


class AsyncLarkParser:
    """Async wrapper for Lark parser with caching and error handling."""
    
    def __init__(self):
        self.cache = ParseCache(settings.parse_cache_size)
        self.active_parsers: Dict[str, lark.Lark] = {}
        self.parse_count = 0
        logger.info("Initialized AsyncLarkParser")
    
    def _grammar_hash(self, grammar: str, parse_settings: ParseSettings) -> str:
        """Generate hash for grammar with settings."""
        content = f"{grammar}|{parse_settings.start_rule}|{parse_settings.parser}"
        grammar_hash = hashlib.md5(content.encode()).hexdigest()
        logger.debug(f"Generated grammar hash: {grammar_hash[:8]}... for {len(grammar)} char grammar")
        return grammar_hash
    
    def _lark_tree_to_ast_node(self, node: Union[lark.Tree, lark.Token]) -> Union[ASTNode, str]:
        """Convert Lark tree to API ASTNode structure."""
        if isinstance(node, lark.Tree):
            children = [self._lark_tree_to_ast_node(child) for child in node.children]
            return ASTNode(
                type="tree",
                data=node.data,
                children=children
            )
        else:  # Token
            return ASTNode(
                type="token",
                data=str(node),
                children=[],
                start_pos=getattr(node, 'start_pos', None),
                end_pos=getattr(node, 'end_pos', None),
                line=getattr(node, 'line', None),
                column=getattr(node, 'column', None)
            )
    
    def _create_parse_error(self, error: Exception) -> APIParseError:
        """Convert Lark exception to API error structure."""
        logger.error(f"Creating parse error from exception: {type(error).__name__}: {str(error)}")
        
        if isinstance(error, GrammarError):
            logger.error(f"Grammar error: {str(error)}")
            return APIParseError(
                type=ErrorType.GRAMMAR_ERROR,
                message=str(error),
                suggestions=["Check grammar syntax", "Verify rule definitions"]
            )
        elif isinstance(error, ParseError):
            logger.error(f"Parse error: {str(error)}")
            return APIParseError(
                type=ErrorType.PARSE_ERROR,
                message=str(error),
                line=getattr(error, 'line', None),
                column=getattr(error, 'column', None),
                context=getattr(error, 'get_context', lambda *args: None)(error.text) if hasattr(error, 'text') else None
            )
        elif isinstance(error, asyncio.TimeoutError):
            logger.error("Parse operation timed out")
            return APIParseError(
                type=ErrorType.TIMEOUT_ERROR,
                message="Parse operation timed out",
                suggestions=["Simplify grammar", "Reduce input text size"]
            )
        else:
            logger.error(f"Internal error: {type(error).__name__}: {str(error)}")
            return APIParseError(
                type=ErrorType.INTERNAL_ERROR,
                message=f"Internal error: {str(error)}"
            )
    
    async def validate_grammar(self, grammar: str, parse_settings: ParseSettings) -> GrammarValidationResult:
        """Validate grammar syntax without parsing text."""
        logger.info(f"Validating grammar ({len(grammar)} chars) with settings: {parse_settings}")
        start_time = time.time()
        
        try:
            # Run in thread pool to avoid blocking
            logger.debug("Creating Lark parser for validation...")
            parser = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: lark.Lark(
                    grammar,
                    propagate_positions=True,
                    start=parse_settings.start_rule,
                    parser=parse_settings.parser.value,
                    debug=parse_settings.debug
                )
            )
            
            # Count rules and terminals
            rule_count = len([rule for rule in parser.rules])
            terminal_count = len(parser.terminals)
            validation_time = time.time() - start_time
            
            logger.info(f"Grammar validation successful in {validation_time:.3f}s: {rule_count} rules, {terminal_count} terminals")
            
            return GrammarValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                rule_count=rule_count,
                terminal_count=terminal_count
            )
            
        except Exception as e:
            validation_time = time.time() - start_time
            logger.error(f"Grammar validation failed in {validation_time:.3f}s: {str(e)}")
            return GrammarValidationResult(
                is_valid=False,
                errors=[self._create_parse_error(e)],
                warnings=[],
                rule_count=0,
                terminal_count=0
            )
    
    async def parse_async(
        self, 
        grammar: str, 
        text: str, 
        parse_settings: ParseSettings,
        use_cache: bool = True
    ) -> ParseResult:
        """Parse text with grammar asynchronously."""
        logger.info(f"Starting parse operation: grammar({len(grammar)} chars), text({len(text)} chars), cache={use_cache}")
        start_time = time.time()
        grammar_hash = self._grammar_hash(grammar, parse_settings)
        
        # Check cache first
        if use_cache:
            cache_key = self.cache.get_cache_key(grammar, text, parse_settings)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached result for parse (cache hit)")
                return cached_result
        
        try:
            # Validate input lengths
            if len(grammar) > settings.max_grammar_size:
                raise ValueError(f"Grammar too large: {len(grammar)} > {settings.max_grammar_size}")
            if len(text) > settings.max_text_length:
                raise ValueError(f"Text too large: {len(text)} > {settings.max_text_length}")
            
            logger.debug(f"Input validation passed")
            
            # Create or reuse parser
            if grammar_hash not in self.active_parsers:
                logger.debug(f"Creating new Lark parser for grammar hash: {grammar_hash[:8]}...")
                parser_start = time.time()
                parser = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: lark.Lark(
                            grammar,
                            propagate_positions=True,
                            start=parse_settings.start_rule,
                            parser=parse_settings.parser.value,
                            debug=parse_settings.debug
                        )
                    ),
                    timeout=settings.max_parse_time / 2  # Allow time for parsing too
                )
                parser_time = time.time() - parser_start
                logger.debug(f"Created Lark parser in {parser_time:.3f}s")
                self.active_parsers[grammar_hash] = parser
            else:
                logger.debug(f"Reusing existing parser for grammar hash: {grammar_hash[:8]}...")
                parser = self.active_parsers[grammar_hash]
            
            # Parse the text
            logger.debug("Starting text parsing...")
            parse_start = time.time()
            lark_tree = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: parser.parse(text)
                ),
                timeout=settings.max_parse_time
            )
            parse_time_internal = time.time() - parse_start
            logger.debug(f"Text parsing completed in {parse_time_internal:.3f}s")
            
            # Convert to API format
            logger.debug("Converting Lark tree to API format...")
            convert_start = time.time()
            ast_tree = self._lark_tree_to_ast_node(lark_tree)
            convert_time = time.time() - convert_start
            logger.debug(f"Tree conversion completed in {convert_time:.3f}s")
            
            total_parse_time = time.time() - start_time
            
            result = ParseResult(
                status=ParseStatus.SUCCESS,
                tree=ast_tree,
                error=None,
                parse_time=total_parse_time,
                grammar_hash=grammar_hash,
                timestamp=datetime.now()
            )
            
            # Cache successful result
            if use_cache:
                cache_key = self.cache.get_cache_key(grammar, text, parse_settings)
                self.cache.put(cache_key, result)
            
            self.parse_count += 1
            logger.info(f"Parse completed successfully in {total_parse_time:.3f}s (parse #{self.parse_count})")
            return result
            
        except asyncio.TimeoutError:
            parse_time = time.time() - start_time
            logger.error(f"Parse operation timed out after {parse_time:.3f}s")
            return ParseResult(
                status=ParseStatus.TIMEOUT,
                tree=None,
                error=self._create_parse_error(asyncio.TimeoutError()),
                parse_time=parse_time,
                grammar_hash=grammar_hash,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            parse_time = time.time() - start_time
            error_type = ParseStatus.INVALID_GRAMMAR if isinstance(e, GrammarError) else ParseStatus.ERROR
            logger.error(f"Parse operation failed after {parse_time:.3f}s: {type(e).__name__}: {str(e)}")
            
            return ParseResult(
                status=error_type,
                tree=None,
                error=self._create_parse_error(e),
                parse_time=parse_time,
                grammar_hash=grammar_hash,
                timestamp=datetime.now()
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parser statistics."""
        stats = {
            "parse_count": self.parse_count,
            "cache_size": len(self.cache.cache),
            "active_parsers": len(self.active_parsers)
        }
        logger.debug(f"Parser stats: {stats}")
        return stats
    
    def clear_cache(self):
        """Clear parse cache."""
        cache_size = len(self.cache.cache)
        self.cache.cache.clear()
        self.cache.access_order.clear()
        logger.info(f"Cleared parse cache ({cache_size} entries)")
    
    def cleanup_parsers(self):
        """Clean up unused parsers."""
        initial_count = len(self.active_parsers)
        # Simple cleanup - could be enhanced with LRU for parsers too
        if len(self.active_parsers) > 50:
            # Keep only the most recent 25
            keys = list(self.active_parsers.keys())
            for key in keys[:-25]:
                del self.active_parsers[key]
        
        final_count = len(self.active_parsers)
        if initial_count != final_count:
            logger.info(f"Cleaned up parsers: {initial_count} -> {final_count}")


# Global parser instance
_parser_instance: Optional[AsyncLarkParser] = None


def get_parser() -> AsyncLarkParser:
    """Get global parser instance."""
    global _parser_instance
    if _parser_instance is None:
        logger.info("Creating global parser instance")
        _parser_instance = AsyncLarkParser()
    return _parser_instance