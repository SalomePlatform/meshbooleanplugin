#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/Polygon_mesh_processing/IO/polygon_mesh_io.h>
#include <CGAL/Polygon_mesh_processing/corefinement.h>
#include <CGAL/Surface_mesh.h>

#include <iostream>

typedef CGAL::Exact_predicates_exact_constructions_kernel K;
typedef CGAL::Surface_mesh<K::Point_3> Mesh;

namespace PMP = CGAL::Polygon_mesh_processing;

int main(int argc, const char** argv)
{
    const std::string filename1 = argv[2];
    const std::string filename2 = argv[3];

    Mesh mesh1, mesh2;

    if(!PMP::IO::read_polygon_mesh(filename1, mesh1) || !PMP::IO::read_polygon_mesh(filename2, mesh2))
    {
        std::cerr << "Invalid input." << std::endl;
        return 1;
    }

    bool valid_op;
    Mesh result;

    if (!strcmp(argv[1], "union")) {
        valid_op = PMP::corefine_and_compute_union(mesh1, mesh2, result);
    } else if (!strcmp(argv[1], "intersection")) {
        valid_op = PMP::corefine_and_compute_intersection(mesh1, mesh2, result);
    } else {
        valid_op = PMP::corefine_and_compute_difference(mesh1, mesh2, result);
    }

    if(valid_op)
    {
        std::cout << "Union was successfully computed\n";
        CGAL::IO::write_polygon_mesh(argv[4], result, CGAL::parameters::stream_precision(17));
        return 0;
    }

    std::cout << "Union could not be computed\n";
    return 1;
}
