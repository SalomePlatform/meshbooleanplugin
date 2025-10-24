from meshbooleanplugin.mesh_boolean_utils import execCommand, meshIOConvert

def perform_boolean_operation(mesh1_path, mesh2_path, operation, output_path):
  import subprocess
  import os
  import time
  import platform
  RED = '\033[91m'
  RESET = '\033[0m"'

  cwd = os.getcwd()
  if not os.path.isabs(output_path):
    output_path = os.path.join(cwd, output_path)

  new_output_path = output_path[:-3] + 'off'
  if platform.system() == "Windows" :
    binary_path = "exec_cgal.exe"
  else:
    if 'CGAL_ROOT_DIR' in os.environ:
      binary_path = os.path.join(os.environ["CGAL_ROOT_DIR"], "bin", "exec_cgal")
    else:
      binary_path = os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh", "meshbooleanplugin", "cgal", "exec_cgal")

  try:
    command = [binary_path, operation, mesh1_path, mesh2_path, new_output_path]
    p = execCommand(command)
  except Exception as e:
    raise
  return p

#same convert_result fonction used for every algorithm
def convert_result(med_path):
  output_path = med_path[:-3] + 'off'
  meshIOConvert(output_path, med_path)

def cgal_main(operation, fn1, fn2, out_name):
  p = perform_boolean_operation(fn1, fn2, operation, out_name)
  return p
