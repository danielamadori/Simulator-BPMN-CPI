from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from converter import test_bpmn

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
def test(json: test_bpmn.Region):
    return json
