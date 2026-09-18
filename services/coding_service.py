"""
Coding platform service — problem seeding, code execution (sandboxed subprocess),
and progress tracking.

SECURITY: Student code is run in a subprocess with:
  - Strict 5-second timeout
  - No network access (not directly enforced at OS level on Windows,
    but the subprocess inherits minimal environment)
  - stdout/stderr captured, compared against expected output
  - The code is NEVER executed inside the Flask process
"""

import subprocess
import sys
import os
import tempfile
import json

from database.db import get_db


# ==================================================================
# Code Execution (Sandboxed Subprocess)
# ==================================================================

TIMEOUT_SECONDS = 5

def run_code(source_code, test_input, expected_output):
    """
    Execute student Python code in a subprocess and compare output.

    Returns dict:
        {
            'status': 'pass' | 'fail' | 'error' | 'timeout',
            'actual_output': str,
            'expected_output': str,
            'error_message': str | None,
        }
    """
    # Write code to a temp file (we never exec() it inside Flask)
    tmp_dir = tempfile.mkdtemp(prefix='scp_code_')
    code_file = os.path.join(tmp_dir, 'solution.py')

    try:
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(source_code)

        # Build a restricted environment — strip PATH-like vars to reduce attack surface
        safe_env = {
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONDONTWRITEBYTECODE': '1',
        }
        # On Windows we need SystemRoot for subprocess to work
        if os.name == 'nt':
            safe_env['SystemRoot'] = os.environ.get('SystemRoot', r'C:\Windows')
            safe_env['PATH'] = os.path.dirname(sys.executable)

        result = subprocess.run(
            [sys.executable, '-u', code_file],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env=safe_env,
            cwd=tmp_dir,  # isolate working directory
        )

        actual = result.stdout.strip()
        expected = expected_output.strip()

        if result.returncode != 0:
            return {
                'status': 'error',
                'actual_output': actual,
                'expected_output': expected,
                'error_message': result.stderr.strip()[:1000],  # cap error length
            }

        if actual == expected:
            return {
                'status': 'pass',
                'actual_output': actual,
                'expected_output': expected,
                'error_message': None,
            }
        else:
            return {
                'status': 'fail',
                'actual_output': actual,
                'expected_output': expected,
                'error_message': None,
            }

    except subprocess.TimeoutExpired:
        return {
            'status': 'timeout',
            'actual_output': '',
            'expected_output': expected_output.strip(),
            'error_message': f'Code execution exceeded {TIMEOUT_SECONDS} second time limit.',
        }
    except Exception as e:
        return {
            'status': 'error',
            'actual_output': '',
            'expected_output': expected_output.strip(),
            'error_message': str(e)[:500],
        }
    finally:
        # Clean up temp files
        try:
            os.remove(code_file)
            os.rmdir(tmp_dir)
        except OSError:
            pass


def run_all_tests(source_code, problem_id):
    """
    Run student code against ALL test cases for a problem.

    Returns dict:
        {
            'overall': 'accepted' | 'wrong_answer' | 'error' | 'timeout',
            'passed': int,
            'total': int,
            'results': [per-test-case result dicts],
        }
    """
    db = get_db()
    test_cases = db.execute(
        'SELECT * FROM test_cases WHERE problem_id = ? ORDER BY is_sample DESC, id ASC',
        (problem_id,),
    ).fetchall()

    if not test_cases:
        return {
            'overall': 'error',
            'passed': 0,
            'total': 0,
            'results': [],
            'error_message': 'No test cases found for this problem.',
        }

    results = []
    passed = 0

    for tc in test_cases:
        res = run_code(source_code, tc['input_data'], tc['expected_output'])
        res['test_case_id'] = tc['id']
        res['is_sample'] = bool(tc['is_sample'])
        results.append(res)

        if res['status'] == 'pass':
            passed += 1
        elif res['status'] == 'timeout':
            # Stop on first timeout — no point continuing
            break
        elif res['status'] == 'error':
            break

    total = len(test_cases)

    if passed == total:
        overall = 'accepted'
    elif any(r['status'] == 'timeout' for r in results):
        overall = 'timeout'
    elif any(r['status'] == 'error' for r in results):
        overall = 'error'
    else:
        overall = 'wrong_answer'

    return {
        'overall': overall,
        'passed': passed,
        'total': total,
        'results': results,
    }


# ==================================================================
# Coding Progress / Dashboard
# ==================================================================

def get_coding_summary(user_id):
    """Build coding progress summary for the dashboard."""
    db = get_db()

    # Total problems
    total = db.execute('SELECT COUNT(*) AS n FROM coding_problems').fetchone()['n']

    # Solved by this user (at least one 'accepted' submission)
    solved = db.execute(
        "SELECT COUNT(DISTINCT problem_id) AS n FROM coding_submissions "
        "WHERE user_id = ? AND result = 'accepted'",
        (user_id,),
    ).fetchone()['n']

    # Attempted (submitted but not necessarily solved)
    attempted = db.execute(
        'SELECT COUNT(DISTINCT problem_id) AS n FROM coding_submissions WHERE user_id = ?',
        (user_id,),
    ).fetchone()['n']

    # Topic-wise breakdown
    topics = db.execute(
        '''SELECT p.topic,
                  COUNT(DISTINCT p.id) AS total,
                  COUNT(DISTINCT CASE WHEN s.result = 'accepted' THEN p.id END) AS solved
           FROM coding_problems p
           LEFT JOIN coding_submissions s ON p.id = s.problem_id AND s.user_id = ?
           GROUP BY p.topic
           ORDER BY p.topic''',
        (user_id,),
    ).fetchall()

    # Difficulty-wise breakdown
    difficulties = db.execute(
        '''SELECT p.difficulty,
                  COUNT(DISTINCT p.id) AS total,
                  COUNT(DISTINCT CASE WHEN s.result = 'accepted' THEN p.id END) AS solved
           FROM coding_problems p
           LEFT JOIN coding_submissions s ON p.id = s.problem_id AND s.user_id = ?
           GROUP BY p.difficulty
           ORDER BY CASE p.difficulty WHEN 'easy' THEN 1 WHEN 'medium' THEN 2 WHEN 'hard' THEN 3 END''',
        (user_id,),
    ).fetchall()

    # Recent submissions
    recent = db.execute(
        '''SELECT s.*, p.title AS problem_title, p.difficulty
           FROM coding_submissions s
           JOIN coding_problems p ON s.problem_id = p.id
           WHERE s.user_id = ?
           ORDER BY s.submitted_at DESC LIMIT 10''',
        (user_id,),
    ).fetchall()

    return {
        'total': total,
        'solved': solved,
        'attempted': attempted,
        'remaining': total - solved,
        'topics': [dict(t) for t in topics],
        'difficulties': [dict(d) for d in difficulties],
        'recent': recent,
        'solve_rate': round((solved / total * 100), 1) if total > 0 else 0,
    }


# ==================================================================
# Problem Seeding — ~20 problems across 10 topics
# ==================================================================

SEED_PROBLEMS = [
    # ---- Arrays ----
    {
        'title': 'Two Sum',
        'topic': 'arrays',
        'difficulty': 'easy',
        'description': (
            'Given an array of integers and a target sum, find two numbers that add up to the target.\n\n'
            'Print the indices (0-based) of the two numbers separated by a space. '
            'There is exactly one solution.'
        ),
        'input_format': 'First line: space-separated integers (the array).\nSecond line: the target sum.',
        'output_format': 'Two space-separated indices.',
        'examples': 'Input:\n2 7 11 15\n9\n\nOutput:\n0 1',
        'test_cases': [
            {'input': '2 7 11 15\n9', 'output': '0 1', 'sample': True},
            {'input': '3 2 4\n6', 'output': '1 2', 'sample': False},
            {'input': '1 5 3 7 2\n9', 'output': '1 3', 'sample': False},
        ],
    },
    {
        'title': 'Maximum Element',
        'topic': 'arrays',
        'difficulty': 'easy',
        'description': 'Given an array of integers, find and print the maximum element.',
        'input_format': 'A single line of space-separated integers.',
        'output_format': 'The maximum integer.',
        'examples': 'Input:\n3 1 4 1 5 9 2 6\n\nOutput:\n9',
        'test_cases': [
            {'input': '3 1 4 1 5 9 2 6', 'output': '9', 'sample': True},
            {'input': '-5 -2 -8 -1', 'output': '-1', 'sample': False},
            {'input': '42', 'output': '42', 'sample': False},
        ],
    },
    # ---- Strings ----
    {
        'title': 'Reverse String',
        'topic': 'strings',
        'difficulty': 'easy',
        'description': 'Given a string, print it reversed.',
        'input_format': 'A single line string.',
        'output_format': 'The reversed string.',
        'examples': 'Input:\nhello\n\nOutput:\nolleh',
        'test_cases': [
            {'input': 'hello', 'output': 'olleh', 'sample': True},
            {'input': 'racecar', 'output': 'racecar', 'sample': False},
            {'input': 'Python', 'output': 'nohtyP', 'sample': False},
        ],
    },
    {
        'title': 'Palindrome Check',
        'topic': 'strings',
        'difficulty': 'easy',
        'description': 'Given a string, determine if it is a palindrome (reads the same forwards and backwards). Ignore case.',
        'input_format': 'A single line string.',
        'output_format': 'Print "Yes" if palindrome, "No" otherwise.',
        'examples': 'Input:\nRacecar\n\nOutput:\nYes',
        'test_cases': [
            {'input': 'Racecar', 'output': 'Yes', 'sample': True},
            {'input': 'hello', 'output': 'No', 'sample': False},
            {'input': 'Madam', 'output': 'Yes', 'sample': False},
        ],
    },
    # ---- Searching ----
    {
        'title': 'Binary Search',
        'topic': 'searching',
        'difficulty': 'easy',
        'description': (
            'Given a sorted array of integers and a target value, find the index of the target using binary search.\n\n'
            'If the target is not found, print -1.'
        ),
        'input_format': 'First line: space-separated sorted integers.\nSecond line: the target value.',
        'output_format': 'The 0-based index of the target, or -1.',
        'examples': 'Input:\n1 3 5 7 9 11\n7\n\nOutput:\n3',
        'test_cases': [
            {'input': '1 3 5 7 9 11\n7', 'output': '3', 'sample': True},
            {'input': '2 4 6 8 10\n5', 'output': '-1', 'sample': False},
            {'input': '1 2 3 4 5\n1', 'output': '0', 'sample': False},
        ],
    },
    {
        'title': 'Count Occurrences',
        'topic': 'searching',
        'difficulty': 'easy',
        'description': 'Given an array of integers and a target value, count how many times the target appears.',
        'input_format': 'First line: space-separated integers.\nSecond line: the target value.',
        'output_format': 'The count of occurrences.',
        'examples': 'Input:\n1 2 3 2 4 2 5\n2\n\nOutput:\n3',
        'test_cases': [
            {'input': '1 2 3 2 4 2 5\n2', 'output': '3', 'sample': True},
            {'input': '5 5 5 5\n5', 'output': '4', 'sample': False},
            {'input': '1 2 3\n7', 'output': '0', 'sample': False},
        ],
    },
    # ---- Sorting ----
    {
        'title': 'Sort Array',
        'topic': 'sorting',
        'difficulty': 'easy',
        'description': 'Given an array of integers, sort them in ascending order and print the result.',
        'input_format': 'A single line of space-separated integers.',
        'output_format': 'Space-separated integers in ascending order.',
        'examples': 'Input:\n5 3 8 1 2\n\nOutput:\n1 2 3 5 8',
        'test_cases': [
            {'input': '5 3 8 1 2', 'output': '1 2 3 5 8', 'sample': True},
            {'input': '9 7 5 3 1', 'output': '1 3 5 7 9', 'sample': False},
            {'input': '1', 'output': '1', 'sample': False},
        ],
    },
    {
        'title': 'Kth Largest Element',
        'topic': 'sorting',
        'difficulty': 'medium',
        'description': 'Given an array of integers and a value k, find the kth largest element.',
        'input_format': 'First line: space-separated integers.\nSecond line: the value k.',
        'output_format': 'The kth largest element.',
        'examples': 'Input:\n3 2 1 5 6 4\n2\n\nOutput:\n5',
        'test_cases': [
            {'input': '3 2 1 5 6 4\n2', 'output': '5', 'sample': True},
            {'input': '3 2 3 1 2 4 5 5 6\n4', 'output': '4', 'sample': False},
            {'input': '1\n1', 'output': '1', 'sample': False},
        ],
    },
    # ---- Recursion ----
    {
        'title': 'Factorial',
        'topic': 'recursion',
        'difficulty': 'easy',
        'description': 'Calculate the factorial of a given non-negative integer n using recursion.',
        'input_format': 'A single integer n (0 <= n <= 20).',
        'output_format': 'The factorial of n.',
        'examples': 'Input:\n5\n\nOutput:\n120',
        'test_cases': [
            {'input': '5', 'output': '120', 'sample': True},
            {'input': '0', 'output': '1', 'sample': False},
            {'input': '10', 'output': '3628800', 'sample': False},
        ],
    },
    {
        'title': 'Fibonacci Number',
        'topic': 'recursion',
        'difficulty': 'easy',
        'description': 'Given n, find the nth Fibonacci number (0-indexed: F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)).',
        'input_format': 'A single integer n (0 <= n <= 30).',
        'output_format': 'The nth Fibonacci number.',
        'examples': 'Input:\n6\n\nOutput:\n8',
        'test_cases': [
            {'input': '6', 'output': '8', 'sample': True},
            {'input': '0', 'output': '0', 'sample': False},
            {'input': '10', 'output': '55', 'sample': False},
        ],
    },
    # ---- Linked Lists ----
    {
        'title': 'Reverse Linked List',
        'topic': 'linked lists',
        'difficulty': 'medium',
        'description': (
            'Given a singly linked list as space-separated values, reverse it and print the reversed list.\n\n'
            'Simulate the linked list using a Python list.'
        ),
        'input_format': 'A single line of space-separated integers representing the linked list.',
        'output_format': 'Space-separated integers in reversed order.',
        'examples': 'Input:\n1 2 3 4 5\n\nOutput:\n5 4 3 2 1',
        'test_cases': [
            {'input': '1 2 3 4 5', 'output': '5 4 3 2 1', 'sample': True},
            {'input': '10 20 30', 'output': '30 20 10', 'sample': False},
            {'input': '1', 'output': '1', 'sample': False},
        ],
    },
    {
        'title': 'Detect Cycle Length',
        'topic': 'linked lists',
        'difficulty': 'medium',
        'description': (
            'Given a list of integers, determine the length of the first repeated subsequence.\n\n'
            'Specifically, find the first element that appears twice and print the distance '
            'between its two occurrences. If no element repeats, print 0.'
        ),
        'input_format': 'A single line of space-separated integers.',
        'output_format': 'The distance between the two occurrences of the first repeated element, or 0.',
        'examples': 'Input:\n1 2 3 4 2 5\n\nOutput:\n3',
        'test_cases': [
            {'input': '1 2 3 4 2 5', 'output': '3', 'sample': True},
            {'input': '1 2 3 4 5', 'output': '0', 'sample': False},
            {'input': '5 5', 'output': '1', 'sample': False},
        ],
    },
    # ---- Stacks ----
    {
        'title': 'Valid Parentheses',
        'topic': 'stacks',
        'difficulty': 'easy',
        'description': (
            'Given a string containing only parentheses (), brackets [], and braces {}, '
            'determine if the input string is valid.\n\n'
            'A string is valid if every opening bracket has a matching closing bracket in the correct order.'
        ),
        'input_format': 'A single line string of brackets.',
        'output_format': 'Print "Valid" or "Invalid".',
        'examples': 'Input:\n({[]})\n\nOutput:\nValid',
        'test_cases': [
            {'input': '({[]})', 'output': 'Valid', 'sample': True},
            {'input': '({[})', 'output': 'Invalid', 'sample': False},
            {'input': '()', 'output': 'Valid', 'sample': False},
            {'input': '((', 'output': 'Invalid', 'sample': False},
        ],
    },
    {
        'title': 'Next Greater Element',
        'topic': 'stacks',
        'difficulty': 'medium',
        'description': (
            'For each element in an array, find the next greater element to its right. '
            'If no greater element exists, use -1.'
        ),
        'input_format': 'A single line of space-separated integers.',
        'output_format': 'Space-separated next greater elements.',
        'examples': 'Input:\n4 5 2 25\n\nOutput:\n5 25 25 -1',
        'test_cases': [
            {'input': '4 5 2 25', 'output': '5 25 25 -1', 'sample': True},
            {'input': '13 7 6 12', 'output': '-1 12 12 -1', 'sample': False},
            {'input': '1 2 3 4', 'output': '2 3 4 -1', 'sample': False},
        ],
    },
    # ---- Queues ----
    {
        'title': 'Queue Using Stacks',
        'topic': 'queues',
        'difficulty': 'medium',
        'description': (
            'Simulate a queue using operations. Process commands:\n'
            '- "enqueue X": add X to the queue\n'
            '- "dequeue": remove and print the front element\n'
            '- "peek": print the front element without removing\n\n'
            'If dequeue or peek is called on an empty queue, print "Empty".'
        ),
        'input_format': 'First line: number of operations n.\nNext n lines: operations.',
        'output_format': 'Output for each dequeue/peek operation, one per line.',
        'examples': 'Input:\n5\nenqueue 1\nenqueue 2\npeek\ndequeue\ndequeue\n\nOutput:\n1\n1\n2',
        'test_cases': [
            {'input': '5\nenqueue 1\nenqueue 2\npeek\ndequeue\ndequeue', 'output': '1\n1\n2', 'sample': True},
            {'input': '3\ndequeue\nenqueue 5\ndequeue', 'output': 'Empty\n5', 'sample': False},
        ],
    },
    {
        'title': 'Generate Binary Numbers',
        'topic': 'queues',
        'difficulty': 'easy',
        'description': 'Given a number n, generate binary representations of 1 to n using a queue-based approach.',
        'input_format': 'A single integer n.',
        'output_format': 'Binary representations from 1 to n, one per line.',
        'examples': 'Input:\n5\n\nOutput:\n1\n10\n11\n100\n101',
        'test_cases': [
            {'input': '5', 'output': '1\n10\n11\n100\n101', 'sample': True},
            {'input': '3', 'output': '1\n10\n11', 'sample': False},
            {'input': '1', 'output': '1', 'sample': False},
        ],
    },
    # ---- Trees ----
    {
        'title': 'Tree Traversal',
        'topic': 'trees',
        'difficulty': 'medium',
        'description': (
            'Given a binary tree represented as a level-order array (use -1 for null nodes), '
            'print the inorder traversal.\n\n'
            'Example tree: [1, 2, 3, 4, 5, -1, -1] represents:\n'
            '       1\n      / \\\n     2   3\n    / \\\n   4   5'
        ),
        'input_format': 'A single line of space-separated integers (-1 for null).',
        'output_format': 'Space-separated inorder traversal values.',
        'examples': 'Input:\n1 2 3 4 5 -1 -1\n\nOutput:\n4 2 5 1 3',
        'test_cases': [
            {'input': '1 2 3 4 5 -1 -1', 'output': '4 2 5 1 3', 'sample': True},
            {'input': '1 -1 2 -1 3', 'output': '1 2 3', 'sample': False},
            {'input': '5', 'output': '5', 'sample': False},
        ],
    },
    {
        'title': 'Max Depth of Tree',
        'topic': 'trees',
        'difficulty': 'easy',
        'description': (
            'Given a binary tree represented as a level-order array (-1 for null), '
            'find the maximum depth (height) of the tree.'
        ),
        'input_format': 'A single line of space-separated integers (-1 for null).',
        'output_format': 'The maximum depth as an integer.',
        'examples': 'Input:\n1 2 3 4 5 -1 -1\n\nOutput:\n3',
        'test_cases': [
            {'input': '1 2 3 4 5 -1 -1', 'output': '3', 'sample': True},
            {'input': '1', 'output': '1', 'sample': False},
            {'input': '1 2 -1 3 -1', 'output': '3', 'sample': False},
        ],
    },
    # ---- Dynamic Programming ----
    {
        'title': 'Climbing Stairs',
        'topic': 'dynamic programming',
        'difficulty': 'easy',
        'description': (
            'You are climbing a staircase of n steps. Each time you can climb 1 or 2 steps. '
            'How many distinct ways can you reach the top?'
        ),
        'input_format': 'A single integer n.',
        'output_format': 'The number of distinct ways.',
        'examples': 'Input:\n5\n\nOutput:\n8',
        'test_cases': [
            {'input': '5', 'output': '8', 'sample': True},
            {'input': '1', 'output': '1', 'sample': False},
            {'input': '10', 'output': '89', 'sample': False},
        ],
    },
    {
        'title': 'Longest Common Subsequence',
        'topic': 'dynamic programming',
        'difficulty': 'hard',
        'description': 'Given two strings, find the length of their longest common subsequence.',
        'input_format': 'First line: string s1.\nSecond line: string s2.',
        'output_format': 'The length of the LCS.',
        'examples': 'Input:\nabcde\nace\n\nOutput:\n3',
        'test_cases': [
            {'input': 'abcde\nace', 'output': '3', 'sample': True},
            {'input': 'abc\nabc', 'output': '3', 'sample': False},
            {'input': 'abc\ndef', 'output': '0', 'sample': False},
        ],
    },
]


def seed_problems():
    """Insert seed problems and test cases if the problems table is empty."""
    db = get_db()
    existing = db.execute('SELECT COUNT(*) AS n FROM coding_problems').fetchone()['n']
    if existing > 0:
        return  # already seeded

    for prob in SEED_PROBLEMS:
        cursor = db.execute(
            '''INSERT INTO coding_problems (title, topic, difficulty, description,
               input_format, output_format, examples)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (prob['title'], prob['topic'], prob['difficulty'],
             prob['description'], prob['input_format'],
             prob['output_format'], prob['examples']),
        )
        problem_id = cursor.lastrowid

        for tc in prob['test_cases']:
            db.execute(
                '''INSERT INTO test_cases (problem_id, input_data, expected_output, is_sample)
                   VALUES (?, ?, ?, ?)''',
                (problem_id, tc['input'], tc['output'], 1 if tc['sample'] else 0),
            )

    db.commit()
    print(f'  [OK] Seeded {len(SEED_PROBLEMS)} coding problems with test cases')
