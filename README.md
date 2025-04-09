# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/acquisition.py                               |       58 |        4 |        6 |        2 |     91% |44, 102, 133-138 |
| FlowCyPy/circuits.py                                  |       34 |       15 |        0 |        0 |     56% |21, 34, 45-48, 66-68, 79-87, 104-106, 117-125 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       26 |        1 |        4 |        2 |     90% |78->92, 120 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       23 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        6 |        1 |        0 |        0 |     83% |        40 |
| FlowCyPy/cytometer.py                                 |      103 |       14 |       26 |        6 |     81% |118, 296->309, 319-325, 370, 372, 375-378, 398-402 |
| FlowCyPy/dataframe\_subclass.py                       |      279 |      119 |       56 |        9 |     53% |26-28, 44-53, 85-105, 140-155, 257-270, 288, 312->315, 387-407, 456->459, 468, 469->exit, 483-508, 521, 536-537, 547->exit, 582, 643-644, 693-713, 717, 729-738, 761-767, 771, 783-792 |
| FlowCyPy/detector.py                                  |       76 |        6 |       14 |        4 |     89% |81, 101, 113, 249-250, 267 |
| FlowCyPy/distribution/base\_class.py                  |       27 |        4 |        2 |        1 |     83% |32, 36, 65, 72 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |       16 |        4 |        0 |     51% |86-94, 120-130, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/filters.py                                   |       22 |        2 |        4 |        2 |     85% |    39, 83 |
| FlowCyPy/flow\_cell.py                                |       62 |        5 |        8 |        3 |     89% |66, 74, 81, 112, 142 |
| FlowCyPy/helper.py                                    |       91 |       40 |       30 |        8 |     54% |38, 42, 46, 116-121, 124-127, 130, 132->135, 160-203, 235 |
| FlowCyPy/noises.py                                    |       27 |       13 |        6 |        0 |     42% |3-5, 65-67, 77, 81-87 |
| FlowCyPy/particle\_count.py                           |       45 |       20 |       20 |        4 |     51% |30-31, 41, 64-72, 101-104, 110, 115-120, 127 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       25 |       21 |        0 |        0 |     16% |69-73, 119-152 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |       31 |       12 |        0 |     28% |33-43, 51, 67-87, 103-132, 150-153, 157-163 |
| FlowCyPy/peak\_locator/basic.py                       |       14 |        1 |        4 |        1 |     89% |        96 |
| FlowCyPy/peak\_locator/derivative.py                  |       16 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |       22 |       18 |        4 |        0 |     15% |54-56, 95-121 |
| FlowCyPy/peak\_locator/scipy.py                       |       19 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       54 |       13 |       12 |        5 |     73% |57, 80-81, 86, 109-110, 115, 128-137 |
| FlowCyPy/populations\_instances.py                    |       24 |        6 |        2 |        0 |     77% |7, 17, 56-65 |
| FlowCyPy/scatterer\_collection.py                     |       81 |       11 |       24 |        6 |     80% |48-50, 68, 127, 145, 149, 156-161, 214, 279->282 |
| FlowCyPy/signal\_digitizer.py                         |       45 |        4 |       10 |        3 |     87% |66-67, 90, 99 |
| FlowCyPy/source.py                                    |       72 |        7 |       18 |        6 |     86% |33, 38, 48, 51, 58, 61, 71 |
| FlowCyPy/triggered\_acquisition.py                    |       93 |       10 |       32 |        9 |     82% |49-51, 148, 156, 160, 192, 200, 204, 226, 246->248, 248->exit |
| FlowCyPy/units.py                                     |       21 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       65 |       29 |       14 |        0 |     48% |28-38, 41, 107-145 |
|                                             **TOTAL** | **1752** |  **439** |  **338** |   **79** | **71%** |           |


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