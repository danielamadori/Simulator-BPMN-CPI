import logging
import traceback

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse

from model.context import NetContext
from model.endpoints.execute.request import ExecuteRequest
from model.endpoints.execute.response import create_response
from model.extree import ExTree
from model.snapshot import Snapshot
from strategy.duration import DurationExecution

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s - %(name)s - %(funcName)s - %(lineno)d - %(filename)s",
)

api = FastAPI()


@api.exception_handler(404)
@api.get("/")
def root():
    return RedirectResponse("/docs/", status_code=status.HTTP_303_SEE_OTHER)


@api.post("/steps")
def steps(data: ExecuteRequest):
    try:
        region, net, im, fm, extree, choices = data.to_object()
        if not net:
            ctx = NetContext.from_region(region, strategy=DurationExecution())
        else:
            ctx = NetContext(region=region, net=net, im=im, fm=fm, strategy=DurationExecution())

        new_marking, p, i, t = ctx.strategy.consume(ctx, extree.current_node.snapshot.marking)
        extree.add_snapshot(ctx, Snapshot(marking=new_marking, probability=p, impacts=i, time=t))

        return create_response(ctx.region, ctx.net, new_marking, ctx.final_marking, extree).model_dump(
            exclude_unset=True, exclude_none=True,
            exclude_defaults=True)
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return {
            "type": "error",
            "message": str(e),
            "traceback": traceback.format_tb(e.__traceback__),
        }


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

            new_marking, probability, impacts, execution_time = ctx.strategy.consume(ctx, current_marking, choices)
            new_snapshot = Snapshot(marking=new_marking, probability=probability, impacts=impacts, time=execution_time)
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

    uvicorn.run(api, port=8001)
