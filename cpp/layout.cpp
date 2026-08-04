#include "layout.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>

std::vector<Node> loadNodes(const std::string& path) {
    std::vector<Node> nodes;
    std::ifstream file(path);
    std::string line;
    std::getline(file, line);

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string id, bipartite_str, node_type, x_str, y_str, z_str;
        std::getline(ss, id, ',');
        std::getline(ss, bipartite_str, ',');
        std::getline(ss, node_type, ',');
        std::getline(ss, x_str, ',');
        std::getline(ss, y_str, ',');
        std::getline(ss, z_str, ',');

        Node n;
        n.id = id;
        n.bipartite = std::stoi(bipartite_str);
        n.x = std::stod(x_str);
        n.y = std::stod(y_str);
        n.z = std::stod(z_str);
        n.fx = n.fy = n.fz = 0;
        nodes.push_back(n);
    }
    return nodes;
}

std::vector<Edge> loadEdges(const std::string& edge_path,
                            const std::string& node_path,
                            const std::vector<Node>& nodes) {
    std::map<std::string, int> id_to_idx;
    for (int i = 0; i < (int)nodes.size(); i++) {
        id_to_idx[nodes[i].id] = i;
    }

    std::vector<Edge> edges;
    std::ifstream file(edge_path);
    std::string line;
    std::getline(file, line);

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string src_str, dst_str;
        std::getline(ss, src_str, ',');
        std::getline(ss, dst_str, ',');

        if (id_to_idx.count(src_str) && id_to_idx.count(dst_str)) {
            Edge e;
            e.src = id_to_idx[src_str];
            e.dst = id_to_idx[dst_str];
            edges.push_back(e);
        }
    }
    return edges;
}

void applyForces(std::vector<Node>& nodes,
                 const std::vector<Edge>& edges,
                 double k) {
    for (auto& n : nodes) n.fx = n.fy = n.fz = 0;
    for (auto& n : nodes) {
        double dist_from_origin = std::sqrt(n.x*n.x + n.y*n.y + n.z*n.z) + 1e-6;
        // 原点から外側へ押し出す力（全体を球状に広げるイメージ）
        double push_out = (k * k) / dist_from_origin;
        n.fx += push_out * n.x / dist_from_origin;
        n.fy += push_out * n.y / dist_from_origin;
        n.fz += push_out * n.z / dist_from_origin;
    }

    for (const auto& e : edges) {
        double dx = nodes[e.dst].x - nodes[e.src].x;
        double dy = nodes[e.dst].y - nodes[e.src].y;
        double dz = nodes[e.dst].z - nodes[e.src].z;
        double dist = std::sqrt(dx*dx + dy*dy + dz*dz) + 1e-6;
        
        double force = (dist * dist) / k;

        nodes[e.src].fx += force * dx / dist;
        nodes[e.src].fy += force * dy / dist;
        nodes[e.src].fz += force * dz / dist;
        nodes[e.dst].fx -= force * dx / dist;
        nodes[e.dst].fy -= force * dy / dist;
        nodes[e.dst].fz -= force * dz / dist;
    }

    double dt = 0.01; 
    double max_move = 0.1; 
    
    for (auto& n : nodes) {
        double f_mag = std::sqrt(n.fx*n.fx + n.fy*n.fy + n.fz*n.fz);
        
        if (f_mag > 10.0) {
            n.fx = (n.fx / f_mag) * 10.0;
            n.fy = (n.fy / f_mag) * 10.0;
            n.fz = (n.fz / f_mag) * 10.0;
        }
        
        double dx = dt * n.fx;
        double dy = dt * n.fy;
        double dz = dt * n.fz;
        
        double move = std::sqrt(dx*dx + dy*dy + dz*dz);
        if (move > max_move) {
            dx *= max_move / move;
            dy *= max_move / move;
            dz *= max_move / move;
        }
        
        n.x += dx;
        n.y += dy;
        n.z += dz;
        
        if (std::isnan(n.x) || std::isnan(n.y) || std::isnan(n.z) || std::isinf(n.x)) {
            n.x = n.y = n.z = 0.0;
        }
    }
}

void saveNodes(const std::vector<Node>& nodes, const std::string& path) {
    std::ofstream file(path);
    file << "node_id,bipartite,x,y,z\n";
    for (const auto& n : nodes) {
        file << n.id << ","
             << n.bipartite << ","
             << n.x << ","
             << n.y << ","
             << n.z << "\n";
    }
}