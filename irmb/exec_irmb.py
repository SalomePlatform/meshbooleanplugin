from meshbooleanplugin.mesh_boolean_utils import execCommand, meshIOConvert

def perform_boolean_operation(mesh1_path, mesh2_path, operation, output_path):
  import subprocess
  import os
  import time
  RED = '\033[91m'
  RESET = '\033[0m"'

  cwd = os.getcwd()
  if not os.path.isabs(output_path):
    output_path = os.path.join(cwd, output_path)
  obj_output_path = os.path.splitext(output_path)[0] + ".obj"
  if (operation == "difference"):
      operation = "subtraction"
  if 'IRMB_ROOT_DIR' in os.environ:
    binary_path = os.path.join(os.environ["IRMB_ROOT_DIR"], "bin", "mesh_booleans")
  else:
    binary_path = os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh", "meshbooleanplugin", "irmb", "mesh_booleans")
  command = [binary_path, operation, mesh1_path, mesh2_path, obj_output_path]

  try:
    start_time = time.time()
    execCommand(command)
    end_time = time.time()
  except Exception as e:
    raise

  meshIOConvert(obj_output_path, output_path)
  return end_time - start_time

def IRMB_main(operation, fn1, fn2, out_name):
    return perform_boolean_operation(fn1, fn2, operation, out_name)
