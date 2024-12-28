# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/classifier.py                                |       44 |       44 |       10 |        0 |      0% |     1-190 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       42 |        2 |        6 |        3 |     90% |80->94, 117, 181 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       22 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |       84 |        8 |       16 |        2 |     88% |142, 147-150, 192-198 |
| FlowCyPy/detector.py                                  |      166 |       32 |       40 |        9 |     74% |110, 132, 152, 174, 188-190, 332->335, 468->472, 473, 477, 500-504, 522-523, 544-550, 581-595, 603-616 |
| FlowCyPy/distribution/base\_class.py                  |       20 |        3 |        0 |        0 |     85% |26, 30, 59 |
| FlowCyPy/distribution/delta.py                        |       22 |        1 |        0 |        0 |     95% |        86 |
| FlowCyPy/distribution/lognormal.py                    |       22 |        1 |        0 |        0 |     95% |        94 |
| FlowCyPy/distribution/normal.py                       |       22 |        1 |        0 |        0 |     95% |        95 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       31 |        8 |        4 |        2 |     71% |65, 67, 100-107, 110 |
| FlowCyPy/distribution/uniform.py                      |       22 |        1 |        0 |        0 |     95% |        96 |
| FlowCyPy/distribution/weibull.py                      |       22 |        8 |        0 |        0 |     64% |38, 54-56, 75-80 |
| FlowCyPy/event\_correlator.py                         |       81 |       13 |       12 |        6 |     80% |130, 156-157, 207->211, 212-215, 218-221, 225->exit, 238-244 |
| FlowCyPy/flow\_cell.py                                |       37 |        6 |        6 |        3 |     79% |55, 77, 99, 114-115, 118 |
| FlowCyPy/helper.py                                    |       19 |        1 |        8 |        2 |     89% |74->77, 78 |
| FlowCyPy/logger.py                                    |       96 |       33 |        8 |        3 |     63% |82-84, 100-110, 121-127, 156, 168-183, 199-209, 258->exit, 286-287, 321-322 |
| FlowCyPy/noises.py                                    |       22 |       10 |        4 |        0 |     46% |7-9, 19, 23-29 |
| FlowCyPy/particle\_count.py                           |       29 |       11 |       14 |        5 |     53% |32-33, 39, 65, 69, 91, 98-102 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |        5 |       12 |        5 |     83% |34, 37, 51, 84->87, 104, 107 |
| FlowCyPy/peak\_locator/basic.py                       |       27 |        2 |        4 |        2 |     87% |46->49, 50, 108 |
| FlowCyPy/peak\_locator/derivative.py                  |       40 |        2 |        6 |        2 |     91% |50->55, 55->exit, 128-137 |
| FlowCyPy/peak\_locator/moving\_average.py             |       36 |        0 |        4 |        1 |     98% |    51->54 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/plottings.py                                 |       69 |       69 |       14 |        0 |      0% |     1-269 |
| FlowCyPy/population.py                                |       73 |       12 |       18 |        7 |     77% |58, 79-81, 104-105, 110, 133-134, 139, 145, 237 |
| FlowCyPy/populations\_instances.py                    |       14 |        4 |        2 |        0 |     75% |     39-49 |
| FlowCyPy/report.py                                    |      109 |       75 |        2 |        0 |     31% |13-22, 44-48, 52-57, 61-63, 67-75, 79-92, 96-127, 131-147, 151-155, 159, 172-183, 189-236 |
| FlowCyPy/scatterer.py                                 |      116 |       45 |       38 |        4 |     53% |75-85, 105-112, 148, 161-164, 168->exit, 176-189, 199-201, 258-271, 292-297, 334, 351-369, 372-373 |
| FlowCyPy/source.py                                    |       74 |        7 |       18 |        6 |     86% |36, 41, 51, 54, 61, 64, 74 |
| FlowCyPy/units.py                                     |       19 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       67 |        6 |        8 |        3 |     88% |31, 35, 43, 89->92, 156-157, 179 |
|                                             **TOTAL** | **1519** |  **414** |  **258** |   **65** | **69%** |           |


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