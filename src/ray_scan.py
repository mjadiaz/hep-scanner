from omegaconf import OmegaConf, DictConfig

import numpy as np
import random
import string

from src.models import MODELS 
from src.likelihoods import LIKELIHOODS 
import pandas as pd
import rich
import ray


SCANNER_DEFAULT_CONFIG = OmegaConf.create({
    'hep_stack_name': 'SPhenoHbHs',
    'scanner': {
        'max_samples': 10,
        'n_workers': 2,
        },
    'worker': {
        'send_samples_freq': 2,
        },
    'logger': {
        'type': 'Wandb',
        'update_freq': 2
        }
    })

HEP_DEFAULT_CONFIG = OmegaConf.create(
    """
    model:
        name: 'BLSSM'
        neutral_higgs: 6
        charged_higgs: 1
        parameters:
            name:      ['m0', 'm12',   'a0', 'tanbeta']
            low_lim:   [100.,  1000., 1000.,        1.]
            high_lim:  [1000., 4500., 4000.,       60.]
            lhs:
                index: [1,        2,      5,         3]
                block: ['MINPAR', 'MINPAR', 'MINPAR', 'MINPAR']
        observation:
            name:      ['Mh(1)', 'Mh(2)', 'obsratio', 'csq(tot)']
        goal:
            name:      ['Mh(1)', 'Mh2(2)', 'obsratio', 'csq(tot)']
            value:     [    93.,     125.,         3.,       180.]
            lh_type:   ['gaussian', 'gaussian', 'sigmoid', 'sigmoid']
            lh_hp:     [10, 10, 0.3, 14]
    directories:
        scan_dir: '/mainfs/scratch/mjad1g20/scan_dir_test'
        reference_lhs: '/scratch/mjad1g20/pheno-game/distributed-ddpg/SLHA_BLSSM/reference_lhs'
        spheno: '/home/mjad1g20/HEP/SPHENO/SPheno-4.0.5'
        higgsbounds: '/home/mjad1g20/HEP/HB/higgsbounds-5.10.2/build'
        madgraph: '/scratch/mjad1g20/HEP/MG5_aMC_v3_1_1'
        higgssignals: '/home/mjad1g20/HEP/HS/higgssignals-2.6.2/build'
    """)


def id_generator(size=7, chars=string.ascii_lowercase + string.digits):
    '''
    Generate random string to use it as a temporary id.
    '''
    return ''.join(random.choice(chars) for _ in range(size))

        
    
@ray.remote
class RemoteRandomSampler:  
    '''
    The RemoteRandomSampler class uses a HEP software stack defined
    in HEPSTACK to generate random uniform samples.

    Args:
        scanner (Ray Actor): 
            Reference to call remotely the Scanner Class.
        scan_config (DictConfig):
            Config for global Scanner parameters.
        hep_config (DictConfig): 
            Config for the HEP stack software configuration.
    '''
    def __init__(self, scanner, scan_config, hep_config):
        '''Constructor for the RemoteRandomSampler Class'''
        # Save scanner reference to call remote functions
        self.scanner = scanner
        # Generate a random id for hep_stack temp dir and initiate stack
        self.random_id = id_generator()
        self.hep_stack = MODELS[scan_config.hep_stack_name](
                self.random_id, 
                hep_config
                )
        # Save config files and variables
        self.config = scan_config
        self.send_samples_freq = self.config.worker.send_samples_freq
        self.n_workers = self.config.scanner.n_workers
        self.observables = hep_config.model.observation.name
        self.parameters = hep_config.model.parameters.name
        self.parameters_dimension = len(self.parameters)
        self.observation_dimension = len(self.observables)

        # Initiate internal storage
        self.data = np.zeros((
            self.send_samples_freq,
            self.observation_dimension + self.parameters_dimension
            ))

        # Initiate counter
        self.counter = 0
        self.send = False

    def collect_samples(self) -> None:
        '''
        Sample a random point from the hep_stack.space() uniform 
        distribution and run hep_stack.sample().
        '''
        # Sample random point
        random_uniform_point = self.hep_stack.space.sample() 
        params_obs = self.hep_stack.sample(random_uniform_point)
        
        # Receive parameters as a dict and turn in to np.array
        params_obs = np.fromiter(
                params_obs.values(),
                dtype=float
                )

        # Add to internal storage
        self.add_data(params_obs)
        

    def send_samples_and_reset(self) -> None:
        '''Send internal storage to global if full and reset'''
        if self.send:
            self.scanner.add_global_data.remote(self.data)
            self.counter = 0
            self.send = False


    def add_data(self , sample_point: np.ndarray) -> None:
        '''Add data point an increment counter'''
        idx = self.counter
        self.data[idx] = sample_point
        self.counter += 1 
        if self.counter >= self.send_samples_freq:
            self.send = True

    def run(self):
        '''
        While global stop is False collect samples and send
        to global storage. If stop remove temporary scann dir.
        '''
        while not ray.get(self.scanner.stop.remote()):
            self.collect_samples()
            self.send_samples_and_reset()
        self.hep_stack.close()


@ray.remote
class Scanner:
    def __init__(self,
            config: DictConfig,
            hep_config: DictConfig,
            ):
        self.config = config
        self.hep_config = hep_config
        self.max_samples = self.config.scanner.max_samples
        self.n_workers = self.config.scanner.n_workers
        self.observables = hep_config.model.observation.name
        self.parameters = hep_config.model.parameters.name

        self.send_samples_freq = self.config.worker.send_samples_freq

        self.n_workers = self.config.scanner.n_workers
        self.parameters_dimension = len(self.parameters)
        self.observation_dimension = len(self.observables)
        self.data = np.zeros((
            self.max_samples,
            self.observation_dimension + self.parameters_dimension
            ))
        self.counter = 0
        self._stop = False

    def increment_counter(self, n_points):
        self.counter += n_points
        if self.counter >= self.max_samples:
            self._stop = True

    def get_counter(self):
        return self.counter

    def stop(self):
        return self._stop

    def add_global_data(self , data):
        idx = self.counter
        n_points = len(data) 
        self.data[idx:idx+n_points,:] = data
        self.increment_counter(n_points)

    def get_data(self, save=False):
        columns = self.parameters + self.observables
        df = pd.DataFrame(self.data, columns = columns)
        return df

@ray.remote
class Reporter:
    def __init__(self, scanner, config):
        self.scanner = scanner
        self._data = None
        self.update_rate = config.logger.update_freq
        self.last_counter = 0
        self.logger = config.logger

    def update_data(self):
        data = ray.get(self.scanner.get_data.remote())
        self._data = data

    def data(self):
        return self._data

    def save_csv(self):
        self._data.to_csv('data.csv', index=False)

    def run(self):
        while not ray.get(self.scanner.stop.remote()):
            self.last_counter = ray.get(self.scanner.get_counter.remote())
            if self.last_counter % self.update_rate == 0:
                self.update_data()
                print(self.data())
                self.save_csv()
        self.update_data()
        self.save_csv()
