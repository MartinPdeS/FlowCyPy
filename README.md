# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|---------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/calibration.py                       |      158 |      158 |       22 |        0 |      0.00% |     1-477 |
| FlowCyPy/flow\_cytometer.py                   |      126 |       40 |       40 |        7 |     65.66% |107, 110, 154-205, 340-355, 408, 417, 438-469 |
| FlowCyPy/fluidics/event\_collection.py        |      118 |       79 |       54 |        4 |     27.33% |32-40, 62, 85, 122, 123->130, 131, 159-189, 195-202, 258-344, 375-390, 427-443 |
| FlowCyPy/fluidics/scatterer\_collection.py    |       31 |        7 |       12 |        2 |     74.42% |37-39, 79, 99, 109-112 |
| FlowCyPy/instances/detector.py                |       11 |       11 |        0 |        0 |      0.00% |      1-62 |
| FlowCyPy/instances/flow\_cytometer.py         |       50 |       50 |        0 |        0 |      0.00% |     1-217 |
| FlowCyPy/instances/population.py              |       24 |       24 |        2 |        0 |      0.00% |      1-66 |
| FlowCyPy/opto\_electronics/\_source.py        |       81 |       81 |       24 |        0 |      0.00% |     1-398 |
| FlowCyPy/opto\_electronics/coupling\_model.py |       46 |       14 |       14 |        3 |     61.67% |61-64, 130, 154, 174-205 |
| FlowCyPy/opto\_electronics/detector.py        |       39 |        7 |        2 |        1 |     80.49% |72, 161-169, 189-195 |
| FlowCyPy/opto\_electronics/main.py            |       15 |        1 |        4 |        1 |     89.47% |        51 |
| FlowCyPy/run\_record.py                       |       69 |       18 |       16 |        2 |     67.06% |74, 90-92, 108-110, 126, 142-144, 219->225, 222-223, 237-246 |
| FlowCyPy/simulation\_settings.py              |       35 |       13 |        6 |        1 |     56.10% |8-13, 66-68, 83, 87-93 |
| FlowCyPy/sub\_frames/acquisition.py           |      116 |       40 |       40 |        4 |     64.10% |107, 113, 119, 142-144, 164-186, 201-207, 240-256, 274->277, 292, 299-313 |
| FlowCyPy/sub\_frames/base.py                  |        5 |        1 |        0 |        0 |     80.00% |         8 |
| FlowCyPy/sub\_frames/classifier.py            |       18 |       11 |        2 |        0 |     35.00% |     38-58 |
| FlowCyPy/sub\_frames/peaks.py                 |       78 |       57 |       12 |        0 |     23.33% |23-29, 49-51, 71-73, 89-90, 110-125, 159-176, 199-222, 247-267 |
| FlowCyPy/sub\_frames/scatterer.py             |       88 |       88 |       16 |        0 |      0.00% |     1-288 |
| FlowCyPy/sub\_frames/utils.py                 |       13 |        9 |        6 |        0 |     21.05% |     26-41 |
| FlowCyPy/utils.py                             |       70 |       51 |       22 |        0 |     20.65% |16-31, 41-46, 57-69, 72, 97-106, 130-179 |
| FlowCyPy/workflow.py                          |       45 |       45 |        4 |        0 |      0.00% |     1-162 |
| **TOTAL**                                     | **1270** |  **805** |  **300** |   **25** | **34.78%** |           |

4 files skipped due to complete coverage.


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