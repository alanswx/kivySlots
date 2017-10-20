sudo apt-get update
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
   pkg-config libgl1-mesa-dev libgles2-mesa-dev \
   python-setuptools libgstreamer1.0-dev git-core \
   gstreamer1.0-plugins-{bad,base,good,ugly} \
   gstreamer1.0-{omx,alsa} python-dev libmtdev-dev \
   xclip
sudo pip install -U Cython==0.25.2
sudo pip install git+https://github.com/kivy/kivy.git@master
sudo pip install Adafruit_PCA9685
echo "Remember to enable i2c for the servo controller"
