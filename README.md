# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/acquisition.py                               |       58 |        3 |        6 |        2 |     92% |44, 118, 152 |
| FlowCyPy/circuits.py                                  |       34 |        6 |        0 |        0 |     82% |21, 104-106, 117-125 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        9 |        4 |        0 |        0 |     56% |     39-47 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       45 |        8 |        6 |        3 |     78% |80->94, 148, 198-235 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       23 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        6 |        1 |        0 |        0 |     83% |        40 |
| FlowCyPy/cytometer.py                                 |      121 |        8 |       40 |        7 |     89% |118, 282->295, 383, 413->exit, 443, 445, 448-451 |
| FlowCyPy/dataframe\_subclass.py                       |      282 |      121 |       58 |       10 |     53% |26-28, 44-53, 85-105, 140-155, 257-270, 288, 312-313, 316->319, 391-411, 459->462, 471, 472->exit, 486-511, 524, 539-540, 550->exit, 585, 646-647, 696-716, 720, 732-741, 764-770, 774, 786-795 |
| FlowCyPy/detector.py                                  |      112 |       13 |       28 |        9 |     84% |86, 108, 130, 152, 174, 194, 214, 320, 385, 401, 460, 482, 505 |
| FlowCyPy/distribution/base\_class.py                  |       25 |        3 |        0 |        0 |     88% |32, 36, 65 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |       16 |        4 |        0 |     51% |86-94, 120-130, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/filters.py                                   |       22 |       22 |        4 |        0 |      0% |      1-92 |
| FlowCyPy/flow\_cell.py                                |       62 |        5 |        8 |        3 |     89% |66, 74, 81, 112, 142 |
| FlowCyPy/helper.py                                    |       91 |       40 |       30 |        8 |     54% |38, 42, 46, 116-121, 124-127, 130, 132->135, 160-203, 235 |
| FlowCyPy/noises.py                                    |       27 |       11 |        6 |        1 |     52% |4, 65-67, 77, 81-87 |
| FlowCyPy/particle\_count.py                           |       45 |       20 |       20 |        4 |     51% |30-31, 41, 64-72, 101-104, 110, 115-120, 127 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       25 |       21 |        0 |        0 |     16% |69-73, 119-152 |
| FlowCyPy/peak\_locator/base\_class.py                 |       48 |       31 |       12 |        0 |     28% |33-43, 51, 67-87, 103-132, 150-153, 157-163 |
| FlowCyPy/peak\_locator/basic.py                       |       40 |        1 |       18 |        3 |     93% |91, 112->115, 115->89 |
| FlowCyPy/peak\_locator/derivative.py                  |       46 |       42 |       20 |        0 |      6% |49-53, 83-137 |
| FlowCyPy/peak\_locator/moving\_average.py             |       65 |       61 |       28 |        0 |      4% |51-56, 78-150 |
| FlowCyPy/peak\_locator/scipy.py                       |       54 |        0 |       16 |        6 |     91% |111->119, 122->129, 135->139, 139->99, 147->149, 149->151 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       80 |       21 |       18 |        5 |     69% |46-47, 50, 79-80, 83, 145, 227-231, 253-255, 281, 291, 301, 340-349 |
| FlowCyPy/scatterer\_collection.py                     |       78 |       11 |       26 |        6 |     80% |45-47, 65, 124, 142, 146, 153-158, 211, 276->279 |
| FlowCyPy/signal\_digitizer.py                         |       45 |        5 |       10 |        4 |     84% |66-67, 90, 99, 121 |
| FlowCyPy/source.py                                    |      145 |       19 |       54 |       15 |     81% |33, 41, 53, 59-65, 73, 85, 88, 126, 128, 223, 225, 229, 231, 333, 335, 376->379, 379->382 |
| FlowCyPy/triggered\_acquisition.py                    |       62 |        7 |       14 |        2 |     83% |46-48, 102-103, 105-106 |
| FlowCyPy/units.py                                     |       21 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       56 |       56 |       14 |        0 |      0% |     1-134 |
|                                             **TOTAL** | **1992** |  **580** |  **462** |   **96** | **66%** |           |


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