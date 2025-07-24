#!/usr/bin/env python3
"""Test script for analyzing session configuration."""

import json
from app.core.state import get_session_manager
from app.models.requests import ParseSettings, ParserType

def test_session_config():
    """Test the provided session configuration."""
    # Create session data matching the provided JSON
    session_data = {
        'session_id': 'session_d07zvm5hc_1749667699355',
        'connection_count': 1,
        'has_grammar': True,
        'has_text': False,
        'settings': {
            'parser': 'earley',
            'start_rule': 'start',
            'debug': False
        }
    }

    print('📊 Session Configuration Analysis:')
    print(f'Session ID: {session_data["session_id"]}')
    print(f'Connections: {session_data["connection_count"]}')
    print(f'Grammar loaded: {session_data["has_grammar"]}')
    print(f'Text available: {session_data["has_text"]}')
    print(f'Parser type: {session_data["settings"]["parser"]}')
    print(f'Start rule: {session_data["settings"]["start_rule"]}')
    print(f'Debug mode: {session_data["settings"]["debug"]}')

    # Test ParseSettings creation
    try:
        settings = ParseSettings(
            parser=ParserType.EARLEY,
            start_rule=session_data['settings']['start_rule'],
            debug=session_data['settings']['debug']
        )
        print(f'\n✅ ParseSettings created successfully:')
        print(f'   Parser: {settings.parser}')
        print(f'   Start rule: {settings.start_rule}')
        print(f'   Debug: {settings.debug}')
        return True
    except Exception as e:
        print(f'\n❌ Error creating ParseSettings: {e}')
        return False

if __name__ == "__main__":
    test_session_config() 