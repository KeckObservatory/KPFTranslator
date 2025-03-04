from kpf import log

class KPFException(Exception):
    def __init__(self, message=""):
        self.message = message
        log.error(self.message)
        super().__init__(self.message)


class InvalidObservingBlock(KPFException):
    def __init__(self, iobmessage=""):
        self.iobmessage = f"OB Invalid: {iobmessage}"
        super().__init__(self.iobmessage)


class FailedPreCondition(KPFException):
    def __init__(self, pcmessage=""):
        self.pcmessage = f"Failed PreCondition: {pcmessage}"
        super().__init__(self.pcmessage)


class FailedPostCondition(KPFException):
    def __init__(self, pcmessage=""):
        self.pcmessage = f"Failed PostCondition: {pcmessage}"
        super().__init__(self.pcmessage)


class FailedToReachDestination(FailedPostCondition):
    def __init__(self, value="", destination="", ):
        self.destination = destination
        self.value = value
        msg = f"Current value ({value}) != destination ({destination})"
        super().__init__(msg)


LostTipTiltStar = KPFException
ScriptStopTriggered = KPFException


##-------------------------------------------------------------------------
## Utility functions for pre- or post- conditions
##-------------------------------------------------------------------------
def check_input(args, input_name, allowed_types=None, allowed_values=None,
                value_min=None, value_max=None, version_check=False):
        target = args.get(input_name, None)
        if target is None:
            raise FailedPreCondition(f"Input {input_name} is None")

        if version_check is True:
            target = version.parse(f"{target}")
            if value_min is not None:
                value_min = version.parse(f"{value_min}")
            if value_max is not None:
                value_max = version.parse(f"{value_max}")

        # Check against allowed types
        if allowed_types is not None:
            if type(allowed_types) != list:
                allowed_types = [allowed_types]
            if type(target) not in allowed_types:
                raise FailedPreCondition(f"Input {input_name} value {target} ({type(target)}) "
                                         f"is not an allowed type: {allowed_types}")
        # Check against value_min and value_max
        if type(target) in [float, int, version.Version]:
            if value_min is not None:
                if target < value_min:
                    raise FailedPreCondition(f"Input {input_name} value {target} "
                                             f"below minimum allowed ({value_min})")
            if value_max is not None:
                if target > value_max:
                    raise FailedPreCondition(f"Input {input_name} value {target} "
                                             f"above maximum allowed ({value_max})")
        # Check against allowed_values
        if allowed_values is not None:
            allowed_values = [val.lower() if type(val) == str else str(val)\
                              for val in allowed_values]
            target = str(target)
            if target.lower().strip() not in allowed_values:
                raise FailedPreCondition(f"Input {input_name} value {target} "
                                         f"not in allowed values")
