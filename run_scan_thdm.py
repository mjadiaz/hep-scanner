from src.utils import run_scan
from src.parallel_scanner import SCANNER_DEFAULT_CONFIG
from src.parallel_scanner import HEP_DEFAULT_CONFIG
from omegaconf import OmegaConf


SCANNER_DEFAULT_CONFIG = OmegaConf.create({
    'hep_stack_name': 'SPhenoHbHs',
    'scanner': {
        'max_samples': 100,
        'n_workers': 39,
        },
    'worker': {
        'send_samples_freq':25,
        },
    'logger': {
        'type': 'Wandb',
        'update_freq': 2
        }
    })

HEP_DEFAULT_CONFIG = OmegaConf.create(
    """
    model:
        name: 'THDMIII'
        neutral_higgs: 3
        charged_higgs: 1
        parameters:
            name:      ['Lambda1', 'Lambda2',   'Lambda3', 'Lambda4', 'Lambda5', 'M12input', 'TanBeta']
            low_lim:   [0,  0, 0, 0, 0, 50, 1.1]
            high_lim:  [25, 25, 25, 25, 25,80, 1.5]
            lhs:
                index: [1,2,3,4,5,9,10]
                block: ['MINPAR','MINPAR','MINPAR','MINPAR','MINPAR','MINPAR','MINPAR']
                distribution: ['uniform', 'uniform', 'uniform', 'uniform','uniform','uniform','uniform']
    directories:
        scan_dir: '/mainfs/scratch/mjad1g20/scan_dir_test'
        final_dataset: 'datasets'
        reference_lhs: '/scratch/mjad1g20/ParameterScan/input_files/LesHouches.in.THDMIII'
        spheno: '/home/mjad1g20/HEP/SPHENO/SPheno-4.0.5'
        higgsbounds: '/home/mjad1g20/HEP/HB/higgsbounds-5.10.2/build'
        madgraph: '/scratch/mjad1g20/HEP/MG5_aMC_v3_1_1'
        higgssignals: '/home/mjad1g20/HEP/HS/higgssignals-2.6.2/build'
    """)
run_scan(
        SCANNER_DEFAULT_CONFIG,
        HEP_DEFAULT_CONFIG,
        )
