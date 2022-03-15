# Geoprocessing_Python (Sentinel-2 Preprocess Workflow)
## Using GDAL and Object Oriented Progamming

[![PyPI - Python](https://img.shields.io/pypi/pyversions/iconsdk?logo=pypi)](https://pypi.org/project/iconsd)

The script convert jp2 files into GeoTiffs. The latter is resampled in 10m spatial resolution and reprojected to pseudomercator (3857) having the potential to be clippedto a specific bounding box given by the user. It also generated several vegetation indices such as  .
- NDVI
- NDWI
- PSRI
- SAVI

Last but not least, it produces a binary cloud mask dedicated to vegetation existence.

It is recommended to install GDAL (osgeo) using conda
```sh
conda install GDAL
```

## License


