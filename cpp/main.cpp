#include <iostream>
#include "layout.h"
#include "sampling.h"
#include "projection.h"

int main() {
    std::string nodes_path = "nodes.csv";
    std::string edges_path = "edges.csv";

    std::cout << "CSVを読み込み中..." << std::endl;
    auto nodes = loadNodes(nodes_path);
    auto edges = loadEdges(edges_path, nodes_path, nodes);

    std::cout << "ノード数: " << nodes.size() << std::endl;
    std::cout << "エッジ数: " << edges.size() << std::endl;

std::cout << "Force-Directed計算中..." << std::endl;
    for (int i = 0; i < 1000; i++) {
        applyForces(nodes, edges);
        if (i % 100 == 0) {
            std::cout << "イテレーション " << i << " 完了" << std::endl;
        }
    }

    saveNodes(nodes, "nodes_3d.csv");
    std::cout << "3次元配置完了" << std::endl;

    auto viewpoints = generateViewpoints(200);
    saveViewpoints(viewpoints, "viewpoints.csv");
    std::cout << "視点候補: " << viewpoints.size() << "個生成" << std::endl;

    std::vector<std::vector<Node2D>> all_projections;
    for (const auto& vp : viewpoints) {
        all_projections.push_back(project(nodes, vp));
    }
    saveProjections(all_projections, "projections.csv");
    std::cout << "全視点の投影完了" << std::endl;

    return 0;
}