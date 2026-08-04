#pragma once
#include <string>
#include <vector>
#include <map>

struct Node {
    std::string id;
    int bipartite;
    double x, y, z;
    double fx, fy, fz;
};

struct Edge {
    int src, dst;
};

std::vector<Node> loadNodes(const std::string& path);
std::vector<Edge> loadEdges(const std::string& edge_path,
                            const std::string& node_path,
                            const std::vector<Node>& nodes);
void applyForces(std::vector<Node>& nodes,
                 const std::vector<Edge>& edges,
                 double k = 1.0);
void saveNodes(const std::vector<Node>& nodes, const std::string& path);