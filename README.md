# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                                  |      112 |        7 |       20 |        6 |     90% |157-158, 219, 241-242, 271->exit, 320->327, 329->exit, 342-348 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        8 |        4 |        0 |        0 |     50% |     38-46 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       24 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       21 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        4 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |      108 |       10 |       20 |        3 |     88% |141-142, 182, 187-190, 243-249 |
| FlowCyPy/detector.py                                  |      133 |       10 |       26 |        7 |     87% |117, 139, 159, 181, 189, 195-197, 322, 452 |
| FlowCyPy/distribution/base\_class.py                  |       20 |        2 |        0 |        0 |     90% |    26, 30 |
| FlowCyPy/distribution/delta.py                        |       22 |        1 |        0 |        0 |     95% |        86 |
| FlowCyPy/distribution/lognormal.py                    |       22 |        1 |        0 |        0 |     95% |        94 |
| FlowCyPy/distribution/normal.py                       |       22 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/distribution/particle\_size\_distribution.py |       27 |        6 |        0 |        0 |     78% |91-98, 101 |
| FlowCyPy/distribution/uniform.py                      |       22 |        1 |        0 |        0 |     95% |        96 |
| FlowCyPy/distribution/weibull.py                      |       22 |        8 |        0 |        0 |     64% |38, 54-56, 75-80 |
| FlowCyPy/flow\_cell.py                                |       40 |        6 |        6 |        3 |     80% |58, 80, 102, 132-133, 136 |
| FlowCyPy/peak\_finder/base\_class.py                  |       31 |        6 |        4 |        1 |     80% | 39-48, 90 |
| FlowCyPy/peak\_finder/basic.py                        |       32 |        7 |        4 |        1 |     72% |81->exit, 99-118 |
| FlowCyPy/peak\_finder/moving\_average.py              |       52 |        0 |        8 |        1 |     98% |    89->92 |
| FlowCyPy/population.py                                |       73 |        9 |       18 |        7 |     82% |77, 101-102, 107, 130-131, 136, 143, 227 |
| FlowCyPy/report.py                                    |      109 |       75 |        2 |        0 |     31% |13-22, 44-48, 52-57, 61-63, 67-75, 79-92, 96-127, 131-147, 151-155, 159, 172-183, 189-236 |
| FlowCyPy/scatterer.py                                 |      101 |       27 |       34 |        5 |     64% |75-85, 128, 146-149, 153->exit, 202, 235-240, 279, 296-314 |
| FlowCyPy/source.py                                    |       26 |        1 |        2 |        1 |     93% |        60 |
| FlowCyPy/units.py                                     |       18 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       45 |        5 |        2 |        0 |     89% |25, 30, 91-92, 114 |
|                                             **TOTAL** | **1094** |  **186** |  **150** |   **35** | **80%** |           |


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