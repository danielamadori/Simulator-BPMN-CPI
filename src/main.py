import logging
import traceback

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse, HTMLResponse
from pm4py.objects.petri_net.utils.petri_utils import get_transition_by_name

from model.context import NetContext
from model.endpoints.execute.request import ExecuteRequest
from model.endpoints.execute.response import create_response
from model.extree import ExTree
from model.snapshot import Snapshot
from utils.net_utils import get_all_choices

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s - %(name)s - %(funcName)s - %(lineno)d - %(filename)s",
)

api = FastAPI()


@api.exception_handler(404)
@api.get("/")
def root():
    return RedirectResponse("/docs/", status_code=status.HTTP_303_SEE_OTHER)


@api.post("/execute")
def execute(data: ExecuteRequest):
    try:
        region, net, im, fm, extree, choices = data.to_object()
        if not net:
            ctx = NetContext.from_region(region)
            net = ctx.net
            im = ctx.initial_marking
            fm = ctx.final_marking
            extree = ExTree.from_context(ctx)
        else:
            if choices is None:
                choices = []
            if not all(choices):
                raise ValueError("One or more choices are not valid transitions in the Petri net.")

            ctx = NetContext(region=region, net=net, im=im, fm=fm)
            current_marking = extree.current_node.snapshot.marking

            all_transitions_fired = get_all_choices(ctx, current_marking, choices)
            new_marking, probability, impacts, execution_time = ctx.strategy.consume(ctx, current_marking, choices)
            new_snapshot = Snapshot(marking=new_marking, probability=probability, impacts=impacts, time=execution_time)
            extree.add_snapshot(ctx, new_snapshot, all_transitions_fired)

        return create_response(region, net, im, fm, extree).model_dump(exclude_unset=True, exclude_none=True, exclude_defaults=True)
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return {
            "type": "error",
            "message": str(e),
            "traceback": traceback.format_tb(e.__traceback__),
        }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(api, port=8001)
