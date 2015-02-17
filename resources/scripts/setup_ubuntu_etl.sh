# USE THIS TO INSTALL PYTHON 2.7 ONTO UBUNTU EC2 INSTANCE
# 2.7 IS ALREADY DEFAULT

mkdir  /home/ubuntu/temp
cd  /home/ubuntu/temp
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py

cd  /home/ubuntu
sudo apt-get -y install git-core


git clone https://github.com/klahnakoski/TestLog-ETL.git

cd /home/ubuntu/TestLog-ETL/
git checkout etl
sudo pip install -r requirements.txt

