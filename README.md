# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                   |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|--------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/analysis.py                   |       79 |        8 |       30 |        8 |     85.32% |26, 29, 35, 78, 119, 123, 148, 163 |
| FlowCyPy/flow\_cytometer.py            |      132 |       15 |       46 |       15 |     83.15% |71, 76, 79, 164, 169, 172, 188, 301-304, 314-\>319, 356, 362, 444, 448, 450, 477 |
| FlowCyPy/fluidics/event\_collection.py |      269 |       88 |      118 |       25 |     63.05% |76, 150, 171-175, 198, 201, 229-\>228, 261, 266, 281, 308, 353, 374, 401-403, 431, 470, 476, 497-523, 541-548, 577-586, 660-664, 670, 675, 687, 690-693, 698-710, 714-\>721, 727, 748, 750-755, 836, 841, 851, 856, 859, 980-1013, 1035-1045, 1074 |
| FlowCyPy/fluidics/system.py            |       81 |        4 |       20 |        4 |     92.08% |40, 42, 132, 158 |
| FlowCyPy/opto\_electronics/system.py   |       65 |        3 |       26 |        4 |     92.31% |136, 140-\>147, 168, 255 |
| FlowCyPy/presets/detector.py           |       20 |       20 |        0 |        0 |      0.00% |      1-81 |
| FlowCyPy/presets/flow\_cytometer.py    |       73 |       73 |        0 |        0 |      0.00% |     1-422 |
| FlowCyPy/presets/population.py         |       24 |       24 |        2 |        0 |      0.00% |     1-110 |
| FlowCyPy/run\_record.py                |      152 |       86 |       68 |        3 |     35.00% |80-82, 94, 107-110, 123-129, 168, 245, 258-261, 290-335, 339-342, 352-365, 405-445, 485-517, 550, 559-562, 575 |
| FlowCyPy/sub\_frames/acquisition.py    |      113 |       34 |       58 |       19 |     63.16% |40, 53-\>exit, 87, 107-112, 140, 143, 150, 153, 164, 170, 175, 214, 217, 233, 245, 254-257, 269-270, 323, 328-336, 338-\>346, 342, 347-353, 355-\>358, 358-\>361, 361-\>365 |
| FlowCyPy/sub\_frames/classifier.py     |       21 |       12 |        2 |        0 |     39.13% | 15, 39-59 |
| FlowCyPy/sub\_frames/events.py         |       55 |       14 |       18 |        6 |     67.12% |25-\>28, 34, 65, 77, 95, 109, 129, 133-147 |
| FlowCyPy/sub\_frames/peak\_metrics.py  |       26 |       17 |        6 |        0 |     28.12% |15, 21-22, 26, 32-47 |
| FlowCyPy/sub\_frames/peaks.py          |      281 |      121 |      126 |       40 |     52.09% |92, 95, 107, 114, 121, 126, 138, 169-176, 185-\>188, 209-216, 230, 249, 264-275, 289-295, 355, 360, 370, 375, 379-\>382, 401, 404, 407, 427, 533, 545-546, 549-550, 563, 568, 573, 579, 587, 590, 595, 598, 630-670, 711-712, 715-716, 736, 739-740, 745, 749-777, 798-818, 849-859, 876-899 |
| FlowCyPy/sub\_frames/triggered.py      |       67 |       26 |       28 |        9 |     56.84% |27, 40-\>exit, 61-66, 109, 112, 115, 118, 121, 128, 138, 146, 182, 189, 210-216, 234-241 |
| FlowCyPy/workflow.py                   |      105 |       10 |       36 |        8 |     87.23% |87-\>89, 90, 92, 117, 132, 135, 148-150, 153, 165 |
| **TOTAL**                              | **1573** |  **555** |  **584** |  **141** | **60.87%** |           |

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