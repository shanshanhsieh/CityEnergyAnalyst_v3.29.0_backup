# -*- coding: utf-8 -*-
"""
Data required for Slave from Master
This File sets all variables for the slave optimization, that have to be set by the Master
"""

import numpy as np

__author__ = "Thuy-An Nguyen"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SlaveData(object):
    def __init__(self):
        # Name the file which should be loaded:
        self.number_of_buildings_district_scale_heating = 0  # number of buildings connected to DHN
        self.number_of_buildings_district_scale_cooling = 0  # number of buildings connected to DCN
        self.total_csv_name_heating = ""
        self.total_csv_name_cooling = ""
        self.DCN_barcode = ""  # barcode of 0s and 1s indicating which buildings are connected to DCN
        self.DHN_barcode = ""  # barcode of 0s and 1s identifying which buildings are connected to DHN
        self.individual_number = ""  # unique identifier of individual in generation
        self.generation_number = ""  # unique identifier of generation
        self.debug = False  # activates debugging behavior in some scripts inside the optimization
        self.num_total_buildings = 0  # total number of buildings in identified district
        self.DHN_exists = False  # boolean showing if a DHN exists in this district
        self.DCN_exists = False  # boolean showing if a DCN exists (is investigated) in this district
        self.technologies_cooling_allowed = None  # list of cooling technologies allowed in this optimization run
        self.technologies_heating_allowed = None  # list of heating technologies allowed in this optimization run
        self.individual_with_names_dict = {}
        self.building_names_all = []
        self.building_names_heating = []
        self.building_names_cooling = []
        self.building_names_electricity = []
        self.buildings_district_scale_to_district_heating = "nan"
        self.buildings_district_scale_to_district_cooling = "nan"
        self.DH_network_summary_individual = None
        self.DC_network_summary_individual = None

        # HEATING TECHNOLOGIES
        # NG fired cogen
        self.CC_on = 0
        self.CCGT_SIZE_W = 0.0
        self.CCGT_SIZE_electrical_W = 0.0

        # Wet biomass cogen
        self.Furnace_wet_on = 0
        self.WBFurnace_Q_max_W = 0.0
        self.WBFurnace_electrical_W = 0.0

        # Dry biomass cogen
        self.Furnace_dry_on = 0
        self.DBFurnace_Q_max_W = 0.0
        self.DBFurnace_electrical_W = 0.0

        # NG-fired Boilers
        self.Boiler_on = 0
        self.Boiler_Q_max_W = 0.0

        self.BoilerPeak_on = 0
        self.BoilerPeak_Q_max_W = 0.0

        self.BackupBoiler_on = 0
        self.BackupBoiler_size_W = 0.0

        # water-source Heat Pump
        self.HPLake_on = 0
        self.HPLake_maxSize_W = 0.0

        # Sewage-source Heat Pump
        self.HPSew_on = 0
        self.HPSew_maxSize_W = 0.0

        # ground-source Heat Pump
        self.GHP_on = 0
        self.GHP_maxSize_W = 0.0  # number of probes

        # data-centre source heat pump
        self.WasteServersHeatRecovery = 0  # server heat
        self.HPServer_maxSize_W = 0.0

        # PVT
        self.PVT_on = 0
        self.PVT_share = 0.0  # share of available building area
        self.A_PVT_m2 = 0.0  # area installed of building area connected

        # PV
        self.PV_on = 0
        self.A_PV_m2 = 0.0
        self.PV_share = 0.0

        self.SC_ET_on = 0
        self.A_SC_ET_m2 = 0.0
        self.SC_ET_share = 0.0

        self.SC_FP_on = 0
        self.A_SC_FP_m2 = 0.0
        self.SC_FP_share = 0.0

        # COOLING TECHNOLOGIES
        # NG-fired trigen
        self.NG_Trigen_on = 0
        self.NG_Trigen_ACH_size_W = 0.0
        self.NG_Trigen_CCGT_size_thermal_W = 0.0
        self.NG_Trigen_CCGT_size_electrical_W = 0.0

        # Water-source vapour compression chillers
        self.WS_BaseVCC_on = 0
        self.WS_BaseVCC_size_W = 0.0

        self.WS_PeakVCC_on = 0
        self.WS_PeakVCC_size_W = 0.0

        # Air-source vapour compression chiller
        self.AS_BaseVCC_on = 0
        self.AS_BaseVCC_size_W = 0.0

        self.AS_PeakVCC_on = 0
        self.AS_PeakVCC_size_W = 0.0

        self.AS_BackupVCC_on = 0
        self.AS_BackupVCC_size_W = 0.0

        # Storage Cooling
        self.Storage_cooling_on = 0
        self.Storage_cooling_size_W = 0.0

        # Storage
        self.STORAGE_SIZE = 1000000.0  # in m^3 - size of hot water storage tank (up to now a random variable)
        self.STORAGE_HEIGHT = 3.0  # in m - height of hot water storage tank
        self.A_storage_outside = self.STORAGE_SIZE / self.STORAGE_HEIGHT + 2 * np.pi * \
                                 (self.STORAGE_SIZE / self.STORAGE_HEIGHT / np.pi) ** 0.5
        # neglecting ground area for heat losses
        self.alpha_loss = 0.0111  # EnergyPRO: 0.3 * 0.037 ; \
        # Saplamidis: 0.293542 # Wh / h= 0( .005 / (math.log10(26/25.0) ) ,
        # from Vassilis-Storage Optimization Code ** ACHTUNG !! CHANGE - SCALES WITH SIZE (?!)
        self.Storage_conv_loss = 0.0111  # losses due to energy conversion from and to storage
        self.T_storage_initial = 10 + 273.0  # initial Storage Temperature
        self.T_storage_zero = 10 + 273.0  # Reference Temperature Storage
        self.Q_in_storage_zero = self.STORAGE_SIZE * 1 / 3600 * 983.21 * 4185 * (
                self.T_storage_zero - self.T_storage_initial)
        self.dT_buffer = 5  # maintain a buffer for "uncertainties", never go below this temperature
        # Storage is initially empty

        self.T_ST_MAX = 90 + 273.0  # Maximum Temperature of storage allowed
        self.T_ST_MIN = 10 + 273.0
