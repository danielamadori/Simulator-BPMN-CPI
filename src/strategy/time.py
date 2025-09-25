class TimeStrategy:
    """
    Strategy that execute specific time amount.
    """


    def saturate(self, ctx: "ContextType", marking: "MarkingType"):
        # Implement saturation logic considering time constraints
        pass

    def consume(self, ctx: "ContextType", marking: "MarkingType", choices: list["TransitionType"] | None = None):
        # Implement consumption logic considering time constraints
        pass