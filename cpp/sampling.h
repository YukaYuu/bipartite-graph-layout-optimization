#pragma once
#include <string>
#include <vector>

struct Viewpoint {
    double theta;
    double phi; 
    double vx, vy, vz;
};

std::vector<Viewpoint> generateViewpoints(int n = 200);
void saveViewpoints(const std::vector<Viewpoint>& vps, 
                    const std::string& path);