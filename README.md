# text-classification-by-cnn
**A convolutional neural network model for sentence classification by using tensorflow.**

## Requirement
- python3
- tensorflow 1.6.0
- numpy
- python-gflags (for processing the input arguments)

## Start training
```python
python train.py
```

## Visualizing results in TensorBoard
```shell
tensorboard --logdir /"PATH_OF_CODE"/log/"TIMESTAMP"/summaries/
```

## Descreption of files
- **inputs (directory)**: The dataset contains 10,662 examples of movie review sentences. download from -> ["Movie Review data from Rotten Tomatoes"](http://www.cs.cornell.edu/people/pabo/movie-review-data/). One positive sentences file, one negative sentences file.
- **data_helpers.py**: It contains functions for the data loading, data clean and generating batch data for training.
- **text_cnn.py**: The core function for generating a cnn for text classification. Model structure: embedding layer -> convolutional layer -> max-pooling layer -> softmax layer.
- **train.py**: It implements the reading parameters, data preperation and training procedure.

## *Refer to the papers*

[1]. [Kim, Y. (2014). Convolutional neural networks for sentence classification. Eprint Arxiv.](https://arxiv.org/pdf/1408.5882)

[2]. [Zhang, Y., & Wallace, B. (2015). A sensitivity analysis of (and practitioners' guide to) convolutional neural networks for sentence classification. Computer Science.](https://arxiv.org/pdf/1510.03820.pdf)
