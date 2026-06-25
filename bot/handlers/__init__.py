from aiogram import Router

# echo ВСЕГДА ПОСЛЕДНИЙ
from . import (
    commands,
    callback,
    echo,
)

def get_routers() -> list[Router]:
    return [
        commands.router,
        callback.router,
        echo.router
    ]