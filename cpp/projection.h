#pragma once
#include <vector>
#include "sampling.h"
#include "layout.h" 

struct Node2D {
    std::string id;
    int bipartite;
    double u, v;
};

std::vector<Node2D> project(const std::vector<Node>& nodes,
                             const Viewpoint& vp);

void saveProjections(const std::vector<std::vector<Node2D>>& projections,
                     const std::string& path);