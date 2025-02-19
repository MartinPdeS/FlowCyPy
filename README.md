# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/acquisition.py                               |       43 |        4 |        4 |        2 |     87% |43, 93, 117-122 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       43 |        2 |        6 |        3 |     90% |82->96, 119, 183 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       23 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        6 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |       96 |        9 |       18 |        3 |     88% |237, 333, 338-341, 361-365 |
| FlowCyPy/dataframe\_subclass.py                       |      191 |       69 |       32 |        5 |     60% |30-62, 210->213, 218, 219->exit, 263-291, 311-327, 384->387, 390->exit, 409-413, 433-457, 476-486, 527-544 |
| FlowCyPy/detector.py                                  |       77 |        5 |       12 |        3 |     91% |82, 102, 114, 252-253 |
| FlowCyPy/distribution/base\_class.py                  |       27 |        4 |        2 |        1 |     83% |32, 36, 65, 72 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |        3 |        4 |        2 |     88% |87, 89, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/filters.py                                   |       22 |       16 |        4 |        0 |     23% |34-48, 78-92 |
| FlowCyPy/flow\_cell.py                                |       62 |        5 |        8 |        3 |     89% |66, 74, 81, 112, 142 |
| FlowCyPy/helper.py                                    |       59 |       12 |       22 |        9 |     74% |33->32, 37, 41, 45, 115-120, 123-126, 129, 131->134, 165 |
| FlowCyPy/noises.py                                    |       27 |       13 |        6 |        0 |     42% |3-5, 65-67, 77, 81-87 |
| FlowCyPy/particle\_count.py                           |       45 |       22 |       20 |        6 |     45% |30-31, 35, 41, 64-72, 94, 101-104, 110, 115-120, 127 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |        8 |       12 |        5 |     75% |34, 37, 51, 84->87, 104, 107, 150-153 |
| FlowCyPy/peak\_locator/basic.py                       |       27 |        2 |        4 |        2 |     87% |46->49, 50, 108 |
| FlowCyPy/peak\_locator/derivative.py                  |       40 |        2 |        6 |        2 |     91% |50->55, 55->exit, 128-137 |
| FlowCyPy/peak\_locator/moving\_average.py             |       56 |       15 |        4 |        2 |     72% |53->56, 58->exit, 107-116, 121-129, 136-166 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       50 |       13 |       12 |        5 |     71% |53, 76-77, 82, 105-106, 111, 124-133 |
| FlowCyPy/populations\_instances.py                    |       24 |        6 |        2 |        0 |     77% |7, 17, 56-65 |
| FlowCyPy/scatterer\_collection.py                     |       92 |       24 |       22 |        1 |     66% |48-50, 67-86, 124, 141-159, 212 |
| FlowCyPy/signal\_digitizer.py                         |       44 |        4 |       10 |        3 |     87% |67-68, 91, 103 |
| FlowCyPy/source.py                                    |       72 |        7 |       18 |        6 |     86% |33, 38, 48, 51, 58, 61, 71 |
| FlowCyPy/triggered\_acquisition.py                    |       70 |       40 |       28 |        1 |     32% |45-47, 65, 113-147, 167-202, 211-220, 234-237 |
| FlowCyPy/units.py                                     |       21 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       33 |        3 |        6 |        2 |     87% |26, 30, 38 |
|                                             **TOTAL** | **1572** |  **316** |  **284** |   **74** | **75%** |           |


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