#!/usr/bin/env python
import sys
# we use argparse to parse the arguments of the command ligne
import argparse
#import the boolean operation fonction
from exec_vtk import boolean_operation
def main():
    parser = argparse.ArgumentParser(
        description="Perform a boolean operation on two meshes using VTK"
    )
    parser.add_argument("operation", type=str, choices=["union", "intersection", "difference"],
                        help="Boolean operation to perform")
    parser.add_argument("mesh1", type=str, help="Path to the first input mesh")
    parser.add_argument("mesh2", type=str, help="Path to the second input mesh")
    parser.add_argument("output", type=str, help="Path to the output mesh file (.stl or .med)")

    args = parser.parse_args()

    try:
      elapsed = boolean_operation(args.operation, args.mesh1, args.mesh2, args.output)
      print(f"Boolean operation '{args.operation}' completed successfully in {elapsed:.2f} seconds.")
      print(f"Result saved to: {args.output}")
    except Exception as e:
      print("Error during VTK boolean operation:", e)
      sys.exit(1)

if __name__ == "__main__":
  main()