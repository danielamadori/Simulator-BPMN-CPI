import enum

class ActivityState(enum.IntEnum):
	WILL_NOT_BE_EXECUTED = -1
	WAITING = 0
	ACTIVE = 1
	COMPLETED = 2
	COMPLETED_WITHOUT_PASSING_OVER = 3

	def __str__(self):
		if self.value > 2:
			return "Completed"
		return self.name.lower().replace("_", " ").capitalize()


