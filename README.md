# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                  |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|-------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/analysis.py                  |       98 |        7 |       36 |        8 |     88.81% |38, 41, 43, 89, 120, 124, 131-\>133, 155 |
| FlowCyPy/event\_collection.py         |      257 |       87 |      112 |       23 |     62.06% |69, 74, 145, 166-170, 193, 196, 224-\>223, 237, 264, 306, 327, 348-350, 378, 417, 423, 444-470, 488-495, 524-533, 607-611, 617, 622, 634, 637-640, 645-657, 661-\>668, 674, 695, 697-702, 783, 788, 798, 803, 806, 927-960, 982-992, 1021 |
| FlowCyPy/flow\_cytometer.py           |      123 |       15 |       46 |       13 |     83.43% |73, 76, 133, 165, 170, 173, 177-\>175, 181, 285-291, 326, 375, 379, 381, 412 |
| FlowCyPy/fluorescence.py              |      155 |       20 |       72 |       18 |     83.26% |29, 87, 91, 102, 130, 137, 156, 169, 171, 173, 190, 201, 212, 273, 276, 278, 308, 315-320 |
| FlowCyPy/run\_record.py               |      170 |       56 |       74 |       14 |     59.02% |95, 97, 150-\>155, 168, 181, 195, 210-216, 286, 299-302, 368-374, 393-406, 447, 465, 471, 474-475, 478-479, 484, 526-558, 591, 600-603, 616 |
| FlowCyPy/sub\_frames/acquisition.py   |      115 |       18 |       58 |       19 |     77.46% |55-\>exit, 89, 111-\>114, 140, 143, 150, 153, 164, 170, 175, 215, 218, 246, 256, 270-271, 324, 332, 343, 351, 359-\>362, 362-\>366 |
| FlowCyPy/sub\_frames/classifier.py    |       33 |       24 |        8 |        0 |     21.95% | 15, 39-79 |
| FlowCyPy/sub\_frames/events.py        |       55 |       14 |       18 |        6 |     67.12% |25-\>28, 34, 65, 77, 95, 109, 129, 133-147 |
| FlowCyPy/sub\_frames/peak\_metrics.py |       26 |       17 |        6 |        0 |     28.12% |15, 21-22, 26, 32-47 |
| FlowCyPy/sub\_frames/peaks.py         |      276 |      113 |      124 |       39 |     54.50% |92, 95, 107, 114, 121, 126, 138, 169-176, 185-\>188, 209-216, 230, 249, 264-275, 289-295, 355, 360, 370, 375, 379-\>382, 401, 404, 407, 515, 527-528, 531-532, 545, 550, 555, 561, 569, 572, 577, 580, 612-652, 693-694, 697-698, 718, 721-722, 727, 731-759, 780-800, 851-874 |
| FlowCyPy/sub\_frames/triggered.py     |       67 |       21 |       28 |       10 |     63.16% |40-\>exit, 63-\>66, 109, 112, 115, 118, 121, 128, 138, 146, 182, 189, 210-216, 234-241 |
| FlowCyPy/systems/\_assembly.py        |       25 |        1 |        2 |        1 |     92.59% |       104 |
| FlowCyPy/systems/agilent.py           |        6 |        6 |        0 |        0 |      0.00% |      3-47 |
| FlowCyPy/systems/beckman\_coulter.py  |        5 |        5 |        0 |        0 |      0.00% |      3-33 |
| FlowCyPy/systems/cytek.py             |       24 |       13 |        0 |        0 |     45.83% |    39-127 |
| FlowCyPy/systems/miltenyi.py          |        3 |        3 |        0 |        0 |      0.00% |       3-7 |
| FlowCyPy/systems/nanofcm.py           |        3 |        3 |        0 |        0 |      0.00% |       3-7 |
| FlowCyPy/systems/stratedigm.py        |        4 |        4 |        0 |        0 |      0.00% |      3-27 |
| FlowCyPy/systems/thermo\_fisher.py    |        4 |        4 |        0 |        0 |      0.00% |      3-21 |
| FlowCyPy/workflow.py                  |      135 |        9 |       36 |        6 |     91.23% |160, 173, 176, 189-191, 194, 206, 321 |
| **TOTAL**                             | **1668** |  **440** |  **620** |  **157** | **68.92%** |           |

11 files skipped due to complete coverage.


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