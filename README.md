# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                          |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|---------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| FlowCyPy/flow\_cytometer.py                   |       91 |       36 |       36 |        7 |     53.54% |66, 69, 104-141, 205-208, 265-287, 324, 330, 416 |
| FlowCyPy/fluidics/event\_collection.py        |      179 |      109 |       58 |        5 |     32.49% |100, 124, 135, 187-198, 250, 273, 284, 304, 323-327, 357, 358-\>365, 366, 376-\>exit, 395-452, 458-465, 521-608, 639-654, 691-707, 723, 747 |
| FlowCyPy/fluidics/main.py                     |       81 |       38 |       12 |        2 |     52.69% |56-64, 100-139, 165-204, 298-299 |
| FlowCyPy/fluidics/scatterer\_collection.py    |       31 |        7 |       12 |        2 |     74.42% |37-39, 79, 99, 109-112 |
| FlowCyPy/instances/detector.py                |       11 |       11 |        0 |        0 |      0.00% |      1-62 |
| FlowCyPy/instances/flow\_cytometer.py         |       42 |       42 |        0 |        0 |      0.00% |     1-208 |
| FlowCyPy/instances/population.py              |       24 |       24 |        2 |        0 |      0.00% |      1-66 |
| FlowCyPy/opto\_electronics/coupling\_model.py |       44 |       14 |       14 |        3 |     60.34% |58-61, 126, 150, 170-201 |
| FlowCyPy/opto\_electronics/detector.py        |       36 |        6 |        8 |        2 |     81.82% |78, 159, 192-199 |
| FlowCyPy/opto\_electronics/main.py            |       64 |        3 |       26 |        4 |     92.22% |129, 133-\>140, 160, 245 |
| FlowCyPy/run\_record.py                       |       78 |       24 |       20 |        3 |     62.24% |84, 97, 110-113, 126-132, 144, 157-160, 236, 248, 270-283, 294 |
| FlowCyPy/sub\_frames/acquisition.py           |      139 |       37 |       66 |       19 |     68.78% |43, 56-\>exit, 86, 106-111, 139, 142, 149, 152, 163, 169, 174, 213, 216, 239, 249, 258-259, 302, 310, 321, 329, 337-\>340, 340-\>344, 355-378, 390-395 |
| FlowCyPy/sub\_frames/classifier.py            |       21 |       12 |        2 |        0 |     39.13% | 16, 42-62 |
| FlowCyPy/sub\_frames/peaks.py                 |      206 |      181 |       82 |        0 |      8.68% |22, 25, 75-174, 180-189, 209-211, 231-233, 249-250, 270-285, 319-336, 432-627, 652-672 |
| FlowCyPy/sub\_frames/scatterer.py             |       87 |       87 |       16 |        0 |      0.00% |     1-286 |
| FlowCyPy/sub\_frames/triggered.py             |       97 |       76 |       36 |        0 |     15.79% |30, 41-44, 64-69, 111-178, 185, 192, 213-219, 237-244, 256-261, 272-292, 303-316 |
| FlowCyPy/sub\_frames/utils.py                 |       13 |        9 |        6 |        0 |     21.05% |     26-41 |
| FlowCyPy/utils.py                             |       70 |       44 |       22 |        2 |     34.78% |17-18, 27, 41-46, 57-69, 72, 97-106, 130-179 |
| FlowCyPy/workflow.py                          |       44 |       44 |        4 |        0 |      0.00% |     1-157 |
| **TOTAL**                                     | **1378** |  **804** |  **422** |   **49** | **38.50%** |           |

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