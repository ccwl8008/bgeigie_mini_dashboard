from fastapi.templating import Jinja2Templates

from app.config import settings

templates = Jinja2Templates(directory="app/templates")

# Todos los templates pueden usar {{ base_path }} para que los enlaces
# funcionen tanto en la raiz del dominio como en un subdirectorio
# (ej. https://cybersoft.com/BGeigie via BASE_PATH=/BGeigie).
templates.env.globals["base_path"] = settings.BASE_PATH
