import typing as t

from starlette.testclient import TestClient as TestClient

from ellar.core.factory import AppFactory
from ellar.core.main import App
from ellar.core.modules import ApplicationModuleDecorator, BaseModuleDecorator
from ellar.core.routing import ModuleRouter
from ellar.core.routing.controller import ControllerDecorator
from ellar.di import ProviderConfig


class _TestingModule:
    def __init__(self, app: App) -> None:
        self.app = app

    def get_client(
        self,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
        backend: str = "asyncio",
        backend_options: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> TestClient:
        return TestClient(
            app=self.app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            backend=backend,
            backend_options=backend_options,
            root_path=root_path,
        )


class TestClientFactory:
    @classmethod
    def create_test_module(
        cls,
        controllers: t.Sequence[t.Union[ControllerDecorator, t.Any]] = tuple(),
        routers: t.Sequence[ModuleRouter] = tuple(),
        services: t.Sequence[ProviderConfig] = tuple(),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[str] = None,
        static_folder: str = "static",
    ) -> _TestingModule:
        app = AppFactory.create_app(
            controllers=controllers,
            routers=routers,
            services=services,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
        )
        return _TestingModule(app=app)

    @classmethod
    def create_test_module_from_module(
        cls,
        module: t.Union[t.Type[BaseModuleDecorator], t.Type],
        mock_services: t.Sequence[ProviderConfig] = tuple(),
    ) -> _TestingModule:
        if isinstance(module, ApplicationModuleDecorator):
            if mock_services:
                after_initialisation = module.get_module().get_after_initialisation()

                @after_initialisation
                def _register_services(application: App) -> None:
                    for service in mock_services:
                        if isinstance(service, ProviderConfig):
                            service.register(application.injector.container)

            return _TestingModule(app=AppFactory.create_from_app_module(module))
        app = AppFactory.create_app(modules=(module,), services=mock_services)
        return _TestingModule(app=app)
