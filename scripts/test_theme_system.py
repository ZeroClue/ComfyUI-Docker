#!/usr/bin/env python3
"""
Test script to validate the theme system implementation
"""

import os
import re
import sys

def test_css_variables():
    """Test that CSS variables are properly defined"""
    print("Testing CSS variables...")

    try:
        # Read base template
        with open('templates/base.html', 'r') as f:
            base_content = f.read()

        # Check for CSS variables in light theme
        light_vars = [
            '--bg-primary: #ffffff',
            '--bg-secondary: #f8f9fa',
            '--text-primary: #212529',
            '--card-bg: #ffffff'
        ]

        for var in light_vars:
            if var not in base_content:
                print(f"✗ Missing light theme variable: {var}")
                return False

        # Check for CSS variables in dark theme
        dark_vars = [
            '--bg-primary: #1a1d23',
            '--bg-secondary: #2d3139',
            '--text-primary: #e9ecef',
            '--card-bg: #2d3139'
        ]

        for var in dark_vars:
            if var not in base_content:
                print(f"✗ Missing dark theme variable: {var}")
                return False

        print("✓ CSS variables properly defined")
        return True

    except Exception as e:
        print(f"✗ CSS variables test failed: {e}")
        return False

def test_theme_toggle_button():
    """Test that theme toggle button is present"""
    print("Testing theme toggle button...")

    try:
        # Read base template
        with open('templates/base.html', 'r') as f:
            base_content = f.read()

        # Check for theme toggle button
        if 'theme-toggle' not in base_content:
            print("✗ Theme toggle button not found in base template")
            return False

        if 'onclick="toggleTheme()"' not in base_content:
            print("✗ Theme toggle onclick handler not found")
            return False

        if 'id="themeIcon"' not in base_content:
            print("✗ Theme icon element not found")
            return False

        print("✓ Theme toggle button properly implemented")
        return True

    except Exception as e:
        print(f"✗ Theme toggle button test failed: {e}")
        return False

def test_javascript_theme_manager():
    """Test that JavaScript theme manager is implemented"""
    print("Testing JavaScript theme manager...")

    try:
        # Read base template
        with open('templates/base.html', 'r') as f:
            base_content = f.read()

        # Check for ThemeManager class
        if 'class ThemeManager' not in base_content:
            print("✗ ThemeManager class not found")
            return False

        # Check for key methods
        required_methods = [
            'loadTheme()',
            'setTheme(theme)',
            'toggle()',
            'updateToggleIcon(theme)'
        ]

        for method in required_methods:
            if method not in base_content:
                print(f"✗ Missing ThemeManager method: {method}")
                return False

        # Check for default dark theme
        if "const theme = savedTheme || 'dark'" not in base_content:
            print("✗ Dark theme not set as default")
            return False

        # Check for localStorage persistence
        if 'localStorage.setItem(\'theme\', theme)' not in base_content:
            print("✗ Theme persistence not implemented")
            return False

        print("✓ JavaScript theme manager properly implemented")
        return True

    except Exception as e:
        print(f"✗ JavaScript theme manager test failed: {e}")
        return False

def test_chart_integration():
    """Test that Chart.js integration is implemented"""
    print("Testing Chart.js integration...")

    try:
        # Read base template
        with open('templates/base.html', 'r') as f:
            base_content = f.read()

        # Check for chart theme management
        if 'updateCharts(theme)' not in base_content:
            print("✗ Chart theme updating not found")
            return False

        if 'updateChartColors(chart, theme)' not in base_content:
            print("✗ Chart color updating not found")
            return False

        if 'registerChart(chart)' not in base_content:
            print("✗ Chart registration not found")
            return False

        # Check index template for chart registration
        with open('templates/index.html', 'r') as f:
            index_content = f.read()

        if 'themeManager.registerChart(' not in index_content:
            print("✗ Charts not registered with theme manager in index template")
            return False

        print("✓ Chart integration properly implemented")
        return True

    except Exception as e:
        print(f"✗ Chart integration test failed: {e}")
        return False

def test_login_page_theming():
    """Test that login page theming is implemented"""
    print("Testing login page theming...")

    try:
        # Read login template
        with open('templates/login.html', 'r') as f:
            login_content = f.read()

        # Check for login theme variables
        if '--login-bg:' not in login_content:
            print("✗ Login background variable not found")
            return False

        if '[data-theme="dark"]' not in login_content:
            print("✗ Dark theme selector not found in login page")
            return False

        # Check for login theme toggle
        if 'login-theme-toggle' not in login_content:
            print("✗ Login theme toggle button not found")
            return False

        # Check for LoginThemeManager class
        if 'class LoginThemeManager' not in login_content:
            print("✗ LoginThemeManager class not found")
            return False

        print("✓ Login page theming properly implemented")
        return True

    except Exception as e:
        print(f"✗ Login page theming test failed: {e}")
        return False

def test_transition_effects():
    """Test that transition effects are implemented"""
    print("Testing transition effects...")

    try:
        # Read base template
        with open('templates/base.html', 'r') as f:
            base_content = f.read()

        # Check for CSS transitions
        transition_patterns = [
            'transition: background-color 0.3s ease',
            'transition: color 0.3s ease',
            'transition: all 0.3s ease'
        ]

        found_transitions = 0
        for pattern in transition_patterns:
            if pattern in base_content:
                found_transitions += 1

        if found_transitions < 2:
            print(f"✗ Insufficient transition effects found ({found_transitions}/3)")
            return False

        # Check for theme toggle icon animation
        if 'transform: rotate(20deg)' not in base_content:
            print("✗ Theme toggle icon animation not found")
            return False

        print("✓ Transition effects properly implemented")
        return True

    except Exception as e:
        print(f"✗ Transition effects test failed: {e}")
        return False

def test_template_consistency():
    """Test that templates are consistent"""
    print("Testing template consistency...")

    try:
        # Check if all required template files exist
        required_templates = [
            'templates/base.html',
            'templates/login.html',
            'templates/index.html',
            'templates/presets.html',
            'templates/preset_detail.html',
            'templates/storage.html'
        ]

        for template in required_templates:
            if not os.path.exists(template):
                print(f"✗ Missing template: {template}")
                return False

        print("✓ All required templates exist")
        return True

    except Exception as e:
        print(f"✗ Template consistency test failed: {e}")
        return False

def main():
    """Run all theme system tests"""
    print("=== Theme System Test Suite ===\n")

    tests = [
        test_css_variables,
        test_theme_toggle_button,
        test_javascript_theme_manager,
        test_chart_integration,
        test_login_page_theming,
        test_transition_effects,
        test_template_consistency
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("🎉 All theme system tests passed! The implementation is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())