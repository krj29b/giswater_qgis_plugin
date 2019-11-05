"""
This file is part of Giswater 3
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
import json
import os
import subprocess
from collections import OrderedDict
from functools import partial

from .. import utils_giswater
from ..ui_manager import DlgTrace
from .api_parent import ApiParent


class CrmTrace(ApiParent):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control 'Trace' of toolbar 'edit' """
        ApiParent.__init__(self, iface, settings, controller, plugin_dir)


    def manage_trace(self):

        self.controller.log_info("manage_trace")

        # Create the dialog and signals
        self.dlg_trace = DlgTrace()
        self.load_settings(self.dlg_trace)

        # Set listeners
        self.dlg_trace.btn_accept.clicked.connect(self.process)
        self.dlg_trace.btn_cancel.clicked.connect(partial(self.close_dialog, self.dlg_trace))
        self.dlg_trace.rejected.connect(partial(self.save_settings, self.dlg_trace))

        # Fill combo 'exploitation'
        sql = "SELECT name FROM exploitation WHERE active = True ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox(self.dlg_trace, 'cbo_expl', rows, allow_nulls=False)

        # Open dialog
        self.open_dialog(self.dlg_trace)


    def process(self):
        """ Main process """

        # Get selected 'exploitation'
        expl_name = utils_giswater.getWidgetText(self.dlg_trace, 'cbo_expl')
        self.controller.log_info(str(expl_name))

        # Execute synchronization script
        status = self.execute_script(expl_name)

        # Execute PG function 'gw_fct_odbc2pg_main'
        if status:
            self.execute_odbc2pg()


    def execute_script(self, expl_name=None):
        """ Execute synchronization script """

        self.controller.log_info("execute_script")

        if expl_name is None or expl_name == 'null':
            self.controller.show_warning("Any exploitation selected")
            return False

        # Get python synchronization script path
        try:
            param_name = 'crm_daily_script_folderpath'
            script_folder = self.controller.cfgp_system[param_name].value
            script_path = script_folder + os.sep + 'main.py'
        except KeyError as e:
            self.controller.show_warning(str(e))
            return False

        # Check if script path exists
        if not os.path.exists(script_path):
            msg = "File not found: {}. Check config system parameter: '{}'".format(script_path, param_name)
            self.controller.show_warning(msg, duration=20)
            return False

        # Get database current user
        cur_user = self.controller.get_current_user()

        # Execute script
        args = ['python', script_path, expl_name, cur_user, self.schema_name]
        self.controller.log_info(str(args))
        try:
            status = subprocess.call(args)
            self.controller.log_info(str(status))
            msg = "Process executed successfully. Open script .log file to get more details"
            self.controller.show_info(msg, duration=20)
        except Exception as e:
            self.controller.show_warning(str(e))
            return False
        finally:
            return True


    def execute_odbc2pg(self, function_name='gw_fct_odbc2pg_main'):
        """ Execute PG function @function_name """

        self.controller.log_info("execute_odbc2pg")
        exists = self.controller.check_function(function_name)
        if not exists:
            self.controller.show_warning("Function not found", parameter=function_name)
            return False

        # SELECT gw_fct_odbc2pg_main($${"client": {"device":3, "infoType":100, "lang":"ES"},
        # "feature": {}, "data": {"parameters": {"exploitation":"557", "period":"4T", "year":"2019"} } }$$)

        # Get expl_id, year and period from table 'audit_log'
        sql = ("SELECT to_json(log_message) as log_message "
               "FROM utils.audit_log "
               "WHERE fprocesscat_id = 74 "
               "ORDER BY id DESC LIMIT 1")
        row = self.controller.get_row(sql, log_sql=True)
        if not row:
            self.controller.show_warning("Error getting data from audit table", parameter=sql)
            return False

        result = json.loads(row[0])
        self.controller.log_info(str(result))
        if 'expl_id' in result:
            expl_id = result['expl_id']
        if 'year' in result:
            year = result['year']
        if 'period' in result:
            period = result['period']

        # Set function parameters
        client = '"client": {"device":3, "infoType":100, "lang":"ES"}, '
        feature = '"feature": {}, '
        data = f'"data": {{"parameters": {{"exploitation":"{expl_id}", "period":"{period}", "year":"{year}"}}}}'
        body = client + feature + data
        sql = f"SELECT {function_name}($${{{body}}}$$)::text"
        self.controller.log_info(sql)

        # Execute function and show results
        row = self.controller.get_row(sql, commit=True)
        if not row or row[0] is None:
            self.controller.show_warning("Process failed", parameter=sql)
            return False

        # Process result
        result = [json.loads(row[0], object_pairs_hook=OrderedDict)]
        if 'status' not in result[0]:
            self.controller.show_warning("Parameter not found", parameter="status")
            return False
        if 'message' not in result[0]:
            self.controller.show_warning("Parameter not found", parameter="message")
            return False

        geometry_type = ''
        if result[0]['status'] == "Accepted":
            if 'body' in result[0]:
                if 'data' in result[0]['body']:
                    if 'info' in result[0]['body']['data']:
                        if 'geometryType' in result[0]['body']['data']['info']:
                            geometry_type = result[0]['body']['data']['info']['geometryType']
                            self.controller.log_info(geometry_type)

                    if geometry_type != '':
                        self.add_result_memory_layer(geometry_type)
                    else:
                        qtabwidget = self.dlg_trace.tab_main
                        qtextedit = self.dlg_trace.txt_infolog
                        self.populate_info_text(self.dlg_trace, qtabwidget, qtextedit, result[0]['body']['data'])

        message = result[0]['message']['text']
        msg = "Process executed successfully. Read 'Info log' for more details"
        self.controller.show_info(msg, parameter=message, duration=20)

        return True


    def add_result_memory_layer(self, geometry_type):
        """ Add result memory layer """

        self.controller.log_info("add_result_memory_layer")

        srid = self.controller.plugin_settings_value('srid')
        layer_name = "Resultado sincronización"
        #v_layer = QgsVectorLayer(f"{geometry_type}?crs=epsg:{srid}", layer_name, 'memory')
        #self.populate_vlayer(v_layer, data, k, counter)
