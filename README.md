# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                                  |       78 |        3 |       24 |        5 |     92% |49, 113, 118, 164->138, 190->176 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        8 |        4 |        0 |        0 |     50% |     38-45 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       18 |       10 |        2 |        0 |     40% |     45-77 |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       21 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        4 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/dataset.py                                   |       25 |        2 |        8 |        1 |     85% |     72-73 |
| FlowCyPy/detector.py                                  |      104 |       16 |       28 |       10 |     77% |82->81, 85, 89->88, 92, 96->95, 99, 103->102, 106, 133-134, 136, 160-162, 185->exit, 208-215 |
| FlowCyPy/distribution/base\_class.py                  |       19 |        2 |        2 |        0 |     90% |    26, 30 |
| FlowCyPy/distribution/delta.py                        |       20 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/lognormal.py                    |       20 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/normal.py                       |       21 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/particle\_size\_distribution.py |       25 |       11 |        2 |        0 |     59% |48, 64-71, 92-99 |
| FlowCyPy/distribution/uniform.py                      |       21 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/weibull.py                      |       24 |        8 |        2 |        0 |     69% |39, 55-57, 76-81 |
| FlowCyPy/flow\_cell.py                                |       24 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/flow\_cytometer.py                           |       64 |        6 |       20 |        1 |     87% |   113-118 |
| FlowCyPy/joint\_plot.py                               |       45 |        4 |       12 |        6 |     82% |51, 57->62, 63, 66->72, 122, 135 |
| FlowCyPy/peak\_detector/base\_class.py                |        8 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/peak\_detector/basic.py                      |       17 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/peak\_detector/moving\_average.py            |       24 |        1 |        4 |        1 |     93% |        77 |
| FlowCyPy/peak\_detector/threshold.py                  |       18 |       10 |        4 |        0 |     45% |     42-61 |
| FlowCyPy/plotter.py                                   |       21 |        6 |        6 |        0 |     63% |     46-61 |
| FlowCyPy/population.py                                |       40 |        2 |        6 |        2 |     91% |   29, 107 |
| FlowCyPy/report.py                                    |       98 |       98 |        2 |        0 |      0% |     1-205 |
| FlowCyPy/scatterer\_distribution.py                   |       42 |        1 |       12 |        2 |     94% |86->66, 102 |
| FlowCyPy/source.py                                    |       19 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/units.py                                     |       26 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       25 |        0 |        2 |        0 |    100% |           |
|                                             **TOTAL** |  **879** |  **184** |  **152** |   **28** | **77%** |           |


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