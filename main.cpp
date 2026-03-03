#include "raylib.h"
#include <vector>
#include <string>
#include <thread>
#include <mutex>
#include <chrono>
#include <algorithm>

struct DataPoint {
    int step;
    float cost;
};

struct Algorithm {
    std::string name;
    Color color;
    std::string command;

    std::vector<DataPoint> points;
    float finalTime = 0.0f;
    int currentStep = 0;
    float currentCost = 0.0f;
    float memoryUsage = 0.0f;
    float velocity = 0.0f;
    float peakVelocity = 0.0f;
    bool isFinished = false;

    float elapsedTime = 0.0f;
    float stepsPerSecond = 0.0f;
    std::chrono::high_resolution_clock::time_point startTime;
};

std::vector<Algorithm> algos;
std::mutex dataMutex;
auto startTime = std::chrono::high_resolution_clock::now();

void RunAlgorithm(const int index) {
    {
        std::lock_guard<std::mutex> lock(dataMutex);
        algos[index].startTime = std::chrono::high_resolution_clock::now();
    }

    FILE* pipe = popen(algos[index].command.c_str(), "r");
    if (!pipe) return;

    char buffer[256];
    while (fgets(buffer, sizeof(buffer), pipe)) {
        std::string line(buffer);
        if (line.rfind("DATA|", 0) == 0) {
            std::vector<std::string> parts;
            size_t s = 0, e = 0;
            while ((e = line.find('|', s)) != std::string::npos) {
                parts.push_back(line.substr(s, e - s));
                s = e + 1;
            }
            parts.push_back(line.substr(s));

            if (parts.size() >= 5) {
                std::lock_guard<std::mutex> lock(dataMutex);
                algos[index].currentStep = std::stoi(parts[1]);
                algos[index].currentCost = std::stof(parts[2]);
                algos[index].memoryUsage = std::stof(parts[3]);
                algos[index].velocity = std::stof(parts[4]);
                if (algos[index].velocity > algos[index].peakVelocity) {
                    algos[index].peakVelocity = algos[index].velocity;
                }

                if (algos[index].currentCost > 0.0f && algos[index].currentCost < 1000000.0f) {
                    algos[index].points.push_back({algos[index].currentStep, algos[index].currentCost});
                }
            }
        }

        auto now = std::chrono::high_resolution_clock::now();
        algos[index].elapsedTime = std::chrono::duration<float>(now - algos[index].startTime).count();

        if (algos[index].elapsedTime > 0) {
            algos[index].stepsPerSecond = static_cast<float>(algos[index].currentStep) / algos[index].elapsedTime;
        }
    }
    std::lock_guard<std::mutex> lock(dataMutex);
    algos[index].isFinished = true;
    algos[index].finalTime = std::chrono::duration<float>(std::chrono::high_resolution_clock::now() - startTime).count();
    pclose(pipe);
}

int main() {
    SetConfigFlags(FLAG_WINDOW_RESIZABLE | FLAG_MSAA_4X_HINT);
    InitWindow(1280, 900, "Supply Chain Optimization: Telemetry Dashboard");
    SetTargetFPS(60);

    Font font = LoadFontEx("resources/Inter-Medium.ttf", 32, nullptr, 250);
    if (font.texture.id == 0) font = GetFontDefault();

    algos.push_back({"Tabu Search", SKYBLUE, "python3 algorithms/tabu_search.py data/benchmark_large.json"});
    algos.push_back({"Branch & Bound", PURPLE, "python3 algorithms/branch_and_bound.py data/benchmark_large.json"});
    algos.push_back({"Simplex (Exact)", RED, "python3 algorithms/simplex.py data/benchmark_large.json"});
    algos.push_back({"Genetic Algo", ORANGE, "python3 algorithms/genetic_algo.py data/benchmark_large.json"});

    std::vector<std::thread> threads;
    for (size_t i = 0; i < algos.size(); i++) threads.emplace_back(RunAlgorithm, i);

    while (!WindowShouldClose()) {
        const auto sw = static_cast<float>(GetScreenWidth());
        const auto sh = static_cast<float>(GetScreenHeight());
        const Rectangle graph = { sw * 0.08f, sh * 0.12f, sw * 0.84f, sh * 0.45f };

        BeginDrawing();
        ClearBackground({ 240, 242, 245, 255 });

        DrawRectangle(0, 0, static_cast<int>(sw), static_cast<int>(sh * 0.07f), { 30, 35, 45, 255 });
        DrawTextEx(font, "AMINE (Jaune) - SALMA (Rouje) - SLIM (Bleu) - TAREK (Violet)", { 25, sh * 0.02f }, 24, 1, WHITE);

        int maxSteps = 100;
        float minC = 9e9f, maxC = -9e9f;
        {
            std::lock_guard<std::mutex> lock(dataMutex);
            for (auto& a : algos) {
                if (a.currentStep > maxSteps) maxSteps = a.currentStep;
                for (auto& p : a.points) {
                    if (p.cost < minC) minC = p.cost;
                    if (p.cost > maxC) maxC = p.cost;
                }
            }
        }
        float renderMax = (maxC > 120000.0f) ? 120000.0f : maxC;
        if (minC > renderMax) minC = 0;


        DrawRectangleRec(graph, WHITE);
        DrawRectangleLinesEx(graph, 2, LIGHTGRAY);


        for (int i = 0; i <= 4; i++) {
            const float fraction = static_cast<float>(i) / 4.0f;
            const float costVal = minC + (renderMax - minC) * fraction;
            const float yPos = (graph.y + graph.height) - (fraction * graph.height);

            DrawLineEx({graph.x, yPos}, {graph.x + graph.width, yPos}, 1.0f, {200, 200, 200, 100});

            DrawTextEx(font, TextFormat("%.0f", costVal), {graph.x - 65, yPos - 10}, 16, 1, DARKGRAY);
        }

        int stepInterval = 100;

        if (maxSteps > 2000) stepInterval = 500;
        if (maxSteps > 10000) stepInterval = 2000;

        for (int s = 0; s <= maxSteps; s += stepInterval) {
            const float xPos = graph.x + (static_cast<float>(s) / static_cast<float>(maxSteps)) * graph.width;

            DrawLineEx({xPos, graph.y}, {xPos, graph.y + graph.height}, 1.0f, {200, 200, 200, 100});


            DrawTextEx(font, TextFormat("%d", s), {xPos - 15, graph.y + graph.height + 10}, 14, 1, DARKGRAY);
        }

        DrawTextEx(font, "ÉTAPES", {graph.x + graph.width + 10, graph.y + graph.height + 10}, 16, 1, DARKGRAY);

        {
            std::lock_guard<std::mutex> lock(dataMutex);
            for (auto& a : algos) {
                if (a.points.empty()) continue;

                const float costRange = (renderMax - minC == 0) ? 1.0f : (renderMax - minC);
                const float stepRange = (maxSteps == 0) ? 1.0f : static_cast<float>(maxSteps);

                const float val0 = std::clamp(a.points[0].cost, minC, renderMax);
                const float y0 = (graph.y + graph.height) - ((val0 - minC) / costRange) * graph.height;
                const float x_first = graph.x + (static_cast<float>(a.points[0].step) / stepRange) * graph.width;
                DrawLineEx({graph.x, y0}, {x_first, y0}, 3.0f, a.color);

                for (size_t i = 1; i < a.points.size(); i++) {
                    const float v1 = std::clamp(a.points[i-1].cost, minC, renderMax);
                    const float v2 = std::clamp(a.points[i].cost, minC, renderMax);

                    const float x1 = graph.x + (static_cast<float>(a.points[i - 1].step) / stepRange) * graph.width;
                    const float x2 = graph.x + (static_cast<float>(a.points[i].step) / stepRange) * graph.width;
                    const float y1 = (graph.y + graph.height) - ((v1 - minC) / costRange) * graph.height;
                    const float y2 = (graph.y + graph.height) - ((v2 - minC) / costRange) * graph.height;

                    DrawLineEx({x1, y1}, {x2, y2}, 3.0f, a.color);
                }
            }
        }

        const float boxW = (graph.width / 4) - 15;
        for (int i = 0; i < 4; i++) {
            const float bx = graph.x + static_cast<float>(i) * (boxW + 20);
            const float by = sh * 0.62f;
            DrawRectangle(static_cast<int>(bx), static_cast<int>(by), static_cast<int>(boxW), static_cast<int>(sh * 0.35f), WHITE);
            DrawRectangleLinesEx({bx, by, boxW, sh * 0.35f}, 2, algos[i].color);


            DrawTextEx(font, algos[i].name.c_str(), {bx + 10, by + 10}, 20, 1, algos[i].color);
            DrawTextEx(font, TextFormat("Coût: %.2f", algos[i].currentCost), {bx + 10, by + 40}, 24, 1, DARKGREEN);

            float memPerc = algos[i].memoryUsage / 500.0f;
            const Color memCol = (memPerc > 0.8f) ? RED : (memPerc > 0.4f) ? ORANGE : LIME;
            DrawTextEx(font, TextFormat("RAM: %.1f MB", algos[i].memoryUsage), {bx + 10, by + 80}, 16, 1, DARKGRAY);
            DrawRectangle(static_cast<int>(bx) + 10, static_cast<int>(by) + 100, static_cast<int>(boxW) - 20, 8, LIGHTGRAY);
            DrawRectangle(static_cast<int>(bx) + 10, static_cast<int>(by) + 100, static_cast<int>((boxW - 20) * std::min(memPerc, 1.0f)), 8, memCol);

            const Color velCol = (algos[i].velocity > 0) ? LIME : (algos[i].peakVelocity > 0 ? ORANGE : DARKGRAY);
            const float velToShow = algos[i].isFinished ? algos[i].peakVelocity : algos[i].velocity;
            DrawTextEx(font, TextFormat("AMÉLIORATION MAX: %.2f", velToShow), {bx + 10, by + 120}, 16, 1, velCol);

            DrawTextEx(font, TextFormat("ÉTAPES: %d", algos[i].currentStep), {bx + 10, by + 150}, 16, 1, DARKGRAY);
            const Color statusColor = algos[i].isFinished ? RED : LIME;
            const char* statusText = algos[i].isFinished ? "INACTIF / TERMINÉ" : "TRAITEMENT...";

            DrawTextEx(font, statusText, {bx + 10, by + 180}, 16, 1, statusColor);


            DrawTextEx(font, TextFormat("TIME: %.2fs", algos[i].elapsedTime), {bx + 10, by + 210}, 16, 1, DARKGRAY);
            DrawTextEx(font, TextFormat("FREQ: %.0f étape/s", algos[i].stepsPerSecond), {bx + 10, by + 235}, 16, 1, SKYBLUE);



        }

        EndDrawing();
        if (IsKeyPressed(KEY_S)) {
            TakeScreenshot("optimization_results.png");
        }
    }
    for (auto& t : threads) t.detach();
    CloseWindow();
    return 0;
}