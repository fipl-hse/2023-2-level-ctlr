set -x

echo $1
if [[ "$1" == "smoke" ]]; then
  DIRS_TO_CHECK=(
    "config"
    "seminars"
  )
else
  DIRS_TO_CHECK=(
    "config"
    "seminars"
    "core_utils"
    "lab_5_scrapper"
    "lab_6_pipeline"
  )
fi

python -m pylint --exit-zero --rcfile config/stage_1_style_tests/.pylintrc "${DIRS_TO_CHECK[@]}"

mypy "${DIRS_TO_CHECK[@]}"

python -m flake8 "${DIRS_TO_CHECK[@]}"

if [[ "$1" != "smoke" ]]; then
  python -m pytest -m "mark10 and lab_5_scrapper"
  python -m pytest -m "mark10 and lab_6_pipeline"
fi

