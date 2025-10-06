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

def parse(region, activated_nodes_ids:list[str]):
	if region.type != RegionType.SEQUENTIAL and region.id not in activated_nodes_ids:
		return []

	if region.children is None:
		return [region]

	active_regions = []
	for region in region.children:
		active_regions.extend(parse(region, activated_nodes_ids))

	return active_regions




@api.post("/execute")
def execute(data: ExecuteRequest):
	try:
		region, net, im, fm, extree, decisions = data.to_object()
		logger.info("Request received:")
		if not net:
			logger.info(f"No net defined. Creating new context and execution tree.")
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

			logger.info(f"Net defined, using provided markings and execution tree.")
			ctx = NetContext(region=region, net=net, im=im, fm=fm)
			logger.info(f"Strategy Type: {type(ctx.strategy)}")
			current_marking = extree.current_node.snapshot.marking
			logger.info(f"Current marking: {current_marking}")

			logger.info(f"Consuming decisions: {decisions}")
			new_marking, probability, impacts, execution_time, choices, fired_transitions = ctx.strategy.consume(ctx, current_marking, decisions)

			status = {}
			for active in parse(region, [t.get_region_id() for t in fired_transitions]): #Finding active regions in the parse_tree
				status[active.id] = ActivityState.ACTIVE

			choices_node_id = []
			for place in get_choices(ctx, new_marking).keys():
				choices_node_id.append(place.entry_id) #is string; todo convert to int

			print("execute:", status, decisions, choices_node_id)
			#filter loop to increase bound/visit_limit
			new_snapshot = Snapshot(marking=new_marking, probability=probability, impacts=impacts, time=execution_time,
									status=status, decisions=decisions, choices=choices_node_id)

			extree.add_snapshot(ctx, new_snapshot)

		return create_response(region, net, im, fm, extree).model_dump(exclude_unset=True, exclude_none=True,
																	   exclude_defaults=True)
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
