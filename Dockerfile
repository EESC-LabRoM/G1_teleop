# Base: local spot_ros2 image (already has spot_description built in /ros_ws)
FROM spot_ros2:latest

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3-pip python3-colcon-common-extensions \
      ros-humble-realsense2-camera ros-humble-realsense2-description \
      ros-humble-cv-bridge ros-humble-rviz2 ros-humble-joint-state-publisher \
      libgl1 libglib2.0-0 usbutils \
    && rm -rf /var/lib/apt/lists/*

# Pinned: mediapipe 0.10.14 still ships mp.solutions (used by the original nodes);
# numpy<2 + opencv 4.10 keep ABI compatible with ROS Humble cv_bridge/matplotlib.
RUN pip3 install "numpy<2" "opencv-contrib-python==4.10.0.84" "mediapipe==0.10.14"

WORKDIR /workspace
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc \
 && echo "source /ros_ws/install/setup.bash" >> ~/.bashrc \
 && echo "[ -f /workspace/install/setup.bash ] && source /workspace/install/setup.bash" >> ~/.bashrc

CMD ["bash"]
