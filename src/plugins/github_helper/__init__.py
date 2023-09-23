from nonebot import get_driver

from .config import Config
from . import webhook  # noqa: F401

global_config = get_driver().config
config = Config.parse_obj(global_config)

# sub_plugins = nonebot.load_plugins(
#     str(Path(__file__).parent.joinpath("plugins").resolve())
# )
