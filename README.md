# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/amplifier.py                                 |       27 |        1 |        4 |        2 |     90% |113, 123->exit |
| FlowCyPy/calibration.py                               |      158 |      158 |       22 |        0 |      0% |     1-444 |
| FlowCyPy/circuits.py                                  |       34 |        9 |        0 |        0 |     74% |104-108, 121-126 |
| FlowCyPy/classifier.py                                |       43 |        0 |        8 |        4 |     92% |34->37, 84->88, 140->144, 201->205 |
| FlowCyPy/coupling.py                                  |       57 |       23 |       16 |        2 |     52% |61-62, 143, 163-188, 217-219, 232-237, 250-258 |
| FlowCyPy/detector.py                                  |       48 |        7 |        4 |        2 |     83% |78, 104->112, 199-207, 227-233 |
| FlowCyPy/digitizer.py                                 |       47 |        9 |       12 |        5 |     73% |89-90, 103, 106-112, 123-130, 150 |
| FlowCyPy/distribution/base\_class.py                  |       22 |        3 |        0 |        0 |     86% |27, 31, 57 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   79, 112 |
| FlowCyPy/distribution/lognormal.py                    |       36 |        3 |        4 |        2 |     88% |95, 97, 133 |
| FlowCyPy/distribution/normal.py                       |       35 |        2 |        2 |        1 |     92% |   94, 139 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       36 |       16 |        4 |        0 |     50% |91-101, 129-139, 142 |
| FlowCyPy/distribution/uniform.py                      |       33 |        1 |        0 |        0 |     97% |       119 |
| FlowCyPy/distribution/weibull.py                      |       35 |       16 |        2 |        0 |     51% |31, 35, 39, 62-67, 84, 104-121, 124 |
| FlowCyPy/event\_frame.py                              |       83 |       38 |       28 |        1 |     50% |30-38, 76, 126-133, 169-195, 219-234, 268-284 |
| FlowCyPy/flow\_cell.py                                |       43 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/flow\_cytometer.py                           |       69 |       16 |       26 |        3 |     69% |108-115, 123-130, 161, 185->196, 253-266 |
| FlowCyPy/fluid\_region.py                             |       27 |        2 |        0 |        0 |     93% |    25, 33 |
| FlowCyPy/fluidics.py                                  |       39 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/fluorescence.py                              |       34 |       18 |        0 |        0 |     47% |19-23, 28, 31, 48, 55-60, 70, 74-75, 85, 88-89 |
| FlowCyPy/instances/detector.py                        |       11 |       11 |        0 |        0 |      0% |      1-62 |
| FlowCyPy/instances/flow\_cytometer.py                 |       47 |       47 |        0 |        0 |      0% |     1-209 |
| FlowCyPy/instances/population.py                      |       24 |       24 |        2 |        0 |      0% |      2-66 |
| FlowCyPy/opto\_electronics.py                         |       30 |        5 |       12 |        3 |     76% |75, 87-94, 156 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       26 |       21 |        0 |        0 |     19% |79-83, 129-164 |
| FlowCyPy/peak\_locator/base\_class.py                 |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/derivative.py                  |       47 |       42 |       20 |        0 |      7% |58-62, 92-161 |
| FlowCyPy/peak\_locator/global\_.py                    |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |       17 |        0 |        6 |        2 |     91% |99->102, 102->exit |
| FlowCyPy/peak\_locator/scipy.py                       |       42 |        0 |       10 |        4 |     92% |95->103, 106->113, 122->129, 129->136 |
| FlowCyPy/physical\_constant.py                        |        9 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       65 |       24 |       22 |        4 |     56% |25, 52-59, 89, 119-121, 151-153, 187-188, 405-422 |
| FlowCyPy/run\_record.py                               |       67 |       18 |       16 |        2 |     66% |72, 88-90, 106-108, 124, 140-142, 217->223, 220-221, 239-250 |
| FlowCyPy/scatterer\_collection.py                     |       32 |        7 |       12 |        2 |     75% |44-46, 86, 106, 116-119 |
| FlowCyPy/signal\_generator.py                         |       62 |       16 |       16 |        5 |     68% |43-47, 105, 127, 175, 193-202, 239, 272-280, 318 |
| FlowCyPy/signal\_processing.py                        |       12 |        0 |        2 |        0 |    100% |           |
| FlowCyPy/simulation\_settings.py                      |       33 |       13 |        6 |        1 |     54% |8-13, 66-68, 81, 85-91 |
| FlowCyPy/source.py                                    |       85 |       17 |       24 |        9 |     76% |40, 45-48, 52-69, 138, 146, 217, 219, 225, 227, 268, 341, 343 |
| FlowCyPy/sub\_frames/acquisition.py                   |      116 |       40 |       38 |        3 |     64% |115, 121, 127, 150-152, 172-194, 214-220, 253-269, 302, 309-322 |
| FlowCyPy/sub\_frames/base.py                          |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/sub\_frames/classifier.py                    |       15 |        8 |        2 |        0 |     41% |     38-54 |
| FlowCyPy/sub\_frames/peaks.py                         |       78 |       57 |       12 |        0 |     23% |23-29, 49-51, 71-73, 89-90, 110-125, 159-176, 199-222, 247-267 |
| FlowCyPy/sub\_frames/scatterer.py                     |       88 |       88 |       16 |        0 |      0% |     1-289 |
| FlowCyPy/sub\_frames/utils.py                         |       13 |        9 |        6 |        0 |     21% |     26-41 |
| FlowCyPy/triggering\_system.py                        |       93 |       40 |       20 |        3 |     53% |61-66, 81, 137-144, 160-170, 174-184, 253-263, 303-313, 329-352, 356-374 |
| FlowCyPy/utils.py                                     |       71 |       42 |       22 |        1 |     39% |29, 43-48, 59-71, 74, 99-108, 132-181 |
| FlowCyPy/workflow.py                                  |       41 |       41 |        4 |        0 |      0% |     1-149 |
|                                             **TOTAL** | **2100** |  **894** |  **418** |   **62** | **54%** |           |


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