> ⚠️ **Note:** This repository is currently under active structural development.

# Autonomous Mobile Robot (AMR) Warehouse Pallet Lifter Simulation

An enterprise-grade, full-stack AMR simulation designed for autonomous material handling in dynamic, human-shared warehouse environments. This project features an undercarriage pallet-lifting robot built completely within the ROS 2 ecosystem, utilizing modern Gazebo simulation physics, advanced perception pipelines, and deterministic behavior tree orchestration.

---

## 🏗️ System Architecture Overview

This project is architected to decouple high-level decision-making from safety-critical perception and low-level actuation. The system is divided into four distinct layers:

              ┌────────────────────────────────────────┐
              │       BehaviorTree.CPP (Brain)         │
              └──────┬──────────────────────────┬──────┘
                     │                          │ Handles Fallbacks & Task Flow
                     ▼                          ▼
        ┌────────────────────────┐  ┌───────────────────────┐
        │  YOLOv8 + Depth Fusion │  │  Nav2 Stack + AMCL    │
        └────────────┬───────────┘  └───────────┬───────────┘
           3D Point  │                          │ /cmd_vel
           Streams   ▼                          ▼
        ┌───────────────────────────────────────────────────┐
        │  Nav2 Collision Monitor (Safe Speed / Hard Stop)  │
        └───────────────────────┬───────────────────────────┘
                                │ Multiplexed /cmd_vel
                                ▼
                    ┌───────────────────────┐
                    │  gz_ros2_control AMR  │
                    └───────────────────────┘
---

## 🚀 Key Engineering Highlights

* **Dynamic 3D Safety Zones:** Real-time human tracking using YOLOv8 fused with RGB-D depth data, feeding into the `nav2_collision_monitor` to enforce geometric safety envelopes (Slowdown, Velocity-Limit, and Emergency Brake).
* **Precision Visually-Guided Docking:** Custom OpenCV eye-in-hand alignment node tracking ArUco markers to execute closed-loop sub-centimeter docking maneuvers beneath pallet racks.
* **Modern Gazebo Physics Workspace:** Implemented completely within **Gazebo Harmonic** using the native `gz-sim-detachable-joint-system` plugin to eliminate rigid-body contact solver jitter when handling cargo.
* **Deterministic Mission Control:** Complex task orchestration and edge-case error recovery managed via **BehaviorTree.CPP** and monitored using Groot.

---

## 🗺️ Project Implementation Roadmap

This project is being executed in a structured, testable, 5-phase engineering lifecycle:

### Phase 1: Kinematics & Gazebo Base 🔄 [Current Focus]
* Construct the parametric Xacro/URDF model of the differential-drive AMR base.
* Integrate a prismatic lifting joint and payload attachment links.
* Configure the low-level controllers using `gazebo_ros2_control`.

### Phase 2: Navigation & Spatial Awareness 📅 [Planned]
* Generate high-fidelity occupancy grid maps using `slam_toolbox`.
* Configure `robot_localization` using an Extended Kalman Filter (EKF) to fuse IMU and wheel odometry.
* Tune Nav2 utilizing the Regulated Pure Pursuit (RPP) or Model Predictive Path Integral (MPPI) local planners.

### Phase 3: Perception & 3D Spatial Projection 📅 [Planned]
* Develop the 2D-to-3D projection pipeline using YOLOv8 bounding boxes matched to camera depth fields.
* Write an absolute spatial tracking node utilizing OpenCV for ArUco-based relative pose evaluation ($X, Y, \text{Yaw}$).

### Phase 4: Precision Docking & Manipulation Controls 📅 [Planned]
* Implement custom low-level precision docking script overrides.
* Integrate Gazebo system service calls to programmatically dock and lock cargo assets securely.

### Phase 5: Behavior Tree Orchestration & Telemetry 📅 [Planned]
* Draft the end-to-end operational mission tree loops.
* Build a monitoring dashboard via **Foxglove Studio** for advanced runtime telemetry analysis.
