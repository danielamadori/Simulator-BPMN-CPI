from fastapi import FastAPI, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from converter.spin import from_region
from pm4py.visualization.petri_net.common.visualize import graphviz_visualization

from model.region import RegionModel
import logging

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
def test(data: RegionModel):
    raw_petri_net, im, fm = from_region(data)

    graph_obj = graphviz_visualization(
        raw_petri_net, "png", initial_marking=im, final_marking=fm
    )
    graph_obj.save("tests/iron_petri.dot")

    return Response(content=str(raw_petri_net), media_type="text/plain")
