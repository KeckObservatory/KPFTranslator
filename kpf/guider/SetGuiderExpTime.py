from time import sleep
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetGuiderExpTime(KPFTranslatorFunction):
    '''Set the guider exposure time (in seconds) via the kpfguide.EXPTIME
    keyword.
    
    The guider exposure time is governed by several factors.  The exposure time
    controlled here is generated by stacking (averaging) multiple frames as
    needed to obtain the specified exposure time.  Those individual frames are
    controlled by the FPS, AVERAGE, STACK, and EXPTIME keywords.


    From Kyle:

    If you want to tweak an exposure setting, I recommend MAGIQ use the
    EXPTIME keyword as its preferred knob. This will translate to changing
    the number of frames averaged together. You can also choose to stack
    frames, but I doubt that will be necessary.

    Notice how EXPTIME remains unchanged when I change the STACK keyword:

    [klanclos@kpffiuserver ~]$ gshow -s kpfguide fps average stack exptime
             FPS =  100.0000 frames/second
         AVERAGE =  100 frames
           STACK =  1 averaged frames
         EXPTIME =  1.000000 seconds

    [klanclos@kpffiuserver ~]$ modify -s kpfguide stack=2
    setting stack = 2 (wait)
    [klanclos@kpffiuserver ~]$ gshow -s kpfguide fps average stack exptime
             FPS =  100.0000 frames/second
         AVERAGE =  50 frames
           STACK =  2 averaged frames
         EXPTIME =  1.000000 seconds

    ...but if I change AVERAGE, EXPTIME reflects the change:

    [klanclos@kpffiuserver ~]$ modify -s kpfguide average=20
    setting average = 20 (wait)
    [klanclos@kpffiuserver ~]$ gshow -s kpfguide fps average stack exptime
             FPS =  100.0000 frames/second
         AVERAGE =  20 frames
           STACK =  1 averaged frames
         EXPTIME =  0.200000 seconds

    Stick to changing EXPTIME and you won't have to worry about it.
    Changing the frames per second is not recommended, because the tip/tilt
    system will be consuming this image stream, and it needs to retain full
    control of what an individual frame looks like.

    ARGS:
    =====
    :exptime: The exposure time in seconds.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        exptime = args.get('exptime', None)
        return (exptime is not None) and (float(exptime) > 0)

    @classmethod
    def perform(cls, args, logger, cfg):
        exptimekw = ktl.cache('kpfguide', 'EXPTIME')
        exptime = args.get('exptime')
        exptimekw.write(exptime)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        exptol = cfg.get('tolerances', 'guider_exptime_tolerance', fallback=0.01)

        exptimekw = ktl.cache('kpfguide', 'EXPTIME')
        exptimeread = exptimekw.read(binary=True)
        exptime = args.get('exptime')

        expr = (f'($kpfguide.EXPTIME >= {exptime-exptol}) and '\
                f'($kpfguide.EXPTIME <= {exptime+exptol})')
        success = ktl.waitFor(expr, timeout=exptimeread+1)
        if not success:
            exptimeread = exptimekw.read(binary=True)
            log.error(f"Failed to set exposure time.")
            log.error(f"Requested {exptime:.3f} s, found {exptimeread:.3f} s")
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['exptime'] = {'type': float,
                                  'help': 'The exposure time in seconds.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
