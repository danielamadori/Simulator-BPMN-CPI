class ValidationError(Exception):
    def __init__(self, message="La regione non è valida, impossibile quindi da tradurre correttamente in Petri Net"):
        super().__init__(message)
