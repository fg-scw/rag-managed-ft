#!/bin/bash

# Mettre à jour la liste des paquets
echo "Mise à jour de la liste des paquets..."
sudo apt update

# Installer python3-pip
echo "Installation de python3-pip..."
sudo apt install -y python3-pip

#Suppression Extension python3
sudo apt remove -y python3-typing-extensions

# Installer postgresql
echo "Installation de postgresql..."
sudo apt install -y postgresql

# Installer wget
echo "Installation de wget..."
sudo apt install -y wget
sudo apt install -y pandoc

# Installer libdl1
sudo apt install -y libgl1

#Installation des requirements app
pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Vérifier l'installation des paquets
echo "Vérification des installations..."
dpkg -l | grep -E 'python3-pip|postgresql|wget|pandoc|libgl1'

echo "Installation terminée."