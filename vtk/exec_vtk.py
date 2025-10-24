#!/usr/bin/env python
import sys
from meshbooleanplugin.mesh_boolean_utils import meshIOConvert
import os
import time

# noinspection PyUnresolvedReferences
# noinspection PyUnresolvedReferences
from vtkmodules.vtkFiltersCore import (
  vtkCleanPolyData,
  vtkTriangleFilter
)
from vtkmodules.vtkFiltersGeneral import vtkBooleanOperationPolyDataFilter
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkIOGeometry import (
  vtkOBJReader,
  vtkSTLWriter
)
from vtkmodules.vtkIOLegacy import vtkPolyDataReader
from vtkmodules.vtkIOPLY import vtkPLYReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader

def ReadPolyData(file_name):
  print("Reading", file_name)
  path, extension = os.path.splitext(file_name)
  extension = extension.lower()
  reader = vtkOBJReader()
  reader.SetFileName(file_name)
  reader.Update()
  poly_data = reader.GetOutput()
  return poly_data

def WriteSTLMesh(mesh, output_file):
  print("Writing", output_file)
  try:
    writer = vtkSTLWriter()
    writer.SetFileName(output_file)
    writer.SetInputData(mesh)
    writer.Write()
    print("WriteSTLMesh: ", output_file, "...done")
  except Exception:
      raise

def boolean_operation(operation, fn1, fn2, out_name):
  start_time = time.time()

  # Read the input meshes
  poly1 = ReadPolyData(fn1)
  if poly1 is None:
    raise IOError(f"Failed to read file: {fn1}")
  tri1 = vtkTriangleFilter()
  tri1.SetInputData(poly1)
  clean1 = vtkCleanPolyData()
  clean1.SetInputConnection(tri1.GetOutputPort())
  clean1.Update()
  input1 = clean1.GetOutput()

  nb_points1 = input1.GetNumberOfPoints()
  print("Number of points input1: ",  nb_points1)
  print("   Input1 bounds: {}".format(input1.GetBounds()))

  poly2 = ReadPolyData(fn2)
  if poly2 is None:
    raise IOError(f"Failed to read file: {fn2}")
  tri2 = vtkTriangleFilter()
  tri2.SetInputData(poly2)
  tri2.Update()
  clean2 = vtkCleanPolyData()
  clean2.SetInputConnection(tri2.GetOutputPort())
  clean2.Update()
  input2 = clean2.GetOutput()

  nb_points2 = input2.GetNumberOfPoints()
  print("Number of points input2: ",  nb_points2)
  print("   Input2 bounds: {}".format(input2.GetBounds()))

  # Read the operation
  booleanFilter = vtkBooleanOperationPolyDataFilter()
  if operation.lower() == 'union':
    booleanFilter.SetOperationToUnion()
  elif operation.lower() == 'intersection':
    booleanFilter.SetOperationToIntersection()
  elif operation.lower() == 'difference':
    booleanFilter.SetOperationToDifference()
  else:
      raise NameError(f"Failed to parse boolean operation {str(operation.lower())}")

  booleanFilter.SetInputData(0, input1)
  booleanFilter.SetInputData(1, input2)
  try:
    booleanFilter.Update()
    result_mesh = booleanFilter.GetOutput()
  except:
    raise RuntimeError

  nb_points = result_mesh.GetNumberOfPoints()
  print("Number of points output: ",  nb_points)
  print("   Ouput bounds: {}".format(result_mesh.GetBounds()))
  if nb_points == 0:
    raise RuntimeError(f"{operation} failed. No points in the computed mesh.")

  new_out_name = out_name[:-3] + "stl"
  try:
    WriteSTLMesh(result_mesh, new_out_name)
  except:
    raise IOError("Could not write the result in the STL file")
  end_time = time.time()
  if not os.path.exists(new_out_name):
    raise RuntimeError("Result has not been written correctly, an error occured during the boolean operation.")

  with open(new_out_name, 'r+') as file:
    content = file.read()
    modified_content = content.replace(',', '.')
    file.seek(0)
    file.truncate()
    file.write(modified_content)
    file.seek(0, 2)

  return end_time - start_time

def convert_result(med_path):
  output_path = med_path[:-3] + "stl"
  meshIOConvert(output_path, med_path)
  return med_path


def VTK_main(operation, fn1, fn2, fnout):
  from meshbooleanplugin.mesh_boolean_utils import execCommand

  current_dir= os.path.dirname(os.path.abspath(__file__))
  run_vtk_path = os.path.join(current_dir, "run_vtk.py")

  new_output_path = os.path.splitext(fnout)[0] + ".stl"
  command = ["python3", run_vtk_path, operation, fn1, fn2, new_output_path]
  print("Running VTK command:", " ".join(command))

  p = execCommand(command)
  return p