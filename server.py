#!/usr/bin/env python3

from sanic import Sanic
from sanic.response import text, html
import jinja2

app = Sanic("My Hello, world app")

app.static("/static", "static")


@app.get("/")
async def hello_world(request):
    return text("Hello, world.")


@app.get("/myron")
async def respond_to_myron(request):
    if "name" in request.args.keys():
        name = request.args["name"][0]
    else:
        name = "Myron"
    print(request.args)
    return html(
        f"<html><body><p style='color: red; font-size: 24'>Hello from {name}!</p></body></html>"
    )


@app.get("/cover")
async def cover(request):
    if "name" in request.args.keys():
        name = request.args["name"][0]
    else:
        name = "NAME"

    templateLoader = jinja2.FileSystemLoader(searchpath="./static/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("index.html")

    response = template.render(name=name)
    return html(response)
