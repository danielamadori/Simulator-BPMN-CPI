from fastapi import FastAPI, Request, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from converter.spin import create_pnml_from_region
from converter.test_bpmn import region_to_bpmn, Region, _region_info
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


@api.post("/test")
def test(data: RegionModel):
    pnml = create_pnml_from_region(data)
    with open("iron.pnml", "w+") as f:
        f.write(pnml)

    petri_net, im, fm = import_net_from_string(pnml)
    graph_obj = graphviz_visualization(
        petri_net, "png", initial_marking=im, final_marking=fm
    )
    graph_obj.save("tests/iron_petri.dot")

    # return _region_info
    return Response(content=str(petri_net), media_type="text/plain")
    # return Response(content=region_to_bpmn(data), media_type="application/xml")
