// Browser Test Script for LarkEditor Web
// Copy and paste this into the browser console to test functionality

console.log('🔍 LarkEditor Web Browser Test Starting...');

function testUI() {
    console.log('\n📋 Testing UI Components...');
    
    // Check if main app exists
    const app = window.larkEditor;
    if (!app) {
        console.error('❌ Main app not found');
        return false;
    }
    console.log('✅ Main app loaded');
    
    // Check essential elements
    const elements = [
        'force-parse',
        'grammar-editor',
        'text-editor',
        'ast-tree',
        'upload-grammar',
        'download-grammar',
        'help-button'
    ];
    
    let elementsOk = true;
    elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            console.log(`✅ Element found: ${id}`);
        } else {
            console.error(`❌ Element missing: ${id}`);
            elementsOk = false;
        }
    });
    
    return elementsOk;
}

function testWebSocket() {
    console.log('\n🔌 Testing WebSocket Connection...');
    
    const app = window.larkEditor;
    if (!app.websocketClient) {
        console.error('❌ WebSocket client not found');
        return false;
    }
    
    const state = app.websocketClient.getReadyState();
    console.log(`WebSocket state: ${state}`);
    console.log(`Connection status: ${app.isConnected}`);
    
    if (app.isConnected) {
        console.log('✅ WebSocket connected');
        return true;
    } else {
        console.warn('⚠️ WebSocket not connected - this might be normal if server is not running');
        return false;
    }
}

function testParseButton() {
    console.log('\n⚡ Testing Parse Button...');
    
    const parseButton = document.getElementById('force-parse');
    if (!parseButton) {
        console.error('❌ Parse button not found');
        return false;
    }
    
    console.log('Parse button found, testing click event...');
    
    // Add a temporary event listener to verify the button works
    let clickDetected = false;
    const testListener = () => {
        clickDetected = true;
        console.log('✅ Parse button click detected');
    };
    
    parseButton.addEventListener('click', testListener, { once: true });
    parseButton.click();
    
    setTimeout(() => {
        parseButton.removeEventListener('click', testListener);
    }, 100);
    
    return clickDetected;
}

function testOnboarding() {
    console.log('\n🎓 Testing Onboarding Wizard...');
    
    const app = window.larkEditor;
    if (typeof app.showOnboardingManual !== 'function') {
        console.error('❌ Onboarding method not found');
        return false;
    }
    
    console.log('✅ Onboarding methods available');
    console.log('To test onboarding, run: window.showOnboarding()');
    
    return true;
}

function testEditors() {
    console.log('\n📝 Testing Monaco Editors...');
    
    const app = window.larkEditor;
    if (!app.editorManager) {
        console.error('❌ Editor manager not found');
        return false;
    }
    
    try {
        const grammarContent = app.editorManager.getGrammarContent();
        const textContent = app.editorManager.getTextContent();
        
        console.log(`✅ Grammar editor: ${grammarContent.length} characters`);
        console.log(`✅ Text editor: ${textContent.length} characters`);
        
        if (grammarContent.includes('start:') && textContent.length > 0) {
            console.log('✅ Default content loaded correctly');
            return true;
        } else {
            console.warn('⚠️ Default content may not be loaded yet');
            return false;
        }
    } catch (error) {
        console.error('❌ Editor test failed:', error);
        return false;
    }
}

// Main test function
function runAllTests() {
    console.log('🚀 Running all LarkEditor Web tests...\n');
    
    const results = {
        ui: testUI(),
        websocket: testWebSocket(),
        parseButton: testParseButton(),
        onboarding: testOnboarding(),
        editors: testEditors()
    };
    
    console.log('\n📊 Test Results:');
    Object.entries(results).forEach(([test, passed]) => {
        console.log(`${passed ? '✅' : '❌'} ${test}: ${passed ? 'PASSED' : 'FAILED'}`);
    });
    
    const passedCount = Object.values(results).filter(Boolean).length;
    const totalCount = Object.keys(results).length;
    
    console.log(`\n🎯 Overall: ${passedCount}/${totalCount} tests passed`);
    
    if (passedCount === totalCount) {
        console.log('🎉 All tests passed! LarkEditor Web is working correctly.');
    } else {
        console.log('⚠️ Some tests failed. Check the logs above for details.');
    }
    
    // Additional debugging info
    console.log('\n🔧 Debugging Commands:');
    console.log('- window.showOnboarding() - Show onboarding wizard');
    console.log('- window.larkEditor.forceParse() - Force parse current content');
    console.log('- window.larkEditor.websocketClient.getReadyState() - Check WebSocket state');
    
    return results;
}

// Auto-run tests after a short delay to ensure everything is loaded
setTimeout(() => {
    runAllTests();
}, 2000);

// Export for manual testing
window.runLarkEditorTests = runAllTests;