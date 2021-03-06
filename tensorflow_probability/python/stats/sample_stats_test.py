# Copyright 2018 The TensorFlow Probability Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Tests for Sample Stats Ops."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Dependency imports
import numpy as np
import tensorflow as tf
import tensorflow_probability as tfp

from tensorflow.python.ops import spectral_ops_test_util

tfe = tf.contrib.eager
rng = np.random.RandomState(0)


class _AutoCorrelationTest(object):

  @property
  def use_static_shape(self):
    raise NotImplementedError('Subclass failed to implement `use_static_shape`')

  @property
  def dtype(self):
    raise NotImplementedError('Subclass failed to implement `dtype`.')

  def test_constant_sequence_axis_0_max_lags_none_center_false(self):
    x_ = np.array([[0., 0., 0.], [1., 1., 1.]]).astype(self.dtype)
    x_ph = tf.placeholder_with_default(
        input=x_, shape=x_.shape if self.use_static_shape else None)
    with spectral_ops_test_util.fft_kernel_label_map():
      # Setting normalize = True means we divide by zero.
      auto_corr = tfp.stats.auto_correlation(
          x_ph, axis=1, center=False, normalize=False)
      if self.use_static_shape:
        self.assertEqual((2, 3), auto_corr.shape)
      auto_corr_ = self.evaluate(auto_corr)
      self.assertAllClose([[0., 0., 0.], [1., 1., 1.]], auto_corr_)

  def test_constant_sequence_axis_0_max_lags_none_center_true(self):
    x_ = np.array([[0., 0., 0.], [1., 1., 1.]]).astype(self.dtype)
    x_ph = tf.placeholder_with_default(
        input=x_, shape=x_.shape if self.use_static_shape else None)
    with spectral_ops_test_util.fft_kernel_label_map():
      # Setting normalize = True means we divide by zero.
      auto_corr = tfp.stats.auto_correlation(
          x_ph, axis=1, normalize=False, center=True)
      if self.use_static_shape:
        self.assertEqual((2, 3), auto_corr.shape)
      auto_corr_ = self.evaluate(auto_corr)
      self.assertAllClose([[0., 0., 0.], [0., 0., 0.]], auto_corr_)

  def check_results_versus_brute_force(self, x, axis, max_lags, center,
                                       normalize):
    """Compute auto-correlation by brute force, then compare to tf result."""
    # Brute for auto-corr -- avoiding fft and transpositions.
    axis_len = x.shape[axis]
    if max_lags is None:
      max_lags = axis_len - 1
    else:
      max_lags = min(axis_len - 1, max_lags)
    auto_corr_at_lag = []
    if center:
      x -= x.mean(axis=axis, keepdims=True)
    for m in range(max_lags + 1):
      auto_corr_at_lag.append(
          (np.take(x, indices=range(0, axis_len - m), axis=axis) * np.conj(
              np.take(x, indices=range(m, axis_len), axis=axis))).mean(
                  axis=axis, keepdims=True))
    rxx = np.concatenate(auto_corr_at_lag, axis=axis)
    if normalize:
      rxx /= np.take(rxx, [0], axis=axis)

    x_ph = tf.placeholder_with_default(
        x, shape=x.shape if self.use_static_shape else None)
    with spectral_ops_test_util.fft_kernel_label_map():
      auto_corr = tfp.stats.auto_correlation(
          x_ph,
          axis=axis,
          max_lags=max_lags,
          center=center,
          normalize=normalize)
      if self.use_static_shape:
        output_shape = list(x.shape)
        output_shape[axis] = max_lags + 1
        self.assertAllEqual(output_shape, auto_corr.shape)
      self.assertAllClose(rxx, self.evaluate(auto_corr), rtol=1e-5, atol=1e-5)

  def test_axis_n1_center_false_max_lags_none(self):
    x = rng.randn(2, 3, 4).astype(self.dtype)
    if self.dtype in [np.complex64]:
      x = 1j * rng.randn(2, 3, 4).astype(self.dtype)
    self.check_results_versus_brute_force(
        x, axis=-1, max_lags=None, center=False, normalize=False)

  def test_axis_n2_center_false_max_lags_none(self):
    x = rng.randn(3, 4, 5).astype(self.dtype)
    if self.dtype in [np.complex64]:
      x = 1j * rng.randn(3, 4, 5).astype(self.dtype)
    self.check_results_versus_brute_force(
        x, axis=-2, max_lags=None, center=False, normalize=False)

  def test_axis_n1_center_false_max_lags_none_normalize_true(self):
    x = rng.randn(2, 3, 4).astype(self.dtype)
    if self.dtype in [np.complex64]:
      x = 1j * rng.randn(2, 3, 4).astype(self.dtype)
    self.check_results_versus_brute_force(
        x, axis=-1, max_lags=None, center=False, normalize=True)

  def test_axis_n2_center_false_max_lags_none_normalize_true(self):
    x = rng.randn(3, 4, 5).astype(self.dtype)
    if self.dtype in [np.complex64]:
      x = 1j * rng.randn(3, 4, 5).astype(self.dtype)
    self.check_results_versus_brute_force(
        x, axis=-2, max_lags=None, center=False, normalize=True)

  def test_axis_0_center_true_max_lags_none(self):
    x = rng.randn(3, 4, 5).astype(self.dtype)
    if self.dtype in [np.complex64]:
      x = 1j * rng.randn(3, 4, 5).astype(self.dtype)
    self.check_results_versus_brute_force(
        x, axis=0, max_lags=None, center=True, normalize=False)

  def test_axis_2_center_true_max_lags_1(self):
    x = rng.randn(3, 4, 5).astype(self.dtype)
    if self.dtype in [np.complex64]:
      x = 1j * rng.randn(3, 4, 5).astype(self.dtype)
    self.check_results_versus_brute_force(
        x, axis=2, max_lags=1, center=True, normalize=False)

  def test_axis_2_center_true_max_lags_100(self):
    # There are less than 100 elements in axis 2, so expect we get back an array
    # the same size as x, despite having asked for 100 lags.
    x = rng.randn(3, 4, 5).astype(self.dtype)
    if self.dtype in [np.complex64]:
      x = 1j * rng.randn(3, 4, 5).astype(self.dtype)
    self.check_results_versus_brute_force(
        x, axis=2, max_lags=100, center=True, normalize=False)

  def test_long_orthonormal_sequence_has_corr_length_0(self):
    l = 10000
    x = rng.randn(l).astype(self.dtype)
    x_ph = tf.placeholder_with_default(
        x, shape=(l,) if self.use_static_shape else None)
    with spectral_ops_test_util.fft_kernel_label_map():
      rxx = tfp.stats.auto_correlation(
          x_ph, max_lags=l // 2, center=True, normalize=False)
      if self.use_static_shape:
        self.assertAllEqual((l // 2 + 1,), rxx.shape)
      rxx_ = self.evaluate(rxx)
      # OSS CPU FFT has some accuracy issues is not the most accurate.
      # So this tolerance is a bit bad.
      self.assertAllClose(1., rxx_[0], rtol=0.05)
      # The maximal error in the rest of the sequence is not great.
      self.assertAllClose(np.zeros(l // 2), rxx_[1:], atol=0.1)
      # The mean error in the rest is ok, actually 0.008 when I tested it.
      self.assertLess(np.abs(rxx_[1:]).mean(), 0.02)

  def test_step_function_sequence(self):
    # x jumps to new random value every 10 steps.  So correlation length = 10.
    x = (rng.randint(-10, 10, size=(1000, 1)) * np.ones(
        (1, 10))).ravel().astype(self.dtype)
    x_ph = tf.placeholder_with_default(
        x, shape=(1000 * 10,) if self.use_static_shape else None)
    with spectral_ops_test_util.fft_kernel_label_map():
      rxx = tfp.stats.auto_correlation(
          x_ph, max_lags=1000 * 10 // 2, center=True, normalize=False)
      if self.use_static_shape:
        self.assertAllEqual((1000 * 10 // 2 + 1,), rxx.shape)
      rxx_ = self.evaluate(rxx)
      rxx_ /= rxx_[0]
      # Expect positive correlation for the first 10 lags, then significantly
      # smaller negative.
      self.assertGreater(rxx_[:10].min(), 0)
      self.assertGreater(rxx_[9], 5 * rxx_[10:20].mean())
      # RXX should be decreasing for the first 10 lags.
      diff = np.diff(rxx_)
      self.assertLess(diff[:10].max(), 0)

  def test_normalization(self):
    l = 10000
    x = 3 * rng.randn(l).astype(self.dtype)
    x_ph = tf.placeholder_with_default(
        x, shape=(l,) if self.use_static_shape else None)
    with spectral_ops_test_util.fft_kernel_label_map():
      rxx = tfp.stats.auto_correlation(
          x_ph, max_lags=l // 2, center=True, normalize=True)
      if self.use_static_shape:
        self.assertAllEqual((l // 2 + 1,), rxx.shape)
      rxx_ = self.evaluate(rxx)
      # Note that RXX[0] = 1, despite the fact that E[X^2] = 9, and this is
      # due to normalize=True.
      # OSS CPU FFT has some accuracy issues is not the most accurate.
      # So this tolerance is a bit bad.
      self.assertAllClose(1., rxx_[0], rtol=0.05)
      # The maximal error in the rest of the sequence is not great.
      self.assertAllClose(np.zeros(l // 2), rxx_[1:], atol=0.1)
      # The mean error in the rest is ok, actually 0.008 when I tested it.
      self.assertLess(np.abs(rxx_[1:]).mean(), 0.02)


@tfe.run_all_tests_in_graph_and_eager_modes
class AutoCorrelationTestStaticShapeFloat32(tf.test.TestCase,
                                            _AutoCorrelationTest):

  @property
  def dtype(self):
    return np.float32

  @property
  def use_static_shape(self):
    return True


@tfe.run_all_tests_in_graph_and_eager_modes
class AutoCorrelationTestStaticShapeComplex64(tf.test.TestCase,
                                              _AutoCorrelationTest):

  @property
  def dtype(self):
    return np.complex64

  @property
  def use_static_shape(self):
    return True


@tfe.run_all_tests_in_graph_and_eager_modes
class AutoCorrelationTestDynamicShapeFloat32(tf.test.TestCase,
                                             _AutoCorrelationTest):

  @property
  def dtype(self):
    return np.float32

  @property
  def use_static_shape(self):
    return False


@tfe.run_all_tests_in_graph_and_eager_modes
class PercentileTestWithLowerInterpolation(tf.test.TestCase):

  _interpolation = 'lower'

  def test_one_dim_odd_input(self):
    x = [1., 5., 3., 2., 4.]
    for q in [0, 10, 25, 49.9, 50, 50.01, 90, 95, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation, axis=0)
      pct = tfp.stats.percentile(
          x, q=q, interpolation=self._interpolation, axis=[0])
      self.assertAllEqual((), pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_one_dim_odd_input_vector_q(self):
    x = [1., 5., 3., 2., 4.]
    q = np.array([0, 10, 25, 49.9, 50, 50.01, 90, 95, 100])
    expected_percentile = np.percentile(
        x, q=q, interpolation=self._interpolation, axis=0)
    pct = tfp.stats.percentile(
        x, q=q, interpolation=self._interpolation, axis=[0])
    self.assertAllEqual(q.shape, pct.shape)
    self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_one_dim_even_input(self):
    x = [1., 5., 3., 2., 4., 5.]
    for q in [0, 10, 25, 49.9, 50, 50.01, 90, 95, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation)
      pct = tfp.stats.percentile(x, q=q, interpolation=self._interpolation)
      self.assertAllEqual((), pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_two_dim_odd_input_axis_0(self):
    x = np.array([[-1., 50., -3.5, 2., -1], [0., 0., 3., 2., 4.]]).T
    for q in [0, 10, 25, 49.9, 50, 50.01, 90, 95, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation, axis=0)
      # Get dim 1 with negative and positive indices.
      pct_neg_index = tfp.stats.percentile(
          x, q=q, interpolation=self._interpolation, axis=[0])
      pct_pos_index = tfp.stats.percentile(
          x, q=q, interpolation=self._interpolation, axis=[0])
      self.assertAllEqual((2,), pct_neg_index.shape)
      self.assertAllEqual((2,), pct_pos_index.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct_neg_index))
      self.assertAllClose(expected_percentile, self.evaluate(pct_pos_index))

  def test_two_dim_even_axis_0(self):
    x = np.array([[1., 2., 4., 50.], [1., 2., -4., 5.]]).T
    for q in [0, 10, 25, 49.9, 50, 50.01, 90, 95, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation, axis=0)
      pct = tfp.stats.percentile(
          x, q=q, interpolation=self._interpolation, axis=[0])
      self.assertAllEqual((2,), pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_two_dim_even_input_and_keep_dims_true(self):
    x = np.array([[1., 2., 4., 50.], [1., 2., -4., 5.]]).T
    for q in [0, 10, 25, 49.9, 50, 50.01, 90, 95, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation, keepdims=True, axis=0)
      pct = tfp.stats.percentile(
          x, q=q, interpolation=self._interpolation, keep_dims=True, axis=[0])
      self.assertAllEqual((1, 2), pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_four_dimensional_input(self):
    x = rng.rand(2, 3, 4, 5)
    for axis in [None, 0, 1, -2, (0,), (-1,), (-1, 1), (3, 1), (-3, 0)]:
      expected_percentile = np.percentile(
          x, q=0.77, interpolation=self._interpolation, axis=axis)
      pct = tfp.stats.percentile(
          x, q=0.77, interpolation=self._interpolation, axis=axis)
      self.assertAllEqual(expected_percentile.shape, pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_four_dimensional_input_q_vector(self):
    x = rng.rand(3, 4, 5, 6)
    q = [0.25, 0.75]
    for axis in [None, 0, (-1, 1)]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation, axis=axis)
      pct = tfp.stats.percentile(
          x, q=q, interpolation=self._interpolation, axis=axis)
      self.assertAllEqual(expected_percentile.shape, pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_four_dimensional_input_q_vector_and_keepdims(self):
    x = rng.rand(3, 4, 5, 6)
    q = [0.25, 0.75]
    for axis in [None, 0, (-1, 1)]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation, axis=axis, keepdims=True)
      pct = tfp.stats.percentile(
          x, q=q, interpolation=self._interpolation, axis=axis, keep_dims=True)
      self.assertAllEqual(expected_percentile.shape, pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_four_dimensional_input_and_keepdims(self):
    x = rng.rand(2, 3, 4, 5)
    for axis in [None, 0, 1, -2, (0,), (-1,), (-1, 1), (3, 1), (-3, 0)]:
      expected_percentile = np.percentile(
          x,
          q=0.77,
          interpolation=self._interpolation,
          axis=axis,
          keepdims=True)
      pct = tfp.stats.percentile(
          x,
          q=0.77,
          interpolation=self._interpolation,
          axis=axis,
          keep_dims=True)
      self.assertAllEqual(expected_percentile.shape, pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_four_dimensional_input_x_static_ndims_but_dynamic_sizes(self):
    x = rng.rand(2, 3, 4, 5)
    x_ph = tf.placeholder_with_default(input=x, shape=[None, None, None, None])
    for axis in [None, 0, 1, -2, (0,), (-1,), (-1, 1), (3, 1), (-3, 0)]:
      expected_percentile = np.percentile(
          x, q=0.77, interpolation=self._interpolation, axis=axis)
      pct = tfp.stats.percentile(
          x_ph, q=0.77, interpolation=self._interpolation, axis=axis)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_four_dimensional_input_and_keepdims_x_static_ndims_dynamic_sz(self):
    x = rng.rand(2, 3, 4, 5)
    x_ph = tf.placeholder_with_default(input=x, shape=[None, None, None, None])
    for axis in [None, 0, 1, -2, (0,), (-1,), (-1, 1), (3, 1), (-3, 0)]:
      expected_percentile = np.percentile(
          x,
          q=0.77,
          interpolation=self._interpolation,
          axis=axis,
          keepdims=True)
      pct = tfp.stats.percentile(
          x_ph,
          q=0.77,
          interpolation=self._interpolation,
          axis=axis,
          keep_dims=True)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_with_integer_dtype(self):
    x = [1, 5, 3, 2, 4]
    for q in [0, 10, 25, 49.9, 50, 50.01, 90, 95, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation)
      pct = tfp.stats.percentile(x, q=q, interpolation=self._interpolation)
      self.assertEqual(tf.int32, pct.dtype)
      self.assertAllEqual((), pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))


class PercentileTestWithHigherInterpolation(
    PercentileTestWithLowerInterpolation):

  _interpolation = 'higher'


class PercentileTestWithNearestInterpolation(tf.test.TestCase):
  """Test separately because np.round and tf.round make different choices."""

  _interpolation = 'nearest'

  def test_one_dim_odd_input(self):
    x = [1., 5., 3., 2., 4.]
    for q in [0, 10.1, 25.1, 49.9, 50.1, 50.01, 89, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation)
      pct = tfp.stats.percentile(x, q=q, interpolation=self._interpolation)
      self.assertAllEqual((), pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_one_dim_even_input(self):
    x = [1., 5., 3., 2., 4., 5.]
    for q in [0, 10.1, 25.1, 49.9, 50.1, 50.01, 89, 100]:
      expected_percentile = np.percentile(
          x, q=q, interpolation=self._interpolation)
      pct = tfp.stats.percentile(x, q=q, interpolation=self._interpolation)
      self.assertAllEqual((), pct.shape)
      self.assertAllClose(expected_percentile, self.evaluate(pct))

  def test_invalid_interpolation_raises(self):
    x = [1., 5., 3., 2., 4.]
    with self.assertRaisesRegexp(ValueError, 'interpolation'):
      tfp.stats.percentile(x, q=0.5, interpolation='bad')

  def test_2d_q_raises_static(self):
    x = [1., 5., 3., 2., 4.]
    with self.assertRaisesRegexp(ValueError, 'Expected.*ndims'):
      tfp.stats.percentile(x, q=[[0.5]])

  def test_2d_q_raises_dynamic(self):
    x = [1., 5., 3., 2., 4.]
    q_ph = tf.placeholder_with_default(input=[[0.5]], shape=None)
    pct = tfp.stats.percentile(x, q=q_ph, validate_args=True)
    with self.assertRaisesOpError('rank'):
      self.evaluate(pct)

  def test_finds_max_of_long_array(self):
    # d - 1 == d in float32 and d = 3e7.
    # So this test only passes if we use double for the percentile indices.
    # If float is used, it fails with InvalidArgumentError about an index out of
    # bounds.
    x = tf.linspace(0., 3e7, num=int(3e7))
    minval = tfp.stats.percentile(x, q=0, validate_args=True)
    self.assertAllEqual(0, self.evaluate(minval))


@tfe.run_all_tests_in_graph_and_eager_modes
class CovarianceTest(tf.test.TestCase):

  def _np_cov_1d(self, x, y):
    return ((x - x.mean(axis=0)) * (y - y.mean(axis=0))).mean(axis=0)

  def test_batch_scalar(self):
    # X and Y are correlated, albeit less so in the first component.
    # They both are 100 samples of 3-batch scalars.
    x = rng.randn(100, 3)
    y = x + 0.1 * rng.randn(100, 3)
    x[:, 0] += 0.1 * rng.randn(100)

    cov = tfp.stats.covariance(x, y, sample_axis=0, event_axis=None)
    self.assertAllEqual((3,), cov.shape)
    cov = self.evaluate(cov)

    for i in range(3):  # Iterate over batch index.
      self.assertAllClose(self._np_cov_1d(x[:, i], y[:, i]), cov[i])

  def test_batch_vector_sampaxis0_eventaxisn1(self):
    # X and Y are correlated, albeit less so in the first component.
    # They both are both 100 samples of 3-batch vectors in R^2.
    x = rng.randn(100, 3, 2)
    y = x + 0.1 * rng.randn(100, 3, 2)
    x[:, :, 0] += 0.1 * rng.randn(100, 3)

    cov = tfp.stats.covariance(x, y, event_axis=-1)
    self.assertAllEqual((3, 2, 2), cov.shape)
    cov = self.evaluate(cov)

    cov_kd = tfp.stats.covariance(x, y, event_axis=-1, keepdims=True)
    self.assertAllEqual((1, 3, 2, 2), cov_kd.shape)
    cov_kd = self.evaluate(cov_kd)
    self.assertAllEqual(cov, cov_kd[0, ...])

    for i in range(3):  # Iterate over batch index.
      x_i = x[:, i, :]  # Pick out ith batch of samples.
      y_i = y[:, i, :]
      cov_i = cov[i, :, :]
      for m in range(2):  # Iterate over row of matrix
        for n in range(2):  # Iterate over column of matrix
          self.assertAllClose(
              self._np_cov_1d(x_i[:, m], y_i[:, n]), cov_i[m, n])

  def test_batch_vector_sampaxis13_eventaxis2(self):
    # x.shape = batch, sample, event, sample
    x = rng.randn(4, 10, 2, 10)
    y = x + 0.1 * rng.randn(10, 2, 10)
    x[:, :, 0, :] += 0.1 * rng.randn(4, 10, 10)

    cov = tfp.stats.covariance(x, y, sample_axis=[1, 3], event_axis=[2])
    self.assertAllEqual((4, 2, 2), cov.shape)
    cov = self.evaluate(cov)

    cov_kd = tfp.stats.covariance(
        x, y, sample_axis=[1, 3], event_axis=[2], keepdims=True)
    self.assertAllEqual((4, 1, 2, 2, 1), cov_kd.shape)
    cov_kd = self.evaluate(cov_kd)
    self.assertAllEqual(cov, cov_kd[:, 0, :, :, 0])

    for i in range(4):  # Iterate over batch index.
      # Get ith batch of samples, and permute/reshape to [n_samples, n_events]
      x_i = np.reshape(np.transpose(x[i, :, :, :], [0, 2, 1]), [10 * 10, 2])
      y_i = np.reshape(np.transpose(y[i, :, :, :], [0, 2, 1]), [10 * 10, 2])
      # Will compare with ith batch of covariance.
      cov_i = cov[i, :, :]
      for m in range(2):  # Iterate over row of matrix
        for n in range(2):  # Iterate over column of matrix
          self.assertAllClose(
              self._np_cov_1d(x_i[:, m], y_i[:, n]), cov_i[m, n])

  def test_batch_vector_sampaxis02_eventaxis1(self):
    # x.shape = sample, event, sample, batch
    x = rng.randn(2, 3, 4, 5)
    y = x + 0.1 * rng.randn(2, 3, 4, 5)

    cov = tfp.stats.covariance(x, y, sample_axis=[0, 2], event_axis=[1])
    self.assertAllEqual((3, 3, 5), cov.shape)
    cov = self.evaluate(cov)

    cov_kd = tfp.stats.covariance(
        x, y, sample_axis=[0, 2], event_axis=[1], keepdims=True)
    self.assertAllEqual((1, 3, 3, 1, 5), cov_kd.shape)
    cov_kd = self.evaluate(cov_kd)
    self.assertAllEqual(cov, cov_kd[0, :, :, 0, :])

    for i in range(5):  # Iterate over batch index.
      # Get ith batch of samples, and permute/reshape to [n_samples, n_events]
      x_i = np.reshape(np.transpose(x[:, :, :, i], [0, 2, 1]), [2 * 4, 3])
      y_i = np.reshape(np.transpose(y[:, :, :, i], [0, 2, 1]), [2 * 4, 3])
      # Will compare with ith batch of covariance.
      cov_i = cov[:, :, i]
      for m in range(3):  # Iterate over row of matrix
        for n in range(3):  # Iterate over column of matrix
          self.assertAllClose(
              self._np_cov_1d(x_i[:, m], y_i[:, n]), cov_i[m, n])

  def test_batch_vector_sampaxis03_eventaxis12_dynamic(self):
    # x.shape = sample, event, event, sample, batch
    x = rng.randn(2, 3, 4, 5, 6)
    y = x + 0.1 * rng.randn(2, 3, 4, 5, 6)

    x_ph = tf.placeholder_with_default(input=x, shape=None)
    y_ph = tf.placeholder_with_default(input=y, shape=None)

    cov = tfp.stats.covariance(
        x_ph, y_ph, sample_axis=[0, 3], event_axis=[1, 2])
    cov = self.evaluate(cov)
    self.assertAllEqual((3, 4, 3, 4, 6), cov.shape)

    cov_kd = tfp.stats.covariance(
        x_ph, y_ph, sample_axis=[0, 3], event_axis=[1, 2], keepdims=True)
    cov_kd = self.evaluate(cov_kd)
    self.assertAllEqual((1, 3, 4, 3, 4, 1, 6), cov_kd.shape)
    self.assertAllEqual(cov, cov_kd[0, :, :, :, :, 0, :])

    for i in range(6):  # Iterate over batch index.
      # Get ith batch of samples, and permute/reshape to [n_samples, n_events]
      x_i = np.reshape(
          np.transpose(x[:, :, :, :, i], [0, 3, 1, 2]), [2 * 5, 3 * 4])
      y_i = np.reshape(
          np.transpose(y[:, :, :, :, i], [0, 3, 1, 2]), [2 * 5, 3 * 4])
      # Will compare with ith batch of covariance.
      cov_i = np.reshape(cov[..., i], [3 * 4, 3 * 4])
      for m in range(0, 3 * 4, 3):  # Iterate over some rows of matrix
        for n in range(0, 3 * 4, 3):  # Iterate over some columns of matrix
          self.assertAllClose(
              self._np_cov_1d(x_i[:, m], y_i[:, n]), cov_i[m, n])

  def test_non_contiguous_event_axis_raises(self):
    # They both are both 100 samples of 3-batch vectors in R^2.
    x = rng.randn(100, 3, 2)
    y = x + 0.1 * rng.randn(100, 3, 2)

    with self.assertRaisesRegexp(ValueError, 'must be contiguous'):
      tfp.stats.covariance(x, y, sample_axis=1, event_axis=[0, 2])

  def test_overlapping_axis_raises(self):
    # They both are both 100 samples of 3-batch vectors in R^2.
    x = rng.randn(100, 3, 2)
    y = x + 0.1 * rng.randn(100, 3, 2)

    with self.assertRaisesRegexp(ValueError, 'overlapped'):
      tfp.stats.covariance(x, y, sample_axis=[0, 1], event_axis=[1, 2])

  def test_batch_vector_shape_dtype_ok(self):
    # Test addresses a particular bug.
    x = tf.ones((5, 2))
    # This next line failed, due to concatenating [float32, int32, int32]
    # traceback went to tf.concat((batch_axis, event_axis, sample_axis), 0)
    # Test passes when this does not fail.
    tfp.stats.covariance(x)


@tfe.run_all_tests_in_graph_and_eager_modes
class CorrelationTest(tf.test.TestCase):

  def _np_corr_1d(self, x, y):
    assert x.ndim == y.ndim == 1
    x = x - x.mean()
    y = y - y.mean()
    sigma_x = np.sqrt((x**2).mean())
    sigma_y = np.sqrt((y**2).mean())
    return (x * y).mean() / (sigma_x * sigma_y)

  def test_batch_scalar(self):
    # X and Y are correlated, albeit less so in the first component.
    # They both are 100 samples of 3-batch scalars.
    x = rng.randn(100, 3)
    y = x + 0.1 * rng.randn(100, 3)
    x[:, 0] += 0.1 * rng.randn(100)

    corr = tfp.stats.correlation(x, y, sample_axis=0, event_axis=None)
    self.assertAllEqual((3,), corr.shape)
    corr = self.evaluate(corr)

    for i in range(3):  # Iterate over batch index.
      self.assertAllClose(self._np_corr_1d(x[:, i], y[:, i]), corr[i])

  def test_diagonal_of_correlation_matrix_x_with_x_is_one(self):
    # Some big numbers, to test stability.
    x = np.float32(1e10 * rng.randn(100, 3))

    corr = tfp.stats.correlation(x, sample_axis=0, event_axis=1)
    self.assertAllEqual((3, 3), corr.shape)
    corr = self.evaluate(corr)
    self.assertAllClose([1., 1., 1.], np.diag(corr))

  def test_batch_vector_sampaxis0_eventaxisn1(self):
    # X and Y are correlated, albeit less so in the first component.
    # They both are both 100 samples of 3-batch vectors in R^2.
    x = rng.randn(100, 3, 2)
    y = x + 0.1 * rng.randn(100, 3, 2)
    x[:, :, 0] += 0.1 * rng.randn(100, 3)

    corr = tfp.stats.correlation(x, y, event_axis=-1)
    self.assertAllEqual((3, 2, 2), corr.shape)
    corr = self.evaluate(corr)

    corr_kd = tfp.stats.correlation(x, y, event_axis=-1, keepdims=True)
    self.assertAllEqual((1, 3, 2, 2), corr_kd.shape)
    corr_kd = self.evaluate(corr_kd)
    self.assertAllEqual(corr, corr_kd[0, ...])

    for i in range(3):  # Iterate over batch index.
      x_i = x[:, i, :]  # Pick out ith batch of samples.
      y_i = y[:, i, :]
      corr_i = corr[i, :, :]
      for m in range(2):  # Iterate over row of matrix
        for n in range(2):  # Iterate over column of matrix
          self.assertAllClose(
              self._np_corr_1d(x_i[:, m], y_i[:, n]), corr_i[m, n])


@tfe.run_all_tests_in_graph_and_eager_modes
class CholeskyCovarianceTest(tf.test.TestCase):

  def test_batch_vector_sampaxis1_eventaxis2(self):
    # x.shape = [2, 5000, 2],
    # 2-batch members, 5000 samples each, events in R^2.
    x0 = rng.randn(5000, 2)
    x1 = 2 * rng.randn(5000, 2)
    x = np.stack((x0, x1), axis=0)

    # chol.shape = [2 (batch), 2x2 (event x event)]
    chol = tfp.stats.cholesky_covariance(x, sample_axis=1)
    chol_kd = tfp.stats.cholesky_covariance(x, sample_axis=1, keepdims=True)

    # Make sure static shape of keepdims works
    self.assertAllEqual((2, 2, 2), chol.shape)
    self.assertAllEqual((2, 1, 2, 2), chol_kd.shape)

    chol, chol_kd = self.evaluate([chol, chol_kd])

    # keepdims should not change the numbers in the result.
    self.assertAllEqual(chol, np.squeeze(chol_kd, axis=1))

    # Covariance is trivial since these are independent normals.
    # Tolerance chosen to be 2x the lowest passing atol.
    self.assertAllClose(np.eye(2), chol[0, ...], atol=0.06)
    self.assertAllClose(2 * np.eye(2), chol[1, ...], atol=0.06)


@tfe.run_all_tests_in_graph_and_eager_modes
class VarianceTest(tf.test.TestCase):
  """Light test:  Most methods tested implicitly by CovarianceTest."""

  def test_independent_uniform_samples(self):
    x = rng.rand(10, 10, 10)

    var = tfp.stats.variance(x, sample_axis=None)
    self.assertAllEqual((), var.shape)

    var_kd = tfp.stats.variance(x, sample_axis=None, keepdims=True)
    self.assertAllEqual((1, 1, 1), var_kd.shape)

    var, var_kd = self.evaluate([var, var_kd])

    self.assertAllEqual(var, var_kd.reshape(()))

    self.assertAllClose(np.var(x), var)


@tfe.run_all_tests_in_graph_and_eager_modes
class StddevTest(tf.test.TestCase):
  """Light test:  Most methods tested implicitly by VarianceTest."""

  def test_independent_uniform_samples(self):
    x = rng.rand(10, 10, 10)

    stddev = tfp.stats.stddev(x, sample_axis=[1, -1])
    self.assertAllEqual((10,), stddev.shape)

    stddev_kd = tfp.stats.stddev(x, sample_axis=[1, -1], keepdims=True)
    self.assertAllEqual((10, 1, 1), stddev_kd.shape)

    stddev, stddev_kd = self.evaluate([stddev, stddev_kd])

    self.assertAllEqual(stddev, stddev_kd.reshape((10,)))

    self.assertAllClose(np.std(x, axis=(1, -1)), stddev)


if __name__ == '__main__':
  tf.test.main()
