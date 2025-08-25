# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/\_detector\_instances.py                     |       11 |        3 |        0 |        0 |     73% |15, 34, 54 |
| FlowCyPy/\_flow\_cytometer\_instances.py              |       23 |       11 |        0 |        0 |     52% |     25-82 |
| FlowCyPy/\_population\_instances.py                   |       24 |        6 |        2 |        0 |     77% |11, 21, 60-69 |
| FlowCyPy/amplifier.py                                 |       29 |        1 |        4 |        2 |     91% |112, 122->exit |
| FlowCyPy/calibration.py                               |      188 |      188 |       30 |        0 |      0% |     1-393 |
| FlowCyPy/circuits.py                                  |       34 |        9 |        0 |        0 |     74% |98-102, 113-118 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling.py                                  |       42 |       10 |       10 |        2 |     73% |50, 137, 154-176 |
| FlowCyPy/detector.py                                  |       48 |        7 |        4 |        2 |     83% |61, 82->86, 166-174, 189-194 |
| FlowCyPy/digitizer.py                                 |       49 |        9 |       12 |        5 |     74% |88-89, 103, 106-109, 118-125, 141 |
| FlowCyPy/distribution/base\_class.py                  |       24 |        3 |        0 |        0 |     88% |26, 30, 59 |
| FlowCyPy/distribution/delta.py                        |       32 |        2 |        2 |        1 |     91% |   75, 105 |
| FlowCyPy/distribution/lognormal.py                    |       38 |        3 |        4 |        2 |     88% |91, 93, 125 |
| FlowCyPy/distribution/normal.py                       |       37 |        2 |        2 |        1 |     92% |   90, 129 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       38 |       16 |        4 |        0 |     52% |88-96, 122-132, 135 |
| FlowCyPy/distribution/uniform.py                      |       35 |        1 |        0 |        0 |     97% |       119 |
| FlowCyPy/distribution/weibull.py                      |       37 |       16 |        2 |        0 |     54% |30, 34, 38, 59-64, 81, 104-114, 117 |
| FlowCyPy/flow\_cell.py                                |       59 |        3 |       12 |        3 |     92% |203, 206, 233 |
| FlowCyPy/flow\_cytometer.py                           |       71 |        6 |       16 |        4 |     89% |22, 163, 183->191, 227-233, 261 |
| FlowCyPy/fluid\_region.py                             |       27 |        2 |        0 |        0 |     93% |    24, 32 |
| FlowCyPy/fluidics.py                                  |       35 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/helper.py                                    |       90 |       55 |       30 |        6 |     34% |44-45, 47->50, 68-94, 117-162, 230-235, 238-241, 244, 246->249 |
| FlowCyPy/opto\_electronics.py                         |       30 |        3 |        8 |        3 |     84% |73, 148, 153 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       26 |       21 |        0 |        0 |     19% |70-74, 120-153 |
| FlowCyPy/peak\_locator/base\_class.py                 |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/derivative.py                  |       47 |       42 |       20 |        0 |      7% |50-54, 84-138 |
| FlowCyPy/peak\_locator/global\_.py                    |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |       17 |        0 |        6 |        2 |     91% |95->98, 98->exit |
| FlowCyPy/peak\_locator/scipy.py                       |       42 |        0 |       10 |        4 |     92% |86->94, 97->104, 111->116, 116->121 |
| FlowCyPy/physical\_constant.py                        |        9 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       55 |       14 |       16 |        3 |     65% |34-41, 69, 98-100, 130-132, 276 |
| FlowCyPy/scatterer\_collection.py                     |       57 |        7 |       20 |        4 |     83% |62, 119, 137, 145-148, 203 |
| FlowCyPy/signal\_generator.py                         |       62 |       16 |       16 |        5 |     68% |44-47, 104, 127, 171, 187-196, 229, 260-268, 304 |
| FlowCyPy/signal\_processing.py                        |       20 |        4 |        4 |        0 |     75% |     84-89 |
| FlowCyPy/simulation\_settings.py                      |       35 |       13 |        6 |        1 |     56% |8-13, 65-67, 82, 86-92 |
| FlowCyPy/source.py                                    |      100 |       20 |       28 |       11 |     76% |29, 32-35, 39-51, 118, 123, 162, 164, 212, 219, 268, 270, 274, 276, 330, 350 |
| FlowCyPy/sub\_frames/acquisition.py                   |      128 |       36 |       46 |        3 |     70% |125, 131, 137, 158-162, 259-275, 310, 318-346 |
| FlowCyPy/sub\_frames/base.py                          |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/sub\_frames/classifier.py                    |       15 |        8 |        2 |        0 |     41% |     36-50 |
| FlowCyPy/sub\_frames/peaks.py                         |       75 |       42 |       12 |        2 |     40% |21, 26, 44-46, 64-66, 82-83, 101-116, 156-173, 247-262 |
| FlowCyPy/sub\_frames/scatterer.py                     |       98 |       61 |       20 |        1 |     34% |27-34, 50-59, 84-104, 138-150, 187-198, 225, 241-247, 253-265, 283-302 |
| FlowCyPy/sub\_frames/utils.py                         |       13 |        9 |        6 |        0 |     21% |     23-38 |
| FlowCyPy/triggering\_system.py                        |       80 |       28 |       12 |        3 |     64% |48-53, 68, 129-136, 152-164, 268-278, 294-317 |
| FlowCyPy/utils.py                                     |       58 |       41 |       14 |        0 |     24% |23-28, 37-47, 50, 75-84, 106-144 |
| FlowCyPy/workflow.py                                  |       58 |       58 |        4 |        0 |      0% |     2-149 |
|                                             **TOTAL** | **2079** |  **776** |  **404** |   **74** | **59%** |           |


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