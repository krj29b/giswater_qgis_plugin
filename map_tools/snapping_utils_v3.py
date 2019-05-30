"""
/***************************************************************************
        begin                : 2016-08-16
        copyright            : (C) 2016 by BGEO SL
        email                : vicente.medina@gits.ws
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from builtins import object

# -*- coding: utf-8 -*-
try:
    from qgis.core import Qgis
except ImportError:
    from qgis.core import QGis as Qgis

from qgis.gui import QgsMapCanvas
from qgis.core import QgsProject, QgsSnappingUtils, QgsPointLocator, QgsTolerance


class SnappingConfigManager(object):

    def __init__(self, iface):
        """ Class constructor """

        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.layer_arc = None
        self.layer_connec = None
        self.layer_node = None
        self.previous_snapping = None
        self.controller = None

        # Snapper
        self.snapper = self.get_snapper()
        proj = QgsProject.instance()
        proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')


    def set_layers(self, layer_arc_man, layer_connec_man, layer_node_man, layer_gully_man=None):

        self.layer_arc_man = layer_arc_man
        self.layer_connec_man = layer_connec_man
        self.layer_node_man = layer_node_man
        self.layer_gully_man = layer_gully_man


    def get_snapping_options(self):
        """ Function that collects all the snapping options and put it in an array """

        globalSnappingConfig = QgsProject.instance().snappingConfig()
        return globalSnappingConfig



    def store_snapping_options(self):
        """ Store the project user snapping configuration """

        # Get an array containing the snapping options for all the layers
        self.previous_snapping = self.get_snapping_options()


    def clear_snapping(self):
        """ Removing snap """

        QgsProject.instance().blockSignals(True)
        layers = self.controller.get_layers()
        # Loop through all the layers in the project
        for layer in layers:
            QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.All, 15, QgsTolerance.Pixels)
        QgsProject.instance().blockSignals(False)
        #QgsProject.instance().snapSettingsChanged.emit()


    def snap_to_node(self):
        """ Set snapping to 'node' """

        QgsProject.instance().blockSignals(True)
        for layer in self.layer_node_man:
            QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Edge, 15, QgsTolerance.Pixels)
        QgsProject.instance().blockSignals(False)
        QgsProject.instance().snapSettingsChanged.emit()


    def snap_to_connec_gully(self):
        """ Set snapping to 'connec' and 'gully' """

        QgsProject.instance().blockSignals(True)
        for layer in self.layer_connec_man:
            QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Edge, 15, QgsTolerance.Pixels)
        if self.layer_gully_man:
            for layer in self.layer_gully_man:
                QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.Edge, 15, QgsTolerance.Pixels)
        QgsProject.instance().blockSignals(False)
        QgsProject.instance().snapSettingsChanged.emit()


    def snap_to_layer(self, layer):
        """ Set snapping to @layer """

        if layer is None:
            return
        QgsSnappingUtils.LayerConfig(layer, QgsPointLocator.All, 15, QgsTolerance.Pixels)


    def apply_snapping_options(self, snappings_options):
        """ Function that restores the previous snapping """

        QgsProject.instance().blockSignals(True)

        if snappings_options:
            QgsProject.instance().setSnappingConfig(snappings_options)

        QgsProject.instance().blockSignals(False)


    def recover_snapping_options(self):
        """ Function to restore user configuration """
        self.apply_snapping_options(self.previous_snapping)


    def check_node_group(self, snapped_layer):
        """ Check if snapped layer is in the node group """
        if snapped_layer in self.layer_node_man:
            return 1


    def check_connec_group(self, snapped_layer):
        """ Check if snapped layer is in the connec group """
        if snapped_layer in self.layer_connec_man:
            return 1


    def check_gully_group(self, snapped_layer):
        """ Check if snapped layer is in the gully group """
        if self.layer_gully_man:
            if snapped_layer in self.layer_gully_man:
                return 1


    def get_snapper(self):
        """ Return snapper """
        snapper = QgsMapCanvas.snappingUtils(self.canvas)

        return snapper
