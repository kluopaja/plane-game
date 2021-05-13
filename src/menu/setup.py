import pygame
from user_dao import UserDao
from game.setup import GameFactory
from graphics.menu_rendering import MenuItemRenderer, MenuListRenderer
from menu.input import MenuInput
from menu.menu_list import MenuListFactory
from game.game_stats import create_results_viewer, create_high_score_viewer
from stats_dao import StatsDao
from game.game import GameOrganizer
from menu.menus import NewGameMenu, AddUserMenu, MainMenu
from user import UserFactory, User
from utils.timing import Clock, sleep_wait

def create_main_menu(screen, event_handler, assets_path, config, database_connection):
    user_dao = UserDao(database_connection)
    user_dao.create(User("default user"))

    game_factory = GameFactory(config, user_dao, event_handler, screen)

    menu_item_renderer = MenuItemRenderer(font_color=config.menu_font_color)
    menu_list_renderer = MenuListRenderer(
        screen, background_color=config.menu_background_color,
        item_spacing=config.menu_item_spacing, item_renderer=menu_item_renderer)
    menu_input = MenuInput(event_handler, config.menu_input_config)

    menu_list_factory = MenuListFactory(menu_list_renderer, menu_input, Clock(20, sleep_wait))

    results_viewer = create_results_viewer(menu_input, screen)

    stats_dao = StatsDao(database_connection)
    game_organizer = GameOrganizer(results_viewer, stats_dao)

    new_game_menu = NewGameMenu(game_factory, menu_list_factory, game_organizer)
    user_factory = UserFactory(user_dao)
    add_user_menu = AddUserMenu(menu_list_factory, user_factory)
    high_score_viewer = create_high_score_viewer(stats_dao, 5,  menu_input, screen)
    return MainMenu(menu_list_factory, new_game_menu, add_user_menu, high_score_viewer)