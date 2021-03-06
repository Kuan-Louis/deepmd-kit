import dpdata,os,sys,json,unittest
import numpy as np
from deepmd.env import tf
from common import Data,gen_data

from deepmd.RunOptions import RunOptions
from deepmd.DataSystem import DataSystem
from deepmd.DescrptSeA import DescrptSeA
from deepmd.Fitting import EnerFitting
from deepmd.Model import Model
from deepmd.common import j_must_have, j_must_have_d, j_have

global_ener_float_precision = tf.float64
global_tf_float_precision = tf.float64
global_np_float_precision = np.float64

class TestModel(unittest.TestCase):
    def setUp(self) :
        gen_data()

    def test_model(self):
        jfile = 'water_se_a_fparam.json'
        with open(jfile) as fp:
            jdata = json.load (fp)
        run_opt = RunOptions(None) 
        systems = j_must_have(jdata, 'systems')
        set_pfx = j_must_have(jdata, 'set_prefix')
        batch_size = j_must_have(jdata, 'batch_size')
        test_size = j_must_have(jdata, 'numb_test')
        batch_size = 1
        test_size = 1
        stop_batch = j_must_have(jdata, 'stop_batch')
        rcut = j_must_have (jdata['model']['descriptor'], 'rcut')
        
        data = DataSystem(systems, set_pfx, batch_size, test_size, rcut, run_opt = None)
        
        test_data = data.get_test ()
        numb_test = 1
        
        descrpt = DescrptSeA(jdata['model']['descriptor'])
        fitting = EnerFitting(jdata['model']['fitting_net'], descrpt)
        model = Model(jdata['model'], descrpt, fitting)

        model._compute_dstats([test_data['coord']], [test_data['box']], [test_data['type']], [test_data['natoms_vec']], [test_data['default_mesh']])
        model.bias_atom_e = data.compute_energy_shift()

        t_prop_c           = tf.placeholder(tf.float32, [5],    name='t_prop_c')
        t_energy           = tf.placeholder(global_ener_float_precision, [None], name='t_energy')
        t_force            = tf.placeholder(global_tf_float_precision, [None], name='t_force')
        t_virial           = tf.placeholder(global_tf_float_precision, [None], name='t_virial')
        t_atom_ener        = tf.placeholder(global_tf_float_precision, [None], name='t_atom_ener')
        t_coord            = tf.placeholder(global_tf_float_precision, [None], name='i_coord')
        t_type             = tf.placeholder(tf.int32,   [None], name='i_type')
        t_natoms           = tf.placeholder(tf.int32,   [model.ntypes+2], name='i_natoms')
        t_box              = tf.placeholder(global_tf_float_precision, [None, 9], name='i_box')
        t_mesh             = tf.placeholder(tf.int32,   [None], name='i_mesh')
        t_fparam           = tf.placeholder(global_tf_float_precision, [None], name='i_fparam')
        is_training        = tf.placeholder(tf.bool)
        input_dict = {}
        input_dict['fparam'] = t_fparam

        model_pred\
            = model.build (t_coord, 
                           t_type, 
                           t_natoms, 
                           t_box, 
                           t_mesh,
                           input_dict,
                           suffix = "se_a_fparam", 
                           reuse = False)
        energy = model_pred['energy']
        force  = model_pred['force']
        virial = model_pred['virial']
        atom_ener =  model_pred['atom_ener']

        feed_dict_test = {t_prop_c:        test_data['prop_c'],
                          t_energy:        test_data['energy']              [:numb_test],
                          t_force:         np.reshape(test_data['force']    [:numb_test, :], [-1]),
                          t_virial:        np.reshape(test_data['virial']   [:numb_test, :], [-1]),
                          t_atom_ener:     np.reshape(test_data['atom_ener'][:numb_test, :], [-1]),
                          t_coord:         np.reshape(test_data['coord']    [:numb_test, :], [-1]),
                          t_box:           test_data['box']                 [:numb_test, :],
                          t_type:          np.reshape(test_data['type']     [:numb_test, :], [-1]),
                          t_natoms:        test_data['natoms_vec'],
                          t_mesh:          test_data['default_mesh'],
                          t_fparam:        np.reshape(test_data['fparam']   [:numb_test, :], [-1]),
                          is_training:     False}

        sess = tf.Session()
        sess.run(tf.global_variables_initializer())
        [e, f, v] = sess.run([energy, force, virial], 
                             feed_dict = feed_dict_test)

        e = e.reshape([-1])
        f = f.reshape([-1])
        v = v.reshape([-1])
        refe = [6.135136929183754972e+01]
        reff = [7.761477777656561328e-02,9.383013575207051205e-02,3.776776376267230399e-03,1.428268971463224069e-01,1.143858253900619654e-01,-1.318441687719179231e-02,-7.271897092708884403e-02,6.494907553857684479e-02,5.355599592111062821e-04,5.840910251709752199e-02,-1.599042555763417750e-01,-5.067165555590445389e-03,-2.546246315216804113e-01,3.073296814647456451e-02,1.505994759166155023e-02,4.849282500878367153e-02,-1.439937492508420736e-01,-1.120701494357654411e-03]
        refv = [-6.054303146013112480e-01,1.097859194719944115e-01,1.977605183964963390e-02,1.097859194719943976e-01,-3.306167096812382966e-01,-5.978855662865613894e-03,1.977605183964964083e-02,-5.978855662865616497e-03,-1.196331922996723236e-03]
        refe = np.reshape(refe, [-1])
        reff = np.reshape(reff, [-1])
        refv = np.reshape(refv, [-1])

        places = 10
        for ii in range(e.size) :
            self.assertAlmostEqual(e[ii], refe[ii], places = places)
        for ii in range(f.size) :
            self.assertAlmostEqual(f[ii], reff[ii], places = places)
        for ii in range(v.size) :
            self.assertAlmostEqual(v[ii], refv[ii], places = places)
