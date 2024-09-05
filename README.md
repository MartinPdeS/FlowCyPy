# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/detector.py                |       42 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/flow\_cytometer.py         |       79 |        1 |       14 |        1 |     98% |        79 |
| FlowCyPy/gaussian\_pulse.py         |       22 |        1 |        2 |        1 |     92% |        85 |
| FlowCyPy/peak.py                    |       13 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/plottings.py               |        9 |        6 |        4 |        0 |     23% |      8-16 |
| FlowCyPy/pulse\_analyzer.py         |       58 |        5 |       18 |        4 |     88% |57-61, 79, 94, 97->96, 138->135 |
| FlowCyPy/scatterer\_distribution.py |       81 |       10 |       28 |        6 |     83% |53, 78, 83-86, 105, 118-119, 136 |
| FlowCyPy/utils.py                   |        7 |        0 |        2 |        0 |    100% |           |
|                           **TOTAL** |  **311** |   **23** |   **72** |   **12** | **89%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/MartinPdeS/FlowCyPy/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FMartinPdeS%2FFlowCyPy%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.