# Script by Tyler Hatch, Spring 2020.

import arcpy
import os

arcpy.CheckOutExtension('spatial')
arcpy.env.overwriteOutput = True

initial_points = arcpy.GetParameterAsText(0)
output_folder = arcpy.GetParameterAsText(1)
save_rasters_bool = arcpy.GetParameterAsText(2)
save_polygons_bool = arcpy.GetParameterAsText(3)

with arcpy.da.SearchCursor(initial_points, 'Animal') as searcher:
    animals = []
    for row in searcher:
        animal = row[0]
        if animal not in animals:
            animals.append(animal)

home_range_list = []
core_range_list = []
home_range_raster_list = []
core_range_raster_list = []


for animal in animals:
 
    arcpy.AddMessage('Working on animal {}...'.format(animal))
    
    coyote_points = os.path.join(output_folder, "temp_animal{}.shp".format(animal))    
    arcpy.Select_analysis(initial_points, coyote_points, where_clause='"animal" = \'{}\''.format(animal))

    raster = arcpy.sa.KernelDensity(coyote_points, None,30)
    kernel_raster = os.path.join(output_folder, "kernel_raster_animal{}.tif".format(animal))
    raster.save(kernel_raster)
    
    coyote_points_values = os.path.join(output_folder, "temp2_animal{}.shp".format(animal))
    arcpy.sa.ExtractValuesToPoints(coyote_points, kernel_raster, coyote_points_values)

    kernel_list = []
    
    with arcpy.da.SearchCursor(coyote_points_values, 'RASTERVALU') as searcher:
        for row in searcher:
            kernel_list.append(row[0])
            
    kernel_list.sort(reverse=True)

    num_records = len(kernel_list)
    
    fifty_cut = int(num_records*.5)
    ninety_five_cut = int(num_records*.95)
    
    core_cut = kernel_list[fifty_cut-1]
    home_range_cut = kernel_list[ninety_five_cut-1]

    raster_max = arcpy.GetRasterProperties_management(kernel_raster, "MAXIMUM")
    core_raster = arcpy.sa.Reclassify(kernel_raster, "Value", "0 {0} NODATA;{0} {1} {2}".format(core_cut, raster_max, int(animal[1:])), "DATA")
    home_range_raster = arcpy.sa.Reclassify(kernel_raster, "Value", "0 {0} NODATA;{0} {1} {2}".format(home_range_cut, raster_max, int(animal[1:])), "DATA")
         
    core_raster.save(os.path.join(output_folder, "Core_Raster_{}.tif".format(animal)))
    home_range_raster.save(os.path.join(output_folder, "Home_Range_Raster_{}.tif".format(animal)))

    core_range_raster_list.append(os.path.join(output_folder, "Core_Raster_{}.tif".format(animal)))
    home_range_raster_list.append(os.path.join(output_folder, "Home_Range_Raster_{}.tif".format(animal)))

    arcpy.RasterToPolygon_conversion(core_raster, os.path.join(output_folder, "Core_Polygon_{}.shp".format(animal)),"SIMPLIFY", "Value")
    arcpy.RasterToPolygon_conversion(home_range_raster, os.path.join(output_folder, "Home_Range_Polygon_{}.shp".format(animal)),"SIMPLIFY", "Value")

    core_range_list.append(os.path.join(output_folder, "Core_Polygon_{}.shp".format(animal)))
    home_range_list.append(os.path.join(output_folder, "Home_Range_Polygon_{}.shp".format(animal)))

    arcpy.Delete_management(coyote_points)
    arcpy.Delete_management(coyote_points_values)
    arcpy.Delete_management(kernel_raster)

merged_home = arcpy.Merge_management(home_range_list, os.path.join(output_folder, "merged.shp"))
arcpy.Dissolve_management(merged_home, os.path.join(output_folder, "All_Home_Ranges_95.shp"), "gridcode")
arcpy.Delete_management(merged_home)

merged_core = arcpy.Merge_management(core_range_list, os.path.join(output_folder, "merged.shp"))
arcpy.Dissolve_management(merged_core, os.path.join(output_folder, "All_Core_Ranges_50.shp"), "gridcode")
arcpy.Delete_management(merged_core)

if save_polygons_bool == 'False':
    arcpy.Delete_management(home_range_list)
    arcpy.Delete_management(core_range_list)

if not save_rasters_bool == "False":
    arcpy.Delete_management(home_range_raster_list)
    arcpy.Delete_management(core_range_raster_list)