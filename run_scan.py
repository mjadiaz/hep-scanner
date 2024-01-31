from src.utils import run_scan
from src.parallel_scanner import SCANNER_DEFAULT_CONFIG
from src.parallel_scanner import HEP_DEFAULT_CONFIG
from omegaconf import OmegaConf


SCANNER_DEFAULT_CONFIG = OmegaConf.create({
    'hep_stack_name': 'SPhenoHbHs',
    'scanner': {
        'max_samples': 20,
        'n_workers': 3,
        },
    'worker': {
        'send_samples_freq': 4,
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
            name:      ['m0', 'm12',   'Azero', 'TanBeta', 'TBetaP', 'MZp', 'SignumMu', 'SignumMuP']
            low_lim:   [1.,  1., -9000., 1., 1.,4000., -1., -1.]
            high_lim:  [3000., 5000., 9000.,60.,60,4500., 1., 1.]
            lhs:
                index: [1,2,5,3,7,8, 4, 6]
                block: ['MINPAR','MINPAR','MINPAR','MINPAR','MINPAR', 'MINPAR', 'MINPAR', 'MINPAR']
                distribution: ['uniform', 'uniform', 'uniform', 'uniform', 'uniform', 'uniform', 'binary', 'binary']

    directories:
        scan_dir: '/mainfs/scratch/mjad1g20/scan_dir_test'
        reference_lhs: '/scratch/mjad1g20/ParameterScan/input_files/LesHouches.in.BLSSM'
        spheno: '/home/mjad1g20/HEP/SPHENO/SPheno-4.0.5'
        higgsbounds: '/home/mjad1g20/HEP/HB/higgsbounds-5.10.2/build'
        madgraph: '/scratch/mjad1g20/HEP/MG5_aMC_v3_1_1'
        higgssignals: '/home/mjad1g20/HEP/HS/higgssignals-2.6.2/build'
        final_dataset: 'datasets_higgsprofile_test'
    """)

run_scan(
        SCANNER_DEFAULT_CONFIG,
        HEP_DEFAULT_CONFIG,
        )
