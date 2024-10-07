# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                                  |      108 |        7 |       22 |        6 |     90% |159-160, 222, 244-245, 268->259, 319->327, 327->293, 340-346 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        8 |        4 |        0 |        0 |     50% |     37-46 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       30 |        2 |        6 |        2 |     89% |    31, 78 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       21 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        4 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |      109 |       10 |       26 |        4 |     88% |51->exit, 139-140, 181, 186-189, 248-254 |
| FlowCyPy/detector.py                                  |      132 |       10 |       40 |       12 |     85% |81->80, 93->92, 111, 115->114, 133, 137->136, 153, 157->156, 175, 183, 189-191, 320, 453 |
| FlowCyPy/distribution/base\_class.py                  |       21 |        2 |        2 |        0 |     91% |    26, 30 |
| FlowCyPy/distribution/delta.py                        |       22 |        1 |        2 |        0 |     96% |        86 |
| FlowCyPy/distribution/lognormal.py                    |       22 |        1 |        2 |        0 |     96% |        94 |
| FlowCyPy/distribution/normal.py                       |       22 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/particle\_size\_distribution.py |       27 |        6 |        2 |        0 |     79% |90-97, 100 |
| FlowCyPy/distribution/uniform.py                      |       23 |        1 |        2 |        0 |     96% |        98 |
| FlowCyPy/distribution/weibull.py                      |       23 |        8 |        2 |        0 |     68% |38, 54-56, 75-80 |
| FlowCyPy/flow\_cell.py                                |       41 |        6 |       14 |        6 |     78% |41->40, 59, 63->62, 81, 85->84, 103, 133-134, 137 |
| FlowCyPy/peak\_finder/base\_class.py                  |       30 |        5 |        6 |        1 |     83% | 38-46, 88 |
| FlowCyPy/peak\_finder/basic.py                        |       32 |        7 |        8 |        2 |     72% |81->exit, 86->85, 100-119 |
| FlowCyPy/peak\_finder/moving\_average.py              |       55 |        0 |       12 |        2 |     97% |91->94, 137->136 |
| FlowCyPy/population.py                                |       66 |        5 |       22 |        8 |     85% |57->56, 71, 75->74, 89, 93->92, 107, 115, 199 |
| FlowCyPy/report.py                                    |      107 |       73 |        4 |        0 |     32% |13, 45-49, 53-58, 62-64, 68-76, 80-93, 97-133, 137-154, 158-162, 166, 179-190, 196-244 |
| FlowCyPy/scatterer.py                                 |       52 |        6 |       16 |        3 |     87% |99-103, 106->71, 151 |
| FlowCyPy/source.py                                    |       26 |        1 |        6 |        2 |     91% |42->41, 60 |
| FlowCyPy/units.py                                     |       18 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       46 |        9 |        4 |        1 |     80% |25, 30, 79-84, 88-89, 110, 119 |
|                                             **TOTAL** | **1045** |  **164** |  **204** |   **49** | **82%** |           |


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