import numpy as np

import tensorflow as tf
import tensorflow_text
import tensorflow_hub as tfhub


tf.compat.v1.disable_eager_execution()
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


def normalize_vectors(vectors):
    vectors = np.vstack(vectors)
    norm = np.linalg.norm(vectors, ord=2, axis=-1, keepdims=True)
    return vectors / norm


class Encoder:
    def __init__(self):
        self.sess = tf.compat.v1.Session()
        self.text_placeholder = tf.compat.v1.placeholder(dtype=tf.string, shape=[None])

        self.module = tfhub.Module("/data/convert_model")
        self.context_encoding_tensor = self.module(
            self.text_placeholder, signature="encode_context"
        )
        self.encoding_tensor = self.module(self.text_placeholder)
        self.response_encoding_tensor = self.module(
            self.text_placeholder, signature="encode_response"
        )

        self.sess.run(tf.compat.v1.tables_initializer())
        self.sess.run(tf.compat.v1.global_variables_initializer())

    def encode_sentences(self, sentences):
        vectors = self.sess.run(
            self.encoding_tensor, feed_dict={self.text_placeholder: sentences}
        )
        return normalize_vectors(vectors)

    def encode_contexts(self, sentences):
        vectors = self.sess.run(
            self.context_encoding_tensor, feed_dict={self.text_placeholder: sentences}
        )
        return normalize_vectors(vectors)

    def encode_responses(self, sentences):
        vectors = self.sess.run(
            self.response_encoding_tensor, feed_dict={self.text_placeholder: sentences}
        )
        return normalize_vectors(vectors)
