import enum
import logging
import traceback
from typing import Any

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse

from model.context import NetContext
from model.endpoints.execute.request import ExecuteRequest
from model.endpoints.execute.response import create_response
from model.extree import ExecutionTree
from model.extree.node import Snapshot
from model.region import RegionType, build_region_module, RegionModule, RegionModuleNode, RegionModel
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

def _maybe_build_region_module(region: Any) -> RegionModule | Any:
	"""
	Accepts dict (parse-tree), RegionModel, or RegionModule and returns a RegionModule.
	"""
	if isinstance(region, RegionModule):
		return region
	if isinstance(region, dict):
		# parse-tree dict as produced by GUI / ParseTree.to_dict()
		return build_region_module(region)
	if isinstance(region, RegionModel):
		# Convert RegionModel (which is itself the root node) -> dict -> RegionModule
		def _rm_to_dict(node) -> dict:
			out = {
				"id": getattr(node, "id", None),
				"index_in_parent": getattr(node, "index_in_parent", None),
				# force lowercase string for builder compatibility
				"type": (node.type.name.lower() if hasattr(node.type, "name") else str(node.type).lower()),
			}
			label = getattr(node, "label", None)
			if label is not None:
				out["label"] = label

			duration = getattr(node, "duration", None)
			if duration is not None:
				out["duration"] = float(duration)

			impacts = getattr(node, "impacts", None)
			if impacts is not None:
				out["impacts"] = list(impacts)

			distribution = getattr(node, "distribution", None)
			if distribution is not None:
				out["distribution"] = list(distribution)

			max_delay = getattr(node, "max_delay", None)
			if max_delay is not None:
				out["max_delay"] = max_delay

			children = getattr(node, "children", None)
			if children:
				out["children"] = [_rm_to_dict(ch) for ch in children]
			return out

		rm_dict = _rm_to_dict(region)
		return build_region_module(rm_dict)

	return region  # fallback (shouldn't happen with supported inputs)



def _as_region_node(region: Any) -> RegionModuleNode | Any:
	if isinstance(region, RegionModule):
		return region.root
	if isinstance(region, RegionModuleNode):
		return region
	if isinstance(region, dict):
		return build_region_module(region).root
	if isinstance(region, RegionModel):
		# same idea: convert the node itself
		def _rm_to_dict(node) -> dict:
			out = {
				"id": getattr(node, "id", None),
				"index_in_parent": getattr(node, "index_in_parent", None),
				"type": (node.type.name.lower() if hasattr(node.type, "name") else str(node.type).lower()),
			}
			label = getattr(node, "label", None)
			if label is not None:
				out["label"] = label
			duration = getattr(node, "duration", None)
			if duration is not None:
				out["duration"] = float(duration)
			impacts = getattr(node, "impacts", None)
			if impacts is not None:
				out["impacts"] = list(impacts)
			distribution = getattr(node, "distribution", None)
			if distribution is not None:
				out["distribution"] = list(distribution)
			max_delay = getattr(node, "max_delay", None)
			if max_delay is not None:
				out["max_delay"] = max_delay
			children = getattr(node, "children", None)
			if children:
				out["children"] = [_rm_to_dict(ch) for ch in children]
			return out

		return build_region_module(_rm_to_dict(region)).root

	return region



def parse(region, activated_nodes_ids: list[str | int]):
	region_node = _as_region_node(_maybe_build_region_module(region))

	if not isinstance(activated_nodes_ids, set):
		activated_nodes_ids = {str(_id) for _id in activated_nodes_ids if _id is not None}

	if region_node.type != RegionType.SEQUENTIAL and str(region_node.id) not in activated_nodes_ids:
		return []

	if not region_node.children:
		return [region_node]

	active_regions = []
	for child in region_node.children:
		active_regions.extend(parse(child, activated_nodes_ids))

	return active_regions


@api.post("/execute")
def execute(data: ExecuteRequest):
	try:
		# Keep the original RegionModel from the request
		region_rm, net, im, fm, extree, decisions = data.to_object()

		# DO NOT convert RegionModel -> RegionModule here (validator expects RegionModel)
		logger.info("Request received:")

		if not net:
			logger.info("No net defined. Creating new context and execution tree.")
			# Pass RegionModel to NetContext
			ctx = NetContext.from_region(region_rm)
			net = ctx.net
			im = ctx.initial_marking
			fm = ctx.final_marking
			extree = ExecutionTree.from_context(ctx)
		else:
			# When a net already exists, we may need RegionModule only for helper functions like `parse(...)`
			if decisions is None:
				decisions = []
			if not all(decisions):
				raise ValueError("One or more decisions are not valid transitions in the Petri net.")

			# Convert to RegionModule ONLY for operations that require module/nodes
			region_mod = _maybe_build_region_module(region_rm)

			logger.info("Net defined, using provided markings and execution tree.")
			ctx = NetContext(region=region_rm, net=net, im=im, fm=fm)  # still RegionModel here
			logger.info("Strategy Type: %s", type(ctx.strategy))
			current_marking = extree.current_node.snapshot.marking
			logger.info("Current marking: %s", current_marking)

			logger.info("Consuming decisions: %s", decisions)
			new_marking, probability, impacts, execution_time, choices, fired_transitions = ctx.strategy.consume(
				ctx, current_marking, decisions
			)

			decision_ids = [transition.name for transition in decisions]

			status = {}
			# Use RegionModule for parse() since it navigates RegionModuleNode(s)
			for active in parse(region_mod, [t.get_region_id() for t in fired_transitions]):
				status[active.id] = ActivityState.ACTIVE

			choices_node_id = [place.entry_id for place in get_choices(ctx, new_marking).keys()]

			print("[EXECUTE] consume() -> status:", status, "decisions:", decision_ids, "choices:", choices_node_id)
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

		# IMPORTANT: `create_response` wants a RegionModel (not RegionModule)
		return create_response(region_rm, net, im, fm, extree).model_dump(
			exclude_unset=True, exclude_none=True, exclude_defaults=True
		)
	except Exception as e:
		logging.error(f"Error processing request: {e}")
		print("[EXECUTE] exception:", repr(e))
		return {
			"type": "error",
			"message": str(e),
			"traceback": traceback.format_tb(e.__traceback__),
		}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(api, host=settings.host, port=settings.port)