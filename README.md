# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                  |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|-------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/analysis.py                  |       98 |        7 |       36 |        8 |     88.81% |38, 41, 43, 89, 120, 124, 131-\>133, 155 |
| FlowCyPy/event\_collection.py         |      252 |       86 |      112 |       23 |     61.81% |64, 69, 140, 161-165, 188, 191, 219-\>218, 232, 259, 301, 322, 343-345, 373, 412, 418, 439-465, 483-490, 519-528, 601-605, 611, 616, 628, 631-634, 639-651, 655-\>662, 668, 689, 691-696, 776, 781, 791, 796, 799, 908-937, 959-969, 998 |
| FlowCyPy/flow\_cytometer.py           |      155 |       23 |       68 |       15 |     82.06% |50-51, 53, 85, 88, 146, 179, 184, 187, 191-\>189, 195, 213-217, 306-312, 352, 354, 363, 416, 452 |
| FlowCyPy/fluorescence.py              |      253 |       28 |      142 |       30 |     85.32% |31, 91, 95, 103, 105, 116, 154, 165, 177, 197, 203, 212, 225, 227, 229, 260, 272-\>271, 275-276, 292, 303, 314, 326, 329, 380, 383, 385, 421, 432, 434-\>443, 436-\>438 |
| FlowCyPy/opto\_electronics/laser.py   |       17 |        3 |        8 |        3 |     76.00% |31, 35, 37 |
| FlowCyPy/run\_record.py               |      165 |       55 |       72 |       13 |     58.65% |94, 96, 167, 180, 194, 209-215, 285, 298-301, 363-369, 386-399, 440, 457, 463, 466-467, 470-471, 476, 518-549, 582, 591-594, 607 |
| FlowCyPy/sub\_frames/\_plotting.py    |       27 |        2 |       18 |        4 |     86.67% |21, 23, 26-\>28, 30-\>32 |
| FlowCyPy/sub\_frames/acquisition.py   |      115 |       18 |       58 |       19 |     77.46% |55-\>exit, 89, 111-\>114, 140, 143, 150, 153, 164, 170, 175, 215, 218, 246, 256, 270-271, 324, 332, 343, 351, 359-\>362, 362-\>366 |
| FlowCyPy/sub\_frames/classifier.py    |       25 |       16 |        4 |        0 |     31.03% | 15, 39-66 |
| FlowCyPy/sub\_frames/events.py        |       55 |       14 |       18 |        6 |     67.12% |24-\>27, 33, 64, 76, 94, 108, 128, 132-146 |
| FlowCyPy/sub\_frames/peak\_metrics.py |       26 |       17 |        6 |        0 |     28.12% |14, 20-21, 25, 31-46 |
| FlowCyPy/sub\_frames/peaks.py         |      272 |      113 |      124 |       39 |     54.04% |89, 92, 104, 111, 118, 123, 135, 166-173, 182-\>185, 206-213, 227, 246, 261-272, 286-292, 351, 356, 366, 371, 375-\>378, 397, 400, 403, 510, 522-523, 526-527, 540, 545, 550, 556, 564, 567, 572, 575, 607-647, 688-689, 692-693, 701, 704-705, 710, 714-742, 763-783, 834-857 |
| FlowCyPy/sub\_frames/triggered.py     |       67 |       21 |       28 |       10 |     63.16% |39-\>exit, 62-\>65, 108, 111, 114, 117, 120, 127, 137, 145, 181, 188, 209-215, 233-240 |
| FlowCyPy/systems/\_assembly.py        |       42 |        6 |       12 |        3 |     79.63% |118, 120-123, 125 |
| FlowCyPy/systems/agilent.py           |        6 |        6 |        0 |        0 |      0.00% |      3-46 |
| FlowCyPy/systems/beckman\_coulter.py  |        5 |        5 |        0 |        0 |      0.00% |      3-32 |
| FlowCyPy/systems/cytek.py             |       25 |       13 |        0 |        0 |     48.00% |    48-137 |
| FlowCyPy/systems/miltenyi.py          |        3 |        3 |        0 |        0 |      0.00% |       3-6 |
| FlowCyPy/systems/nanofcm.py           |        3 |        3 |        0 |        0 |      0.00% |       3-6 |
| FlowCyPy/systems/stratedigm.py        |        4 |        4 |        0 |        0 |      0.00% |      3-26 |
| FlowCyPy/systems/thermo\_fisher.py    |        4 |        4 |        0 |        0 |      0.00% |      3-20 |
| **TOTAL**                             | **1725** |  **447** |  **710** |  **173** | **69.86%** |           |

12 files skipped due to complete coverage.


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