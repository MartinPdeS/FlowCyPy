# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                  |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|-------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/analysis.py                  |       98 |        7 |       36 |        8 |     88.81% |38, 41, 43, 89, 120, 124, 131-\>133, 155 |
| FlowCyPy/event\_collection.py         |      257 |       87 |      112 |       23 |     62.06% |65, 70, 141, 162-166, 189, 192, 220-\>219, 233, 260, 302, 323, 344-346, 374, 413, 419, 440-466, 484-491, 520-529, 603-607, 613, 618, 630, 633-636, 641-653, 657-\>664, 670, 691, 693-698, 779, 784, 794, 799, 802, 923-956, 978-988, 1017 |
| FlowCyPy/flow\_cytometer.py           |      150 |       18 |       64 |       14 |     85.05% |50-51, 53, 85, 88, 145, 177, 182, 185, 189-\>187, 193, 297-303, 343, 345, 354, 407, 443 |
| FlowCyPy/fluorescence.py              |      186 |       23 |       94 |       21 |     84.29% |29, 87, 91, 102, 140, 151, 163, 183, 189, 198, 211, 213, 215, 232, 243, 254, 315, 318, 320, 350, 357-362 |
| FlowCyPy/run\_record.py               |      170 |       56 |       74 |       13 |     59.43% |95, 97, 168, 181, 195, 210-216, 286, 299-302, 368-374, 393-406, 447, 465, 471, 474-475, 478-479, 484, 526-558, 591, 600-603, 616 |
| FlowCyPy/sub\_frames/acquisition.py   |      115 |       18 |       58 |       19 |     77.46% |55-\>exit, 89, 111-\>114, 140, 143, 150, 153, 164, 170, 175, 215, 218, 246, 256, 270-271, 324, 332, 343, 351, 359-\>362, 362-\>366 |
| FlowCyPy/sub\_frames/classifier.py    |       33 |       24 |        8 |        0 |     21.95% | 15, 39-79 |
| FlowCyPy/sub\_frames/events.py        |       55 |       14 |       18 |        6 |     67.12% |24-\>27, 33, 64, 76, 94, 108, 128, 132-146 |
| FlowCyPy/sub\_frames/peak\_metrics.py |       26 |       17 |        6 |        0 |     28.12% |14, 20-21, 25, 31-46 |
| FlowCyPy/sub\_frames/peaks.py         |      276 |      113 |      124 |       39 |     54.50% |90, 93, 105, 112, 119, 124, 136, 167-174, 183-\>186, 207-214, 228, 247, 262-273, 287-293, 353, 358, 368, 373, 377-\>380, 399, 402, 405, 513, 525-526, 529-530, 543, 548, 553, 559, 567, 570, 575, 578, 610-650, 691-692, 695-696, 716, 719-720, 725, 729-757, 778-798, 849-872 |
| FlowCyPy/sub\_frames/triggered.py     |       67 |       21 |       28 |       10 |     63.16% |39-\>exit, 62-\>65, 108, 111, 114, 117, 120, 127, 137, 145, 181, 188, 209-215, 233-240 |
| FlowCyPy/systems/\_assembly.py        |       25 |        1 |        2 |        1 |     92.59% |       104 |
| FlowCyPy/systems/agilent.py           |        6 |        6 |        0 |        0 |      0.00% |      3-46 |
| FlowCyPy/systems/beckman\_coulter.py  |        5 |        5 |        0 |        0 |      0.00% |      3-32 |
| FlowCyPy/systems/cytek.py             |       24 |       13 |        0 |        0 |     45.83% |    39-127 |
| FlowCyPy/systems/miltenyi.py          |        3 |        3 |        0 |        0 |      0.00% |       3-6 |
| FlowCyPy/systems/nanofcm.py           |        3 |        3 |        0 |        0 |      0.00% |       3-6 |
| FlowCyPy/systems/stratedigm.py        |        4 |        4 |        0 |        0 |      0.00% |      3-26 |
| FlowCyPy/systems/thermo\_fisher.py    |        4 |        4 |        0 |        0 |      0.00% |      3-20 |
| **TOTAL**                             | **1608** |  **437** |  **626** |  **154** | **68.44%** |           |

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