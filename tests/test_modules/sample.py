from typing import Optional

from ellar.common import (
    ApplicationModule,
    Body,
    Controller,
    Module,
    ModuleRouter,
    Put,
    Ws,
    WsRoute,
    exception_handler,
    middleware,
    on_app_init,
    on_app_started,
    on_shutdown,
    on_startup,
    template_filter,
    template_global,
)
from ellar.core import App, Config
from ellar.core.connection import WebSocket
from ellar.core.modules import ModuleBase
from ellar.di import ProviderConfig

from ..schema import Item, User


class UserService:
    def __init__(self):
        self.user = User(username="username", full_name="full_name")


class AnotherUserService(UserService):
    pass


@Controller(
    "/items/{orgID:int}",
    tag="Item",
    description="Sample Controller",
    external_doc_url="https://test.com",
    external_doc_description="Find out more here",
)
class SampleController:
    @Put("/{item_id:uuid}")
    async def update_item(
        self,
        *,
        item_id: int,
        item: Item,
        user: User,
        importance: int = Body(gt=0),
        q: Optional[str] = None
    ):
        results = {
            "item_id": item_id,
            "item": item,
            "user": user,
            "importance": importance,
        }
        if q:
            results.update({"q": q})
        return results

    @WsRoute("/websocket")
    async def websocket_test(self, *, web_socket: WebSocket = Ws()):
        await web_socket.accept()
        await web_socket.send_json({"message": "Websocket okay"})
        await web_socket.close()


mr = ModuleRouter("/mr")


@mr.Get("/get")
def get_mr():
    return {"get_mr", "OK"}


@mr.Post("/post")
def post_mr():
    return {"post_mr", "OK"}


class ModuleBaseExample(ModuleBase):
    @exception_handler(404)
    async def exception_404(cls, request, exc):
        pass

    @middleware("http")
    async def middleware(cls, request, call_next):
        response = await call_next(request)
        return response

    @template_global()
    def some_template_global(cls, n):
        pass

    @template_filter()
    def some_template_filter(cls, n):
        pass

    @on_app_init
    def on_app_init_handler(cls, config: Config):
        pass

    @on_app_started
    def on_app_started_handler(cls, app: App):
        pass

    @on_startup
    async def on_startup_handler(cls):
        pass

    @on_shutdown
    def on_shutdown_handler(cls):
        pass


ModuleBaseExample2 = type("ModuleBaseExample2", (ModuleBaseExample,), {})

SampleModule = Module(
    controllers=(SampleController,),
    routers=(mr,),
    providers=(
        UserService,
        ProviderConfig(AnotherUserService, use_value=AnotherUserService()),
    ),
)(ModuleBaseExample2)


@ApplicationModule(
    modules=(SampleModule,),
)
class SampleApplicationModule(ModuleBase):
    @exception_handler(404)
    async def exception_404_override(cls, request, exc):
        pass