import os
import numpy as np
import logging
from osgeo import gdal, ogr, osr


def resample_raster(image_path, input_raster, output_raster):
	'''Resample a 20m raster file to 10m GeoTiff '''

	in_ras = gdal.Open(os.path.join(image_path, input_raster))
	in_band = in_ras.GetRasterBand(1)
	out_rows = in_band.YSize * 2
	out_columns = in_band.XSize * 2

	tmp_ras = gdal.GetDriverByName('MEM').Create('', out_columns, out_rows, 1, in_band.DataType)
	tmp_ras.SetProjection(in_ras.GetProjection())
	geotransform = list(in_ras.GetGeoTransform())
	geotransform[1] /= 2
	geotransform[5] /= 2
	tmp_ras.SetGeoTransform(geotransform)
	data = in_band.ReadAsArray(buf_xsize=out_columns, buf_ysize=out_rows)
	out_band = tmp_ras.GetRasterBand(1)
	out_band.WriteArray(data)

	drv = gdal.GetDriverByName('GTiff')
	drv.CreateCopy(os.path.join(image_path, output_raster), tmp_ras)

	del drv
	del tmp_ras
	del in_ras
