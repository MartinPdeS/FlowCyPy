# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/classifier.py                                |       44 |       44 |       10 |        0 |      0% |     1-190 |
| FlowCyPy/continuous\_acquisition.py                   |      115 |       55 |       24 |        1 |     47% |154-177, 196-210, 286->exit, 304-333, 366-398 |
| FlowCyPy/coupling\_mechanism.py                       |       42 |       42 |        6 |        0 |      0% |     1-205 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       43 |        2 |        6 |        3 |     90% |82->96, 119, 183 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       23 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |       95 |       14 |       18 |        3 |     83% |215-230, 252, 339, 344-347, 367-371 |
| FlowCyPy/detector.py                                  |      119 |       31 |       26 |        4 |     68% |88, 108, 130, 142-144, 148, 284-285, 357-374, 405-419, 427-440 |
| FlowCyPy/distribution/base\_class.py                  |       27 |        4 |        2 |        1 |     83% |32, 36, 65, 72 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       36 |        3 |        4 |        2 |     88% |87, 89, 132 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/event\_correlator.py                         |       77 |       11 |       12 |        6 |     81% |129, 155-156, 206->210, 211-214, 217-220, 224->exit |
| FlowCyPy/flow\_cell.py                                |       59 |       13 |        8 |        3 |     73% |51, 72, 76-84, 114-124, 196 |
| FlowCyPy/helper.py                                    |       17 |       11 |        6 |        0 |     26% |     62-79 |
| FlowCyPy/logger.py                                    |       43 |       14 |        4 |        1 |     64% |84-86, 102-112, 123-129 |
| FlowCyPy/noises.py                                    |       27 |       13 |        6 |        0 |     42% |3-5, 12-14, 24, 28-34 |
| FlowCyPy/particle\_count.py                           |       43 |       18 |       20 |        7 |     51% |30-31, 35, 41, 64-71, 93, 103, 109, 114-119, 126 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |        8 |       12 |        5 |     75% |34, 37, 51, 84->87, 104, 107, 150-153 |
| FlowCyPy/peak\_locator/basic.py                       |       27 |        2 |        4 |        2 |     87% |46->49, 50, 108 |
| FlowCyPy/peak\_locator/derivative.py                  |       40 |        2 |        6 |        2 |     91% |50->55, 55->exit, 128-137 |
| FlowCyPy/peak\_locator/moving\_average.py             |       56 |       15 |        4 |        1 |     73% |53->56, 107-116, 121-129, 136-166 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/plottings.py                                 |       69 |       69 |       14 |        0 |      0% |     1-268 |
| FlowCyPy/population.py                                |       52 |       13 |       12 |        5 |     72% |54, 77-78, 83, 106-107, 112, 125-134 |
| FlowCyPy/populations\_instances.py                    |       24 |        6 |        2 |        0 |     77% |7, 17, 56-65 |
| FlowCyPy/report.py                                    |      109 |      109 |        2 |        0 |      0% |     1-236 |
| FlowCyPy/scatterer\_collection.py                     |       91 |       24 |       22 |        1 |     65% |48-50, 67-86, 124, 141-159, 212 |
| FlowCyPy/signal\_digitizer.py                         |       50 |       10 |       14 |        3 |     73% |67-68, 107, 129-132, 155-159 |
| FlowCyPy/source.py                                    |       74 |        7 |       18 |        6 |     86% |36, 41, 51, 54, 61, 64, 74 |
| FlowCyPy/triggered\_acquisition.py                    |       90 |       69 |       18 |        0 |     19% |22-23, 27, 54-78, 82, 88-104, 108, 112-116, 127-141, 147, 151-169, 187-223 |
| FlowCyPy/units.py                                     |       21 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       67 |       21 |        8 |        2 |     67% |31, 35, 43, 81-95, 156-157, 168-171, 179, 187-191 |
|                                             **TOTAL** | **1826** |  **658** |  **302** |   **62** | **60%** |           |


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