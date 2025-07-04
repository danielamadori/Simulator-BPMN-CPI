import json
import logging

from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse, HTMLResponse

from model.context import NetContext
from model.endpoints.execute.request import ExecuteRequest
from model.endpoints.execute.response import create_response
from model.extree import ExTree
from model.region import RegionModel

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s - %(name)s - %(funcName)s - %(lineno)d - %(filename)s",
)

api = FastAPI()


@api.exception_handler(404)
async def error_to_docs(_, __):
    data = ""
    with open("static/404.html") as f:
        data = f.read()
    return HTMLResponse(data, status_code=status.HTTP_404_NOT_FOUND)


@api.get("/")
def root():
    return RedirectResponse("/docs/", status_code=status.HTTP_303_SEE_OTHER)


@api.post("/step")
def step():
    return ""


@api.post("/start")
def test(data: ExecuteRequest):
    # raw_petri_net, im, fm = from_region(data)
    #
    # graph_obj = graphviz_visualization(
    #     raw_petri_net, "png", initial_marking=im, final_marking=fm
    # )
    # graph_obj.save("tests/iron_petri.dot")
    #
    # return Response(content=str(raw_petri_net), media_type="text/plain")


    region, net, im, fm, extree, choices = data.to_object()

    return create_response(region, net, im, fm, extree).model_dump(exclude_unset=True, exclude_none=True, exclude_defaults=True)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(api, port=8001)
