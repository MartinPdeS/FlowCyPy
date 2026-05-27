# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|---------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/flow\_cytometer.py                   |      110 |       35 |       38 |        9 |     60.81% |67, 70, 75, 78, 162-199, 298-317, 354, 360, 446 |
| FlowCyPy/fluidics/event\_collection.py        |      269 |       88 |      118 |       25 |     63.05% |72, 146, 167-171, 194, 197, 225-\>224, 257, 262, 277, 304, 349, 370, 393-395, 423, 462, 468, 489-515, 533-540, 569-578, 652-656, 662, 667, 679, 682-685, 690-702, 706-\>713, 719, 740, 742-747, 828, 833, 843, 848, 851, 972-1005, 1027-1037, 1066 |
| FlowCyPy/fluidics/main.py                     |       66 |       16 |       10 |        2 |     73.68% |99-106, 132, 161-197 |
| FlowCyPy/fluidics/population\_events.py       |       42 |       14 |        6 |        1 |     60.42% |61, 128, 152, 197-213 |
| FlowCyPy/fluidics/scatterer\_collection.py    |       31 |        7 |       12 |        2 |     74.42% |37-39, 70, 90, 100-103 |
| FlowCyPy/opto\_electronics/coupling\_model.py |       45 |        6 |       10 |        3 |     80.00% |46, 137-147, 162-166 |
| FlowCyPy/opto\_electronics/main.py            |       64 |        3 |       26 |        4 |     92.22% |129, 133-\>140, 160, 245 |
| FlowCyPy/presets/detector.py                  |       11 |       11 |        0 |        0 |      0.00% |      1-78 |
| FlowCyPy/presets/flow\_cytometer.py           |       75 |       75 |        0 |        0 |      0.00% |     1-423 |
| FlowCyPy/presets/population.py                |       24 |       24 |        2 |        0 |      0.00% |      1-98 |
| FlowCyPy/run\_record.py                       |      127 |       85 |       60 |        2 |     24.60% |82-84, 96, 109-112, 125-131, 143, 156-159, 188-233, 237-240, 250-263, 303-343, 383-415, 448, 457-460, 473 |
| FlowCyPy/sub\_frames/acquisition.py           |      114 |       34 |       60 |       20 |     63.22% |41, 54-\>exit, 84, 104-109, 137, 140, 147, 150, 161, 167, 172, 211, 214, 230, 242, 251-254, 266-267, 320, 325-333, 335-\>343, 339, 344-350, 352-\>355, 355-\>358, 358-\>362 |
| FlowCyPy/sub\_frames/classifier.py            |       21 |       12 |        2 |        0 |     39.13% | 16, 40-60 |
| FlowCyPy/sub\_frames/events.py                |       55 |       14 |       18 |        6 |     67.12% |25-\>28, 34, 65, 77, 95, 109, 129, 133-147 |
| FlowCyPy/sub\_frames/peaks.py                 |      304 |      139 |      132 |       40 |     49.77% |93, 96, 108, 115, 122, 127, 139, 170-177, 186-\>189, 210-217, 237-239, 260-262, 280-281, 302-317, 331, 350, 365-376, 390-396, 456, 461, 471, 476, 480-\>483, 502, 505, 508, 528, 634, 646-647, 650-651, 664, 669, 674, 680, 688, 691, 696, 699, 731-771, 812-813, 816-817, 837, 840-841, 846, 850-878, 899-919, 950-960, 977-1000 |
| FlowCyPy/sub\_frames/triggered.py             |       67 |       52 |       28 |        0 |     15.79% |28, 39-42, 62-67, 109-176, 183, 190, 211-217, 235-242 |
| FlowCyPy/workflow.py                          |       44 |       44 |        4 |        0 |      0.00% |     1-191 |
| **TOTAL**                                     | **1483** |  **659** |  **526** |  **114** | **51.67%** |           |

3 files skipped due to complete coverage.


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