"""
Checks the relevance of stubs.
"""

import sys
from pathlib import Path

from config.constants import PROJECT_CONFIG_PATH
from config.generate_stubs.generator import cleanup_code
from config.generate_stubs.run_generator import (format_stub_file,
                                                 sort_stub_imports)
from config.project_config import ProjectConfig


def get_code(code_path: Path) -> str:
    """
    Get clear code from file.

    Args:
        code_path (Path): Path to file with code

    Returns:
        str: Clear code
    """
    with code_path.open(encoding='utf-8') as file:
        code_text = file.read()
    return code_text


def clear_examples(lab_path: Path) -> None:
    """
    Clean temp files.

    Args:
        lab_path (Path): Path to temp files
    """
    example_main_stub_path = lab_path / 'example_main_stub.py'
    example_main_stub_path.unlink()


def main() -> None:
    """
    Check the relevance of stubs.
    """
    project_config = ProjectConfig(PROJECT_CONFIG_PATH)
    labs_paths = project_config.get_labs_paths()[:2]
    code_is_equal = True
    for lab_path in labs_paths:
        print(lab_path.name)
        main_stub_path = lab_path / 'main_stub.py'

        main_stub_code = get_code(main_stub_path)

        if lab_path.name == 'lab_5_scrapper':
            clean_main = cleanup_code(lab_path / 'scrapper.py')

        elif lab_path.name == 'lab_6_pipeline':
            clean_main = cleanup_code(lab_path / 'pipeline.py')

        example_main_stub_path = lab_path / 'example_main_stub.py'
        with example_main_stub_path.open(mode='w', encoding='utf-8') as file:
            file.write(clean_main)
        format_stub_file(example_main_stub_path)
        sort_stub_imports(example_main_stub_path)
        formatted_main = get_code(example_main_stub_path)

        if formatted_main != main_stub_code:
            code_is_equal = False
            print(f'You have different main and main_stub in {lab_path}')

        clear_examples(lab_path)
    if code_is_equal:
        print('All stubs are relevant')
    sys.exit(not code_is_equal)


if __name__ == '__main__':
    main()
