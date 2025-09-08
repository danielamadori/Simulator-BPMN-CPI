class ValidationError(Exception):
    def __init__(self, message="The region is not valid, therefore it cannot be correctly translated into a Petri Net"):
        super().__init__(message)

class MaxIterationsError(Exception):
    def __init__(self, message="The maximum number of iterations has been reached during execution."):
        super().__init__(message)