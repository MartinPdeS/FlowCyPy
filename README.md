# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/amplifier.py                                 |       56 |        4 |        8 |        4 |     88% |68, 74, 129, 134 |
| FlowCyPy/circuits.py                                  |       36 |        6 |        0 |        0 |     83% |22, 108-110, 121-129 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling.py                                  |       41 |       15 |        8 |        3 |     59% |62->64, 65, 157-158, 200-253 |
| FlowCyPy/cytometer.py                                 |       86 |        8 |       26 |        6 |     86% |96, 169, 278, 294, 296->299, 316-320, 338->exit |
| FlowCyPy/dataframe\_subclass.py                       |      250 |      126 |       68 |        6 |     46% |23-30, 46-55, 80-99, 126-138, 174-189, 220-234, 246, 251, 269-271, 289-291, 307-308, 326-341, 382-399, 470-486, 546->549, 549->552, 586, 592->588, 692-708, 748, 756-786 |
| FlowCyPy/detector.py                                  |       83 |       18 |       16 |        5 |     73% |103, 125, 147, 167, 187, 207-225, 317, 335, 353, 372 |
| FlowCyPy/dev.py                                       |      314 |      314 |       54 |        0 |      0% |    1-1114 |
| FlowCyPy/distribution/base\_class.py                  |       25 |        3 |        0 |        0 |     88% |32, 36, 65 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |       16 |        4 |        0 |     51% |86-94, 120-130, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/flow\_cell.py                                |      133 |       11 |       26 |        5 |     86% |116-122, 127, 290->293, 332-341, 415->419, 476->479 |
| FlowCyPy/helper.py                                    |      127 |       50 |       46 |       11 |     57% |33, 64, 68, 72, 143-148, 151-154, 157, 159->162, 187-232, 265, 308, 310->313, 336-351 |
| FlowCyPy/noises.py                                    |       28 |       11 |        6 |        1 |     53% |4, 67-69, 80, 84-90 |
| FlowCyPy/particle\_count.py                           |       45 |       20 |       20 |        4 |     51% |30-31, 41, 64-72, 101-104, 110, 115-120, 127 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       26 |       21 |        0 |        0 |     19% |70-74, 120-153 |
| FlowCyPy/peak\_locator/base\_class.py                 |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/derivative.py                  |       47 |       42 |       20 |        0 |      7% |50-54, 84-138 |
| FlowCyPy/peak\_locator/global\_.py                    |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |       17 |        0 |        6 |        2 |     91% |95->98, 98->exit |
| FlowCyPy/peak\_locator/scipy.py                       |       42 |        0 |       10 |        4 |     92% |104->112, 115->122, 129->134, 134->139 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       80 |       21 |       18 |        5 |     69% |46-47, 50, 79-80, 83, 145, 227-231, 253-255, 281, 291, 301, 340-349 |
| FlowCyPy/scatterer\_collection.py                     |       65 |        9 |       24 |        5 |     80% |64, 121, 139, 143, 150-155, 209 |
| FlowCyPy/signal\_digitizer.py                         |       49 |        7 |       10 |        4 |     78% |92-93, 116, 129-132, 154 |
| FlowCyPy/source.py                                    |      138 |       27 |       54 |       16 |     76% |37, 45, 57, 63-69, 77, 89, 92, 97-109, 176, 181, 220, 222, 269, 276, 325, 327, 331, 333, 387, 393 |
| FlowCyPy/triggering\_system.py                        |       64 |        9 |       12 |        3 |     82% |117-118, 144-146, 180-185 |
| FlowCyPy/units.py                                     |       26 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       56 |       56 |       14 |        0 |      0% |     1-134 |
|                                             **TOTAL** | **2133** |  **818** |  **484** |   **92** | **58%** |           |


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