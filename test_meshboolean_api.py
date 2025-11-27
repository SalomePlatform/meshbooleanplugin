#  -*- coding: iso-8859-1 -*-
# Copyright (C) 2018-2025  CEA, EDF, OPEN CASCADE
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

import unittest
import mesh_boolean_api

class TestMesh(unittest.TestCase):
  
  test_counter = 0
  def setUp(self):
    # stuff done before launching test: create input meshes
    import salome
    salome.salome_init()
    import GEOM
    from salome.geom import geomBuilder
    from salome.smesh import smeshBuilder
    import math
    import SALOMEDS
    import  SMESH

    geompy = geomBuilder.New()

    O = geompy.MakeVertex(0, 0, 0)
    OX = geompy.MakeVectorDXDYDZ(1, 0, 0)
    OY = geompy.MakeVectorDXDYDZ(0, 1, 0)
    OZ = geompy.MakeVectorDXDYDZ(0, 0, 1)
    box = geompy.MakeBoxDXDYDZ(1, 1, 1)
    geompy.addToStudy( O, 'O' )
    geompy.addToStudy( OX, 'OX' )
    geompy.addToStudy( OY, 'OY' )
    geompy.addToStudy( OZ, 'OZ' )
    geompy.addToStudy( box, 'box' )

    smesh = smeshBuilder.New()
    #smesh.SetEnablePublish( False ) # Set to False to avoid publish in study if not needed or in some particular situations:
                                    # multiples meshes built in parallel, complex and numerous mesh edition (performance)

    box_mesh = smesh.Mesh(box,'box_mesh')
    algo1D = box_mesh.Segment()
    LocalLength = algo1D.LocalLength(0.25,None,1e-07)
    algo2D = box_mesh.Quadrangle(algo=smeshBuilder.QUADRANGLE)
    algo3D = box_mesh.Hexahedron(algo=smeshBuilder.Hexa)
    isDone = box_mesh.Compute()
    box_mesh.CheckCompute()
    
    
    box_mesh_translated = box_mesh.TranslateObjectMakeMesh( box_mesh, [ 0.125, 0.125, 0.125 ], 0, 'box_mesh_translated' )
    
    self.mesh_1 = box_mesh
    self.mesh_2 = box_mesh_translated

    self.algos = {
      'CGAL' : mesh_boolean_api.CGAL,
      'MCUT' : mesh_boolean_api.MCUT,
      'VTK' : mesh_boolean_api.VTK,
      'IGL' : mesh_boolean_api.IGL,
      'CORK' : mesh_boolean_api.CORK,
      'IRMB' : mesh_boolean_api.IRMB 
    }
  
  #Functions to get the expected area of a mesh so we can compare it with the results of our algorithms
  def ComputeExpectedDifference(self):
    return 6

  def ComputeExpectedIntersection(self):
    return 4.59375

  def ComputeExpectedUnion(self):
    return 7.40625

  #Runs the Operation Difference on all the algorithms
  def test_difference(self):
    expected_area = self.ComputeExpectedDifference()
    for algo_name, algo in self.algos.items():
      with self.subTest(algo = algo_name):
        #standard way to use the same test for multiple parameters in unittest
        type(self).test_counter +=1
        result_mesh = mesh_boolean_api.Difference(self.mesh_1, self.mesh_2, algo = algo)
        computed_area = result_mesh.GetArea()
        self.assertAlmostEqual(expected_area, computed_area, places = 5)

  #Runs the Operation Intersection on all the algorithms
  def test_intersection(self):
    expected_area = self.ComputeExpectedIntersection()
    for algo_name, algo in self.algos.items():
      with self.subTest(algo = algo_name):
        type(self).test_counter +=1
        result_mesh = mesh_boolean_api.Intersection(self.mesh_1, self.mesh_2, algo = algo)
        computed_area = result_mesh.GetArea()
        self.assertAlmostEqual(expected_area, computed_area, places = 5)

  #Runs the Operation Union on all the algorithms
  def test_union(self):
    expected_area = self.ComputeExpectedUnion()
    for algo_name, algo in self.algos.items():
      with self.subTest(algo = algo_name):
        type(self).test_counter +=1
        result_mesh = mesh_boolean_api.Union(self.mesh_1, self.mesh_2, algo = algo)
        computed_area = result_mesh.GetArea()
        self.assertAlmostEqual(expected_area, computed_area, places = 5)

  def tearDown(self):
    # stuff done after launching test
    print(f"Total sub-tests ran : {self.test_counter}")
    pass

if __name__ == '__main__':
  # launch all tests
  unittest.main(exit = False)
  
  # or launch only tests specific to the algos installed (by checking environement variable)