#!/usr/bin/env python

###
### This file is generated automatically by SALOME v9.11.0 with dump python functionality
###

import sys
from salome.kernel import salome

salome.salome_init()

import os
sys.path.insert(0, f'{os.path.join(os.environ["PWD"], "samples")}')

###
### SHAPER component
###

from salome.shaper import model

model.begin()
partSet = model.moduleDocument()

### Create Part
Part_1 = model.addPart(partSet)
Part_1_doc = Part_1.document()

### Create Cylinder
Cylinder_1 = model.addCylinder(Part_1_doc, model.selection("VERTEX", "PartSet/Origin"), model.selection("EDGE", "PartSet/OY"), 5, 10)

### Create Box
Box_1 = model.addBox(Part_1_doc, 0, 0, 0, 6, 6, 6)

### Create Sphere
Sphere_1 = model.addSphere(Part_1_doc, model.selection("VERTEX", "PartSet/Origin"), 10)

### Create Translation
Translation_1 = model.addTranslation(Part_1_doc, [model.selection("COMPOUND", "all-in-Sphere_1")], vector = [3, -1, 0], keepSubResults = True)

model.end()

###
### SHAPERSTUDY component
###

model.publishToShaperStudy()
import SHAPERSTUDY
Cylinder_1_1, = SHAPERSTUDY.shape(model.featureStringId(Cylinder_1))
Box_1_1, = SHAPERSTUDY.shape(model.featureStringId(Box_1))
Translation_1_1, = SHAPERSTUDY.shape(model.featureStringId(Translation_1))
###
### SMESH component
###

from salome.kernel import SMESH, SALOMEDS
from salome.smesh import smeshBuilder

smesh = smeshBuilder.New()
#smesh.SetEnablePublish( False ) # Set to False to avoid publish in study if not needed or in some particular situations:
                                 # multiples meshes built in parallel, complex and numerous mesh edition (performance)

cylinder = smesh.Mesh(Cylinder_1_1,'cylinder')
GMSH_2D = cylinder.Triangle(algo=smeshBuilder.GMSH_2D)
Gmsh_Parameters = GMSH_2D.Parameters()
Gmsh_Parameters.SetMinSize( 3 )
Gmsh_Parameters.Set2DAlgo( 2 )
Gmsh_Parameters.SetMaxSize( 3 )
Gmsh_Parameters.SetIs2d( 1 )
cube = smesh.Mesh(Box_1_1,'cube')
status = cube.AddHypothesis(Gmsh_Parameters)
GMSH_2D_1 = cube.Triangle(algo=smeshBuilder.GMSH_2D)
sphere = smesh.Mesh(Translation_1_1,'sphere')
status = sphere.AddHypothesis(Gmsh_Parameters)
GMSH_2D_2 = sphere.Triangle(algo=smeshBuilder.GMSH_2D)
isDone = cylinder.Compute()
isDone = cube.Compute()

smesh.SetName(sphere, 'sphere')
isDone = sphere.Compute()
try:
  sphere.ExportMED( f'{os.path.join(os.environ["PWD"], "samples", "sphere.med")}', 0, 41, 1, sphere, 1, [], '',-1, 1 )
  pass
except:
  print('ExportPartToMED() failed. Invalid file name?')
smesh.SetName(cube, 'cube')
try:
  cube.ExportMED( f'{os.path.join(os.environ["PWD"], "samples", "cube.med")}', 0, 41, 1, cube, 1, [], '',-1, 1 )
  pass
except:
  print('ExportPartToMED() failed. Invalid file name?')
smesh.SetName(cylinder, 'cylinder')
try:
  cylinder.ExportMED( f'{os.path.join(os.environ["PWD"], "samples", "cylinder.med")}', 0, 41, 1, cylinder, 1, [], '',-1, 1 )
  pass
except:
  print('ExportPartToMED() failed. Invalid file name?')


## Set names of Mesh objects
smesh.SetName(GMSH_2D.GetAlgorithm(), 'GMSH_2D')
smesh.SetName(cylinder.GetMesh(), 'cylinder')
smesh.SetName(cube.GetMesh(), 'cube')
smesh.SetName(sphere.GetMesh(), 'sphere')
smesh.SetName(Gmsh_Parameters, 'Gmsh Parameters')


if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()
