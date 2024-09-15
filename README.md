# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/analyzer.py                                  |      104 |        5 |       22 |        5 |     92% |53, 165, 233, 257-258, 320->306 |
| FlowCyPy/coupling\_mechanism/empirical.py             |        8 |        4 |        0 |        0 |     50% |     38-45 |
| FlowCyPy/coupling\_mechanism/mie.py                   |       18 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/rayleigh.py              |       21 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/coupling\_mechanism/uniform.py               |        4 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/cytometer.py                                 |       64 |        4 |       20 |        1 |     92% |   115-118 |
| FlowCyPy/dataset.py                                   |       25 |       13 |        8 |        0 |     42% |42-52, 67-92 |
| FlowCyPy/detector.py                                  |      108 |       16 |       28 |       10 |     78% |84->83, 87, 91->90, 94, 98->97, 101, 105->104, 108, 135-136, 138, 162-164, 183->188, 216-223 |
| FlowCyPy/distribution/base\_class.py                  |       19 |        2 |        2 |        0 |     90% |    26, 30 |
| FlowCyPy/distribution/delta.py                        |       20 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/lognormal.py                    |       20 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/normal.py                       |       21 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/particle\_size\_distribution.py |       25 |       11 |        2 |        0 |     59% |48, 64-71, 92-99 |
| FlowCyPy/distribution/uniform.py                      |       21 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/distribution/weibull.py                      |       24 |        8 |        2 |        0 |     69% |39, 55-57, 76-81 |
| FlowCyPy/flow\_cell.py                                |       24 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/joint\_plot.py                               |       79 |       28 |       20 |        6 |     58% |19-24, 28-29, 33-36, 45-47, 57-63, 68-69, 73-75, 124, 130->135, 136, 139->145, 195, 208 |
| FlowCyPy/peak\_detector/base\_class.py                |       15 |        8 |        0 |        0 |     47% |34-42, 46-55 |
| FlowCyPy/peak\_detector/basic.py                      |       68 |       48 |        4 |        0 |     31% |66-91, 111-119, 137-140, 156-160, 182-223, 240-252 |
| FlowCyPy/peak\_detector/moving\_average.py            |       68 |        0 |       12 |        1 |     99% |    96->99 |
| FlowCyPy/plotter.py                                   |       21 |        6 |        6 |        0 |     63% |     46-61 |
| FlowCyPy/population.py                                |       40 |        2 |        6 |        2 |     91% |   29, 107 |
| FlowCyPy/report.py                                    |      104 |        1 |        4 |        1 |     98% |       169 |
| FlowCyPy/scatterer.py                                 |       42 |        1 |       12 |        1 |     96% |       102 |
| FlowCyPy/source.py                                    |       19 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/units.py                                     |       29 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       33 |        3 |        2 |        0 |     91% |     80-85 |
|                                             **TOTAL** | **1044** |  **160** |  **164** |   **27** | **82%** |           |


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