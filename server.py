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


@app.post("/file/upload")
async def upload_file(request):
    if request.files:
        if "multicrit_tbl" in request.files:
            csv = request.files.get("multicrit_tbl")
            print(type(csv))

            return text(csv.body.decode())

    return text("Upload successful!")


heading = ("Μέσο", "Διάταξη", "Τιμή", "Διάρκεια", "Άνεση")
data = (("RER", "1", "3", "10", "1"), ("RER", "1", "3", "10", "1"))


@app.get("/table")
async def table(request):
    templateLoader = jinja2.FileSystemLoader(searchpath="./static/")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template("table.html")

    response = template.render(heading=heading, data=data)
    return html(response)
