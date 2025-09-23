import logging
import traceback

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse

from model.context import NetContext
from model.endpoints.execute.request import ExecuteRequest
from model.endpoints.execute.response import create_response
from model.extree import ExecutionTree
from model.extree.node import Snapshot
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
        region, net, im, fm, extree, choices = data.to_object()
        logger.info("Request received:")
        if not net:
            logger.info(f"No net defined. Creating new context and execution tree.")
            ctx = NetContext.from_region(region)
            net = ctx.net
            im = ctx.initial_marking
            fm = ctx.final_marking
            extree = ExecutionTree.from_context(ctx)
        else:
            if choices is None:
                choices = []
            if not all(choices):
                raise ValueError("One or more choices are not valid transitions in the Petri net.")

            logger.info(f"Net defined, using provided markings and execution tree.")
            ctx = NetContext(region=region, net=net, im=im, fm=fm)
            logger.info(f"Strategy Type: {type(ctx.strategy)}")
            current_marking = extree.current_node.snapshot.marking
            logger.info(f"Current marking: {current_marking}")

            logger.info(f"Consuming choices: {choices}")
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

    uvicorn.run(api, host=settings.host, port=settings.port)
