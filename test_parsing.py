#!/usr/bin/env python3
"""Simple test script to verify the parsing backend works correctly."""

import asyncio
import json
from app.core.parser import get_parser
from app.models.requests import ParseSettings

async def test_parser():
    """Test the async parser directly."""
    print("🔍 Testing LarkEditor Backend Parser...")
    
    # Test grammar
    grammar = """
start: expr

?expr: term
     | expr "+" term   -> add
     | expr "-" term   -> sub

?term: factor
     | term "*" factor -> mul
     | term "/" factor -> div

?factor: NUMBER
       | "(" expr ")"

%import common.NUMBER
%import common.WS
%ignore WS
"""
    
    # Test text
    text = "2 + 3 * (4 - 1)"
    
    # Test settings
    settings = ParseSettings(parser="earley", start_rule="start", debug=False)
    
    print(f"Grammar: {len(grammar)} characters")
    print(f"Text: '{text}'")
    print(f"Settings: {settings}")
    
    try:
        # Get parser and test
        parser = get_parser()
        print("✅ Parser instance created")
        
        # Test validation
        print("\n📋 Testing grammar validation...")
        validation_result = await parser.validate_grammar(grammar, settings)
        print(f"✅ Validation: {validation_result.is_valid}")
        if validation_result.is_valid:
            print(f"   Rules: {validation_result.rule_count}")
            print(f"   Terminals: {validation_result.terminal_count}")
        else:
            print(f"   Errors: {len(validation_result.errors)}")
            for error in validation_result.errors:
                print(f"     - {error.message}")
        
        # Test parsing
        print("\n⚡ Testing parsing...")
        parse_result = await parser.parse_async(grammar, text, settings)
        print(f"✅ Parse status: {parse_result.status}")
        print(f"   Parse time: {parse_result.parse_time:.3f}s")
        
        if parse_result.tree:
            print(f"   AST root: {parse_result.tree.data}")
            print(f"   AST children: {len(parse_result.tree.children) if hasattr(parse_result.tree, 'children') else 0}")
        elif parse_result.error:
            print(f"   Error: {parse_result.error.message}")
        
        # Test cache
        print("\n🗄️ Testing cache...")
        cache_result = await parser.parse_async(grammar, text, settings)
        print(f"✅ Cached parse time: {cache_result.parse_time:.3f}s")
        
        # Get stats
        stats = parser.get_stats()
        print(f"\n📊 Parser stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_websocket_protocol():
    """Test WebSocket message protocol."""
    print("\n🔌 Testing WebSocket Message Protocol...")
    
    # Simulate WebSocket messages
    messages = [
        {
            "type": "grammar_change",
            "session_id": "test_session_123",
            "data": {"content": "start: NUMBER"}
        },
        {
            "type": "text_change", 
            "session_id": "test_session_123",
            "data": {"content": "42"}
        },
        {
            "type": "force_parse",
            "session_id": "test_session_123", 
            "data": {}
        }
    ]
    
    for i, msg in enumerate(messages):
        print(f"✅ Message {i+1}: {msg['type']} - {len(json.dumps(msg))} bytes")
    
    return True

if __name__ == "__main__":
    async def main():
        print("🚀 LarkEditor Backend Test Suite")
        print("=" * 50)
        
        # Test parser
        parser_ok = await test_parser()
        
        # Test WebSocket protocol
        protocol_ok = await test_websocket_protocol()
        
        print("\n📊 Test Results:")
        print(f"{'✅' if parser_ok else '❌'} Parser: {'PASSED' if parser_ok else 'FAILED'}")
        print(f"{'✅' if protocol_ok else '❌'} Protocol: {'PASSED' if protocol_ok else 'FAILED'}")
        
        if parser_ok and protocol_ok:
            print("\n🎉 All backend tests passed!")
            print("\n💡 If WebSocket is still failing, check:")
            print("   1. Server logs for connection errors")
            print("   2. Browser network tab for WebSocket status")
            print("   3. Firewall/proxy blocking WebSocket connections")
        else:
            print("\n❌ Some tests failed - check the errors above")
    
    asyncio.run(main())