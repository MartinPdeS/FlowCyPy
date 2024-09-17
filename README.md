# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                                  |       99 |        5 |       20 |        4 |     92% |156-157, 227, 249-250, 292->278 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        8 |        4 |        0 |        0 |     50% |     38-45 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       18 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       21 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        4 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |       95 |        6 |       24 |        2 |     92% |141-142, 188-191 |
| FlowCyPy/detector.py                                  |       85 |        5 |       30 |       10 |     87% |59->58, 73, 77->76, 91, 95->94, 109, 113->112, 127, 228->exit, 256 |
| FlowCyPy/distribution/base\_class.py                  |       19 |        2 |        2 |        0 |     90% |    26, 30 |
| FlowCyPy/distribution/delta.py                        |       20 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/lognormal.py                    |       20 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/normal.py                       |       21 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/particle\_size\_distribution.py |       25 |       11 |        2 |        0 |     59% |48, 64-71, 92-99 |
| FlowCyPy/distribution/uniform.py                      |       21 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/weibull.py                      |       24 |        8 |        2 |        0 |     69% |39, 55-57, 76-81 |
| FlowCyPy/flow\_cell.py                                |       24 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/joint\_plot.py                               |       86 |       28 |       22 |        6 |     61% |19-24, 28-29, 33-36, 45-47, 57-63, 68-69, 73-75, 126, 132->143, 144, 147->153, 206, 219 |
| FlowCyPy/peak\_finder/base\_class.py                  |       15 |        8 |        0 |        0 |     47% |34-42, 46-55 |
| FlowCyPy/peak\_finder/basic.py                        |       43 |        8 |       12 |        1 |     69% |83->86, 141-152 |
| FlowCyPy/peak\_finder/moving\_average.py              |       70 |        1 |       16 |        2 |     97% |96->99, 213 |
| FlowCyPy/population.py                                |       60 |        5 |       22 |        8 |     84% |50->49, 64, 69->68, 83, 88->87, 102, 108, 186 |
| FlowCyPy/report.py                                    |      104 |        1 |        4 |        1 |     98% |       169 |
| FlowCyPy/scatterer.py                                 |       42 |        1 |       12 |        1 |     96% |       102 |
| FlowCyPy/source.py                                    |       17 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/units.py                                     |       33 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       46 |        6 |        2 |        0 |     88% |79-84, 88-89, 109 |
|                                             **TOTAL** | **1020** |   **99** |  **184** |   **35** | **87%** |           |


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