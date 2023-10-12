import joblib
import os
from aiohttp import web, ClientSession
from gidgethub import routing
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import sansio

GH_SECRET = "<ENTER YOUR SECRET>"
GH_AUTH = "<ENTER YOUR AUTH TOKEN>"
GH_USERNAME = "<ENTER YOUR USERNAME>"

model = joblib.load('model1.sav')
routes = web.RouteTableDef()
router = routing.Router()

def label_prediction(title, body):
    X = [title +' '+ body]
    label = model.predict(X)
    return label[0]


@router.register("issues", action="opened", )
async def issue_opened_event(event, gh, *arg, **kwargs):
    data = event.data
    title = data["issue"]["title"]
    body = data["issue"]["body"]

    label = label_prediction(title, body)

    url1 = data["issue"]["labels_url"]
    await gh.post(url1, data=[{"name": label}])
    url2 = data["issue"]["comments_url"]
    await gh.post(url2, data={"body": "This issue has been automatically labeled as " + label})

@routes.post("/")
async def main(request):
    body = await request.read()

    secret = GH_SECRET
    oauth_token = GH_AUTH

    event = sansio.Event.from_http(request.headers, body, secret=secret)
    async with ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, GH_USERNAME,
                                  oauth_token=oauth_token)
        await router.dispatch(event, gh)
    return web.Response(status=200)

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)
    web.run_app(app, port=port)