#!/usr/bin/env python3
"""Debug script for arithmetic grammar parsing."""

import asyncio
from app.core.parser import get_parser
from app.models.requests import ParseSettings, ParserType

async def test_arithmetic_grammar():
    """Test the exact arithmetic grammar pattern from the web interface."""
    
    # Grammar from the web interface
    grammar = '''
start: expr

expr: term
    | expr "+" term    -> add
    | expr "-" term    -> sub

term: factor
    | term "*" factor  -> mul
    | term "/" factor  -> div

factor: NUMBER
      | "-" factor    -> neg
      | "(" expr ")"

%import common.NUMBER
%import common.WS
%ignore WS
'''
    
    text = '2 + 3 * (4 - 1)'
    settings = ParseSettings(parser=ParserType.EARLEY, start_rule='start', debug=False)
    
    print(f"🧪 Testing Arithmetic Grammar with Earley Parser")
    print(f"Grammar length: {len(grammar)} chars")
    print(f"Text: '{text}'")
    print(f"Parser: {settings.parser}")
    print(f"Start rule: {settings.start_rule}")
    print("-" * 50)
    
    parser = get_parser()
    result = await parser.parse_async(grammar, text, settings)
    
    print(f"Status: {result.status}")
    print(f"Parse time: {result.parse_time:.4f}s")
    print(f"Grammar hash: {result.grammar_hash}")
    
    if result.error:
        print(f"❌ Error Type: {result.error.type}")
        print(f"❌ Error Message: {result.error.message}")
        if result.error.line:
            print(f"❌ Error Line: {result.error.line}")
        if result.error.column:
            print(f"❌ Error Column: {result.error.column}")
        if result.error.context:
            print(f"❌ Error Context: {result.error.context}")
    
    if result.tree:
        print(f"✅ Tree type: {result.tree.type}")
        print(f"✅ Tree data: {result.tree.data}")
        print(f"✅ Children count: {len(result.tree.children)}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_arithmetic_grammar()) 