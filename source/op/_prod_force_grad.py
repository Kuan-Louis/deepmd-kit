#!/usr/bin/env python3
"""
Gradients for prod force.
"""

import os
import tensorflow as tf
from tensorflow.python.framework import ops
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import sparse_ops

module_path = os.path.dirname(os.path.realpath(__file__))
module_file = os.path.join(module_path, 'libop_grads.so')
assert (os.path.isfile(module_file)), 'module op_grads does not exist'
op_grads_module = tf.load_op_library(module_file)
     
@ops.RegisterGradient("ProdForce")
def _prod_force_grad_cc (op, grad):    
    net_grad =  op_grads_module.prod_force_grad (grad, 
                                                 op.inputs[0], 
                                                 op.inputs[1], 
                                                 op.inputs[2], 
                                                 op.inputs[3], 
                                                 op.inputs[4], 
                                                 n_a_sel = op.get_attr("n_a_sel"),
                                                 n_r_sel = op.get_attr("n_r_sel"))
    return [net_grad, None, None, None, None]
