# 激活虚拟环境 source env.sh
PROJ_DIR=`pwd`
VENV=${PROJ_DIR}/.env
PROJ_NAME=chat

# if your python release is not anaconda or cpython, please change the code below
ANACONDA_EXISTS=`which conda`


if [ ! -d ${VENV} ];then
    virtualenv --prompt "(${PROJ_NAME})" ${VENV} -p  python3
fi

echo 'source activate env'
echo ${VENV}
source ${VENV}/bin/activate

export PYTHONPATH=${PROJ_DIR}
export PROJ_DIR
export PATH=${PATH}:${VENV}/bin

# # if your host is in China, use douban's pypi to speed up
# pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt
