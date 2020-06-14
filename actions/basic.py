"""
This file is part of Giswater 3
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSimpleFillSymbolLayer, QgsSymbol

import os
import random
from functools import partial

from ..ui_manager import SelectorUi
from .api_search import ApiSearch
from .api_parent import ApiParent


class Basic(ApiParent):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'basic' """

        self.minor_version = "3.0"
        ApiParent.__init__(self, iface, settings, controller, plugin_dir)
        self.login_file = os.path.join(self.plugin_dir, 'config', 'login.auth')
        self.logged = False
        self.api_search = None


    def set_giswater(self, giswater):
        self.giswater = giswater


    def set_project_type(self, project_type):
        self.project_type = project_type


    def basic_filter_selectors(self):
        """ Button 142: Filter selector """

        selector_values = (f'{{"exploitation": {{"ids":"None", "filter":""}}, "state":{{"ids":"None", "filter":""}}, '
                           f'"hydrometer":{{"ids":"None", "filter":""}}}}')

        # Show form in docker?
        self.controller.init_docker('qgis_form_docker')

        self.dlg_selector = SelectorUi()
        self.load_settings(self.dlg_selector)
        self.get_selector(self.dlg_selector, selector_values)
        if self.controller.dlg_docker:
            self.controller.dock_dialog(self.dlg_selector)
            self.dlg_selector.btn_close.clicked.connect(self.controller.close_docker)
        else:
            self.dlg_selector.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_selector))
            self.dlg_selector.rejected.connect(partial(self.save_settings, self.dlg_selector))
            self.open_dialog(self.dlg_selector, dlg_name='selector', maximize_button=False)

        # Repaint mapzones and refresh canvas
        self.set_style_mapzones()
        self.refresh_map_canvas()


    def basic_api_search(self):
        """ Button 143: ApiSearch """

        if self.api_search is None:
            self.api_search = ApiSearch(self.iface, self.settings, self.controller, self.plugin_dir)

        self.api_search.api_search()

