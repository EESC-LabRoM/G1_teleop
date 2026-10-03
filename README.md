# H_G1 — RealSense 3D Hand Tracking & RViz2 Visualization no Docker (ROS 2 Humble)

Este repositório contém a infraestrutura em **Docker** com **ROS 2 Humble** para o rastreamento 3D da mão do operador usando a câmera **RealSense D435/D435i** e a publicação direta da TF do pulso (`hand_wrist_target`) no **RViz2**.

---

## 🐳 Execução via Docker (Recomendado)

Todo o ambiente ROS 2, drivers da RealSense, MediaPipe, OpenCV e RViz2 estão pré-configurados no Dockerfile.

### 1. Permitir acesso ao Display (X11) e rodar o Docker:

```bash
cd /home/mhc/IC/H_G1
chmod +x run_docker.sh
./run_docker.sh
```

Ou usando `docker compose` diretamente:

```bash
xhost +local:root
docker compose up --build
```

---

## 📁 Estrutura de Arquivos no Repositório

```text
H_G1/
├── Dockerfile                             # Ambiente ROS 2 Humble + RealSense + MediaPipe + RViz2
├── docker-compose.yml                     # Configuração com suporte a USB da RealSense e X11 (GUI)
├── run_docker.sh                          # Script auxiliar para liberar X11 e subir o contêiner
├── README.md
└── src/
    └── g1_teleop/
        ├── config/
        │   └── g1_phase1.rviz             # RViz2 configurado com Fixed Frame = camera_color_optical_frame
        ├── g1_teleop/
        │   ├── __init__.py
        │   ├── hand_tracker_node.py       # Nó de percepção: RealSense RGB + Depth + MediaPipe Pose -> TF do pulso
        │   ├── hand_orientation_estimator.py# Estimador de orientação da mão
        │   └── finger_count.py            # Contador de dedos / gestos da mão
        ├── launch/
        │   └── g1_teleop_phase1.launch.py # Launch file para percepção + RViz2
        ├── package.xml
        ├── setup.cfg
        └── setup.py
```

---

## 🎯 O que o Docker faz ao subir:
1. Compila o pacote `g1_teleop` automaticamente dentro do contêiner (`colcon build`).
2. Conecta à câmera RealSense via repasse USB (`/dev/bus/usb`).
3. Rastreia o pulso direito em 3D sem ArUco via MediaPipe Pose.
4. Publica a TF `camera_color_optical_frame -> hand_wrist_target` e o marcador visual (`Marker`).
5. Abre a interface gráfica do **RViz2** na tela do host via repasse X11!
