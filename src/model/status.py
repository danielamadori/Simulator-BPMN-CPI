import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from model.region import RegionModel

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


def propagate_status(region: "RegionModel", status: dict["RegionModel", "ActivityState"]):
	"""
	Recursively propagate status from children to parent regions.
	This sets parent status based on children's completion/active states.
	"""
	if region.is_task():
		return

	# Capture status calculated by saturate (based on tokens)
	prior_status = status.get(region, ActivityState.WAITING)
	
	status[region] = ActivityState.WAITING

	for child in region.children:
		propagate_status(child, status)

	if region.is_sequential():
		if status[region.children[0]] == ActivityState.ACTIVE or status[region.children[1]] == ActivityState.ACTIVE:
			status[region] = ActivityState.ACTIVE
		elif status[region.children[1]] == ActivityState.COMPLETED:
			status[region] = ActivityState.COMPLETED

	elif region.is_parallel():
		all_completed = True
		any_active = False
		for child in region.children:
			if status[child] == ActivityState.ACTIVE:
				any_active = True
				all_completed = False
			elif status[child] != ActivityState.COMPLETED:
				all_completed = False

		if any_active:
			status[region] = ActivityState.ACTIVE
		elif all_completed:
			status[region] = ActivityState.COMPLETED

	# Exclusive/Nature/Loop gateway (Choice logic)
	elif region.children:
		selected_child = None
		for child in region.children:
			if status[child] == ActivityState.ACTIVE or status[child] == ActivityState.COMPLETED:
				status[region] = status[child]
				selected_child = child
				break
		
		# If a choice was made, mark all other children as WILL_NOT_BE_EXECUTED
		if selected_child is not None:
			for child in region.children:
				if child != selected_child and status[child] == ActivityState.WAITING:
					mark_as_skipped(child, status)
				
	# Restore prior status if we didn't calculate a new state (e.g. Gateway holding a token)
	if status[region] == ActivityState.WAITING and prior_status != ActivityState.WAITING:
		status[region] = prior_status


def mark_as_skipped(region: "RegionModel", status: dict["RegionModel", "ActivityState"]):
	"""Mark a region and all its children as WILL_NOT_BE_EXECUTED (Skipped)."""
	status[region] = ActivityState.WILL_NOT_BE_EXECUTED
	if region.children:
		for child in region.children:
			mark_as_skipped(child, status)
