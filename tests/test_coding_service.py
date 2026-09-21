import pytest
from services.coding_service import run_code

def test_run_code_pass():
    """Test a submission that correctly solves the problem and passes."""
    source_code = "print(eval(input()))"
    test_input = "2 + 2\n"
    expected_output = "4\n"
    
    result = run_code(source_code, test_input, expected_output)
    
    assert result['status'] == 'pass'
    assert result['actual_output'] == '4'
    assert result['error_message'] is None

def test_run_code_fail():
    """Test a submission that completes but returns the wrong answer."""
    source_code = "print('5')"  # Hardcoded wrong answer
    test_input = "2 + 2\n"
    expected_output = "4\n"
    
    result = run_code(source_code, test_input, expected_output)
    
    assert result['status'] == 'fail'
    assert result['actual_output'] == '5'
    assert result['expected_output'] == '4'

def test_run_code_timeout():
    """Test a submission that hangs infinitely to verify sandbox timeout."""
    # This code loops forever and will trigger the 5-second subprocess timeout
    source_code = "while True:\n    pass"
    test_input = "1\n"
    expected_output = "1\n"
    
    result = run_code(source_code, test_input, expected_output)
    
    assert result['status'] == 'timeout'
    assert result['actual_output'] == ''
    assert "Timeout" in result['error_message'] or result['error_message'] != ""

def test_run_code_error():
    """Test a submission with a syntax error."""
    source_code = "print(1 / 0)"
    test_input = ""
    expected_output = ""
    
    result = run_code(source_code, test_input, expected_output)
    
    assert result['status'] == 'error'
    assert "ZeroDivisionError" in result['error_message']
