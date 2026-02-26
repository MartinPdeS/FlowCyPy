# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                  |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|-------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/amplifier.py                 |       29 |        1 |        4 |        2 |     90.91% |114, 125->exit |
| FlowCyPy/calibration.py               |      158 |      158 |       22 |        0 |      0.00% |     1-444 |
| FlowCyPy/classifier.py                |       29 |       29 |        6 |        0 |      0.00% |     1-152 |
| FlowCyPy/coupling\_model.py           |       46 |       14 |       14 |        3 |     61.67% |61-64, 126, 153, 173-205 |
| FlowCyPy/detector.py                  |       43 |        8 |        4 |        2 |     78.72% |73, 100, 198-206, 226-232 |
| FlowCyPy/digitizer.py                 |       47 |        9 |       12 |        5 |     72.88% |89-90, 103, 106-112, 123-130, 150 |
| FlowCyPy/event\_collection.py         |      118 |       79 |       54 |        4 |     27.33% |32-40, 62, 85, 122, 123->130, 131, 159-189, 195-202, 258-344, 375-390, 427-443 |
| FlowCyPy/flow\_cytometer.py           |      131 |       40 |       44 |        8 |     66.86% |107, 110, 153-204, 284->296, 346-359, 412, 421, 448-477 |
| FlowCyPy/instances/detector.py        |       11 |       11 |        0 |        0 |      0.00% |      1-62 |
| FlowCyPy/instances/flow\_cytometer.py |       47 |       47 |        0 |        0 |      0.00% |     1-207 |
| FlowCyPy/instances/population.py      |       24 |       24 |        2 |        0 |      0.00% |      1-66 |
| FlowCyPy/opto\_electronics.py         |       15 |        1 |        4 |        1 |     89.47% |        51 |
| FlowCyPy/run\_record.py               |       69 |       18 |       16 |        2 |     67.06% |74, 90-92, 108-110, 126, 142-144, 225->231, 228-229, 247-258 |
| FlowCyPy/scatterer\_collection.py     |       31 |        7 |       12 |        2 |     74.42% |37-39, 79, 99, 109-112 |
| FlowCyPy/simulation\_settings.py      |       35 |       13 |        6 |        1 |     56.10% |8-13, 66-68, 83, 87-93 |
| FlowCyPy/source.py                    |       85 |       17 |       24 |        9 |     76.15% |40, 45-48, 52-69, 138, 146, 261, 263, 269, 271, 312, 385, 387 |
| FlowCyPy/sub\_frames/acquisition.py   |      117 |       40 |       38 |        3 |     64.52% |114, 120, 126, 149-151, 171-193, 213-219, 252-268, 301, 308-322 |
| FlowCyPy/sub\_frames/base.py          |        5 |        1 |        0 |        0 |     80.00% |         8 |
| FlowCyPy/sub\_frames/classifier.py    |       15 |       15 |        2 |        0 |      0.00% |      2-54 |
| FlowCyPy/sub\_frames/peaks.py         |       78 |       57 |       12 |        0 |     23.33% |23-29, 49-51, 71-73, 89-90, 110-125, 159-176, 199-222, 247-267 |
| FlowCyPy/sub\_frames/scatterer.py     |       88 |       88 |       16 |        0 |      0.00% |     1-288 |
| FlowCyPy/sub\_frames/utils.py         |       13 |        9 |        6 |        0 |     21.05% |     26-41 |
| FlowCyPy/triggering\_system.py        |       93 |       40 |       20 |        3 |     53.10% |61-66, 81, 137-144, 160-170, 174-184, 253-263, 303-313, 329-352, 356-374 |
| FlowCyPy/utils.py                     |       70 |       42 |       22 |        1 |     38.04% |27, 41-46, 57-69, 72, 97-106, 130-179 |
| FlowCyPy/workflow.py                  |       46 |       46 |        4 |        0 |      0.00% |     1-163 |
| **TOTAL**                             | **1498** |  **814** |  **352** |   **46** | **43.78%** |           |

5 files skipped due to complete coverage.


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