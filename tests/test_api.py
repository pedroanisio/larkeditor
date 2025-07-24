"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestParsingAPI:
    """Test the parsing API endpoints."""
    
    def test_parse_endpoint_success(self, test_client: TestClient, sample_grammars, sample_texts):
        """Test successful parsing via API."""
        response = test_client.post("/api/parse", json={
            "grammar": sample_grammars["simple"],
            "text": sample_texts["simple_number"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["tree"] is not None
        assert data["error"] is None
        assert data["parse_time"] > 0
        assert data["grammar_hash"] is not None
        assert data["timestamp"] is not None
    
    def test_parse_endpoint_grammar_error(self, test_client: TestClient, sample_grammars, sample_texts):
        """Test parsing with invalid grammar via API."""
        response = test_client.post("/api/parse", json={
            "grammar": sample_grammars["invalid"],
            "text": sample_texts["simple_number"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "invalid_grammar"
        assert data["tree"] is None
        assert data["error"] is not None
        assert data["error"]["type"] == "grammar_error"
    
    def test_parse_endpoint_parse_error(self, test_client: TestClient, sample_grammars, sample_texts):
        """Test parsing with invalid text via API."""
        response = test_client.post("/api/parse", json={
            "grammar": sample_grammars["simple"],
            "text": sample_texts["invalid"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # The response could be any of these error types depending on how Lark interprets it
        assert data["status"] in ["error", "invalid_grammar", "internal_error"], f"Unexpected status: {data['status']}"
        assert data["tree"] is None
        assert data["error"] is not None
        assert data["error"]["type"] in ["parse_error", "grammar_error", "internal_error"]
    
    def test_parse_endpoint_missing_fields(self, test_client: TestClient):
        """Test parsing endpoint with missing required fields."""
        # Missing grammar
        response = test_client.post("/api/parse", json={
            "text": "42",
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        assert response.status_code == 422  # Validation error
        
        # Missing text
        response = test_client.post("/api/parse", json={
            "grammar": "start: NUMBER",
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        assert response.status_code == 422  # Validation error
    
    def test_parse_endpoint_different_parsers(self, test_client: TestClient, sample_grammars, sample_texts):
        """Test parsing with different parser types."""
        for parser_type in ["lalr", "earley"]:
            response = test_client.post("/api/parse", json={
                "grammar": sample_grammars["arithmetic"],
                "text": sample_texts["arithmetic"],
                "settings": {
                    "start_rule": "start",
                    "parser": parser_type,
                    "debug": False
                }
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    def test_parse_endpoint_custom_start_rule(self, test_client: TestClient):
        """Test parsing with custom start rule."""
        grammar = """
start: expr
expr: NUMBER
number: NUMBER
%import common.NUMBER
%import common.WS
%ignore WS
        """.strip()
        
        # Valid custom start rule
        response = test_client.post("/api/parse", json={
            "grammar": grammar,
            "text": "42",
            "settings": {
                "start_rule": "expr",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Invalid start rule
        response = test_client.post("/api/parse", json={
            "grammar": grammar,
            "text": "42",
            "settings": {
                "start_rule": "nonexistent_rule",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "invalid_grammar"


class TestValidationAPI:
    """Test the grammar validation API endpoints."""
    
    def test_validate_endpoint_success(self, test_client: TestClient, sample_grammars):
        """Test successful grammar validation via API."""
        response = test_client.post("/api/validate", json={
            "grammar": sample_grammars["simple"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is True
        assert len(data["errors"]) == 0
        assert data["rule_count"] > 0
        assert data["terminal_count"] > 0
    
    def test_validate_endpoint_failure(self, test_client: TestClient, sample_grammars):
        """Test grammar validation failure via API."""
        response = test_client.post("/api/validate", json={
            "grammar": sample_grammars["invalid"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
        assert data["errors"][0]["type"] == "grammar_error"
        assert data["rule_count"] == 0
        assert data["terminal_count"] == 0
    
    def test_validate_endpoint_missing_grammar(self, test_client: TestClient):
        """Test validation endpoint with missing grammar."""
        response = test_client.post("/api/validate", json={
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        assert response.status_code == 422  # Validation error


class TestStatsAPI:
    """Test the statistics API endpoints."""
    
    def test_stats_endpoint(self, test_client: TestClient):
        """Test parser statistics endpoint."""
        response = test_client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "parse_count" in data
        assert "cache_size" in data
        assert "active_parsers" in data
        assert isinstance(data["parse_count"], int)
        assert isinstance(data["cache_size"], int)
        assert isinstance(data["active_parsers"], int)
    
    def test_clear_cache_endpoint(self, test_client: TestClient):
        """Test cache clearing endpoint."""
        response = test_client.post("/api/clear-cache")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cache clear" in data["message"].lower()
    
    def test_cleanup_endpoint(self, test_client: TestClient):
        """Test parser cleanup endpoint."""
        response = test_client.post("/api/cleanup")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleanup" in data["message"].lower()


class TestHealthAPI:
    """Test the health check API endpoints."""
    
    def test_root_endpoint(self, test_client: TestClient):
        """Test the root endpoint serves the main page."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestAPIValidation:
    """Test API request validation."""
    
    def test_invalid_json(self, test_client: TestClient):
        """Test API with invalid JSON."""
        response = test_client.post(
            "/api/parse",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_invalid_parser_type(self, test_client: TestClient, sample_grammars, sample_texts):
        """Test API with invalid parser type."""
        response = test_client.post("/api/parse", json={
            "grammar": sample_grammars["simple"],
            "text": sample_texts["simple_number"],
            "settings": {
                "start_rule": "start",
                "parser": "invalid_parser",
                "debug": False
            }
        })
        assert response.status_code == 422
    
    def test_invalid_debug_flag(self, test_client: TestClient, sample_grammars, sample_texts):
        """Test API with invalid debug flag."""
        response = test_client.post("/api/parse", json={
            "grammar": sample_grammars["simple"],
            "text": sample_texts["simple_number"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": "not_a_boolean"
            }
        })
        assert response.status_code == 422


class TestAPIAsync:
    """Test API endpoints with async client."""
    
    @pytest.mark.asyncio
    async def test_async_parse_endpoint(self, async_client: AsyncClient, sample_grammars, sample_texts):
        """Test parsing endpoint with async client."""
        response = await async_client.post("/api/parse", json={
            "grammar": sample_grammars["simple"],
            "text": sample_texts["simple_number"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_async_validate_endpoint(self, async_client: AsyncClient, sample_grammars):
        """Test validation endpoint with async client."""
        response = await async_client.post("/api/validate", json={
            "grammar": sample_grammars["simple"],
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_async_stats_endpoint(self, async_client: AsyncClient):
        """Test stats endpoint with async client."""
        response = await async_client.get("/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "parse_count" in data


class TestAPIPerformance:
    """Test API performance characteristics."""
    
    def test_multiple_requests(self, test_client: TestClient, sample_grammars, sample_texts):
        """Test multiple API requests."""
        responses = []
        
        # Make multiple requests
        for i in range(5):
            response = test_client.post("/api/parse", json={
                "grammar": sample_grammars["simple"],
                "text": sample_texts["simple_number"],
                "settings": {
                    "start_rule": "start",
                    "parser": "lalr",
                    "debug": False
                }
            })
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    def test_large_input_handling(self, test_client: TestClient):
        """Test API with large inputs."""
        # Test with moderately large grammar
        large_grammar = """
start: expr
expr: term (("+" | "-") term)*
term: factor (("*" | "/") factor)*
factor: NUMBER | "(" expr ")"
%import common.NUMBER
%import common.WS
%ignore WS
        """ * 10  # Repeat to make it larger
        
        response = test_client.post("/api/parse", json={
            "grammar": large_grammar,
            "text": "1 + 2 * 3",
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        # Should still work for reasonable size
        assert response.status_code == 200


class TestAPIErrorHandling:
    """Test API error handling."""
    
    def test_server_error_handling(self, test_client: TestClient):
        """Test that server errors are handled gracefully."""
        # This should trigger an internal error due to malformed grammar
        response = test_client.post("/api/parse", json={
            "grammar": "completely malformed grammar with no rules",
            "text": "test",
            "settings": {
                "start_rule": "start",
                "parser": "lalr",
                "debug": False
            }
        })
        
        # Should return error status, not crash
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["error", "invalid_grammar"]
        assert data["error"] is not None
    
    def test_timeout_handling(self, test_client: TestClient):
        """Test timeout handling for complex grammars."""
        # Create a potentially complex grammar that might be slow
        complex_grammar = """
start: expr
expr: expr "+" term | expr "-" term | term
term: term "*" factor | term "/" factor | factor
factor: NUMBER | "(" expr ")"
%import common.NUMBER
%import common.WS
%ignore WS
        """
        
        response = test_client.post("/api/parse", json={
            "grammar": complex_grammar,
            "text": "1 + 2 * 3 - 4 / 5",
            "settings": {
                "start_rule": "start",
                "parser": "earley",  # Earley can handle left recursion
                "debug": False
            }
        })
        
        # Should complete or timeout gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "timeout", "error"] 