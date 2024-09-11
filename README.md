# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                            |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                            |       65 |        3 |       18 |        3 |     93% |48, 112, 117 |
| FlowCyPy/coupling\_mechanism/empirical.py       |        8 |        4 |        0 |        0 |     50% |     38-45 |
| FlowCyPy/coupling\_mechanism/mie.py             |       17 |       10 |        2 |        0 |     37% |     44-76 |
| FlowCyPy/coupling\_mechanism/mie\_experiment.py |       15 |       15 |        0 |        0 |      0% |      1-77 |
| FlowCyPy/coupling\_mechanism/rayleigh.py        |       21 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py         |        4 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/dataset.py                             |       25 |        2 |        8 |        1 |     85% |     72-73 |
| FlowCyPy/detector.py                            |       72 |        9 |       10 |        4 |     84% |83-87, 89, 107-108, 134->exit, 166 |
| FlowCyPy/distribution/base\_class.py            |        9 |        2 |        0 |        0 |     78% |    23, 27 |
| FlowCyPy/distribution/delta.py                  |       19 |        1 |        4 |        1 |     91% |        34 |
| FlowCyPy/distribution/lognormal.py              |       21 |        2 |        6 |        2 |     85% |    39, 42 |
| FlowCyPy/distribution/normal.py                 |       21 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/distribution/uniform.py                |       21 |        2 |        6 |        2 |     85% |    39, 42 |
| FlowCyPy/distribution/weibull.py                |       21 |        2 |        6 |        2 |     85% |    33, 36 |
| FlowCyPy/flow.py                                |       38 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/flow\_cytometer.py                     |       64 |        6 |       20 |        1 |     87% |   113-118 |
| FlowCyPy/peak\_detector/base\_class.py          |        8 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/peak\_detector/basic.py                |       17 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/peak\_detector/moving\_average.py      |       24 |        1 |        4 |        1 |     93% |        77 |
| FlowCyPy/peak\_detector/threshold.py            |       18 |       10 |        4 |        0 |     45% |     42-61 |
| FlowCyPy/plotter.py                             |       26 |        0 |        6 |        1 |     97% |    72->85 |
| FlowCyPy/scatterer\_distribution.py             |       71 |        3 |       14 |        2 |     94% |130, 228, 302 |
| FlowCyPy/source.py                              |       19 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/units.py                               |       18 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/utils.py                               |       22 |        0 |        2 |        0 |    100% |           |
|                                       **TOTAL** |  **664** |   **72** |  **124** |   **20** | **87%** |           |


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