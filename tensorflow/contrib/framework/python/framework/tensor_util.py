# Copyright 2015 Google Inc. All Rights Reserved.
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
# ==============================================================================

"""Tensor utility functions.

@@assert_same_float_dtype
@@is_numeric_tensor
@@assert_scalar_int
@@local_variable
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from tensorflow.python.framework import dtypes
from tensorflow.python.framework import ops
from tensorflow.python.ops import variables

__all__ = [
    'assert_same_float_dtype', 'is_numeric_tensor', 'assert_scalar_int',
    'local_variable']


NUMERIC_TYPES = frozenset([dtypes.float32, dtypes.float64, dtypes.int8,
                           dtypes.int16, dtypes.int32, dtypes.int64,
                           dtypes.uint8, dtypes.qint8, dtypes.qint32,
                           dtypes.quint8, dtypes.complex64])


def is_numeric_tensor(tensor):
  return isinstance(tensor, ops.Tensor) and tensor.dtype in NUMERIC_TYPES


def _assert_same_base_type(items, expected_type=None):
  """Asserts all items are of the same base type.

  Args:
    items: List of graph items (e.g., `Variable`, `Tensor`, `SparseTensor`,
        `Operation`, or `IndexedSlices`). Can include `None` elements, which
        will be ignored.
    expected_type: Expected type. If not specified, assert all items are
        of the same base type.
  Returns:
    Validated type, or none if neither expected_type nor items provided.

  Raises:
    ValueError: If any types do not match.
  """
  original_item_str = None
  for item in items:
    if item is not None:
      item_type = item.dtype.base_dtype
      if not expected_type:
        expected_type = item_type
        original_item_str = item.name if hasattr(item, 'name') else str(item)
      elif expected_type != item_type:
        raise ValueError('%s, type=%s, must be of the same type (%s)%s.' % (
            item.name if hasattr(item, 'name') else str(item),
            item_type, expected_type,
            (' as %s' % original_item_str) if original_item_str else ''))
  return expected_type


def assert_same_float_dtype(tensors=None, dtype=None):
  """Validate and return float type based on `tensors` and `dtype`.

  For ops such as matrix multiplication, inputs and weights must be of the
  same float type. This function validates that all `tensors` are the same type,
  validates that type is `dtype` (if supplied), and returns the type. Type must
  be `dtypes.float32` or `dtypes.float64`. If neither `tensors` nor
  `dtype` is supplied, default to `dtypes.float32`.

  Args:
    tensors: Tensors of input values. Can include `None` elements, which will be
        ignored.
    dtype: Expected type.
  Returns:
    Validated type.
  Raises:
    ValueError: if neither `tensors` nor `dtype` is supplied, or result is not
        float.
  """
  if tensors:
    dtype = _assert_same_base_type(tensors, dtype)
  if not dtype:
    dtype = dtypes.float32
  elif not dtype.is_floating:
    raise ValueError('Expected float, got %s.' % dtype)
  return dtype


def assert_scalar_int(tensor):
  """Assert `tensor` is 0-D, of type `tf.int32` or `tf.int64`.

  Args:
    tensor: Tensor to test.
  Returns:
    `tensor`, for chaining.
  Raises:
    ValueError: if `tensor` is not 0-D, of type `tf.int32` or `tf.int64`.
  """
  data_type = tensor.dtype
  if data_type.base_dtype not in [dtypes.int32, dtypes.int64]:
    raise ValueError('Unexpected type %s for %s.' % (data_type, tensor.name))
  shape = tensor.get_shape()
  if shape.ndims != 0:
    raise ValueError('Unexpected shape %s for %s.' % (shape, tensor.name))
  return tensor


# TODO(ptucker): Move to tf.variables?
def local_variable(initial_value, validate_shape=True, name=None):
  """Create variable and add it to `GraphKeys.LOCAL_VARIABLES` collection.

  Args:
    initial_value: See variables.Variable.__init__.
    validate_shape: See variables.Variable.__init__.
    name: See variables.Variable.__init__.
  Returns:
    New variable.
  """
  return variables.Variable(
      initial_value, trainable=False,
      collections=[ops.GraphKeys.LOCAL_VARIABLES],
      validate_shape=validate_shape, name=name)
