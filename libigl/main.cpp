#include <igl/readOBJ.h>
#include <igl/writeOBJ.h>
//#undef IGL_STATIC_LIBRARY
#include <igl/copyleft/cgal/mesh_boolean.h>
#include <igl/opengl/glfw/Viewer.h>

#include <Eigen/Core>
#include <iostream>


Eigen::MatrixXd VA,VB,VC; // Vertices
Eigen::VectorXi J,I;
Eigen::MatrixXi FA,FB,FC; // Faces
igl::MeshBooleanType boolean_type(
  igl::MESH_BOOLEAN_TYPE_UNION);

const char * MESH_BOOLEAN_TYPE_NAMES[] =
{
  "Union",
  "Intersect",
  "Minus",
};

void boolean(std::string out_path)
{
  igl::copyleft::cgal::mesh_boolean(VA,FA,VB,FB,boolean_type,VC,FC,J);
  Eigen::MatrixXd C(FC.rows(),3);
  for(size_t f = 0;f<C.rows();f++)
  {
    if(J(f)<FA.rows())
    {
      C.row(f) = Eigen::RowVector3d(1,0,0);
    }else
    {
      C.row(f) = Eigen::RowVector3d(0,1,0);
    }
  }
  igl::writeOBJ(out_path, VC, FC);
}

int main(int argc, char *argv[])
{
  using namespace Eigen;
  using namespace std;
  if (argc < 5)
  {
      return 1;
  }
  std::string operation = argv[1];

  if (operation == "intersection")
  {
      boolean_type =
          static_cast<igl::MeshBooleanType>(
                  (boolean_type+1)% igl::NUM_MESH_BOOLEAN_TYPES);
  } else if (operation == "difference")
  {
      boolean_type =
          static_cast<igl::MeshBooleanType>(
                  (boolean_type+2)% igl::NUM_MESH_BOOLEAN_TYPES);
  }
  std::string fn1 = argv[2];
  std::string fn2 = argv[3];
  std::string out_path = argv[4];
  igl::readOBJ(fn1,VA,FA);
  igl::readOBJ(fn2,VB,FB);
  boolean(out_path);
}
