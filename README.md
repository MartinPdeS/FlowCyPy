# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|---------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/flow\_cytometer.py                   |       87 |       33 |       34 |        7 |     55.37% |66, 69, 104-141, 240-259, 296, 302, 388 |
| FlowCyPy/fluidics/event\_collection.py        |      269 |       72 |      118 |       29 |     68.73% |72, 146, 167-171, 194, 197, 225-\>224, 257, 262, 277, 304, 349, 370, 423, 462, 468, 502-503, 514-\>exit, 533-540, 569-578, 652-656, 662, 667, 679, 682-685, 690-702, 706-\>713, 719, 740, 742-747, 828, 833, 843, 848, 851, 972-1005, 1028, 1033, 1066 |
| FlowCyPy/fluidics/main.py                     |       66 |       16 |       10 |        2 |     73.68% |83-90, 116, 145-181 |
| FlowCyPy/fluidics/population\_events.py       |       42 |       14 |        6 |        1 |     60.42% |56, 123, 147, 192-208 |
| FlowCyPy/fluidics/scatterer\_collection.py    |       31 |        7 |       12 |        2 |     74.42% |37-39, 79, 99, 109-112 |
| FlowCyPy/opto\_electronics/coupling\_model.py |       45 |        6 |       10 |        3 |     80.00% |46, 137-147, 162-166 |
| FlowCyPy/opto\_electronics/main.py            |       64 |        3 |       26 |        4 |     92.22% |129, 133-\>140, 160, 245 |
| FlowCyPy/presets/detector.py                  |       11 |       11 |        0 |        0 |      0.00% |      1-69 |
| FlowCyPy/presets/flow\_cytometer.py           |       75 |       75 |        0 |        0 |      0.00% |     1-423 |
| FlowCyPy/presets/population.py                |       24 |       24 |        2 |        0 |      0.00% |      1-66 |
| FlowCyPy/run\_record.py                       |       78 |       24 |       20 |        3 |     62.24% |84, 97, 110-113, 126-132, 144, 157-160, 236, 248, 270-283, 294 |
| FlowCyPy/sub\_frames/acquisition.py           |      139 |       37 |       66 |       19 |     68.78% |43, 56-\>exit, 86, 106-111, 139, 142, 149, 152, 163, 169, 174, 213, 216, 239, 249, 258-259, 302, 310, 321, 329, 337-\>340, 340-\>344, 355-378, 390-395 |
| FlowCyPy/sub\_frames/classifier.py            |       21 |       12 |        2 |        0 |     39.13% | 16, 42-62 |
| FlowCyPy/sub\_frames/events.py                |       55 |       14 |       18 |        6 |     67.12% |25-\>28, 33, 64, 76, 94, 108, 128, 132-146 |
| FlowCyPy/sub\_frames/peaks.py                 |      226 |      197 |       88 |        0 |      9.24% |24, 27, 77-176, 182-191, 211-213, 233-235, 251-252, 272-287, 321-338, 434-629, 654-674, 696-711, 715-738 |
| FlowCyPy/sub\_frames/triggered.py             |       97 |       76 |       36 |        0 |     15.79% |30, 41-44, 64-69, 111-178, 185, 192, 213-219, 237-244, 256-261, 272-292, 303-316 |
| FlowCyPy/workflow.py                          |       44 |       44 |        4 |        0 |      0.00% |     1-157 |
| **TOTAL**                                     | **1388** |  **665** |  **452** |   **76** | **48.97%** |           |

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