#!/bin/bash
# 把指定實驗腳本放進剪貼簿。用法: ./clip.sh 3  或  ./clip.sh 4
case "$1" in
  3) F=exp3_depth_tsdf.py ;;
  4) F=exp4_2dgs_train.py ;;
  *) echo "用法: ./clip.sh [3|4]"; exit 1 ;;
esac
python3 -c "import subprocess;subprocess.Popen(['pbcopy'],stdin=subprocess.PIPE).communicate(open('$HOME/3d/scan2cad/gs2mesh/$F','rb').read())"
echo "✓ 實驗$1 ($F) 已在剪貼簿,到 Colab Cmd+V"
