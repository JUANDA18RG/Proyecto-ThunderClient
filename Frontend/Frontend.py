import asyncio
import json

import httpx
import reflex as rx

from .api import product_router
from .model import Product

DEFAULT_BODY = """{
    "code":"",
    "label":"",
    "image":"/favicon.ico",
    "quantity":0,
    "category":"",
    "seller":"",
    "sender":""
}"""

URL_OPTIONS = {
    "GET": "http://127.0.0.1:8001/products",
    "POST": "http://127.0.0.1:8001/products",
    "PUT": "http://127.0.0.1:8001/products/{pr_id}",
    "DELETE": "http://127.0.0.1:8001/products/{pr_id}",
}


class State(rx.State):
    """The app state."""

    products: list[Product] = []
    _db_updated: bool = False

    async def load_product(self):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.get(URL_OPTIONS["GET"])
                if res.status_code == 200:
                    self.products = res.json()
            except httpx.RequestError as exc:
                print(f"An error occurred while requesting {
                      exc.request.url!r}.")
            except httpx.HTTPStatusError as exc:
                print(f"Error response {exc.response.status_code} while requesting {
                      exc.request.url!r}.")
        yield State.reload_product

    @rx.background
    async def reload_product(self):
        while True:
            await asyncio.sleep(2)
            if self.db_updated:
                async with self:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        try:
                            res = await client.get(URL_OPTIONS["GET"])
                            if res.status_code == 200:
                                self.products = res.json()
                        except httpx.RequestError as exc:
                            print(f"An error occurred while requesting {
                                  exc.request.url!r}.")
                        except httpx.HTTPStatusError as exc:
                            print(f"Error response {exc.response.status_code} while requesting {
                                  exc.request.url!r}.")
                    self._db_updated = False

    @rx.var
    def db_updated(self):
        return self._db_updated

    @rx.var
    def total(self):
        return len(self.products)


class QueryState(State):
    body: str = DEFAULT_BODY
    response_code: str = ""
    response: str = ""
    method: str = "GET"
    url_query: str = URL_OPTIONS["GET"]  # URL por defecto
    query_options = list(URL_OPTIONS.keys())

    def update_method(self, value):
        # Actualiza la URL automáticamente al cambiar el método.
        self.method = value
        if self.url_query == "":
            self.url_query = URL_OPTIONS[value]

    def set_url_query(self, value):
        # Actualiza la URL desde el input.
        self.url_query = value

    def set_body(self, value):
        self.body = value

    @rx.var
    def need_body(self):
        return self.method in ["POST", "PUT"]

    @rx.var
    def f_response(self):
        return f"""```json\n{self.response}\n```"""

    def clear_query(self):
        self.url_query = URL_OPTIONS["GET"]
        self.method = "GET"
        self.body = DEFAULT_BODY

    async def send_query(self):
        # Usa la URL ingresada en el input.
        url = self.url_query
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                match self.method:
                    case "GET":
                        res = await client.get(url)
                    case "POST":
                        res = await client.post(url, data=self.body)
                    case "PUT":
                        res = await client.put(url, data=self.body)
                    case "DELETE":
                        res = await client.delete(url)
                    case _:
                        res = None
                self.response_code = res.status_code
                if self.response_code == 200:
                    self.response = json.dumps(res.json(), indent=2)
                    self._db_updated = True
                else:
                    self.response = res.content.decode()
            except httpx.RequestError as exc:
                self.response = f"An error occurred while requesting {
                    exc.request.url!r}."
            except httpx.HTTPStatusError as exc:
                self.response = f"Error response {
                    exc.response.status_code} while requesting {exc.request.url!r}."


def data_display():
    return rx.vstack(
        rx.heading(State.total, " productos encontrados",
                   size="lg", margin_bottom="1rem", color="cyan"),
        rx.foreach(State.products, render_product),
        rx.spacer(),
        width="40vw",
        height="100%",
        padding="1rem",
        border="solid 1px #00FFFF",
        border_radius="8px",
        box_shadow="0 4px 8px rgba(0, 255, 255, 0.5)",
        background_color="#1a1a1a",
    )


def render_product(product: Product):
    return rx.hstack(
        rx.image(src=product["image"], height="100px",
                 width="100px", border_radius="8px"),
        rx.text(f"({product['code']}) {product['label']}",
                width="20vw", font_weight="bold", color="lime"),
        rx.vstack(
            rx.text("Stock:", product["quantity"], color="magenta"),
            rx.text("Categoría:", product["category"], color="magenta"),
            spacing="1",  # Ajustado a un valor permitido
            width="10vw",
        ),
        rx.vstack(
            rx.text("Vendedor:", product["seller"], color="magenta"),
            rx.text("Remitente:", product["sender"], color="magenta"),
            spacing="1",  # Ajustado a un valor permitido
            width="10vw",
        ),
        rx.spacer(),
        border="solid 1px #00FFFF",
        border_radius="8px",
        padding="1rem",
        margin_bottom="1rem",
        width="100%",
        background_color="#2a2a2a",
    )


def query_form():
    return rx.vstack(
        rx.hstack(
            rx.text("Consulta:", font_weight="bold", color="cyan"),
            rx.select(
                ["GET", "POST", "PUT", "DELETE"],
                # Asegura que refleje el estado actual.
                value=QueryState.method,
                on_change=QueryState.update_method,
                background_color="#1a1a1a",
                color="cyan",
                border="solid 1px #00FFFF",
            ),
            rx.input(
                value=QueryState.url_query,
                # Actualiza el estado al cambiar.
                on_change=QueryState.set_url_query,
                width="30vw",
                background_color="#1a1a1a",
                color="cyan",
                border="solid 1px #00FFFF",
            ),
        ),
        rx.text("Cuerpo de la consulta:",
                font_weight="bold", margin_top="1rem", color="cyan"),
        rx.text_area(
            value=QueryState.body,
            height="20vh",
            width="100%",
            on_change=QueryState.set_body,
            background_color="#1a1a1a",
            color="cyan",
            border="solid 1px #00FFFF",
        ),
        rx.hstack(
            rx.button("Limpiar", on_click=QueryState.clear_query,
                      color_scheme="red"),
            rx.button("Enviar", on_click=QueryState.send_query,
                      color_scheme="green"),
        ),
        rx.divider(orientation="horizontal", border="solid 1px #00FFFF",
                   width="100%", margin_y="1rem"),
        rx.hstack(
            rx.text("Estado: ", QueryState.response_code, font_weight="bold", color="cyan"), rx.spacer(), width="100%"
        ),
        rx.container(
            rx.markdown(
                QueryState.f_response,
                language="json",
                height="30vh",
                padding="1rem",
                border="solid 1px #00FFFF",
                border_radius="8px",
                box_shadow="0 4px 8px rgba(0, 255, 255, 0.5)",
                overflow="auto",  # Evita el desbordamiento
                background_color="#1a1a1a",
                color="cyan",
            ),
            width="100%",  # Asegura que el contenedor ocupe todo el ancho disponible
        ),
        width="100%",
        padding="2rem",
        border="solid 1px #00FFFF",
        border_radius="8px",
        box_shadow="0 4px 8px rgba(0, 255, 255, 0.5)",
        background_color="#1a1a1a",
    )


def index() -> rx.Component:
    return rx.hstack(
        rx.spacer(),
        data_display(),
        rx.spacer(),
        rx.divider(orientation="vertical", border="solid 1px #00FFFF"),
        query_form(),
        rx.spacer(),
        height="100vh",
        width="100vw",
        spacing="2",
        padding="2rem",
        background_color="#0a0a0a",
    )


app = rx.App()
app.add_page(index, on_load=State.load_product)

app.api.include_router(product_router)
