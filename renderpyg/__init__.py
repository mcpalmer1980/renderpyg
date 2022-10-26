'''
Copyright (C) 2020, Michael C Palmer <michaelcpalmer1980@gmail.com>

This file is part of renderpyg

renderpyg is a python package providing higher level features for
pygame. It uses the pygame._sdl2.video API to provide hardware GPU
texture rendering.

renderpyg is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
pytmx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public
License along with renderpyg.

If not, see <http://www.gnu.org/licenses/>.
'''
import os, sys
hide = os.environ.get('PYGAME_HIDE_SUPPORT_PROMPT', False)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame as pg

_version = '0.0.1'
if pg.get_sdl_version()[0] < 2:
    raise SystemExit("This example requires pygame 2 and SDL2.")
if not hide:
    print('renderpy {} running on pygame {} (SDL {}.{}.{}, python {}.{}.{})\n'.format(
            _version, pg.version.ver, *pg.get_sdl_version() + sys.version_info[0:3]))

from .base import (
        fetch_images, load_texture, load_images, scale_rect, scale_rect_ip,
        load_xml_images, sr )
from .sprite import keyfr, keyframes, keyrange
from .sprite import GPUAniSprite as Sprite
from .tilemap import (
        load_tmx, load_tilemap_string, load_tileset, render_tilemap, Tilemap )
from .tfont import TextureFont, NinePatch, round_patch
from .menu import Menu
