"""
Python API for mesh boolean operations in SALOME
no imports from mesh_boolean_dialog = GUI independent
This file is in charge of everything related to Boolean Operations
and gives directly the .med file to the GUI
"""

import tempfile
from enum import Enum
import salome
from salome.smesh import smeshBuilder
from meshbooleanplugin.mesh_boolean_utils import meshIOConvert
from meshbooleanplugin.vtk import exec_vtk
from meshbooleanplugin.irmb import exec_irmb
from meshbooleanplugin.cork import exec_cork
from meshbooleanplugin.mcut import exec_mcut
from meshbooleanplugin.libigl import exec_libigl
from meshbooleanplugin.cgal import exec_cgal

# Dictionary to track naming increments
_counter = {
  "union_num" : 1,
  "intersection_num" : 1,
  "difference_num" : 1
}

class BooleanMeshAlgorithm(str, Enum):
  """ Enumeration of supported mesh boolean algorithms """
  CGAL = 'CGAL'
  IGL  = 'igl'
  VTK  = 'vtk'
  IRMB = 'irmb'
  CORK = 'cork'
  MCUT = 'mcut'

def runAlgo(algo, operator, mesh_left, mesh_right, result_file):
  """ Asserts the boolean operation to the specific algorithm """
  if algo == BooleanMeshAlgorithm.VTK :
    p = exec_vtk.VTK_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.IRMB :
    p = exec_irmb.IRMB_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.CORK :
    p = exec_cork.cork_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.MCUT :
    p = exec_mcut.mcut_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.IGL :
    p = exec_libigl.libigl_main(operator, mesh_left, mesh_right, result_file)
  elif algo == BooleanMeshAlgorithm.CGAL :
    p = exec_cgal.cgal_main(operator, mesh_left, mesh_right, result_file)
  else:
    raise ValueError("Unknown algorithm!")
  return p

def tmpDir():
  """ Creates a secure temporary directory for computation files """
  return tempfile.TemporaryDirectory(prefix="BooleanMeshCompute_")

def tmpFile(suffix, prefix="BooleanMeshCompute", tmp_path= None):
  """ Generates a temporary file path within the provided directory """
  if tmp_path is None:
    raise RuntimeError("tmpfile() called without tmp_path")
  return tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, dir=tmp_path, delete=False).name


def exportToObj(source, tmp_path):
  """ Converts a SMESH object or a file path into an obj file """
  obj_file = tmpFile(".obj", tmp_path=tmp_path)
  stl_tmp = tmpFile(".stl", tmp_path=tmp_path)

  #Smesh Object
  if hasattr(source, "ExportSTL"):
    try:
      source.ExportSTL(stl_tmp, False)
      meshIOConvert(stl_tmp, obj_file)
      return obj_file
    except Exception as e:
      raise RuntimeError(f"Mesh export failed: {e}") from e

  # if the source is already a file path
  try:
    meshIOConvert(str(source), obj_file)
    return obj_file
  except Exception as e:
    raise RuntimeError(f"Conversion to OBJ failed: {e}") from e

# Algorithms aliases for easier access
CGAL = BooleanMeshAlgorithm.CGAL
IGL = BooleanMeshAlgorithm.IGL
VTK = BooleanMeshAlgorithm.VTK
IRMB = BooleanMeshAlgorithm.IRMB
CORK = BooleanMeshAlgorithm.CORK
MCUT = BooleanMeshAlgorithm.MCUT

#Divide the jobs that loadResult does in mesh_boolean_dialog.py
def convertAlgorithmResult(algo, med_file):
  """ Converts the output into a proper MED file that can be read by SALOME """
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


def resetCounter():
  """ Resets the naming counters for automatic object naming """
  for key, value in _counter.items():
    _counter[key] = 1

#what CreateMeshesFromMed does in mesh_boolean_dialog.py
def importMedToSmesh(med_file, operator_name = None, name = None):
  """Imports a MED file into the SALOME SMESH study """
  smesh = smeshBuilder.New()
  smesh.UpdateStudy()

  try:
    meshes, _ = smesh.CreateMeshesFromMED(med_file)
  except Exception as e:
    raise RuntimeError(f"Error importing result: {e}") from e

  if not meshes:
    raise RuntimeError("MED result file not found or empty")

  mesh = meshes[0]

  #The user can set the name manually
  if name :
    smesh.SetName(mesh, name)
  #if name = None automatically set the file names
  else:
    if operator_name is None:
      raise RuntimeError("No operator name defined")
    operator = operator_name.lower()
    if operator == 'union' :
      auto_name = f"{operator_name}_{_counter['union_num']}"
      _counter["union_num"] += 1
    elif operator == 'intersection' :
      auto_name = f"{operator_name}_{_counter['intersection_num']}"
      _counter["intersection_num"]+= 1
    else :
      auto_name = f"{operator_name}_{_counter['difference_num']}"
      _counter["difference_num"] +=1

    smesh.SetName(mesh, auto_name)

  try:
    salome.sg.updateObjBrowser() #Files appear in the Object browser
  except Exception:
    pass

  return mesh

def booleanOperation(operator_name, mesh_left, mesh_right, algo, name = None, worker=None):
  """
  Main function for boolean operations
  Handles temporary directory lifecycle, file conversion, execution and SALOME import
  """

  # We now take care of everything related to temporary files management in this fonction rather than in the GUI
  with tmpDir() as tmp_path:
    # the with assures that the directory is deleted after the compute or if there is an exception
    print(f"Temporary directory created: {tmp_path}")
    # Convert left and right

    objL = exportToObj(mesh_left, tmp_path)
    objR = exportToObj(mesh_right, tmp_path)

    med_result = tmpFile(".med", tmp_path=tmp_path)

    # call runAlgo
    process = runAlgo(algo,
                      operator_name.lower(),
                      objL,
                      objR,
                      med_result
      )
    if worker is not None:
      worker.process = process
    # Wait the end of the process if there is one
    if process :
      rc = process.wait()
      if rc != 0:
        if worker and not worker._isRunning:
          print("Process killed by user")
          return None
        raise RuntimeError("Boolean operation ended in error")

    if worker and not worker._isRunning:
      return None

    #Convert the result
    convertAlgorithmResult(algo, med_result)

    #Import in SALOME
    result_mesh = importMedToSmesh(med_result, operator_name = operator_name, name = name)
    print("End of compute, temporary directory will be erased")
    return result_mesh


#Mesh boolean operations that can be called in terminal
def Union(mesh_left, mesh_right, algo, name = None):
  """ Performs a Union operation between two meshes """
  return booleanOperation("Union", mesh_left, mesh_right, algo, name = name)

def Difference(mesh_left, mesh_right, algo, name = None):
  """ Performs a Difference operation (left minus right) """
  return booleanOperation("Difference", mesh_left, mesh_right, algo, name = name)

def Intersection(mesh_left, mesh_right, algo, name = None):
  """ Performs an Intersection operation between two meshes """
  return booleanOperation("Intersection", mesh_left, mesh_right, algo, name = name)
