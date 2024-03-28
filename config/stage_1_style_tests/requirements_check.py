"""
Checks dependencies.
"""
import re
import sys
from pathlib import Path

from config.constants import PROJECT_ROOT


def get_paths() -> list[Path]:
    """
    Get paths to non-python files.

    Returns:
        list[Path]: Paths to non-python files
    """
    list_with_paths = []
    for file in PROJECT_ROOT.iterdir():
        if file.name in ['requirements.txt', 'requirements_qa.txt']:
            list_with_paths.append(file)
    return list_with_paths


def get_requirements(path: Path) -> list:
    """
    Get dependencies.

    Args:
        path (Path): Path to non-python file

    Returns:
        list: Dependencies
    """
    with path.open(encoding='utf-8') as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]


def compile_pattern() -> re.Pattern:
    """
    Compile pattern.

    Returns:
        re.Pattern: Compiled pattern
    """
    return re.compile(r'\w+(-\w+|\[\w+\])*==\d+(\.\d+)+')


def check_dependencies(lines: list, compiled_pattern: re.Pattern) -> bool:
    """
    Check that dependencies confirm to the template.

    Args:
        lines (list): Dependencies
        compiled_pattern (re.Pattern): Compiled pattern

    Returns:
        bool: Do dependencies confirm to the template or not
    """
    expected = list(sorted(map(str.lower, lines)))
    if expected != list(map(str.lower, lines)):
        print('Dependencies in requirements.txt do not follow sorting rule.')
        print('Expected:')
        print('\n'.join(expected))
        return False
    for line in lines:
        if not re.search(compiled_pattern, line):
            print('Specific dependency in requirements.txt do not conform to the template.')
            print(line)
            return False
    return True


def main() -> None:
    """
    Call functions.
    """
    paths = get_paths()
    compiled_pattern = compile_pattern()
    for path in paths:
        lines = get_requirements(path)
        if not check_dependencies(lines, compiled_pattern):
            sys.exit(1)
        else:
            print(f'{path.name} : OK.')


if __name__ == '__main__':
    main()
