#!/usr/bin/env python
import sys
import argparse
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
tf.reset_default_graph()


from .model import OpenNsfwModel, InputType
from .image_utils import create_tensorflow_image_loader, create_yahoo_image_loader

import numpy as np


IMAGE_LOADER_TENSORFLOW = "tensorflow"
IMAGE_LOADER_YAHOO = "yahoo"


def main(input_file, model_weights=r"./nsfw/data/open_nsfw-weights.npy", input_type="tensor", image_loader=IMAGE_LOADER_YAHOO):
    model = OpenNsfwModel()

    with tf.compat.v1.Session() as sess:

        input_type = InputType[input_type.upper()]
        model.build(weights_path=model_weights, input_type=input_type)

        fn_load_image = None

        if input_type == InputType.TENSOR:
            if image_loader == IMAGE_LOADER_TENSORFLOW:
                fn_load_image = create_tensorflow_image_loader(tf.Session(graph=tf.Graph()))
            else:
                fn_load_image = create_yahoo_image_loader()
        elif input_type == InputType.BASE64_JPEG:
            import base64
            fn_load_image = lambda filename: np.array([base64.urlsafe_b64encode(open(filename, "rb").read())])

        sess.run(tf.global_variables_initializer())

        image = fn_load_image(input_file)

        predictions = \
            sess.run(model.predictions,
                     feed_dict={model.input: image})

        print("Results for '{}'".format(input_file))
        print("\tSFW score:\t{}\n\tNSFW score:\t{}".format(*predictions[0]))
        predictionsDict = {}
        predictionsDict["sfw"] = predictions[0][0]
        predictionsDict["nsfw"] = predictions[0][1]
        return predictionsDict

