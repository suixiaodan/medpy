#!/usr/bin/python

"""Executes the watershed algorithm over images."""

# build-in modules
import argparse
import logging
import os

# third-party modules
import itk
import vtk

# path changes

# own modules
from medpy.core import Logger
import medpy.itkvtk.utilities.itku as itku
import medpy.itkvtk.utilities.vtku as vtku


# information
__author__ = "Oskar Maier"
__version__ = "r0.4, 2011-12-12"
__email__ = "oskar.maier@googlemail.com"
__status__ = "Release"
__description__ = """
                  Applies the watershed segmentation to a number of images with a range
                  of parameters..
                  The resulting image is saved in the supplied folder with the same
                  name as the input image, but with a suffix '_watershed_[parameters]'
                  attached.
                  """

# code
def main():
    # parse cmd arguments
    parser = getParser()
    parser.parse_args()
    args = getArguments(parser)
    
    # prepare logger
    logger = Logger.getInstance()
    if args.debug: logger.setLevel(logging.DEBUG)
    elif args.verbose: logger.setLevel(logging.INFO)
    
    # iterate over input images
    for image in args.images:
        
        # load image as float using ITK
        logger.info('Loading image {} as float using ITK...'.format(image))
        image_type = itk.Image[itk.F, 3]
        reader = itk.ImageFileReader[image_type].New()
        reader.SetFileName(image)
        reader.Update()
        
        logger.debug(itku.getInformation(reader.GetOutput()))
        
        # apply the watershed
        logger.info('Applying watershed...')
        for threshold in args.thresholds:
            # initialize the watershed filter object
            # this is only done once for all level values, as a repeated execution
            # with a lower level value is significantly faster than a complete
            # new execution
            image_watershed = itk.WatershedImageFilter[image_type].New()
            image_watershed.SetInput(reader.GetOutput())
            image_watershed.SetThreshold(threshold)
            
            for level in reversed(sorted(args.levels)): # make sure to start with highest first
                # build output image name
                image_watershed_name = args.folder + '/' + image.split('/')[-1][:-4] + '_watershed'
                image_watershed_name += '_thr{}_lvl{}'.format(threshold, level)
                image_watershed_name += image.split('/')[-1][-4:]
                
                # check if output image exists
                if not args.force:
                    if os.path.exists(image_watershed_name):
                        logger.warning('The output image {} already exists. Skipping this step.'.format(image_watershed_name))
                        continue
                
                logger.info('Watershedding with settings: thr={} / level={}...'.format(threshold, level))
                image_watershed.SetLevel(level)
                image_watershed.Update()
                
                logger.debug(itku.getInformation(image_watershed.GetOutput()))
                
                ######## UL ENABLED VERSION #######
                # pro: everything
                # contra: none

                # save file
                logger.info('Saving watershed image as {}...'.format(image_watershed_name))
                watershed_image_type = itku.getImageType(image_watershed.GetOutput())
                writer = itk.ImageFileWriter[watershed_image_type].New()
                writer.SetFileName(image_watershed_name)
                writer.SetInput(image_watershed.GetOutput())
                writer.Update()
                
                
                ######## VTK CAST VERSION ########
                # pro: more than 65000 labels possible
                # con: only saves to metaIO file format
#                logger.info('Cast to VTK...')
#                watershed_image_type = itku.getImageType(image_watershed.GetOutput())
#                itk_vtk_converter = itk.ImageToVTKImageFilter[watershed_image_type].New()
#                itk_vtk_converter.SetInput(image_watershed.GetOutput())
#                itk_vtk_converter.Update()
#                
#                logger.debug(vtku.getInformation(itk_vtk_converter.GetOutput()))
#                
#                # save file
#                logger.info('Saving watershed image as {}...'.format(image_watershed_name))
#                vtku.saveImageMetaIO(itk_vtk_converter.GetOutput(), image_watershed_name)
                
                ######## RELABEL VERSION #######
                # pro: output file format the same as input file format
                # con: can't work with more than 65000 labels
#                logger.info('Relabel components to be consecutive and cast to ushort...')
#                watershed_image_type = itku.getImageType(image_watershed.GetOutput())
#                watershed_image_dimensions = itk.template(image_watershed.GetOutput())[1][1]
#                image_type_out = itk.Image[itk.US, watershed_image_dimensions]
#                image_relabeled = itk.RelabelComponentImageFilter[watershed_image_type, image_type_out].New()
#                image_relabeled.SetInput(image_watershed.GetOutput())
#                image_relabeled.Update()
#                
#                logger.debug(itku.getInformation(image_relabeled.GetOutput()))
#
#                # save file
#                logger.info('Saving watershed image as {}...'.format(image_watershed_name))
#                writer = itk.ImageFileWriter[image_type_out].New()
#                writer.SetFileName(image_watershed_name)
#                writer.SetInput(image_relabeled.GetOutput())
#                writer.Update()
    
    logger.info('Successfully terminated.')
        
def getArguments(parser):
    "Provides additional validation of the arguments collected by argparse."
    args = parser.parse_args()
    args.thresholds = map(float, args.thresholds.split(','))
    args.levels = map(float, args.levels.split(','))
    return args

def getParser():
    "Creates and returns the argparse parser object."
    parser = argparse.ArgumentParser(description=__description__)

    parser.add_argument('folder', help='The place to store the created images in.')
    parser.add_argument('levels', help='A colon separated list of values to be passed to the levels attribute (e.g. 0.1,0.2).')
    parser.add_argument('thresholds', help='A colon separated list of values to be passed to the threshold attribute (e.g. 0.01,0.05).')
    parser.add_argument('images', nargs='+', help='One or more input images (best in .mhd format).')
    parser.add_argument('-v', dest='verbose', action='store_true', help='Display more information.')
    parser.add_argument('-d', dest='debug', action='store_true', help='Display debug information.')
    parser.add_argument('-f', dest='force', action='store_true', help='Silently override existing output images.')
    
    return parser    
    
if __name__ == "__main__":
    main()        