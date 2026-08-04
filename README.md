# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                   |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|--------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/flow\_cytometer.py            |      134 |       15 |       46 |       15 |     83.33% |75, 80, 83, 168, 173, 176, 192, 305-308, 318-\>323, 360, 366, 448, 452, 454, 481 |
| FlowCyPy/fluidics/event\_collection.py |      271 |       88 |      118 |       25 |     63.24% |77, 151, 172-176, 199, 202, 230-\>229, 262, 267, 282, 309, 354, 375, 402-404, 432, 471, 477, 498-524, 542-549, 578-587, 661-665, 671, 676, 688, 691-694, 699-711, 715-\>722, 728, 749, 751-756, 837, 842, 852, 857, 860, 981-1014, 1036-1046, 1075 |
| FlowCyPy/fluidics/system.py            |       80 |        4 |       20 |        4 |     92.00% |34, 36, 126, 152 |
| FlowCyPy/opto\_electronics/system.py   |       66 |        3 |       26 |        4 |     92.39% |137, 141-\>148, 169, 256 |
| FlowCyPy/presets/detector.py           |       11 |       11 |        0 |        0 |      0.00% |      1-78 |
| FlowCyPy/presets/flow\_cytometer.py    |       75 |       75 |        0 |        0 |      0.00% |     1-423 |
| FlowCyPy/presets/population.py         |       24 |       24 |        2 |        0 |      0.00% |     1-110 |
| FlowCyPy/run\_record.py                |      127 |       85 |       60 |        2 |     24.60% |82-84, 96, 109-112, 125-131, 143, 156-159, 188-233, 237-240, 250-263, 303-343, 383-415, 448, 457-460, 473 |
| FlowCyPy/sub\_frames/acquisition.py    |      114 |       34 |       60 |       20 |     63.22% |41, 54-\>exit, 84, 104-109, 137, 140, 147, 150, 161, 167, 172, 211, 214, 230, 242, 251-254, 266-267, 320, 325-333, 335-\>343, 339, 344-350, 352-\>355, 355-\>358, 358-\>362 |
| FlowCyPy/sub\_frames/classifier.py     |       21 |       12 |        2 |        0 |     39.13% | 16, 40-60 |
| FlowCyPy/sub\_frames/events.py         |       55 |       14 |       18 |        6 |     67.12% |25-\>28, 34, 65, 77, 95, 109, 129, 133-147 |
| FlowCyPy/sub\_frames/peak\_metrics.py  |       26 |       17 |        6 |        0 |     28.12% |15, 21-22, 26, 32-47 |
| FlowCyPy/sub\_frames/peaks.py          |      283 |      121 |      126 |       40 |     52.32% |94, 97, 109, 116, 123, 128, 140, 171-178, 187-\>190, 211-218, 232, 251, 266-277, 291-297, 357, 362, 372, 377, 381-\>384, 403, 406, 409, 429, 535, 547-548, 551-552, 565, 570, 575, 581, 589, 592, 597, 600, 632-672, 713-714, 717-718, 738, 741-742, 747, 751-779, 800-820, 851-861, 878-901 |
| FlowCyPy/sub\_frames/triggered.py      |       67 |       26 |       28 |        9 |     56.84% |28, 41-\>exit, 62-67, 110, 113, 116, 119, 122, 129, 139, 147, 183, 190, 211-217, 235-242 |
| FlowCyPy/workflow.py                   |      106 |       10 |       36 |        8 |     87.32% |89-\>91, 92, 94, 119, 134, 137, 150-152, 155, 167 |
| **TOTAL**                              | **1471** |  **539** |  **548** |  **133** | **59.39%** |           |

2 files skipped due to complete coverage.


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