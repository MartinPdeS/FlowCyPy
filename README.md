# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/acquisition.py                               |       58 |       35 |        6 |        0 |     36% |44, 48, 52, 101-162, 167-182 |
| FlowCyPy/circuits.py                                  |       34 |       15 |        0 |        0 |     56% |21, 34, 45-48, 66-68, 79-87, 104-106, 117-125 |
| FlowCyPy/classifier.py                                |       44 |       44 |        8 |        0 |      0% |     1-182 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       40 |       18 |        4 |        0 |     50% |82-98, 121-163 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       23 |       16 |        0 |        0 |     30% |44-63, 100-116 |
| FlowCyPy/coupling\_mechanism/uniform.py               |        6 |        1 |        0 |        0 |     83% |        40 |
| FlowCyPy/cytometer.py                                 |      102 |       15 |       26 |        7 |     80% |115, 253, 284->298, 308-314, 358, 360, 363-366, 386-390 |
| FlowCyPy/dataframe\_subclass.py                       |      256 |      200 |       46 |        0 |     19% |31-63, 96-123, 141-162, 179-191, 211, 234-252, 264, 284-303, 308-320, 328, 332, 338-369, 375-408, 414, 420-437, 443, 459-474, 494-507, 513-526, 532, 552-565, 575-593, 599, 611-621, 637-645, 651, 663-673 |
| FlowCyPy/detector.py                                  |       77 |       16 |       14 |        7 |     75% |79, 99, 107, 111, 160-168, 192-202, 249-250, 269 |
| FlowCyPy/distribution/base\_class.py                  |       27 |       10 |        2 |        1 |     62% |32, 36, 49-62, 65, 72 |
| FlowCyPy/distribution/delta.py                        |       31 |       15 |        2 |        0 |     48% |31, 34, 53, 73-78, 89-101, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |       16 |        4 |        0 |     51% |38, 42, 46, 65, 89-97, 117-121, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |       11 |        2 |        0 |     66% |88-95, 117-125, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |       21 |        4 |        0 |     39% |40, 58-65, 86-94, 120-130, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |       12 |        0 |        0 |     65% |35, 39, 43, 46, 62-65, 84, 106-114, 117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/filters.py                                   |       22 |       16 |        4 |        0 |     23% |34-48, 78-92 |
| FlowCyPy/flow\_cell.py                                |       62 |        5 |        8 |        4 |     87% |66, 74, 81, 104->115, 112, 142 |
| FlowCyPy/helper.py                                    |       90 |       58 |       30 |        4 |     32% |34->33, 38, 42, 46, 111-135, 160-202, 229-242 |
| FlowCyPy/noises.py                                    |       27 |       13 |        6 |        0 |     42% |3-5, 65-67, 77, 81-87 |
| FlowCyPy/particle\_count.py                           |       45 |       30 |       20 |        3 |     28% |30-31, 37-41, 64-72, 96-98, 101-104, 107-112, 115-120, 124-127 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       25 |       21 |        0 |        0 |     16% |69-73, 119-152 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |       31 |       12 |        0 |     28% |33-43, 51, 67-87, 103-132, 150-153, 157-163 |
| FlowCyPy/peak\_locator/basic.py                       |       14 |       10 |        4 |        0 |     22% |51, 90-100 |
| FlowCyPy/peak\_locator/derivative.py                  |       16 |       12 |        2 |        0 |     22% |53-54, 79-96 |
| FlowCyPy/peak\_locator/moving\_average.py             |       22 |       18 |        4 |        0 |     15% |54-56, 95-121 |
| FlowCyPy/peak\_locator/scipy.py                       |       19 |       14 |        2 |        0 |     24% |70-75, 112-129 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       50 |       14 |       12 |        5 |     69% |53, 76-77, 82, 105-106, 111, 114, 124-133 |
| FlowCyPy/populations\_instances.py                    |       24 |        6 |        2 |        0 |     77% |7, 17, 56-65 |
| FlowCyPy/scatterer\_collection.py                     |       91 |       49 |       22 |        1 |     40% |48-50, 67-86, 124, 140-158, 186-187, 211, 251-305 |
| FlowCyPy/signal\_digitizer.py                         |       46 |       18 |       10 |        2 |     54% |37, 49, 66-70, 91, 97-100, 106-124 |
| FlowCyPy/source.py                                    |       72 |       18 |       18 |        7 |     68% |33, 38, 41, 47-53, 58, 61, 68, 71, 74, 217, 241-246 |
| FlowCyPy/triggered\_acquisition.py                    |       93 |       72 |       32 |        0 |     17% |28-29, 33, 49-51, 70-127, 147-171, 191-216, 225-232, 246-249, 253-272 |
| FlowCyPy/units.py                                     |       21 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       65 |       65 |       14 |        0 |      0% |     1-145 |
|                                             **TOTAL** | **1749** |  **935** |  **326** |   **41** | **42%** |           |


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