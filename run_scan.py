from src.ray_scan import *
from omegaconf import OmegaConf

import numpy as np
import os 
import ray

cwd = os.getcwd()
scan_dir = os.path.join(cwd, 'test')

config = OmegaConf.load('hep_tools.yaml')
config.directories.scan_dir = scan_dir


ray.init(local_mode=False)

scanner = Scanner.remote(config = config)
reporter = Reporter.remote(scanner)
remote_samplers = [RemoteSampler.remote(scanner, i, config) for i in range(config.scanner.n_workers)]

processes = []
for remote_sampler in remote_samplers:
	processes.append(remote_sampler)
processes.append(reporter)

processes = [p.run.remote() for p in processes]
ray.wait(processes)


