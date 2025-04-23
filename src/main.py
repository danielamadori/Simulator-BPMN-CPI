from enum import Enum
from fastapi import FastAPI, Request, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from converter.spin import (
    create_pnml_from_region,
    get_place_prop,
    getProps,
    from_region,
)
from src.model.time_spin import PropertiesKeys
from pm4py.objects.petri_net.importer.variants.pnml import import_net_from_string
from pm4py.objects.conversion.bpmn.variants import to_petri_net
from pm4py.objects.conversion.bpmn.variants.to_petri_net import Parameters
from pm4py.visualization.petri_net.common.visualize import graphviz_visualization

from model.region import RegionModel

api = FastAPI()


@api.exception_handler(404)
async def error_to_docs(_, __):
    data = ""
    with open("static/404.html") as f:
        data = f.read()
    return HTMLResponse(data, status_code=status.HTTP_404_NOT_FOUND)


@api.get("/")
def root(request: Request):
    return RedirectResponse("/docs/", status_code=status.HTTP_303_SEE_OTHER)


@api.post("/step")
def step():
    return ""


@api.post("/start")
def test(data: RegionModel):
    # pnml = create_pnml_from_region(data)
    # with open("tests/iron.pnml", "w+") as f:
    #     f.write(pnml)

    # raw_petri_net, im, fm = import_net_from_string(pnml)

    # props, d_match = getProps()
    # spin = DataSPIN(raw_petri_net, props, d_match)
    raw_petri_net, im, fm = from_region(data)

    # data_check = {}

    # for place in raw_petri_net.places:
    #     raw_prop = get_place_prop(place)
    #     prop = {}
    #     for key in raw_prop:
    #         if isinstance(key, Enum):
    #             prop[key.value] = (
    #                 raw_prop[key]
    #                 if not isinstance(raw_prop[key], Enum)
    #                 else raw_prop[key].value
    #             )
    #         else:
    #             prop[key] = (
    #                 raw_prop[key]
    #                 if not isinstance(raw_prop[key], Enum)
    #                 else raw_prop[key].value
    #             )

    #     data_check[place.name] = prop

    # with open("tests/data_json", "w") as f:
    #     output = str(data_check).replace("'", '"').replace("None", "null")

    #     f.write(output)

    graph_obj = graphviz_visualization(
        raw_petri_net, "png", initial_marking=im, final_marking=fm
    )
    graph_obj.save("tests/iron_petri.dot")

    # return _region_info
    return Response(content=str(raw_petri_net), media_type="text/plain")
    # return Response(content=region_to_bpmn(data), media_type="application/xml")
