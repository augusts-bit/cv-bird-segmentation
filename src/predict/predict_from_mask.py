# ==============================================================

# Setup and import

# ==============================================================

# To avoid error: NotImplementedError: A UTF-8 locale is required. Got ANSI_X3.4-1968
import locale
# print(locale.getpreferredencoding())

def getpreferredencoding(do_setlocale = True):
    return "UTF-8"
locale.getpreferredencoding = getpreferredencoding

# YOLO and torch (check for correct versions)
import torch, detectron2
from ultralytics import YOLO

# import some common detectron2 utilities
from detectron2.utils.logger import setup_logger
setup_logger()
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog
from detectron2.structures import BoxMode
from detectron2.data.transforms import RandomFlip
from detectron2.engine import HookBase
from detectron2.data import build_detection_train_loader
import detectron2.utils.comm as comm
from detectron2.utils.events import get_event_storage
from detectron2.utils.visualizer import ColorMode
from detectron2.engine import DefaultTrainer

# SAHI
# from sahi.utils.detectron2 import export_cfg_as_yaml
# from sahi.utils.detectron2 import Detectron2TestConstants
# from sahi import AutoDetectionModel
# from sahi.predict import get_sliced_prediction, predict, get_prediction
# from sahi.utils.file import download_from_url
# from sahi.utils.cv import read_image

# Parse arguments
import argparse

# import some common libraries
import numpy as np
import pandas as pd
import os, json, random
import re
import torch
import gc
import shutil
import time

# Other
import sys, os, distutils.core
from torchvision.io import read_image
import cv2
from osgeo import gdal
import geopandas as gpd
from pyproj import CRS
import matplotlib.image as mpimg
import rasterio
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.affinity import scale
import random
import rasterio
from rasterio.windows import from_bounds
from rasterio.windows import Window
from rasterio.transform import from_origin
from rasterio.transform import Affine
import matplotlib.pyplot as plt
from osgeo import gdal

# Install GDAL like this?
import subprocess
import sys

# Import helpers
from helpers.mask2shape import *

from gooey import Gooey, GooeyParser # GUI

# ==============================================================

# Arguments

# ==============================================================

@Gooey(program_name="Vogel Segmentatie", language="dutch", program_description="Segmenteer vogels aan de hand van drone beelden.")
def main():
    def range_limited_float_type(arg):
        """ Type function for argparse - a float within some predefined bounds """
        try:
            f = float(arg)
        except ValueError:
            raise argparse.ArgumentTypeError("Must be a floating point number")
        if f < 0 or f > 1:
            raise argparse.ArgumentTypeError("Ingevoerde overlap of threshold is niet <= " + str(1) + "en >= " + str(0))
        return f

    # Argument parser
    parser = GooeyParser()
    parser.add_argument("mask", type=str, widget="FileChooser", # Mask of orthophoto
                        help="Mask (.npy) waarvan shapes moeten worden gemaakt")
    parser.add_argument("raster", type=str, widget="FileChooser",  # raster of orthophoto
                        help="Raster (zoals een .tif) waarop je de predictie uitvoerde")
    # parser.add_argument("modeltype", type=str, choices=['Mask R-CNN', 'YOLOv8'], default='YOLOv8', widget="Dropdown",
    #                     help="Geef aan welk model je had gebruikt")
    parser.add_argument("model", type=str, widget="DirChooser",  # subfolder name of location of model
                        help="(Model) folder met de categories.json (anders krijg je alleen de soort index)",
                        default=os.getcwd())
    parser.add_argument("output", type=str, widget="DirChooser", default=os.getcwd(),  # Output location
                        help="Locatie voor output shapes")
    args = parser.parse_args()
    
    # Obtain mask
    unique_mask = np.load(args.mask)

    # Get gt
    raster_data_set = gdal.Open(args.raster)
    gt = raster_data_set.GetGeoTransform()
    rastername = os.path.basename(args.raster)

    # Get categories
    if os.path.isfile(os.path.join(str(args.model), 'model_categories.json')):
        with open(os.path.join(str(args.model), 'model_categories.json'), 'r') as json_file:
            categories = json.load(json_file) # make sure the categories are from the training and follow the indexing
    else:
        # This might be incorrect incase different/new species are added in training
        # categories = {'0': 'anders', '1': 'dwergmeeuw', '2': 'grote stern', '3': 'kluut', '4': 'kokmeeuw', '5': 'visdief', '6': 'zwartkopmeeuw'}
        print("Kon geen 'model_categories.json' bestand vinden in aangegeven folder...", "\n"
                 "Het model weet wel de soort index, maar niet bij welke index welke soort hoort... (wordt nu 'Unknown')")
        categories = {}

    print("-----------------------------------")
    print("De mask wordt geconverteerd naar shapefile...")
    print("-----------------------------------")

    # Run mask_to_shape
    mask_to_shape(args, unique_mask, categories, gt, "FromMask", frommask=True)

if __name__ == "__main__":
    main()