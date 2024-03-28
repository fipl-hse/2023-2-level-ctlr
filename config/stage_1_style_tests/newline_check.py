"""
Check newline at the end.
"""
import sys

from config.constants import PROJECT_ROOT


def get_paths() -> list:
    """
    Get paths to non-python files.

    Returns:
        list: Paths to non-python files
    """
    paths_to_exclude = [
        'venv',
        '.git',
        '.idea',
        '.coverage',
        '.mypy_cache',
        '.pytest_cache',
        'build',
        'russian-syntagrus-ud-2.0-170801.udpipe'
    ]

    list_with_paths = []
    for file in PROJECT_ROOT.iterdir():
        if file.name in paths_to_exclude or file.name.endswith('.udpipe'):
            continue
        if file.is_dir():
            list_with_paths.extend(sorted(file.rglob('*')))
        else:
            list_with_paths.append(file)
    return list_with_paths


def check_paths(list_with_paths: list) -> list:
    """
    Check if the path is correct.

    Args:
        list_with_paths (list): Paths to non-python files

    Returns:
        list: Appropriate paths
    """
    paths_to_exclude = [
        '1_raw.txt',
        '__init__.cpython-310.pyc',
        'test_params.cpython-310.pyc'
    ]
    bad_endings = ['.jpg', '.png', '.pkl', '.udpipe']
    paths = []
    for path in sorted(list_with_paths):
        is_file = path.is_file() and path.stat().st_size != 0
        is_ok_file = (
                path.name not in paths_to_exclude and
                '__pycache__' not in str(path) and
                'assets' not in str(path) and
                path.suffix not in bad_endings
        )
        if is_file and is_ok_file:
            paths.append(path)
    return paths


def has_newline(paths: list) -> bool:
    """
    Check for a newline at the end.

    Args:
        paths (list): Appropriate paths

    Returns:
        bool: Has newline or not
    """
    bad_paths = []
    check_is_good = True
    for path in paths:
        print(f'Analyzing {path}')
        with open(path, encoding='utf-8') as file:
            lines = file.readlines()
        if lines[-1][-1] != '\n':
            bad_paths.append(path)
            check_is_good = False
    if check_is_good:
        print('All files conform to the template.')
    else:
        for bad_path in bad_paths:
            print(f'No newline at the end of the {bad_path}')
    return check_is_good


def main() -> None:
    """
    Entrypoint for module.
    """
    list_with_paths = get_paths()
    paths = check_paths(list_with_paths)
    result = has_newline(paths)
    sys.exit(not result)


if __name__ == '__main__':
    main()
