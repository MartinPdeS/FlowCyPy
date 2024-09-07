# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                      |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                      |       59 |        2 |       16 |        2 |     95% |   46, 102 |
| FlowCyPy/coupling\_mechanism/empirical.py |       10 |        6 |        0 |        0 |     40% |     38-46 |
| FlowCyPy/coupling\_mechanism/mie.py       |       14 |        6 |        0 |        0 |     57% |     42-73 |
| FlowCyPy/coupling\_mechanism/rayleigh.py  |       21 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py   |        4 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/dataset.py                       |       32 |        9 |       12 |        1 |     68% |37-38, 54-64, 101-102 |
| FlowCyPy/detector.py                      |       55 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/flow.py                          |       36 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/flow\_cytometer.py               |       70 |        7 |       24 |        2 |     86% |64, 120-125 |
| FlowCyPy/gaussian\_pulse.py               |       23 |        1 |        4 |        1 |     93% |        85 |
| FlowCyPy/peak.py                          |       20 |        7 |        2 |        0 |     68% | 33, 41-53 |
| FlowCyPy/plotter.py                       |       22 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/scatterer\_distribution.py       |       86 |        5 |       26 |        4 |     92% |54, 96, 115-116, 133 |
| FlowCyPy/source.py                        |       19 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/utils.py                         |       22 |        0 |        2 |        0 |    100% |           |
|                                 **TOTAL** |  **493** |   **43** |   **98** |   **10** | **90%** |           |


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