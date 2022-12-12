import io
from PIL import Image, ImageDraw
import imageio 
import numpy as np

class LikelihoodCalculator:
    def __init__(self, hep_config):
        self.goal_value = hep_config.model.goal.value
        self.lh_type = hep_config.model.goal.lh_type
        self.lh_hp = hep_config.model.goal.lh_hp
        self.random_id = id_generator()
        self.model = MODELS[self.name](self.random_id, hep_config)
        self.lh_functions = LIKELIHOODS

    def higgs_masses_likelihood(self, observables_array: np.ndarray) -> float:
        likelihood_total = 1
        goal_iter = zip(observables_array, self.goal_value, self.lh_type, self.lh_hp)
        for obs_value, goal_value, lh_type, lh_hp in goal_iter:
            likelihood_total *= self.lh_functions[lh_type](obs_value, goal_value, width=lh_hp)
        return likelihood_total

    def likelihood(self, observables_array: np.ndarray):
        if None in observables_array:
            return None
        else:
            return self.higgs_masses_likelihood(observables_array)
    
    def run(self, observables_array: np.ndarray):
        obs = self.model(observables_array)
        lh = self.likelihood(obs)
        return lh
    

def fig2img(fig):
    """Convert a Matplotlib figure to a PIL Image and return it"""
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    img = Image.open(buf)
    return img
def save_mp4(images: list, name: str, fps=30):
    imageio.mimwrite(name, images, fps=fps)

def minmax(x, domain, codomain, reverse=False):
    '''
    Normalize an x value given a minimum and maximum mapping.

    Args:
    ----
    x = value to normalize
    domain = tuple for domain (from, to)
    codomain = tuple for codomain (from,to)
    reverse = inverse mapping, boolean.

    Returns:
    -------
    x_normalized (x_unormalized if reverse=True)
    '''
    min_dom, max_dom = domain
    min_codom, max_codom = codomain
    A,B = max_codom - min_codom, min_codom
    if reverse:
        return np.clip((x - B)*(max_dom-min_dom)/A + min_dom, min_dom, max_dom)
    else:
        return np.clip(A*(x - min_dom)/(max_dom-min_dom)+B, min_codom, max_codom)

def minmax_vector(
        x, 
        domain_bottom, 
        domain_top, 
        codomain_bottom, 
        codomain_top,
        reverse=False):
    '''
    Normalize an x value given a minimum and maximum mapping.

    Args:
    ----
    x = value to normalize
    domain = tuple for domain (from, to)
    codomain = tuple for codomain (from,to)
    reverse = inverse mapping, boolean.

    Returns:
    -------
    x_normalized (x_unormalized if reverse=True)
    '''
    A,B = codomain_top - codomain_bottom, codomain_bottom
    Ad, Bd = domain_top - domain_bottom, domain_bottom
    if reverse:
        return np.clip((x - B)*Ad/A + Bd, domain_bottom, domain_top)
    else:
        return np.clip((x - Bd)*A/Ad + B, codomain_bottom, codomain_top)

def run_scan(scan_config, hep_config):
    from src.parallel_scanner import Scanner
    from src.parallel_scanner import Reporter
    from src.parallel_scanner import RemoteRandomSampler
    from omegaconf import OmegaConf
    
    import numpy as np
    import ray
    
    ray.init(local_mode=False)
    
    scanner = Scanner.remote(config=scan_config, hep_config=hep_config)
    reporter = Reporter.remote(scanner, config=scan_config)
    remote_samplers = [RemoteRandomSampler.remote(scanner, scan_config, hep_config) for _ in range(scan_config.scanner.n_workers)]
    
    processes = []
    for remote_sampler in remote_samplers:
    	processes.append(remote_sampler)
    processes.append(reporter)
    
    processes = [p.run.remote() for p in processes]
    ray.wait(processes)
