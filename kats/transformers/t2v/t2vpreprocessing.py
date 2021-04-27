#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
from typing import List, Optional, NamedTuple

import numpy as np
from kats.consts import TimeSeriesData


class T2VPreprocessing:

    """
    A class for preprocessing time series data. Steps
    include - 1. TO-DO: Segmentation 2. TO-DO: Padding
    3. Normalization 4. Label Separation

    :Parameters:
    param: NamedTuple
        T2VParam object containing necessary user defined
        parameters for data preprocessing.
    data: List[TimeSeriesData]
        A list of processed timeseries data.
    label: Optional[List]
        A list of labels provided by the user. If provided,
        treat as 'supervised' modeling, else, treat as 'unsupervised'
        modeling.
    dummy_label: bool
        For translation only, default is False, if set True, meaning
        that you had label for training data for building translator,
        but no label for testing data yet to be translated
    """

    def __init__(
        self,
        param: NamedTuple,  # TO-DO: Add segmented transformation (21Q2)
        data: List[TimeSeriesData],
        label: Optional[List] = None,
        dummy_label: bool = False,
    ):
        self.data = data
        self.param = param

        self.dummy_label = dummy_label
        self.label = label
        self.mode = param.mode
        self.output_size = (
            (np.max(label) + 1)
            if ((label is not None) & (self.mode == "classification"))
            else param.training_output_size
        )  # if label is provided and it's we train it in a classification
        # fashion, then output_size is determined by the max of the labels,
        # else, we train it in a regression fashion

    # TO-DO: function for padding (21Q1)
    def _reshaping(
        self,
        sequence: List[np.ndarray],
    ) -> List[np.ndarray]:
        """
        This internal function turns each array into [window_size, 1] vector
        for Pytorch. Currently only support univariate time series data.
        """
        sequence = [seq.reshape([self.window, 1]) for seq in sequence]

        logging.info("vector reshaping completed.")
        return sequence

    def transform(
        self,
    ) -> NamedTuple:

        # sanity check
        if self.mode == "classification" and not self.dummy_label:
            if self.label is None:
                msg = (
                    "Labels should be provided for training in classification fashion."
                )
                logging.error(msg)
                raise ValueError(msg)
            for label in self.label:
                if (type(label) != int) & (type(label) != np.int64):
                    msg = "Float cannot be used as label for classification training."
                    logging.error(msg)
                    raise ValueError(msg)

        # TO-DO: apply padding first (21Q1)
        ts_sample = self.data[0]
        end = len(ts_sample)
        if self.label is None and not self.dummy_label:
            end -= self.output_size  # when data is unlabeled, using last
            # element as label for training embedding
        self.window = end

        if self.param.normalizer is not None:
            seq = [
                self.param.normalizer(ts.value.values[:end]) for ts in self.data
            ]  # normalize each time series
        else:
            seq = [
                ts.value.values[:end] for ts in self.data
            ]

        if not self.dummy_label:
            label = (
                self.label
                if self.label is not None
                else [ts.value.values[end:] for ts in self.data]
            )  # retrieve the label of each time series
        elif self.dummy_label:
            label = [-1 for _ in range(len(self.data))]

        # sanity check: do we have same count for labels and time series data
        if len(label) != len(seq):
            msg = "Number of labels and time series data mismatch."
            logging.error(msg)
            raise ValueError(msg)

        T2VPreprocessed = NamedTuple(
            "T2VPreprocessed",
            [
                ("seq", List[np.ndarray]),
                ("label", List),
                ("output_size", int),
                ("window", int),
                ("batched", bool),
            ],
        )  # A named tuple for storing relevant content of processed timeseries
        # data sequences.

        seq = self._reshaping(seq)
        T2VPreprocessed.seq = seq
        T2VPreprocessed.label = label
        T2VPreprocessed.output_size = self.output_size
        T2VPreprocessed.window = self.window  # currently only supporting feeding
        # the entire time series data, segmentaion will come later.
        T2VPreprocessed.batched = False  # for downstream functions

        return T2VPreprocessed