from aiogram import Router

from . import (
    commands,
    echo,
)

def get_routers() -> list[Router]:
    return [
        commands.router,
        echo.router,
    ]