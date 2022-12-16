from src.utils import run_scan
from src.parallel_scanner import SCANNER_DEFAULT_CONFIG
from src.parallel_scanner import HEP_DEFAULT_CONFIG


SCANNER_DEFAULT_CONFIG = OmegaConf.create({
    'hep_stack_name': 'SPhenoHbHs',
    'scanner': {
        'max_samples': 4000,
        'n_workers': 39,
        },
    'worker': {
        'send_samples_freq': 50,
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
            name:      ['m0', 'm12',   'Azero', 'TanBeta', 'TBetaP', 'TBetaP', 'MZp', 'MZp', 'gBLinput', 'g1BLinput']
            low_lim:   [100.,  1000., 1000., 1., 1., 1.,2000.,2000.,-1.,-1.]
            high_lim:  [1000., 4500., 4000.,60.,60.,60.,5000.,5000.,1., 1.]
            lhs:
                index: [1,2,5,3,7,10,8,3,1,2]
                block: ['MINPAR','MINPAR','MINPAR','MINPAR','MINPAR','EXTPAR','MINPAR','EXTPAR','EXTPAR','EXTPAR']
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
        final_dataset: 'datasets'
    """)
run_scan(
        SCANNER_DEFAULT_CONFIG,
        HEP_DEFAULT_CONFIG,
        )
