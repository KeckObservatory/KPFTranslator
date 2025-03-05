from pathlib import Path
import yaml

import numpy as np

from kpf import log, cfg
from kpf.exceptions import *
from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.Target import Target


class ObservingBlock(object):
    def __init__(self, OBinput):
        if isinstance(OBinput, dict):
            OBdict = OBinput
        elif isinstance(OBinput, ObservingBlock):
            OBdict = OBinput.to_dict()
        elif OBinput in ['', None]:
            OBdict = {}
        elif isinstance(OBinput, str) or isinstance(OBinput, Path):
            file = Path(OBinput).expanduser().absolute()
            if file.exists() is True:
                try:
                    with open(file, 'r') as f:
                        OBdict = yaml.safe_load(f)
                except Exception as e:
                    log.error(f'Unable to parse input as yaml file')
                    log.error(f'{OBinput}')
                    OBdict = {}
            else:
                log.error(f'Unable to locate file: {OBinput}')
                OBdict = {}
        else:
            log.error(f'Unable to parse input as ObservingBlock')
            log.error(f'{OBinput}')
            OBdict = {}

        # OB Metadata
        self.ProgramID = OBdict.get('semid', '')
        self.OBID = OBdict.get('_id', '')
        self.CommentToObserver = OBdict.get('CommentToObserver', '')
        # Metadata for OB GUI
        self.executed = False
        self.edited = False

        ## ----------------------------------------------------------------
        ## Handle old v1 Observing Block format
        ## ----------------------------------------------------------------
        # v1 Science Observing Block
        if OBdict.get('Template_Name', None) == 'kpf_sci':
            # Target
            GaiaID = OBdict.get('GaiaID', None)
            if GaiaID is None:
                self.Target = Target.resolve_name(OBdict.get('TargetName'))
            elif str(GaiaID)[:2] == 'DR':
                self.Target = Target.resolve_name(f"Gaia {GaiaID}")
            else:
                self.Target = Target.resolve_name(f"Gaia DR3 {GaiaID}")
            self.Target.TargetName.set(OBdict.get('TargetName'))
            # Observations
            self.Observations = []
            self.Calibrations = []
            for obs_v1 in OBdict.get('SEQ_Observations', []):
                original_ExpMeterBin = obs_v1.get('ExpMeterBin', None)
                if original_ExpMeterBin is not None:
                    print(f"Original ExpMeterBin: {original_ExpMeterBin}")
                    if int(original_ExpMeterBin) > 4:
                        try:
                            wav = float(original_ExpMeterBin)
                            idx = (np.abs(np.array([498, 604, 711, 817])-wav)).argmin()
                            obs_v1['ExpMeterBin'] = idx+1
                            print(f"Converting '{original_ExpMeterBin}' to {idx+1}")
                        except:
                            pass
                obs = Observation(obs_v1)
                self.Observations.append(obs)
        # v1 Calibration Observing Block
        elif OBdict.get('Template_Name', None) == 'kpf_cal':
            # Calibrations
            self.Target = None
            self.Observations = []
            self.Calibrations = []
            for cal_v1 in OBdict.get('SEQ_Calibrations', []):
                cal = Calibration(cal_v1)
                self.Calibrations.append(cal)
        ## ----------------------------------------------------------------
        ## Handle v2 Observing Blocks
        ## ----------------------------------------------------------------
        else:
            # Target
            target = OBdict.get('Target', None)
            if target is None:
                self.Target = None
            else:
                self.Target = Target(target)
            # Observations
            observations = OBdict.get('Observations', [])
            self.Observations = [Observation(obs) for obs in observations]
            # Calibrations
            calibrations = OBdict.get('Calibrations', [])
            self.Calibrations = [Calibration(cal) for cal in calibrations]


    def validate(self):
        # Check that components are the correct types and are individually valid
        if self.Target is not None:
            if not isinstance(self.Target, Target):
                raise InvalidObservingBlock('Target component is not a Target object')
            if not self.Target.validate():
                raise InvalidObservingBlock('Target component is not a valid Target object')
        for i,observation in enumerate(self.Observations):
            if not isinstance(observation, Observation):
                raise InvalidObservingBlock(f'Observation component {i+1} is not a Observation object')
            if not observation.validate():
                raise InvalidObservingBlock('Observation component {i+1} is not a valid Observation object')
        for i,calibration in enumerate(self.Calibrations):
            if not isinstance(calibration, Calibration):
                raise InvalidObservingBlock(f'Calibration component {i+1} is not a Calibration object')
            if not calibration.validate():
                raise InvalidObservingBlock('Calibration component {i+1} is not a valid Calibration object')

        # If we have science observations, we must have a target
        if len(self.Observations) > 0:
            if self.Target is None:
                raise InvalidObservingBlock(f"contains observations without a target")

        # We should have at least one observation or calibration
        if len(self.Observations) == 0 and len(self.Calibrations) == 0:
            raise InvalidObservingBlock(f"contains no observations and no calibrations")
        return True


    def to_dict(self):
        OB = {}
        if self.Target is not None:
            OB['Target'] = self.Target.to_dict()
        if len(self.Observations) > 0:
            OB['Observations'] = [o.to_dict() for o in self.Observations]
        if len(self.Calibrations) > 0:
            OB['Calibrations'] = [c.to_dict() for c in self.Calibrations]


    def write_to(self, file, overwrite=False):
        file = Path(file)
        if file.exists == True:
            if overwrite == False:
                print(f'File {file} exists and overwrite is False')
                return
            else:
                fie.unlink()
        with open(file, 'w')as f:
            f.write(self.__repr__())


    def name(self):
        if self.Target is not None:
            out = f"{self.Target.get('TargetName')}"
        else:
            out = 'unknown '
        cal_strings = [str(cal) for cal in self.Calibrations]
        if len(cal_strings) > 0:
            out += f" {','.join(cal_strings)}"
        obs_strings = [str(obs) for obs in self.Observations]
        if len(obs_strings) > 0:
            out += f" {','.join(obs_strings)}"
        return out


    def __str__(self):
        if self.Target is not None:
            out = f"{self.Target}"
        else:
            if len(self.Observations) == 0:
                out = 'Calibration      '
            else:
                out = ' '*17
            out += '-' + ' '*10
            out += '-' + ' '*11
            out += '-' + ' '*5
            out += '-' + ' '*4
        cal_strings = [str(cal) for cal in self.Calibrations]
        if len(cal_strings) > 0:
            out += f" {','.join(cal_strings)}"
        obs_strings = [str(obs) for obs in self.Observations]
        if len(obs_strings) > 0:
            out += f" {','.join(obs_strings)}"
        return out


    def __repr__(self, comments=True):
        lines = []
        if self.Target is not None:
            lines += ['Target:']
            lines += self.Target.to_lines()
        if len(self.Calibrations) > 0:
            lines += ['Calibrations:']
            for j,cal in enumerate(self.Calibrations):
                lines.append(f'# Calibration {j+1}')
                lines += cal.to_lines()
        if len(self.Observations) > 0:
            lines += ['Observations:']
            for i,obs in enumerate(self.Observations):
                lines.append(f'# Observation {i+1}')
                lines += obs.to_lines()
        return '\n'.join(lines)


##--------------------------------------------------------------------------
## For Testing
##--------------------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='')
    p.add_argument('file', type=str,
                    help="The file to read in.")
    ## add options
    p.add_argument("-o", "--output", dest="output", type=str,
        help="Directory for output as a v2 OB.")
    args = p.parse_args()
    
    input_file = Path(args.file).expanduser()
    print(f"Reading: {input_file}")
    ob = ObservingBlock(str(input_file))
    if args.output is not None:
        outpath = Path(args.output).expanduser()
        outfile = outpath / input_file.name
        if outpath.exists() == False:
            print(f'Output directory {args.output} does not exist')
        else:
            print(f"Writing to: {outfile}")
            if outfile.exists(): outfile.unlink()
            ob.write_to(outfile)
    else:
        print(ob.__repr__())
