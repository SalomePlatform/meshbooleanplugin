#Python API for mesh boolean operations in SALOME
#GUI independent 

import os
import tempfile
import salome
from enum import Enum
from meshbooleanplugin.mesh_boolean_dialog import runAlgo, BooleanMeshAlgorithm
from mesh_boolean_utils import meshIOConvert

from meshbooleanplugin.vtk import exec_vtk
from meshbooleanplugin.irmb import exec_irmb
from meshbooleanplugin.cork import exec_cork
from meshbooleanplugin.mcut import exec_mcut
from meshbooleanplugin.libigl import exec_libigl
from meshbooleanplugin.cgal import exec_cgal

from salome.smesh import smeshBuilder
union_num = 1
intersection_num = 1
difference_num = 1



def TmpFile(suffix, prefix="BooleanMeshCompute"):
  tempdir = tempfile.gettempdir()
  return tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, dir=tempdir, delete=False).name


def ExportToObj(source):
  obj_file = TmpFile(".obj")
  stl_tmp = TmpFile(".stl")

  #Smesh Object
  if hasattr(source, "ExportSTL"):
    try:
      source.ExportSTL(stl_tmp, False)
      meshIOConvert(stl_tmp, obj_file)
      return obj_file
    except Exception as e:
      raise RuntimeError(f"Mesh export failed: {e}")

  #File
  try:
    meshIOConvert(str(source), obj_file)
    return obj_file
  except Exception as e:
    raise RuntimeError(f"Conversion to OBJ failed: {e}")


CGAL = BooleanMeshAlgorithm.CGAL
IGL = BooleanMeshAlgorithm.IGL
VTK = BooleanMeshAlgorithm.VTK
IRMB = BooleanMeshAlgorithm.IRMB
CORK = BooleanMeshAlgorithm.CORK
MCUT = BooleanMeshAlgorithm.MCUT

#Divide the jobs that loadResult does in mesh_boolean_dialog.py
def ConvertAlgorithmResult(algo, med_file):
  if algo == CGAL:
    exec_cgal.convert_result(med_file)
  elif algo == MCUT:
    exec_mcut.convert_result(med_file)
  elif algo == CORK:
    exec_cork.convert_result(med_file)
  elif algo == IRMB:
    exec_irmb.convert_result(med_file)
  elif algo == IGL:
    exec_libigl.convert_result(med_file)
  elif algo == VTK:
    exec_vtk.convert_result(med_file)


#what CreateMeshesFromMed does in mesh_boolean_dialog.py
def ImportMedToSmesh(med_file, operator_name = None, name = None):
  global union_num, intersection_num, difference_num
  smesh = smeshBuilder.New()
  smesh.UpdateStudy()

  try:
    meshes, status = smesh.CreateMeshesFromMED(med_file)
  except Exception as e:
    raise RuntimeError(f"Error importing result: {e}")

  if not meshes:
    raise RuntimeError("MED result file not found or empty")
  
  mesh = meshes[0]
  
  #The user can set the name manually
  if name :
    smesh.SetName(mesh, name)
  #if name = None automatically set the file names
  else: 
    if operator_name is None:
      raise Exception("No operator name defined")
    operator = operator_name.lower()
    if operator == 'union' :
      auto_name = f"{operator_name}_{union_num}"
      union_num += 1
    elif operator == 'intersection' :
      auto_name = f"{operator_name}_{intersection_num}"
      intersection_num += 1
    else :
      auto_name = f"{operator_name}_{difference_num}"
      difference_num +=1

    smesh.SetName(mesh, auto_name)

  try:
    salome.sg.updateObjBrowser() #Files appear in the Object browser
  except Exception:
    pass

  return mesh
 
def BooleanOperation(operator_name, mesh_left, mesh_right, algo, name = None):
  # Convert left and right
  objL = ExportToObj(mesh_left)
  objR = ExportToObj(mesh_right)

  med_result = TmpFile(".med")

  # call runAlgo
  process = runAlgo(algo,
                    operator_name.lower(),
                    objL,
                    objR,
                    med_result
    )

  # Wait the end of the process if there is one
  if process is not None:
    rc = process.wait()
    if rc != 0:
      raise RuntimeError("Boolean operation ended in error")

  #Convert the result
  ConvertAlgorithmResult(algo, med_result)

  #Import in SALOME
  return ImportMedToSmesh(med_result, operator_name = operator_name, name = name)


#Mesh boolean operations that can be called in terminal
def Union(mesh_left, mesh_right, algo, name = None):
  return BooleanOperation("Union", mesh_left, mesh_right, algo, name = name)

def Difference(mesh_left, mesh_right, algo, name = None):
  return BooleanOperation("Difference", mesh_left, mesh_right, algo, name = name)

def Intersection(mesh_left, mesh_right, algo, name = None):
  return BooleanOperation("Intersection", mesh_left, mesh_right, algo, name = name)