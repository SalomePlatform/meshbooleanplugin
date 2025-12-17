#Python API for mesh boolean operations in SALOME
#no imports from mesh_boolean_dialog = GUI independent

import tempfile
from enum import Enum
from salome.kernel import salome
from salome.smesh import smeshBuilder
from meshbooleanplugin.mesh_boolean_utils import meshIOConvert
from meshbooleanplugin.vtk import exec_vtk
from meshbooleanplugin.irmb import exec_irmb
from meshbooleanplugin.cork import exec_cork
from meshbooleanplugin.mcut import exec_mcut
from meshbooleanplugin.libigl import exec_libigl
from meshbooleanplugin.cgal import exec_cgal

#to avoid using global variables
_counter = {
  "union_num" : 1,
  "intersection_num" : 1,
  "difference_num" : 1
}

class BooleanMeshAlgorithm(str, Enum):
  CGAL = 'CGAL'
  IGL  = 'igl'
  VTK  = 'vtk'
  IRMB = 'irmb'
  CORK = 'cork'
  MCUT = 'mcut'

def runAlgo(algo, operator, mesh_left, mesh_right, result_file):
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

def tmpFile(suffix, prefix="BooleanMeshCompute"):
  tempdir = tempfile.gettempdir()
  return tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, dir=tempdir, delete=False).name


def exportToObj(source):
  obj_file = tmpFile(".obj")
  stl_tmp = tmpFile(".stl")

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
def convertAlgorithmResult(algo, med_file):
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
def importMedToSmesh(med_file, operator_name = None, name = None):
  smesh = smeshBuilder.New()
  smesh.UpdateStudy()

  try:
    meshes, _ = smesh.CreateMeshesFromMED(med_file)
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

def booleanOperation(operator_name, mesh_left, mesh_right, algo, name = None):
  # Convert left and right
  objL = exportToObj(mesh_left)
  objR = exportToObj(mesh_right)

  med_result = tmpFile(".med")

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
  convertAlgorithmResult(algo, med_result)

  #Import in SALOME
  return importMedToSmesh(med_result, operator_name = operator_name, name = name)


#Mesh boolean operations that can be called in terminal
def Union(mesh_left, mesh_right, algo, name = None):
  return booleanOperation("Union", mesh_left, mesh_right, algo, name = name)

def Difference(mesh_left, mesh_right, algo, name = None):
  return booleanOperation("Difference", mesh_left, mesh_right, algo, name = name)

def Intersection(mesh_left, mesh_right, algo, name = None):
  return booleanOperation("Intersection", mesh_left, mesh_right, algo, name = name)
