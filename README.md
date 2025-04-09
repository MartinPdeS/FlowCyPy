# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/acquisition.py                               |       63 |        4 |       12 |        2 |     92% |44, 145, 179-185 |
| FlowCyPy/amplifier.py                                 |       56 |        4 |        8 |        4 |     88% |68, 74, 129, 134 |
| FlowCyPy/circuits.py                                  |       36 |        6 |        0 |        0 |     83% |22, 108-110, 121-129 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling.py                                  |       36 |        8 |        4 |        2 |     75% |61, 116-158 |
| FlowCyPy/cytometer.py                                 |       90 |        6 |       28 |        5 |     89% |106, 278->292, 295, 297->300, 325-329, 347->exit |
| FlowCyPy/dataframe\_subclass.py                       |      351 |      203 |       90 |        6 |     36% |27-33, 49-58, 90-110, 145-160, 259-288, 325-338, 356, 375-390, 429-465, 533-553, 602->605, 614, 615->exit, 654-702, 715-740, 753, 761-762, 802, 891, 903-932, 936, 948-957, 973, 984-990, 994, 1006-1015 |
| FlowCyPy/detector.py                                  |       83 |       18 |       16 |        5 |     73% |103, 125, 147, 167, 187, 207-225, 317, 335, 353, 372 |
| FlowCyPy/distribution/base\_class.py                  |       25 |        3 |        0 |        0 |     88% |32, 36, 65 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |       16 |        4 |        0 |     51% |86-94, 120-130, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/flow\_cell.py                                |      148 |       16 |       30 |        6 |     84% |114-120, 125, 290->293, 300, 341, 366-374, 428->432, 489->492 |
| FlowCyPy/helper.py                                    |       90 |       39 |       30 |        8 |     54% |38, 42, 46, 116-121, 124-127, 130, 132->135, 160-205, 237 |
| FlowCyPy/noises.py                                    |       28 |       11 |        6 |        1 |     53% |4, 67-69, 80, 84-90 |
| FlowCyPy/particle\_count.py                           |       45 |       20 |       20 |        4 |     51% |30-31, 41, 64-72, 101-104, 110, 115-120, 127 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       25 |       21 |        0 |        0 |     16% |69-73, 119-152 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |       31 |       12 |        0 |     28% |33-43, 51, 67-87, 103-132, 150-153, 157-163 |
| FlowCyPy/peak\_locator/derivative.py                  |       46 |       42 |       20 |        0 |      6% |49-53, 83-137 |
| FlowCyPy/peak\_locator/global\_.py                    |       16 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |       16 |        0 |        6 |        2 |     91% |94->97, 97->exit |
| FlowCyPy/peak\_locator/scipy.py                       |       42 |        0 |       10 |        4 |     92% |104->112, 115->122, 129->134, 134->139 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       80 |       21 |       18 |        5 |     69% |46-47, 50, 79-80, 83, 145, 227-231, 253-255, 281, 291, 301, 340-349 |
| FlowCyPy/scatterer\_collection.py                     |       65 |        9 |       24 |        5 |     80% |64, 121, 139, 143, 150-155, 209 |
| FlowCyPy/signal\_digitizer.py                         |       48 |        7 |       10 |        4 |     78% |92-93, 116, 129-132, 152 |
| FlowCyPy/source.py                                    |      135 |       26 |       52 |       15 |     76% |36, 44, 56, 62-68, 76, 88, 91, 96-108, 175, 180, 219, 221, 268, 322, 324, 328, 330, 384, 390 |
| FlowCyPy/triggered\_acquisition.py                    |       38 |       13 |       12 |        0 |     62% |30, 46-48, 102-121 |
| FlowCyPy/units.py                                     |       26 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       56 |       56 |       14 |        0 |      0% |     1-134 |
|                                             **TOTAL** | **1957** |  **604** |  **454** |   **86** | **64%** |           |


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