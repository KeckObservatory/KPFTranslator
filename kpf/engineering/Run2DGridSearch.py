import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.engineering.GridSearch import GridSearch
from kpf.fvc.PredictFVCParameters import PredictFVCParameters
from kpf.expmeter.PredictExpMeterParameters import PredictExpMeterParameters


##-------------------------------------------------------------------------
## Run2DGridSearch
##-------------------------------------------------------------------------
class Run2DGridSearch(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        n = args.get('n')
        d = args.get('d')
        Gmag = args.get('Gmag')
        comment = args.get('comment', '')
        em_parameters = PredictExpMeterParameters.execute({'Gmag': Gmag})

        # Check if FVCs are on, if so, use them
        FVCs_that_are_on = []
        for camera in ['SCI', 'CAHK']:
            camnum = {'SCI': 1, 'CAHK': 2}[camera]
            powerkw = ktl.cache('kpfpower', f'KPFFVC{camnum}')
            if powerkw.read().lower() == 'on':
                FVCs_that_are_on.append(camera)
        FVCstring = ','.join(FVCs_that_are_on)
        if len(FVCs_that_are_on) > 0:
            fvc_parameters = PredictFVCParameters.execute({'Gmag': Gmag})
            print(f"Predicted FVC parameters:")
            print(fvc_parameters)
            print('Set the FVC parameters manually and press enter to continue')
            user_input = input()

        dcs = ktl.cache('dcs1')
        targname = dcs['TARGNAME'].read()
        args = {'Template_Name': 'kpf_eng_grid', 'Template_Version': 0.4,
                'Grid': 'TipTilt',
                'dx': d,
                'dy': d,
                'TimeOnPosition': 15,
                'TriggerCaHK': False,
                'TriggerGreen': False,
                'TriggerRed': False,
                'TriggerExpMeter': True,
                'UseCRED2': True,
                'SSS_Science': True,
                'SSS_Sky': True,
                'SSS_CalSciSky': False,
                'ExpMeter_exptime': em_parameters['ExpMeterExpTime'],
                'FVCs': FVCstring,
                }
        x_args = {'comment': f'1D in X {targname} (G={Gmag:.1f}) {comment}',
                  'nx': n,
                  'ny': 1,
                  }
        args.update(x_args)
        GridSearch.execute(args)
        y_args = {'comment': f'1D in Y {targname} (G={Gmag:.1f}) {comment}',
                  'nx': 1,
                  'ny': n,
                  }
        args.update(y_args)
        GridSearch.execute(args)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('n', type=int,
                            help="Number of position samples in each axis")
        parser.add_argument('d', type=float,
                            help="Separation between positions (in guder pix)")
        parser.add_argument('Gmag', type=float,
                            help="The G magnitude of the target")
        parser.add_argument("--comment", dest="comment", type=str,
            default='',
            help="Additional comment text")
        return super().add_cmdline_args(parser, cfg)
