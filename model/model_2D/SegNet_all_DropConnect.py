import tensorflow as tf
from config import args

if args.read_tfrecord:
    from model.model_2D.base_model_tfrecord import BaseModel
else:
    from model.model_2D.base_model import BaseModel
from model.model_2D.ops_segnet import initialization, variable_with_weight_decay, up_sampling, max_pool, \
    conv_layer_dropconnect
import numpy as np


class SegNet(BaseModel):
    def __init__(self, sess, conf):

        super(SegNet, self).__init__(sess, conf)
        self.k_size = self.conf.filter_size
        self.use_vgg = True
        self.vgg16_npy_path = 'vgg16.npy'
        self.vgg_param_dict = np.load(self.vgg16_npy_path, encoding='latin1').item()
        self.batch_size_pl = self.conf.batch_size
        self.build_network()
        self.configure_network()

    def build_network(self):
        # Building network...
        self.norm1 = tf.nn.lrn(self.inputs_pl, depth_radius=5, bias=1.0, alpha=0.0001, beta=0.75, name='norm1')
        # first box of convolution layer,each part we do convolution two times, so we have conv1_1, and conv1_2
        self.conv1_1 = conv_layer_dropconnect(self.norm1, "conv1_1", [3, 3, 3, 64], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv1_2 = conv_layer_dropconnect(self.conv1_1, "conv1_2", [3, 3, 64, 64], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.pool1, self.pool1_index, self.shape_1 = max_pool(self.conv1_2, 'pool1')

        # Second box of convolution layer(4)
        self.conv2_1 = conv_layer_dropconnect(self.pool1, "conv2_1", [3, 3, 64, 128], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv2_2 = conv_layer_dropconnect(self.conv2_1, "conv2_2", [3, 3, 128, 128], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.pool2, self.pool2_index, self.shape_2 = max_pool(self.conv2_2, 'pool2')

        # Third box of convolution layer(7)
        self.conv3_1 = conv_layer_dropconnect(self.pool2, "conv3_1", [3, 3, 128, 256], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv3_2 = conv_layer_dropconnect(self.conv3_1, "conv3_2", [3, 3, 256, 256], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv3_3 = conv_layer_dropconnect(self.conv3_2, "conv3_3", [3, 3, 256, 256], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.pool3, self.pool3_index, self.shape_3 = max_pool(self.conv3_3, 'pool3')

        # Fourth box of convolution layer(10)

        self.conv4_1 = conv_layer_dropconnect(self.pool3, "conv4_1", [3, 3, 256, 512], self.is_training_pl,
                                  self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv4_2 = conv_layer_dropconnect(self.conv4_1, "conv4_2", [3, 3, 512, 512], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv4_3 = conv_layer_dropconnect(self.conv4_2, "conv4_3", [3, 3, 512, 512], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.pool4, self.pool4_index, self.shape_4 = max_pool(self.conv4_3, 'pool4')

        # Fifth box of convolution layers(13)

        self.conv5_1 = conv_layer_dropconnect(self.pool4, "conv5_1", [3, 3, 512, 512], self.is_training_pl,
                                  self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv5_2 = conv_layer_dropconnect(self.conv5_1, "conv5_2", [3, 3, 512, 512], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.conv5_3 = conv_layer_dropconnect(self.conv5_2, "conv5_3", [3, 3, 512, 512], self.is_training_pl, self.use_vgg,
                                  self.vgg_param_dict, keep_prob=self.keep_prob_pl)
        self.pool5, self.pool5_index, self.shape_5 = max_pool(self.conv5_3, 'pool5')

        # ------------So Now the encoder process has been Finished-----------------------------------#
        # ------------------Then Let's start Decoder Process----------------------------------------------#
        # First box of deconvolution layers(3)

        self.deconv5_1 = up_sampling(self.pool5, self.pool5_index, self.shape_5, self.batch_size_pl,
                                     name="unpool_5")
        self.deconv5_2 = conv_layer_dropconnect(self.deconv5_1, "deconv5_2", [3, 3, 512, 512], self.is_training_pl,
                                                keep_prob=self.keep_prob_pl)
        self.deconv5_3 = conv_layer_dropconnect(self.deconv5_2, "deconv5_3", [3, 3, 512, 512], self.is_training_pl, keep_prob=self.keep_prob_pl)
        self.deconv5_4 = conv_layer_dropconnect(self.deconv5_3, "deconv5_4", [3, 3, 512, 512], self.is_training_pl, keep_prob=self.keep_prob_pl)
        # Second box of deconvolution layers(6)

        self.deconv4_1 = up_sampling(self.deconv5_4, self.pool4_index, self.shape_4, self.batch_size_pl,
                                     name="unpool_4")
        self.deconv4_2 = conv_layer_dropconnect(self.deconv4_1, "deconv4_2", [3, 3, 512, 512], self.is_training_pl,
                                                keep_prob=self.keep_prob_pl)
        self.deconv4_3 = conv_layer_dropconnect(self.deconv4_2, "deconv4_3", [3, 3, 512, 512], self.is_training_pl, keep_prob=self.keep_prob_pl)
        self.deconv4_4 = conv_layer_dropconnect(self.deconv4_3, "deconv4_4", [3, 3, 512, 256], self.is_training_pl, keep_prob=self.keep_prob_pl)
        # Third box of deconvolution layers(9)

        self.deconv3_1 = up_sampling(self.deconv4_4, self.pool3_index, self.shape_3, self.batch_size_pl,
                                     name="unpool_3")
        self.deconv3_2 = conv_layer_dropconnect(self.deconv3_1, "deconv3_2", [3, 3, 256, 256], self.is_training_pl,
                                                keep_prob=self.keep_prob_pl)
        self.deconv3_3 = conv_layer_dropconnect(self.deconv3_2, "deconv3_3", [3, 3, 256, 256], self.is_training_pl, keep_prob=self.keep_prob_pl)
        self.deconv3_4 = conv_layer_dropconnect(self.deconv3_3, "deconv3_4", [3, 3, 256, 128], self.is_training_pl, keep_prob=self.keep_prob_pl)
        # Fourth box of deconvolution layers(11)

        self.deconv2_1 = up_sampling(self.deconv3_4, self.pool2_index, self.shape_2, self.batch_size_pl,
                                     name="unpool_2")
        self.deconv2_2 = conv_layer_dropconnect(self.deconv2_1, "deconv2_2", [3, 3, 128, 128], self.is_training_pl,
                                                keep_prob=self.keep_prob_pl)
        self.deconv2_3 = conv_layer_dropconnect(self.deconv2_2, "deconv2_3", [3, 3, 128, 64], self.is_training_pl, keep_prob=self.keep_prob_pl)
        # Fifth box of deconvolution layers(13)
        self.deconv1_1 = up_sampling(self.deconv2_3, self.pool1_index, self.shape_1, self.batch_size_pl,
                                     name="unpool_1")
        self.deconv1_2 = conv_layer_dropconnect(self.deconv1_1, "deconv1_2", [3, 3, 64, 64], self.is_training_pl, keep_prob=self.keep_prob_pl)
        self.deconv1_3 = conv_layer_dropconnect(self.deconv1_2, "deconv1_3", [3, 3, 64, 64], self.is_training_pl, keep_prob=self.keep_prob_pl)

        with tf.variable_scope('conv_classifier') as scope:
            self.kernel = variable_with_weight_decay('weights', initializer=initialization(1, 64),
                                                     shape=[1, 1, 64, self.conf.num_cls], wd=False)
            self.conv = tf.nn.conv2d(self.deconv1_3, self.kernel, [1, 1, 1, 1], padding='SAME')
            self.biases = variable_with_weight_decay('biases', tf.constant_initializer(0.0),
                                                     shape=[self.conf.num_cls], wd=False)
            self.logits = tf.nn.bias_add(self.conv, self.biases, name=scope.name)
