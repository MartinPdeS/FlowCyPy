# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/acquisition.py                               |       58 |        4 |        6 |        2 |     91% |44, 102, 133-138 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       43 |        2 |        6 |        3 |     90% |82->96, 119, 183 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       23 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        6 |        1 |        0 |        0 |     83% |        40 |
| FlowCyPy/cytometer.py                                 |       93 |       10 |       18 |        4 |     86% |237, 329, 331, 334-337, 357-361 |
| FlowCyPy/dataframe\_subclass.py                       |      229 |       87 |       42 |        9 |     57% |31-63, 174-192, 284->287, 291, 292->exit, 299-332, 338, 347-348, 359->exit, 384, 423, 440-441, 481, 499-517, 523, 535-545, 561-569, 575, 587-597 |
| FlowCyPy/detector.py                                  |       74 |        5 |       12 |        3 |     91% |79, 99, 111, 249-250 |
| FlowCyPy/distribution/base\_class.py                  |       27 |        4 |        2 |        1 |     83% |32, 36, 65, 72 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |        3 |        4 |        2 |     88% |87, 89, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/filters.py                                   |       22 |        2 |        4 |        2 |     85% |    39, 83 |
| FlowCyPy/flow\_cell.py                                |       62 |        5 |        8 |        3 |     89% |66, 74, 81, 112, 142 |
| FlowCyPy/helper.py                                    |       59 |       12 |       22 |        8 |     75% |37, 41, 45, 115-120, 123-126, 129, 131->134, 165 |
| FlowCyPy/noises.py                                    |       27 |       13 |        6 |        0 |     42% |3-5, 65-67, 77, 81-87 |
| FlowCyPy/particle\_count.py                           |       45 |       22 |       20 |        6 |     45% |30-31, 35, 41, 64-72, 94, 101-104, 110, 115-120, 127 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |       31 |       12 |        0 |     28% |33-43, 51, 67-87, 103-132, 150-153, 157-163 |
| FlowCyPy/peak\_locator/basic.py                       |       19 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/peak\_locator/derivative.py                  |       16 |       12 |        2 |        0 |     22% |53-54, 79-96 |
| FlowCyPy/peak\_locator/moving\_average.py             |       56 |       31 |        4 |        0 |     42% |51-59, 65-69, 73-92, 107-116, 121-129, 136-166 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       50 |       13 |       12 |        5 |     71% |53, 76-77, 82, 105-106, 111, 124-133 |
| FlowCyPy/populations\_instances.py                    |       24 |        6 |        2 |        0 |     77% |7, 17, 56-65 |
| FlowCyPy/scatterer\_collection.py                     |       91 |       18 |       22 |        4 |     77% |48-50, 67-86, 124, 142, 146, 153-158, 211 |
| FlowCyPy/signal\_digitizer.py                         |       46 |        4 |       10 |        3 |     88% |67-68, 91, 100 |
| FlowCyPy/source.py                                    |       72 |        7 |       18 |        6 |     86% |33, 38, 48, 51, 58, 61, 71 |
| FlowCyPy/triggered\_acquisition.py                    |       93 |       10 |       32 |        9 |     82% |49-51, 149, 157, 161, 193, 201, 205, 227, 247->249, 249->exit |
| FlowCyPy/units.py                                     |       21 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       32 |        8 |        6 |        0 |     68% | 25-35, 38 |
|                                             **TOTAL** | **1610** |  **338** |  **294** |   **78** | **75%** |           |


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