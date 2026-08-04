#include "projection.h"
#include "layout.h"
#include <cmath>
#include <fstream>

std::vector<Node2D> project(const std::vector<Node>& nodes,
                             const Viewpoint& vp) {
    double nx = vp.vx, ny = vp.vy, nz = vp.vz;
    double v_len = std::sqrt(nx*nx + ny*ny + nz*nz);
    if (v_len > 1e-8) {
        nx /= v_len;
        ny /= v_len;
        nz /= v_len;
    }

    double ux, uy, uz;
    if (std::abs(ny) > 0.99) {
        ux = 1; uy = 0; uz = 0;
    } else {
        double len = std::sqrt(nz*nz + nx*nx);
        ux = -nz / len;
        uy = 0;
        uz = nx / len;
    }
    double vx = ny*uz - nz*uy;
    double vy = nz*ux - nx*uz;
    double vvz = nx*uy - ny*ux;

    std::vector<Node2D> result;
    for (const auto& node : nodes) {
        Node2D n2d;
        n2d.id = node.id;
        n2d.bipartite = node.bipartite;
        n2d.u = node.x*ux + node.y*uy + node.z*uz;
        n2d.v = node.x*vx + node.y*vy + node.z*vvz;
        result.push_back(n2d);
    }
    return result;
}

void saveProjections(const std::vector<std::vector<Node2D>>& projections,
                     const std::string& path) {
    std::ofstream file(path);
    file << "viewpoint_id,node_id,bipartite,u,v\n";
    for (int i = 0; i < (int)projections.size(); i++) {
        for (const auto& n : projections[i]) {
            file << i << ","
                 << n.id << ","
                 << n.bipartite << ","
                 << n.u << ","
                 << n.v << "\n";
        }
    }
}