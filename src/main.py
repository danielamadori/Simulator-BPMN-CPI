import copy
import enum
import logging
import traceback

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse

from model.context import NetContext
from model.endpoints.execute.request import ExecuteRequest
from model.endpoints.execute.response import create_response
from model.extree import ExecutionTree
from model.extree.node import Snapshot
from model.region import RegionType
from model.types import RegionModelType
from strategy.execution import get_choices
from utils import logging_utils
from utils.settings import settings

api = FastAPI(title=settings.title, version=settings.version, docs_url=settings.docs_url, redoc_url=None)

logger = logging_utils.get_logger(__name__)

@api.exception_handler(404)
@api.get("/")
def root():
	return RedirectResponse("/docs/", status_code=status.HTTP_303_SEE_OTHER)


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



def parse(region: RegionModelType, status: dict, activated_nodes_ids:list[str]):
	region_id = str(region.id)
	current_region_status = ActivityState.WAITING
	if region_id in activated_nodes_ids:# Already present
		current_region_status = ActivityState.ACTIVE

	if region.children is None:
		if current_region_status == ActivityState.ACTIVE: #check if the task is completed
			current_region_status = ActivityState.COMPLETED

		return { region_id : current_region_status }

	#check if all children are completed
	all_completed = True
	sub_status = {}
	for sub_region in region.children:
		sub_status.update(parse(sub_region, status, activated_nodes_ids))
		if str(sub_region.id) in sub_status.keys() and sub_status[str(sub_region.id)] <= ActivityState.ACTIVE:
			all_completed = False

	if all_completed:
		current_region_status = ActivityState.COMPLETED

	return { **sub_status, region_id: current_region_status }


@api.post("/execute")
def execute(data: ExecuteRequest):
	try:
		region, net, im, fm, extree, decisions = data.to_object()
		logger.info("Request received:")
		if not net:
			logger.info("No net defined. Creating new context and execution tree.")
			ctx = NetContext.from_region(region)
			net = ctx.net
			im = ctx.initial_marking
			fm = ctx.final_marking
			extree = ExecutionTree.from_context(ctx)
		else:
			if decisions is None:
				decisions = []
			if not all(decisions):
				raise ValueError("One or more decisions are not valid transitions in the Petri net.")

			logger.info("Net defined, using provided markings and execution tree.")
			ctx = NetContext(region=region, net=net, im=im, fm=fm)
			logger.info("Strategy Type: %s", type(ctx.strategy))
			current_status = extree.current_node.snapshot.status
			current_marking = extree.current_node.snapshot.marking
			logger.info("Current marking: %s", current_marking)

			logger.info("Consuming decisions: %s", decisions)
			new_marking, probability, impacts, execution_time, choices, fired_transitions = ctx.strategy.consume(
				ctx, current_marking, decisions
			)

			decision_ids = [transition.name for transition in decisions]
			activated_nodes_ids = [str(t.get_region_id()) for t in fired_transitions]
			print("Active: ", activated_nodes_ids)
			print("Current status:", current_status)
			new_status = parse(region, copy.deepcopy(current_status), activated_nodes_ids)
			print("new_status:", new_status)

			choices_node_id = [place.entry_id for place in get_choices(ctx, new_marking).keys()]

			print("execute:", status, decisions, choices_node_id)
			new_snapshot = Snapshot(
				marking=new_marking,
				probability=probability,
				impacts=impacts,
				time=execution_time,
				status=new_status,
				decisions=decision_ids,
				choices=choices_node_id,
			)

			extree.add_snapshot(ctx, new_snapshot)

		return create_response(region, net, im, fm, extree).model_dump(
			exclude_unset=True, exclude_none=True, exclude_defaults=True
		)
	except Exception as e:
		logging.error(f"Error processing request: {e}")
		return {
			"type": "error",
			"message": str(e),
			"traceback": traceback.format_tb(e.__traceback__),
		}


if __name__ == '__main__':
	import uvicorn

	uvicorn.run(api, host=settings.host, port=settings.port)
