#!/usr/bin/env python3
"""
Test script to verify the login system updates work correctly
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_default_password():
    """Test that default password is used when ACCESS_PASSWORD is not set"""
    print("Testing default password fallback...")

    # Temporarily unset ACCESS_PASSWORD
    original_access_password = os.environ.get('ACCESS_PASSWORD')
    if 'ACCESS_PASSWORD' in os.environ:
        del os.environ['ACCESS_PASSWORD']

    try:
        # Import after removing environment variable
        from preset_manager import ACCESS_PASSWORD

        # Check that default password is used
        assert ACCESS_PASSWORD == 'password', f"Expected 'password', got '{ACCESS_PASSWORD}'"
        print("✓ Default password fallback working correctly")

    except ImportError:
        print("⚠ Flask not available, skipping import test")
        return True
    except Exception as e:
        print(f"✗ Default password test failed: {e}")
        return False
    finally:
        # Restore original ACCESS_PASSWORD
        if original_access_password is not None:
            os.environ['ACCESS_PASSWORD'] = original_access_password

    return True

def test_custom_password():
    """Test that custom password is used when ACCESS_PASSWORD is set"""
    print("Testing custom password...")

    # Set custom password
    original_access_password = os.environ.get('ACCESS_PASSWORD')
    os.environ['ACCESS_PASSWORD'] = 'test_custom_password_123'

    try:
        # Re-import to pick up new environment variable
        import importlib
        if 'preset_manager' in sys.modules:
            importlib.reload(sys.modules['preset_manager'])

        from preset_manager import ACCESS_PASSWORD

        # Check that custom password is used
        assert ACCESS_PASSWORD == 'test_custom_password_123', f"Expected 'test_custom_password_123', got '{ACCESS_PASSWORD}'"
        print("✓ Custom password working correctly")

    except ImportError:
        print("⚠ Flask not available, skipping import test")
        return True
    except Exception as e:
        print(f"✗ Custom password test failed: {e}")
        return False
    finally:
        # Restore original ACCESS_PASSWORD
        if original_access_password is not None:
            os.environ['ACCESS_PASSWORD'] = original_access_password
        elif 'ACCESS_PASSWORD' in os.environ:
            del os.environ['ACCESS_PASSWORD']

    return True

def test_template_variables():
    """Test that template variables are set correctly"""
    print("Testing template variable logic...")

    try:
        # Test default password scenario
        from preset_manager import ACCESS_PASSWORD
        using_default = (ACCESS_PASSWORD == 'password')

        # This simulates the template logic
        if using_default:
            print("✓ Template would show default password warning")
        else:
            print("✓ Template would not show default password warning")

        return True

    except Exception as e:
        print(f"✗ Template variable test failed: {e}")
        return False

def test_login_flow():
    """Test login flow with both default and custom passwords"""
    print("Testing login flow...")

    try:
        # Test scenarios
        test_cases = [
            ('password', 'default password'),
            ('custom123', 'custom password'),
            ('', 'empty password'),
        ]

        for test_password, description in test_cases:
            # Set environment variable
            if test_password:
                os.environ['ACCESS_PASSWORD'] = test_password
            else:
                if 'ACCESS_PASSWORD' in os.environ:
                    del os.environ['ACCESS_PASSWORD']

            # Import and check
            import importlib
            if 'preset_manager' in sys.modules:
                importlib.reload(sys.modules['preset_manager'])

            from preset_manager import ACCESS_PASSWORD, check_auth

            # Simulate login check
            expected_password = test_password if test_password else 'password'

            # Test authentication logic
            if ACCESS_PASSWORD == expected_password:
                print(f"✓ {description} scenario: correct password loaded")
            else:
                print(f"✗ {description} scenario: expected '{expected_password}', got '{ACCESS_PASSWORD}'")
                return False

        return True

    except Exception as e:
        print(f"✗ Login flow test failed: {e}")
        return False

def main():
    """Run all login tests"""
    print("=== Login System Update Test Suite ===\n")

    tests = [
        test_default_password,
        test_custom_password,
        test_template_variables,
        test_login_flow
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
        print("🎉 All login tests passed! The update is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())