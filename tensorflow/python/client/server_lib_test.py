# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for tf.GrpcServer."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf


class GrpcServerTest(tf.test.TestCase):

  def testRunStep(self):
    server = tf.GrpcServer.create_local_server()

    with tf.Session(server.target) as sess:
      c = tf.constant([[2, 1]])
      d = tf.constant([[1], [2]])
      e = tf.matmul(c, d)
      self.assertAllEqual([[4]], sess.run(e))
    # TODO(mrry): Add `server.stop()` and `server.join()` when these work.

  def testMultipleSessions(self):
    server = tf.GrpcServer.create_local_server()

    c = tf.constant([[2, 1]])
    d = tf.constant([[1], [2]])
    e = tf.matmul(c, d)

    sess_1 = tf.Session(server.target)
    sess_2 = tf.Session(server.target)

    self.assertAllEqual([[4]], sess_1.run(e))
    self.assertAllEqual([[4]], sess_2.run(e))

    sess_1.close()
    sess_2.close()
    # TODO(mrry): Add `server.stop()` and `server.join()` when these work.

  def testLargeConstant(self):
    server = tf.GrpcServer.create_local_server()
    with tf.Session(server.target) as sess:
      const_val = np.empty([10000, 3000], dtype=np.float32)
      const_val.fill(0.5)
      c = tf.constant(const_val)
      shape_t = tf.shape(c)
      self.assertAllEqual([10000, 3000], sess.run(shape_t))

  def testLargeFetch(self):
    server = tf.GrpcServer.create_local_server()
    with tf.Session(server.target) as sess:
      c = tf.fill([10000, 3000], 0.5)
      expected_val = np.empty([10000, 3000], dtype=np.float32)
      expected_val.fill(0.5)
      self.assertAllEqual(expected_val, sess.run(c))

  def testLargeFeed(self):
    server = tf.GrpcServer.create_local_server()
    with tf.Session(server.target) as sess:
      feed_val = np.empty([10000, 3000], dtype=np.float32)
      feed_val.fill(0.5)
      p = tf.placeholder(tf.float32, shape=[10000, 3000])
      min_t = tf.reduce_min(p)
      max_t = tf.reduce_max(p)
      min_val, max_val = sess.run([min_t, max_t], feed_dict={p: feed_val})
      self.assertEqual(0.5, min_val)
      self.assertEqual(0.5, max_val)


class ServerDefTest(tf.test.TestCase):

  def testLocalServer(self):
    cluster_def = tf.make_cluster_def({"local": ["localhost:2222"]})
    server_def = tf.ServerDef(cluster=cluster_def,
                              job_name="local", task_index=0, protocol="grpc")

    self.assertProtoEquals("""
    cluster {
      job { name: 'local' tasks { key: 0 value: 'localhost:2222' } }
    }
    job_name: 'local' task_index: 0 protocol: 'grpc'
    """, server_def)

  def testTwoProcesses(self):
    cluster_def = tf.make_cluster_def({"local": ["localhost:2222",
                                                 "localhost:2223"]})
    server_def = tf.ServerDef(cluster=cluster_def,
                              job_name="local", task_index=1, protocol="grpc")

    self.assertProtoEquals("""
    cluster {
      job { name: 'local' tasks { key: 0 value: 'localhost:2222' }
                          tasks { key: 1 value: 'localhost:2223' } }
    }
    job_name: 'local' task_index: 1 protocol: 'grpc'
    """, server_def)

  def testTwoJobs(self):
    cluster_def = tf.make_cluster_def({
        "ps": ["ps0:2222", "ps1:2222"],
        "worker": ["worker0:2222", "worker1:2222", "worker2:2222"]})
    server_def = tf.ServerDef(cluster=cluster_def,
                              job_name="worker", task_index=2, protocol="grpc")

    self.assertProtoEquals("""
    cluster {
      job { name: 'ps' tasks { key: 0 value: 'ps0:2222' }
                       tasks { key: 1 value: 'ps1:2222' } }
      job { name: 'worker' tasks { key: 0 value: 'worker0:2222' }
                           tasks { key: 1 value: 'worker1:2222' }
                           tasks { key: 2 value: 'worker2:2222' } }
    }
    job_name: 'worker' task_index: 2 protocol: 'grpc'
    """, server_def)


if __name__ == "__main__":
  tf.test.main()
