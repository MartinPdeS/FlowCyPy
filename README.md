# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/acquisition.py                               |       64 |        4 |       10 |        2 |     92% |44, 145, 175-181 |
| FlowCyPy/amplifier.py                                 |       56 |        4 |        8 |        4 |     88% |68, 74, 129, 134 |
| FlowCyPy/circuits.py                                  |       34 |        6 |        0 |        0 |     82% |21, 104-106, 117-125 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       37 |        8 |        4 |        2 |     76% |62, 118-160 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       23 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        6 |        1 |        0 |        0 |     83% |        40 |
| FlowCyPy/cytometer.py                                 |      116 |       21 |       42 |        8 |     77% |122, 283->294, 297, 299->302, 364-387, 403->exit, 433, 435, 438-441 |
| FlowCyPy/dataframe\_subclass.py                       |      359 |      203 |       90 |        8 |     38% |27-33, 49-58, 90-110, 145-160, 258-284, 321-334, 352, 371-386, 425-461, 529-549, 597->600, 609, 610->exit, 649-696, 709-734, 747, 762-763, 773->exit, 808, 864-865, 907, 919-952, 957, 969-978, 994, 1005-1011, 1015, 1027-1036 |
| FlowCyPy/detector.py                                  |       89 |       18 |       16 |        5 |     74% |104, 126, 148, 168, 188, 237-255, 347, 365, 383, 402 |
| FlowCyPy/distribution/base\_class.py                  |       25 |        3 |        0 |        0 |     88% |32, 36, 65 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |       16 |        4 |        0 |     51% |86-94, 120-130, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/flow\_cell.py                                |      148 |       16 |       30 |        6 |     84% |114-120, 125, 290->293, 300, 341, 366-374, 428->432, 489->492 |
| FlowCyPy/helper.py                                    |       91 |       40 |       30 |        8 |     54% |38, 42, 46, 116-121, 124-127, 130, 132->135, 160-203, 235 |
| FlowCyPy/noises.py                                    |       29 |       12 |        6 |        1 |     51% |4, 65-67, 78, 82-89 |
| FlowCyPy/particle\_count.py                           |       45 |       20 |       20 |        4 |     51% |30-31, 41, 64-72, 101-104, 110, 115-120, 127 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       25 |       21 |        0 |        0 |     16% |69-73, 119-152 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |       31 |       12 |        0 |     28% |33-43, 51, 67-87, 103-132, 150-153, 157-163 |
| FlowCyPy/peak\_locator/derivative.py                  |       46 |       42 |       20 |        0 |      6% |49-53, 83-137 |
| FlowCyPy/peak\_locator/global\_.py                    |        8 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |        8 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/peak\_locator/scipy.py                       |       42 |        0 |       10 |        4 |     92% |104->112, 115->122, 129->134, 134->139 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       80 |       21 |       18 |        5 |     69% |46-47, 50, 79-80, 83, 145, 227-231, 253-255, 281, 291, 301, 340-349 |
| FlowCyPy/scatterer\_collection.py                     |       65 |        9 |       24 |        5 |     80% |64, 121, 139, 143, 150-155, 209 |
| FlowCyPy/signal\_digitizer.py                         |       44 |        5 |       10 |        4 |     83% |92-93, 116, 125, 145 |
| FlowCyPy/source.py                                    |      133 |       25 |       50 |       14 |     77% |36, 44, 56, 62-68, 76, 88, 91, 96-108, 177, 216, 218, 265, 319, 321, 325, 327, 381, 387 |
| FlowCyPy/triggered\_acquisition.py                    |       38 |       13 |       10 |        0 |     60% |30, 46-48, 102-121 |
| FlowCyPy/units.py                                     |       26 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       56 |       56 |       14 |        0 |      0% |     1-134 |
|                                             **TOTAL** | **2015** |  **623** |  **450** |   **88** | **64%** |           |


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