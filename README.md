# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/detector.py                |       42 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/flow\_cytometer.py         |       78 |        1 |       14 |        1 |     98% |        77 |
| FlowCyPy/gaussian\_pulse.py         |       22 |        1 |        2 |        1 |     92% |        85 |
| FlowCyPy/peak.py                    |       18 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/plottings.py               |        9 |        6 |        4 |        0 |     23% |      8-16 |
| FlowCyPy/pulse\_analyzer.py         |       57 |        5 |       18 |        4 |     88% |54-58, 87, 107, 110->109, 157->148 |
| FlowCyPy/scatterer\_distribution.py |       91 |       10 |       32 |        6 |     85% |53, 84, 89-92, 111, 130-131, 148 |
| FlowCyPy/source.py                  |       16 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/utils.py                   |       16 |        0 |        2 |        0 |    100% |           |
|                           **TOTAL** |  **349** |   **23** |   **78** |   **12** | **90%** |           |


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