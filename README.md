# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                                  |      120 |       24 |       28 |        8 |     74% |106-107, 168, 190-191, 220->exit, 225-243, 301->305, 306-309, 312-315, 319->exit, 332-338 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       42 |        2 |        6 |        3 |     90% |80->94, 117, 180 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       22 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |       88 |        8 |       14 |        2 |     88% |142, 147-150, 202-208 |
| FlowCyPy/detector.py                                  |      144 |       19 |       30 |        7 |     80% |110, 132, 152, 174, 182, 188-190, 317, 459, 495-509 |
| FlowCyPy/distribution/base\_class.py                  |       20 |        2 |        0 |        0 |     90% |    26, 30 |
| FlowCyPy/distribution/delta.py                        |       22 |        1 |        0 |        0 |     95% |        86 |
| FlowCyPy/distribution/lognormal.py                    |       22 |        1 |        0 |        0 |     95% |        94 |
| FlowCyPy/distribution/normal.py                       |       22 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/distribution/particle\_size\_distribution.py |       31 |        8 |        4 |        2 |     71% |65, 67, 100-107, 110 |
| FlowCyPy/distribution/uniform.py                      |       22 |        1 |        0 |        0 |     95% |        96 |
| FlowCyPy/distribution/weibull.py                      |       22 |        8 |        0 |        0 |     64% |38, 54-56, 75-80 |
| FlowCyPy/flow\_cell.py                                |       40 |        6 |        6 |        3 |     80% |58, 80, 102, 132-133, 136 |
| FlowCyPy/helper.py                                    |       19 |        1 |        8 |        2 |     89% |74->77, 78 |
| FlowCyPy/logger.py                                    |       35 |        4 |        4 |        2 |     85% |46->exit, 74-75, 106-107 |
| FlowCyPy/noises.py                                    |       22 |       10 |        4 |        0 |     46% |7-9, 19, 23-29 |
| FlowCyPy/peak\_locator/base\_class.py                 |       30 |       13 |        4 |        0 |     50% |38-47, 85-98 |
| FlowCyPy/peak\_locator/basic.py                       |       38 |        5 |       12 |        5 |     76% |46, 49, 55->58, 59, 114->exit, 131-132 |
| FlowCyPy/peak\_locator/moving\_average.py             |       50 |        2 |       12 |        4 |     90% |52, 55, 62->65, 136->exit |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       75 |       12 |       18 |        7 |     77% |57, 78-80, 103-104, 109, 132-133, 138, 144, 228 |
| FlowCyPy/populations\_instances.py                    |        9 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/report.py                                    |      109 |       75 |        2 |        0 |     31% |13-22, 44-48, 52-57, 61-63, 67-75, 79-92, 96-127, 131-147, 151-155, 159, 172-183, 189-236 |
| FlowCyPy/scatterer.py                                 |      107 |       34 |       38 |        5 |     59% |74-84, 127, 145-148, 152->exit, 201, 235-248, 269-274, 313, 330-348, 351-352 |
| FlowCyPy/source.py                                    |       74 |        7 |       18 |        6 |     86% |36, 41, 51, 54, 61, 64, 74 |
| FlowCyPy/units.py                                     |       19 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       70 |        7 |       10 |        4 |     86% |32, 36, 40, 48, 94->97, 161-162, 184 |
|                                             **TOTAL** | **1298** |  **254** |  **224** |   **60** | **76%** |           |


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