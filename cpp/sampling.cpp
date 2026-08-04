#include "sampling.h"
#include <cmath>
#include <fstream>
#include <string>

std::vector<Viewpoint> generateViewpoints(int n) {
    std::vector<Viewpoint> vps;
    double golden = M_PI * (3.0 - std::sqrt(5.0));
    for (int i = 0; i < n; i++) {
        double y = 1.0 - (2.0 * i / (n - 1));
        double r = std::sqrt(1.0 - y * y);
        double theta = golden * i;
        double vx = std::cos(theta) * r;
        double vz = std::sin(theta) * r;
        double vy = y;
        double phi = std::asin(y);
        vps.push_back({theta, phi, vx, vy, vz});
    }
    return vps;
}

void saveViewpoints(const std::vector<Viewpoint>& vps,
                    const std::string& path) {
    std::ofstream file(path);
    file << "theta,phi,vx,vy,vz\n";
    for (const auto& vp : vps) {
        file << vp.theta << ","
             << vp.phi << ","
             << vp.vx << ","
             << vp.vy << ","
             << vp.vz << "\n";
    }
}