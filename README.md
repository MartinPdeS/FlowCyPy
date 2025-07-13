# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/MartinPdeS/FlowCyPy/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                  |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| FlowCyPy/\_detector\_instances.py                     |       11 |        3 |        0 |        0 |     73% |15, 34, 54 |
| FlowCyPy/\_flow\_cytometer\_instances.py              |       23 |       11 |        0 |        0 |     52% |     26-83 |
| FlowCyPy/\_population\_instances.py                   |       24 |        6 |        2 |        0 |     77% |9, 19, 58-67 |
| FlowCyPy/amplifier.py                                 |       41 |        3 |        8 |        4 |     86% |67, 73, 124, 134->exit |
| FlowCyPy/calibration.py                               |      192 |      192 |       30 |        0 |      0% |     1-397 |
| FlowCyPy/circuits.py                                  |       38 |        9 |        0 |        0 |     76% |101-105, 116-121 |
| FlowCyPy/classifier.py                                |       44 |        0 |        8 |        4 |     92% |32->35, 74->78, 121->125, 172->176 |
| FlowCyPy/coupling.py                                  |       43 |       10 |       10 |        2 |     74% |50, 137, 154-176 |
| FlowCyPy/cytometer.py                                 |       72 |        6 |       16 |        4 |     89% |22, 159, 179->187, 223-229, 257 |
| FlowCyPy/detector.py                                  |       71 |       11 |       12 |        6 |     80% |85, 107, 129, 149, 157, 178->182, 267-275, 295-300 |
| FlowCyPy/digitizer.py                                 |       53 |        9 |       12 |        5 |     75% |93-94, 117, 130-133, 142-149, 165 |
| FlowCyPy/distribution/base\_class.py                  |       25 |        3 |        0 |        0 |     88% |32, 36, 65 |
| FlowCyPy/distribution/delta.py                        |       31 |        2 |        2 |        1 |     91% |   74, 104 |
| FlowCyPy/distribution/lognormal.py                    |       37 |        3 |        4 |        2 |     88% |90, 92, 124 |
| FlowCyPy/distribution/normal.py                       |       36 |        2 |        2 |        1 |     92% |   89, 128 |
| FlowCyPy/distribution/particle\_size\_distribution.py |       37 |       16 |        4 |        0 |     51% |86-94, 120-130, 133 |
| FlowCyPy/distribution/uniform.py                      |       34 |        1 |        0 |        0 |     97% |       117 |
| FlowCyPy/distribution/weibull.py                      |       36 |       16 |        2 |        0 |     53% |28, 32, 36, 57-62, 79, 102-112, 115 |
| FlowCyPy/flow\_cell.py                                |       76 |        5 |       20 |        5 |     90% |113, 120, 229, 232, 259 |
| FlowCyPy/fluid\_region.py                             |       28 |        2 |        0 |        0 |     93% |    25, 33 |
| FlowCyPy/fluidics.py                                  |       42 |        0 |        4 |        2 |     96% |97->101, 145->148 |
| FlowCyPy/helper.py                                    |       23 |        3 |       10 |        3 |     82% |36, 40, 44 |
| FlowCyPy/opto\_electronics.py                         |       29 |        3 |        8 |        3 |     84% |71, 146, 151 |
| FlowCyPy/particle\_count.py                           |       45 |       20 |       20 |        4 |     51% |31-32, 42, 65-73, 102-105, 111, 116-121, 128 |
| FlowCyPy/peak\_locator/DeepPeak.py                    |       26 |       21 |        0 |        0 |     19% |70-74, 120-153 |
| FlowCyPy/peak\_locator/base\_class.py                 |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/derivative.py                  |       47 |       42 |       20 |        0 |      7% |50-54, 84-138 |
| FlowCyPy/peak\_locator/global\_.py                    |       17 |        0 |        6 |        0 |    100% |           |
| FlowCyPy/peak\_locator/moving\_average.py             |       17 |        0 |        6 |        2 |     91% |95->98, 98->exit |
| FlowCyPy/peak\_locator/scipy.py                       |       42 |        0 |       10 |        4 |     92% |86->94, 97->104, 111->116, 116->121 |
| FlowCyPy/physical\_constant.py                        |       10 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/population.py                                |       51 |        8 |       12 |        5 |     79% |46-47, 50, 79-80, 83, 109, 239 |
| FlowCyPy/scatterer\_collection.py                     |       59 |        9 |       24 |        5 |     78% |54, 111, 129, 133, 140-145, 200 |
| FlowCyPy/signal\_generator.py                         |       68 |       21 |       16 |        5 |     64% |42-45, 70-71, 114, 137, 181, 194-206, 239, 264-278, 314 |
| FlowCyPy/signal\_processing.py                        |       20 |        4 |        4 |        0 |     75% |     83-88 |
| FlowCyPy/simulation\_settings.py                      |       35 |       13 |        6 |        1 |     56% |8-14, 66-68, 83, 87-93 |
| FlowCyPy/source.py                                    |      136 |       33 |       50 |       14 |     69% |37, 41, 48-56, 60-66, 74, 86, 89, 94-106, 173, 178, 217, 219, 266, 273, 322, 324, 328, 330, 384, 404 |
| FlowCyPy/sub\_frames/acquisition.py                   |      123 |       34 |       42 |        1 |     70% |131, 149-153, 250-266, 301, 309-337 |
| FlowCyPy/sub\_frames/base.py                          |        5 |        0 |        0 |        0 |    100% |           |
| FlowCyPy/sub\_frames/classifier.py                    |       15 |        8 |        2 |        0 |     41% |     35-49 |
| FlowCyPy/sub\_frames/peaks.py                         |       74 |       42 |       12 |        2 |     40% |19, 24, 42-44, 62-64, 80-81, 99-114, 155-172, 243-259 |
| FlowCyPy/sub\_frames/scatterer.py                     |      100 |       63 |       20 |        1 |     33% |25-32, 48-57, 82-102, 129-141, 177-192, 215, 228-234, 237-249, 252-271 |
| FlowCyPy/sub\_frames/utils.py                         |       79 |       45 |       26 |        6 |     38% |41, 43->46, 114-119, 122-125, 128, 130->133, 159-204, 228-243 |
| FlowCyPy/triggering\_system.py                        |       82 |       30 |       12 |        3 |     63% |48-53, 68-70, 129-136, 152-164, 268-278, 294-317 |
| FlowCyPy/units.py                                     |       30 |        0 |        4 |        0 |    100% |           |
| FlowCyPy/utils.py                                     |       56 |       56 |       14 |        0 |      0% |     1-134 |
|                                             **TOTAL** | **2200** |  **765** |  **466** |   **95** | **62%** |           |


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