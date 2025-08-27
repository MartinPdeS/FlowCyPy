# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/\_detector\_instances.py                     |       11 |        3 |        0 |        0 |     73% |16, 39, 62 |
| FlowCyPy/\_flow\_cytometer\_instances.py              |       23 |       11 |        0 |        0 |     52% |     27-85 |
| FlowCyPy/\_population\_instances.py                   |       24 |        6 |        2 |        0 |     77% |10, 22, 59-66 |
| FlowCyPy/amplifier.py                                 |       29 |        1 |        4 |        2 |     91% |113, 123->exit |
| FlowCyPy/calibration.py                               |      186 |      186 |       30 |        0 |      0% |     1-450 |
| FlowCyPy/circuits.py                                  |       34 |        9 |        0 |        0 |     74% |104-108, 121-126 |
| FlowCyPy/classifier.py                                |       43 |        0 |        8 |        4 |     92% |34->37, 84->88, 140->144, 201->205 |
| FlowCyPy/coupling.py                                  |       42 |       10 |       10 |        2 |     73% |56, 147, 166-190 |
| FlowCyPy/detector.py                                  |       48 |        7 |        4 |        2 |     83% |73, 99->107, 194-202, 222-228 |
| FlowCyPy/digitizer.py                                 |       49 |        9 |       12 |        5 |     74% |90-91, 104, 107-113, 124-131, 151 |
| FlowCyPy/distribution/base\_class.py                  |       24 |        3 |        0 |        0 |     88% |27, 31, 60 |
| FlowCyPy/distribution/delta.py                        |       32 |        2 |        2 |        1 |     91% |   79, 112 |
| FlowCyPy/distribution/lognormal.py                    |       38 |        3 |        4 |        2 |     88% |93, 95, 129 |
| FlowCyPy/distribution/normal.py                       |       37 |        2 |        2 |        1 |     92% |   92, 135 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       38 |       16 |        4 |        0 |     52% |91-101, 129-139, 142 |
| FlowCyPy/distribution/uniform.py                      |       35 |        1 |        0 |        0 |     97% |       121 |
| FlowCyPy/distribution/weibull.py                      |       37 |       16 |        2 |        0 |     54% |31, 35, 39, 62-67, 84, 106-123, 126 |
| FlowCyPy/flow\_cell.py                                |       59 |        3 |       12 |        3 |     92% |212, 215, 238 |
| FlowCyPy/flow\_cytometer.py                           |       71 |        6 |       16 |        4 |     89% |23, 171, 191->202, 238-244, 272 |
| FlowCyPy/fluid\_region.py                             |       27 |        2 |        0 |        0 |     93% |    25, 33 |
| FlowCyPy/fluidics.py                                  |       33 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/helper.py                                    |       90 |       55 |       30 |        6 |     34% |45-46, 48->51, 71-102, 134-179, 255-260, 263-266, 269, 271->274 |
| FlowCyPy/opto\_electronics.py                         |       30 |        3 |        8 |        3 |     84% |82, 156, 163 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       26 |       21 |        0 |        0 |     19% |79-83, 129-164 |
| FlowCyPy/peak\_locator/base\_class.py                 |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/derivative.py                  |       47 |       42 |       20 |        0 |      7% |58-62, 92-161 |
| FlowCyPy/peak\_locator/global\_.py                    |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |       17 |        0 |        6 |        2 |     91% |99->102, 102->exit |
| FlowCyPy/peak\_locator/scipy.py                       |       42 |        0 |       10 |        4 |     92% |95->103, 106->113, 122->129, 129->136 |
| FlowCyPy/physical\_constant.py                        |        9 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       55 |       14 |       16 |        3 |     65% |46-53, 83, 113-115, 145-147, 292 |
| FlowCyPy/scatterer\_collection.py                     |       57 |        7 |       20 |        4 |     83% |72, 133, 153, 163-166, 221 |
| FlowCyPy/signal\_generator.py                         |       62 |       16 |       16 |        5 |     68% |43-47, 105, 127, 175, 193-202, 239, 272-280, 318 |
| FlowCyPy/signal\_processing.py                        |       18 |        4 |        4 |        0 |     73% |     83-90 |
| FlowCyPy/simulation\_settings.py                      |       35 |       13 |        6 |        1 |     56% |8-13, 66-68, 83, 87-93 |
| FlowCyPy/source.py                                    |      100 |       20 |       28 |       11 |     76% |42, 47-50, 54-71, 140, 148, 188, 190, 255, 264, 313, 315, 321, 323, 398, 420 |
| FlowCyPy/sub\_frames/acquisition.py                   |      128 |       36 |       46 |        3 |     70% |127, 136, 142, 163-167, 277-295, 335, 342-375 |
| FlowCyPy/sub\_frames/base.py                          |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/sub\_frames/classifier.py                    |       15 |        8 |        2 |        0 |     41% |     38-54 |
| FlowCyPy/sub\_frames/peaks.py                         |       75 |       42 |       12 |        2 |     40% |24, 29, 49-51, 71-73, 89-90, 110-125, 166-183, 254-269 |
| FlowCyPy/sub\_frames/scatterer.py                     |       98 |       61 |       20 |        1 |     34% |30-37, 55-64, 97-117, 152-164, 202-221, 255, 278-284, 290-302, 322-341 |
| FlowCyPy/sub\_frames/utils.py                         |       13 |        9 |        6 |        0 |     21% |     26-41 |
| FlowCyPy/triggering\_system.py                        |       80 |       28 |       12 |        3 |     64% |60-65, 80, 145-152, 168-180, 287-297, 313-338 |
| FlowCyPy/utils.py                                     |       58 |       41 |       14 |        0 |     24% |21-26, 37-49, 52, 77-86, 110-159 |
| FlowCyPy/workflow.py                                  |       57 |       57 |        4 |        0 |      0% |     1-149 |
|                                             **TOTAL** | **2071** |  **773** |  **404** |   **74** | **59%** |           |


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