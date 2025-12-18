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
from model.status import ActivityState
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
			extree = ExecutionTree.from_context(ctx, region)
		else:
			if decisions is None:
				decisions = []
			if not all(decisions):
				raise ValueError("One or more decisions are not valid transitions in the Petri net.")

			logger.info("Net defined, using provided markings and execution tree.")
			ctx = NetContext(region=region, net=net, im=im, fm=fm)

			logger.info("Strategy Type: %s", type(ctx.strategy))
			current_status = extree.current_node.snapshot.status

			regions = {}
			def build_region_dict(r: RegionModelType):
				regions[int(r.id)] = r
				if r.children:
					for child in r.children:
						build_region_dict(child)
			build_region_dict(region)

			new_status = {regions[int(r_id)] : r_status for r_id, r_status in current_status.items() }

			current_marking = extree.current_node.snapshot.marking
			logger.info("Current marking: %s", current_marking)
			logger.info("Consuming decisions: %s", decisions)

			new_marking, probability, impacts, execution_time, choices = ctx.strategy.consume(
				ctx, current_marking, regions, new_status, decisions
			)

			decision_ids = [transition.name for transition in decisions]
			choices_node_id = [place.entry_id for place in get_choices(ctx, new_marking).keys()]

			status = {}
			for r, s in new_status.items():
				status[r.id] = s
				print(r.label, ": ", s)


			new_snapshot = Snapshot(
				marking=new_marking,
				probability=probability,
				impacts=impacts,
				time=execution_time,
				status=status,
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
