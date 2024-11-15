# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                                  |      115 |        9 |       20 |        6 |     89% |156-157, 218, 240-241, 270->exit, 329-330, 334->exit, 347-353 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       26 |        1 |        2 |        1 |     93% |        39 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       22 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |       88 |        8 |       14 |        2 |     88% |142, 147-150, 202-208 |
| FlowCyPy/detector.py                                  |      129 |        9 |       24 |        6 |     88% |107, 129, 149, 171, 179, 185-187, 314 |
| FlowCyPy/distribution/base\_class.py                  |       20 |        2 |        0 |        0 |     90% |    26, 30 |
| FlowCyPy/distribution/delta.py                        |       22 |        1 |        0 |        0 |     95% |        86 |
| FlowCyPy/distribution/lognormal.py                    |       22 |        1 |        0 |        0 |     95% |        94 |
| FlowCyPy/distribution/normal.py                       |       22 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/distribution/particle\_size\_distribution.py |       31 |        8 |        4 |        2 |     71% |65, 67, 100-107, 110 |
| FlowCyPy/distribution/uniform.py                      |       22 |        1 |        0 |        0 |     95% |        96 |
| FlowCyPy/distribution/weibull.py                      |       22 |        8 |        0 |        0 |     64% |38, 54-56, 75-80 |
| FlowCyPy/flow\_cell.py                                |       40 |        6 |        6 |        3 |     80% |58, 80, 102, 132-133, 136 |
| FlowCyPy/helper.py                                    |       19 |        5 |        8 |        4 |     67% |63-64, 75, 78, 81 |
| FlowCyPy/logger.py                                    |       35 |        4 |        4 |        2 |     85% |46->exit, 74-75, 106-107 |
| FlowCyPy/noises.py                                    |       22 |       10 |        4 |        0 |     46% |7-9, 19, 23-29 |
| FlowCyPy/peak\_finder/base\_class.py                  |       31 |        6 |        4 |        1 |     80% | 39-48, 90 |
| FlowCyPy/peak\_finder/basic.py                        |       32 |        7 |        4 |        1 |     72% |74->exit, 92-111 |
| FlowCyPy/peak\_finder/moving\_average.py              |       52 |        0 |        8 |        1 |     98% |    82->85 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       73 |        9 |       18 |        7 |     82% |77, 101-102, 107, 130-131, 136, 143, 227 |
| FlowCyPy/report.py                                    |      109 |       75 |        2 |        0 |     31% |13-22, 44-48, 52-57, 61-63, 67-75, 79-92, 96-127, 131-147, 151-155, 159, 172-183, 189-236 |
| FlowCyPy/scatterer.py                                 |      101 |       29 |       36 |        5 |     62% |74-84, 127, 145-148, 152->exit, 201, 234-239, 278, 295-313, 316-317 |
| FlowCyPy/source.py                                    |       72 |        7 |       18 |        6 |     86% |36, 41, 51, 54, 61, 64, 74 |
| FlowCyPy/units.py                                     |       18 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       45 |        5 |        2 |        0 |     89% |25, 30, 91-92, 114 |
|                                             **TOTAL** | **1214** |  **215** |  **182** |   **47** | **79%** |           |


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