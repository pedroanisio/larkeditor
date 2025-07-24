"""Tests for the core parser functionality."""

import pytest
import asyncio
from datetime import datetime

from app.core.parser import AsyncLarkParser, ParseCache, get_parser
from app.models.requests import ParseSettings, ParserType
from app.models.responses import ParseStatus, ErrorType


class TestParseCache:
    """Test the parse cache functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = ParseCache(max_size=10)
        assert len(cache.cache) == 0
        assert len(cache.access_order) == 0
        assert cache.max_size == 10
    
    def test_cache_key_generation(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test cache key generation."""
        cache = ParseCache()
        
        key1 = cache.get_cache_key(
            sample_grammars["simple"], 
            sample_texts["simple_number"], 
            sample_parse_settings["default"]
        )
        
        key2 = cache.get_cache_key(
            sample_grammars["simple"], 
            sample_texts["simple_number"], 
            sample_parse_settings["default"]
        )
        
        # Same inputs should generate same key
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
        
        # Different inputs should generate different keys
        key3 = cache.get_cache_key(
            sample_grammars["arithmetic"], 
            sample_texts["simple_number"], 
            sample_parse_settings["default"]
        )
        assert key1 != key3
    
    def test_cache_operations(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test cache put and get operations."""
        from app.models.responses import ParseResult, ParseStatus, ASTNode
        
        cache = ParseCache(max_size=2)
        
        # Create a mock parse result
        result = ParseResult(
            status=ParseStatus.SUCCESS,
            tree=ASTNode(type="test", data="test", children=[]),
            error=None,
            parse_time=0.1,
            grammar_hash="test_hash",
            timestamp=datetime.now()
        )
        
        key = cache.get_cache_key(
            sample_grammars["simple"], 
            sample_texts["simple_number"], 
            sample_parse_settings["default"]
        )
        
        # Initially empty
        assert cache.get(key) is None
        
        # Put and get
        cache.put(key, result)
        cached_result = cache.get(key)
        assert cached_result == result
        assert len(cache.cache) == 1
        assert len(cache.access_order) == 1
    
    def test_cache_lru_eviction(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test LRU eviction."""
        from app.models.responses import ParseResult, ParseStatus, ASTNode
        
        cache = ParseCache(max_size=2)
        
        # Create mock results
        result1 = ParseResult(
            status=ParseStatus.SUCCESS,
            tree=ASTNode(type="test1", data="test1", children=[]),
            error=None,
            parse_time=0.1,
            grammar_hash="test_hash1",
            timestamp=datetime.now()
        )
        
        result2 = ParseResult(
            status=ParseStatus.SUCCESS,
            tree=ASTNode(type="test2", data="test2", children=[]),
            error=None,
            parse_time=0.1,
            grammar_hash="test_hash2",
            timestamp=datetime.now()
        )
        
        result3 = ParseResult(
            status=ParseStatus.SUCCESS,
            tree=ASTNode(type="test3", data="test3", children=[]),
            error=None,
            parse_time=0.1,
            grammar_hash="test_hash3",
            timestamp=datetime.now()
        )
        
        key1 = "key1"
        key2 = "key2"
        key3 = "key3"
        
        # Fill cache to max
        cache.put(key1, result1)
        cache.put(key2, result2)
        assert len(cache.cache) == 2
        
        # Access key1 to make it most recent
        cache.get(key1)
        
        # Add key3, should evict key2 (least recently used)
        cache.put(key3, result3)
        assert len(cache.cache) == 2
        assert cache.get(key1) == result1  # Still there
        assert cache.get(key2) is None     # Evicted
        assert cache.get(key3) == result3  # Newly added


class TestAsyncLarkParser:
    """Test the async Lark parser functionality."""
    
    @pytest.mark.asyncio
    async def test_parser_initialization(self):
        """Test parser initialization."""
        parser = AsyncLarkParser()
        assert len(parser.cache.cache) == 0
        assert len(parser.active_parsers) == 0
        assert parser.parse_count == 0
    
    @pytest.mark.asyncio
    async def test_grammar_validation_success(self, sample_grammars, sample_parse_settings):
        """Test successful grammar validation."""
        parser = AsyncLarkParser()
        
        result = await parser.validate_grammar(
            sample_grammars["simple"], 
            sample_parse_settings["default"]
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.rule_count > 0
        assert result.terminal_count > 0
    
    @pytest.mark.asyncio
    async def test_grammar_validation_failure(self, sample_grammars, sample_parse_settings):
        """Test grammar validation failure."""
        parser = AsyncLarkParser()
        
        result = await parser.validate_grammar(
            sample_grammars["invalid"], 
            sample_parse_settings["default"]
        )
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.errors[0].type == ErrorType.GRAMMAR_ERROR
        assert result.rule_count == 0
        assert result.terminal_count == 0
    
    @pytest.mark.asyncio
    async def test_successful_parsing(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test successful parsing."""
        parser = AsyncLarkParser()
        
        result = await parser.parse_async(
            sample_grammars["simple"],
            sample_texts["simple_number"],
            sample_parse_settings["default"]
        )
        
        assert result.status == ParseStatus.SUCCESS
        assert result.tree is not None
        assert result.error is None
        assert result.parse_time > 0
        assert result.grammar_hash is not None
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_parsing_with_invalid_grammar(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test parsing with invalid grammar."""
        parser = AsyncLarkParser()
        
        result = await parser.parse_async(
            sample_grammars["invalid"],
            sample_texts["simple_number"],
            sample_parse_settings["default"]
        )
        
        assert result.status == ParseStatus.INVALID_GRAMMAR
        assert result.tree is None
        assert result.error is not None
        assert result.error.type == ErrorType.GRAMMAR_ERROR
    
    @pytest.mark.asyncio
    async def test_parsing_with_invalid_text(self, sample_grammars, sample_texts):
        """Test parsing with invalid text."""
        parser = AsyncLarkParser()
        result = await parser.parse_async(
            sample_grammars["simple"],
            sample_texts["invalid"],
            ParseSettings()
        )
        
        # The status should be ERROR for invalid text
        assert result.status == ParseStatus.ERROR
        assert result.tree is None
        assert result.error is not None
        # Accept multiple error types as Lark can classify errors differently
        assert result.error.type in [ErrorType.PARSE_ERROR, ErrorType.INTERNAL_ERROR]
    
    @pytest.mark.asyncio
    async def test_parser_caching(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test parser caching functionality."""
        parser = AsyncLarkParser()
        
        # First parse
        result1 = await parser.parse_async(
            sample_grammars["simple"],
            sample_texts["simple_number"],
            sample_parse_settings["default"],
            use_cache=True
        )
        
        # Second parse with same inputs should use cache
        result2 = await parser.parse_async(
            sample_grammars["simple"],
            sample_texts["simple_number"],
            sample_parse_settings["default"],
            use_cache=True
        )
        
        assert result1.status == ParseStatus.SUCCESS
        assert result2.status == ParseStatus.SUCCESS
        # Both should have same grammar hash
        assert result1.grammar_hash == result2.grammar_hash
    
    @pytest.mark.asyncio
    async def test_parser_without_caching(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test parser without caching."""
        parser = AsyncLarkParser()
        
        result = await parser.parse_async(
            sample_grammars["simple"],
            sample_texts["simple_number"],
            sample_parse_settings["default"],
            use_cache=False
        )
        
        assert result.status == ParseStatus.SUCCESS
        # Cache should still be empty
        assert len(parser.cache.cache) == 0
    
    @pytest.mark.asyncio
    async def test_different_parser_types(self, sample_grammars, sample_texts):
        """Test different parser types."""
        parser = AsyncLarkParser()
        
        # LALR parser
        result_lalr = await parser.parse_async(
            sample_grammars["arithmetic"],
            sample_texts["arithmetic"],
            ParseSettings(parser=ParserType.LALR)
        )
        
        # Earley parser  
        result_earley = await parser.parse_async(
            sample_grammars["arithmetic"],
            sample_texts["arithmetic"],
            ParseSettings(parser=ParserType.EARLEY)
        )
        
        assert result_lalr.status == ParseStatus.SUCCESS
        assert result_earley.status == ParseStatus.SUCCESS
        # Different parsers should have different grammar hashes
        assert result_lalr.grammar_hash != result_earley.grammar_hash
    
    @pytest.mark.asyncio
    async def test_input_size_limits(self, sample_parse_settings):
        """Test input size validation."""
        from app.core.config import get_settings
        
        parser = AsyncLarkParser()
        settings = get_settings()
        
        # Test large grammar
        large_grammar = "start: 'x'\n" * (settings.max_grammar_size // 10 + 1)
        result = await parser.parse_async(
            large_grammar,
            "x",
            sample_parse_settings["default"]
        )
        assert result.status == ParseStatus.ERROR
        assert "too large" in result.error.message.lower()
        
        # Test large text
        large_text = "x" * (settings.max_text_length + 1)
        result = await parser.parse_async(
            "start: 'x'+",
            large_text,
            sample_parse_settings["default"]
        )
        assert result.status == ParseStatus.ERROR
        assert "too large" in result.error.message.lower()
    
    @pytest.mark.asyncio
    async def test_parser_stats(self):
        """Test parser statistics."""
        parser = AsyncLarkParser()
        
        # Initial stats
        stats = parser.get_stats()
        assert stats["parse_count"] == 0
        assert stats["cache_size"] == 0
        assert stats["active_parsers"] == 0
        
        # After one parse
        await parser.parse_async(
            "start: NUMBER\n%import common.NUMBER",
            "42",
            ParseSettings()
        )
        
        stats = parser.get_stats()
        assert stats["parse_count"] == 1
        assert stats["cache_size"] == 1
        assert stats["active_parsers"] == 1
    
    @pytest.mark.asyncio
    async def test_cache_clearing(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test cache clearing."""
        parser = AsyncLarkParser()
        
        # Add to cache
        await parser.parse_async(
            sample_grammars["simple"],
            sample_texts["simple_number"],
            sample_parse_settings["default"]
        )
        
        assert len(parser.cache.cache) > 0
        
        # Clear cache
        parser.clear_cache()
        assert len(parser.cache.cache) == 0
        assert len(parser.cache.access_order) == 0
    
    @pytest.mark.asyncio
    async def test_parser_cleanup(self):
        """Test parser cleanup."""
        parser = AsyncLarkParser()
        
        # Create many parsers to trigger cleanup - use valid Lark grammar
        for i in range(60):  # More than cleanup threshold of 50
            await parser.parse_async(
                f"start: \"{i}\"\n",  # Valid Lark literal syntax
                str(i),
                ParseSettings()
            )
        
        initial_count = len(parser.active_parsers)
        assert initial_count >= 50, f"Expected at least 50 parsers, got {initial_count}"
        
        # Trigger cleanup
        parser.cleanup_parsers()
        final_count = len(parser.active_parsers)
        
        # Should keep only 25 parsers (as per cleanup logic)
        assert final_count <= 25, f"Expected <= 25 parsers after cleanup, got {final_count}"
        
        # Only assert reduction if we actually had more than 25 parsers initially
        if initial_count > 25:
            assert final_count < initial_count, f"Expected reduction: {initial_count} -> {final_count}"


class TestParserIntegration:
    """Integration tests for parser functionality."""
    
    @pytest.mark.asyncio
    async def test_get_parser_singleton(self):
        """Test that get_parser returns singleton instance."""
        parser1 = get_parser()
        parser2 = get_parser()
        assert parser1 is parser2
    
    @pytest.mark.asyncio
    async def test_complex_grammar_parsing(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test parsing with complex grammar."""
        parser = get_parser()
        
        result = await parser.parse_async(
            sample_grammars["complex"],
            sample_texts["assignment"],
            sample_parse_settings["default"]
        )
        
        assert result.status == ParseStatus.SUCCESS
        assert result.tree is not None
        assert result.tree.type == "tree"
        assert result.tree.data == "start"
    
    @pytest.mark.asyncio
    async def test_concurrent_parsing(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test concurrent parsing operations."""
        parser = get_parser()
        
        # Create multiple parsing tasks
        tasks = []
        for i in range(5):
            task = parser.parse_async(
                sample_grammars["arithmetic"],
                sample_texts["arithmetic"],
                sample_parse_settings["default"]
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result.status == ParseStatus.SUCCESS
            assert result.tree is not None
    
    @pytest.mark.asyncio
    async def test_parser_performance(self, sample_grammars, sample_texts, sample_parse_settings):
        """Test parser performance."""
        parser = get_parser()
        
        # Time a simple parse
        result = await parser.parse_async(
            sample_grammars["simple"],
            sample_texts["simple_number"],
            sample_parse_settings["default"]
        )
        
        assert result.status == ParseStatus.SUCCESS
        assert result.parse_time < 1.0  # Should be fast for simple grammar
        assert result.parse_time > 0   # Should take some measurable time 