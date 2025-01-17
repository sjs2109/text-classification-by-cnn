# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime
import numpy as np
import tensorflow as tf
from tensorflow.contrib import learn
import gflags
import data_helpers
from text_cnn import TextCNN

### parameters ###
# ===============================================

FLAGS = gflags.FLAGS

# data loading parameters
gflags.DEFINE_float('dev_sample_percentage', 0.1, 'Percentage of the training data to user for validation (dev set).')
gflags.DEFINE_string('data_file', './inputs/Womens Clothing E-Commerce Reviews_filtered.csv', 'Data source')


# model hyperparameters
gflags.DEFINE_integer('embedding_dim', 512, 'Dimensionality of word embedding (default: 128).')
gflags.DEFINE_string('filter_sizes', '3,4,5', "Comma-seperated filter sizes (default: '3,4,5').")
gflags.DEFINE_integer('num_filters', 512, 'Number of filters per filter size (default: 128).')
gflags.DEFINE_float('dropout_keep_prob', 0.5, 'Dropout keep probability (default: 0.5).')
gflags.DEFINE_float('l2_reg_lambda', 0.0, 'L2 regularization lambda (default: 0.0).')

# training parameters
gflags.DEFINE_integer('batch_size', 64, 'Batch size (default: 64).')
gflags.DEFINE_integer('num_epochs', 100, 'Number of training epochs (default: 200).')
gflags.DEFINE_integer('evaluate_every', 100, 'Evaluate model on dev set after this many of steps (default: 100).')
gflags.DEFINE_integer('checkpoint_every', 100, 'Save model after this many steps (default: 100).')
gflags.DEFINE_integer('num_checkpoints', 5, 'Number of checkpoints to store (default: 5).')

# device parameters
gflags.DEFINE_bool('allow_soft_placement', True, 'Allow device soft device placement.')
gflags.DEFINE_bool('log_device_placement', False, 'Log placement of ops on devices.')

FLAGS(sys.argv)
# show parameters
print('\nPARAMETERS:')
print('================================')
for attr, value in FLAGS.flag_values_dict().items():
    print('{0}: {1}'.format(attr.upper(), value))
print('================================\n\n')


### data preparation ###
# ===============================================

# load data
x_text, y = data_helpers.load_text_and_label(data_file=FLAGS.data_file)

# build vocabulary
max_sentence_length = max([len(s.split(' ')) for s in x_text])
vocab_prosessor = learn.preprocessing.VocabularyProcessor(max_sentence_length)
x = vocab_prosessor.fit_transform(raw_documents=x_text)
x = np.array(list(x))

# random shuffle data
np.random.seed(314)
shuffle_indices = np.random.permutation(np.arange(len(y)))
x_shuffled = x[shuffle_indices]
y_shuffled = y[shuffle_indices]

# split train/dev set
split_index = -int(float(len(y)) * FLAGS.dev_sample_percentage)
x_train, x_dev = x_shuffled[:split_index], x_shuffled[split_index:]
y_train, y_dev = y_shuffled[:split_index], y_shuffled[split_index:]

del x, y, x_shuffled, y_shuffled

print('max sentence lenght: {:d}'.format(max_sentence_length))
print('vocabulary size: {:d}'.format(len(vocab_prosessor.vocabulary_)))
print('train/dev split: {:d} / {:d}'.format(len(x_train), len(x_dev)))
print('================================\n\n')


### training
# ===============================================

with tf.Graph().as_default():
    session_conf = tf.ConfigProto(
        allow_soft_placement=FLAGS.allow_soft_placement,
        log_device_placement=FLAGS.log_device_placement)
    sess = tf.Session(config=session_conf)
    with sess.as_default():
        cnn = TextCNN(
            num_classes=y_train.shape[1],
            sequence_length=x_train.shape[1],
            vocab_size=len(vocab_prosessor.vocabulary_),
            embedding_size=FLAGS.embedding_dim,
            filter_sizes=list(map(int, FLAGS.filter_sizes.split(','))),
            num_filters=FLAGS.num_filters,
            l2_reg_lambda=FLAGS.l2_reg_lambda
            )

        # define training procedure
        global_step = tf.Variable(0, trainable=False, name='global_step')
        optimizer = tf.train.AdamOptimizer(learning_rate=1e-4)
        grads_and_vars = optimizer.compute_gradients(cnn.loss)
        train_op = optimizer.apply_gradients(grads_and_vars, global_step=global_step)

        # output directory for models and summaries
        timestamp = str(int(time.time()))
        out_dir = os.path.abspath(os.path.join(os.curdir, 'log', timestamp))
        print('Writing log to {}\n'.format(out_dir))

        # summaries for loss and accuracy
        loss_summary = tf.summary.scalar('loss', cnn.loss)
        acc_summary = tf.summary.scalar('accuracy', cnn.accuracy)

        # train summaries
        train_summary_op = tf.summary.merge([loss_summary, acc_summary])
        train_summary_dir = os.path.join(out_dir, 'summaries', 'train')
        train_summary_writer = tf.summary.FileWriter(train_summary_dir, tf.get_default_graph())

        # dev summaries
        dev_summary_op = tf.summary.merge([loss_summary, acc_summary])
        dev_summary_dir = os.path.join(out_dir, 'summaries', 'dev')
        dev_summary_writer = tf.summary.FileWriter(dev_summary_dir, tf.get_default_graph())

        # checkpointing, tensorflow assumes this directory already existed, so we need to create it
        checkpoint_dir = os.path.join(out_dir, 'checkpoints')
        checkpoint_prefix = os.path.join(checkpoint_dir, 'model')
        if not os.path.exists(checkpoint_dir):
            os.makedirs(checkpoint_dir)
        saver = tf.train.Saver(tf.global_variables(), max_to_keep=FLAGS.num_checkpoints)

        # write vocabulary
        vocab_prosessor.save(os.path.join(out_dir, 'vocab'))

        # initialize all variables
        sess.run(tf.global_variables_initializer())

        # function for a single training step
        def train_step(x_batch, y_batch, writer=None):
            '''
            A single training step.
            '''
            feed_dict = {
                cnn.input_x: x_batch,
                cnn.input_y: y_batch,
                cnn.dropout_keep_prob: FLAGS.dropout_keep_prob
            }
            _, step, summaries, loss, accuracy = sess.run(
                [train_op, global_step, train_summary_op, cnn.loss, cnn.accuracy],
                feed_dict)
            timestr = datetime.datetime.now().isoformat()
            print('{}: step {}, loss {:g}, acc {:g}'.format(timestr, step, loss, accuracy))
            if writer:
                writer.add_summary(summaries, step)

        def dev_step(x_batch, y_batch, writer=None):
            '''
            Evalute the model on dev set.
            '''
            feed_dict = {
                cnn.input_x: x_batch,
                cnn.input_y: y_batch,
                cnn.dropout_keep_prob: 1.0
            }
            step, summaries, loss, accuracy = sess.run(
                [global_step, dev_summary_op, cnn.loss, cnn.accuracy],
                feed_dict)
            timestr = datetime.datetime.now().isoformat()
            print('{}: step {}, loss {:g}, acc {:g}'.format(timestr, step, loss, accuracy))
            if writer:
                writer.add_summary(summaries, step)

        ### training loop
        # generate batches
        batches = data_helpers.batch_iter(
            data=list(zip(x_train, y_train)), batch_size=FLAGS.batch_size, num_epochs=FLAGS.num_epochs)
        # train loop, for each batch
        for batch in batches:
            x_batch, y_batch = zip(*batch)
            train_step(x_batch, y_batch, writer=train_summary_writer)
            current_step = tf.train.global_step(sess, global_step)
            if current_step % FLAGS.evaluate_every == 0:
                print('\nEvaluation on dev set:')
                dev_step(x_dev, y_dev, writer=dev_summary_writer)
                print('')
            if current_step % FLAGS.checkpoint_every == 0:
                path = saver.save(sess=sess, save_path=checkpoint_prefix, global_step=global_step)
                print('\nSaved model checkpoint to {}\n'.format(path))

# end
print('\n--- Done! ---\n')
input('\npress any key to exit...\n')
