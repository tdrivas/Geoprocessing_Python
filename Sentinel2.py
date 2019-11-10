import os
import numpy as np
import logging
from osgeo import gdal, ogr, osr

class Sentinel2_pre_process():
    ''' Pre-processing of Sentinel 2 products '''

    prefixes = [('B02_10m', 'blue'), ('B03_10m', 'green'), ('B04_10m', 'red'), ('B05_20m', 'vre1'), ('B06_20m', 'vre2'), ('B07_20m', 'vre3'), ('B08_10m', 'nir1'), ('B8A_20m', 'nir2'), ('B11_20m', 'swir1'), ('B12_20m', 'swir2'), ('SCL_20m', 'cloud'),('TCI_10m','tci')]


    def __init__(self, base_dir, product):
        self.base_dir = base_dir
        self.product = product
        self.ws = os.path.join(self.base_dir, self.product)
        self.bands = self._get_path_bands()
        logging.info('%s %s %s %s',base_dir,product,self.ws,self.bands)

    def converting_rasters(self):
        ''' batch resampling and convertion rasters for the specified bands - returns nothing '''
        self.logger.info("Start to convert")
        logging.info("Start to convert")
        for p, in_image, out_image, prj_image in self.bands.values():
            logging.info('%s',in_image)
            if '20m' in in_image:
                self.resample_raster(p, in_image, out_image)
            if '10m' in in_image:
                self.raster2geotiff(p, in_image, out_image)

        self.logger.info('Resampling and Transformation of 20_m and 10_m bands of %s, respectively, just finished.', self.product)

    def delete_jp2_files(self):
        ''' Delete jp2 files from SAFE directory - returns nothing '''

        for p, in_image, out_image, prj_image in self.bands.values():
            if os.path.exists(os.path.join(p, out_image)):
                os.remove(os.path.join(p, in_image))
                self.logger.info('Removing of %s.', in_image)

    @staticmethod
    def clip_raster(img_dir, in_ras_file, out_ras_file, **extent):
        ''' Clip a raster (one band) - returns nothing'''

        xmin = extent.get('xmin')
        ymin = extent.get('ymin')
        xmax = extent.get('xmax')
        ymax = extent.get('ymax')

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)

        in_ras = gdal.Open(os.path.join(img_dir, in_ras_file))
        # in_ras = gdal.Open(in_ras_file)
        gt = in_ras.GetGeoTransform()
        inv_gt = gdal.InvGeoTransform(gt)

        off_ulx, off_uly = map(int, gdal.ApplyGeoTransform(inv_gt, xmin, ymax))
        off_lrx, off_lry = map(int, gdal.ApplyGeoTransform(inv_gt, xmax, ymin))
        rows, columns = (off_lry - off_uly) + 1, (off_lrx - off_ulx) + 1

        in_band = in_ras.GetRasterBand(1)

        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(os.path.join(img_dir, out_ras_file), columns, rows, 1, in_band.DataType)
        out_ds.SetProjection(in_ras.GetProjection())
        ulx, uly = gdal.ApplyGeoTransform(gt, off_ulx, off_uly)
        out_gt = list(gt)
        out_gt[0], out_gt[3] = ulx, uly
        out_ds.SetGeoTransform(out_gt)

        out_ds.GetRasterBand(1).WriteArray(in_band.ReadAsArray(off_ulx, off_uly, columns, rows))

        del in_ras
        del in_band
        del out_ds

        Sentinel2_pre_process.logger.info('Clipping of %s has been successfully finished', out_ras_file)

    @staticmethod
    def reproject_raster(img_dir, in_ras_file, out_ras_file):
        ''' Reproject a raster to EPSG:3857 - returns nothing'''

        # TODO, the output raster to have the same resolution as the input
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)

        in_ras = gdal.Open(os.path.join(img_dir, in_ras_file))
        projected_vrt = gdal.AutoCreateWarpedVRT(in_ras, None, srs.ExportToWkt(), gdal.GRA_Bilinear)
        out_ds = gdal.GetDriverByName('GTiff').CreateCopy(os.path.join(img_dir, out_ras_file),  projected_vrt)

        Sentinel2_pre_process.logger.info('Reprojection of %s has been successfully finished', in_ras_file)

        del in_ras
        del projected_vrt
        del out_ds

    @staticmethod
    def raster2geotiff(img_dir, in_ras_file, out_ras_file):
        '''Converts a raster file to GeoTiff - returns nothing'''

        # TODO, you can also use gdal.Wrap

        in_ras = gdal.Open(os.path.join(img_dir, in_ras_file))

        x = os.path.join(img_dir,in_ras_file)
        y = os.path.join(img_dir,out_ras_file)

        if '_TCI' in in_ras_file:
            os.system("gdal_translate -of GTiff "+x+" "+y)
        else:
            in_band = in_ras.GetRasterBand(1)
            driver = gdal.GetDriverByName('GTiff')
            out_ds = driver.Create(os.path.join(img_dir, out_ras_file), in_ras.RasterXSize, in_ras.RasterYSize, 1, in_band.DataType)
            out_ds.SetProjection(in_ras.GetProjection())
            out_ds.SetGeoTransform(in_ras.GetGeoTransform())
            out_band = out_ds.GetRasterBand(1)
            out_band.WriteArray(in_band.ReadAsArray())
            out_band.FlushCache()
            out_band.ComputeStatistics(False)

            del out_band
            del out_ds
            del in_ras

        Sentinel2_pre_process.logger.info('Conversion of %s has been successfully finished', out_ras_file)

    @staticmethod
    def resample_raster(img_dir, in_ras_file, out_ras_file):
        '''Resample a 20m raster file to 10m GeoTiff - returns nothing'''
        if not 'TCI' in in_ras_file:
            in_ras = gdal.Open(os.path.join(img_dir, in_ras_file))
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
            drv.CreateCopy(os.path.join(img_dir, out_ras_file), tmp_ras)

            del drv
            del tmp_ras
            del in_ras

        Sentinel2_pre_process.logger.info('Resampling of %s has been successfully finished.', out_ras_file)

    def _get_path_bands(self):
        '''Get the path for each band - returns a dictionary'''

        try:
            metadta_xml = ET.parse(os.path.join(self.ws, 'MTD_MSIL2A.xml'))
            metadta_xml_root = metadta_xml.getroot()

            bands = {}
            for child in metadta_xml_root.iter('IMAGE_FILE_2A'):
                for prf, b in Sentinel2_pre_process.prefixes:
                    if prf in child.text:
                        image_dir = os.path.dirname(os.path.join(self.ws, child.text))
                        in_image_name = child.text.split('/')[-1] + '.jp2'
                        if '20m' in child.text.split('/')[-1]:
                            out_image_name = child.text.split('/')[-1].split('_20m')[0] + '_10m.tif'
                        else:
                            out_image_name = child.text.split('/')[-1] + '.tif'
                        out_proj_image_name = out_image_name.split('.')[0] + '_prj.' + out_image_name.split('.')[1]
                        bands[b] = [image_dir, in_image_name, out_image_name, out_proj_image_name]
            self.logger.info('Directory pathname for the specified bands of %s have been successfully initialized', self.product)
            return bands

        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.logger.error('Line: %d,\t Type: %s,\t Message: %s', exc_tb.tb_lineno, exc_type, exc_obj)
