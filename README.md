# Pythia：基于在线强化学习的可定制硬件预取框架

## 目录

- [1、简介](#1简介) 
- [2、实验环境搭建](#2实验环境搭建) 
- [3、准备工作负载跟踪](#3准备工作负载跟踪) 
- [4、仿真配置与执行](#4仿真配置与执行) 
- [5、数据提取](#5数据提取) 
- [6、数据分析](#6数据分析)

## 1、简介

本工作是基于[Pythia: A Customizable Hardware Prefetching Framework Using Online Reinforcement Learning](https://arxiv.org/pdf/2109.12021.pdf)的实验复现，参考代码仓库https://github.com/CMU-SAFARI/Pythia。

Pythia是一个轻量级、可硬件实现的数据预取框架，利用在线强化学习动态生成高精度、及时且系统感知的预取请求。该工作发表于MICRO 2021。

*Rahul Bera、Konstantinos Kanellopoulos、Anant V. Nori、Taha Shahroodi、Sreenivas Subramoney、Onur Mutlu，" [Pythia: A Customizable Hardware Prefetching Framework Using Online Reinforcement Learning](https://arxiv.org/pdf/2109.12021.pdf) "，发表于第54届IEEE/ACM国际微体系结构研讨会（MICRO）论文集，2021年。*

为了验证Pythia论文中的实验结果并深入理解其性能特性，本研究采用ChampSim模拟器进行了复现实验。复现工作遵循论文中描述的方法论，利用了作者团队公开提供的源代码、仿真框架和工作负载跟踪数据。

## 2、实验环境搭建

1. 操作系统：Ubuntu 20.04（虚拟机环境）

2. 安装所有必要的依赖软件包，包括Perl脚本解释器、GCC编译套件、CMake构建系统以及md5sum校验工具：

    ```Bash
    sudo apt install perl
    sudo apt install gcc g++ cmake md5sum
    ```
    
3. 从GitHub官方仓库克隆Pythia项目的完整源代码：

    ```Bash
    git clone https://github.com/CMU-SAFARI/Pythia.git
    ```
    
4. 进入Pythia主目录，克隆bloomfilter库到`libbf`目录：

    ```Bash
    cd Pythia
    git clone https://github.com/mavam/libbf.git libbf
    ```
    
5. libbf.a构建bloomfilter库，在build目录中创建静态库：

    ```Bash
    cd libbf
    mkdir build && cd build
    cmake ../
    make clean && make
    ```
    
6. 编译ChampSim仿真器，构建单核/多核版本的Pythia，在`bin`目录生成可执行文件：

    ```Bash
    cd $PYTHIA_HOME
    ./build_champsim.sh multi multi no 1
    ```
    
7. 设置环境变量：

    ```Bash
    source setvars.sh
    ```

## 3、准备工作负载跟踪

原始论文使用了来自SPEC CPU2006/2017、PARSEC、Ligra和CloudSuite等基准测试套件的150个内存密集型跟踪文件。复现过程中使用perl脚本自动下载了5个trace文件用于验证部分结论，并验证文件完整性。

1. 创建trace存储目录并下载核心跟踪数据（除Ligra和PARSEC外）：

    ```Bash
    mkdir $PYTHIA_HOME/traces/
    cd $PYTHIA_HOME/scripts/
    perl download_traces.pl --csv artifact_traces.csv --dir ../traces/
    ```
    
2. 验证下载的跟踪文件完整性：

    ```Bash
    cd $PYTHIA_HOME/traces
    md5sum -c ../scripts/artifact_traces.md5
    ```
    
3. 单独下载Ligra和PARSEC跟踪文件（复现时未下载）：

    - Ligra：[https://doi.org/10.5281/zenodo.14267977](https://doi.org/10.5281/zenodo.14267977)

    - PARSEC 2.1：[https://doi.org/10.5281/zenodo.14268118](https://doi.org/10.5281/zenodo.14268118)

4. 若跟踪文件下载路径非默认，需修改`experiments/MICRO_1C.tlist`中的文件路径配置。

## 4、仿真配置与执行

1. 使用`scripts/create_jobfile.pl`脚本批量创建实验命令。

2. 配置文件说明：

    - `MICRO_1C.tlist`：指定要使用的跟踪文件列表

    - `MICRO_1C.exp`：指定预取器类型（Pythia、SPP、Bingo、MLOP等）及相关参数（预热指令数、模拟指令数、内存带宽等）

3. 生成实验任务脚本，确保tlist和exp文件路径正确：

    ```bash
    cd experiements_1C/
    perl ../../scripts/rollup.pl --tlist ../MICRO_1C.tlist --exp ../MICRO_1C.exp --mfile ../rollup_1C_base_config.mfile > rollup.csv
    ```
    
4. 创建并进入运行目录，启动仿真实验：

    ```bash
    mkdir -p experiments_1C
    cd experiments_1C
    source ../jobfile.sh
    ```
    
5. 复现实验示例（与单特征预取器对比）
   
   `MICRO_1C.tlist`文件：指定复现待使用的trace文件：

    ```Plain Text
    NAME=482.sphinx3-417B
    TRACE=$(PYTHIA_HOME)/traces/482.sphinx3-417B.champsintrace.Xz
    KNOBS=
    
    NAME=459.GensFDTD-765B
    TRACE=$(PYTHIA_HOME)/traces/459.GensFDTD-765B.champsintrace.XZ
    KNOBS=
    ```
    
    修改`MICRO_1C.exp`文件：指定预取器类型及相关参数配置

    ```Plain Text
    BASE = --warmup_instructions=100000000 --simulation_instructions=500000000
    NOPREF = --config=$(PYTHIA_HOME)/config/nopref.ini
    STRIDE = --l2c_prefetcher_types=stride --config=$(PYTHIA_HOME)/config/stride.ini
    SPP_DEV2 = --l2c_prefetcher_types=spp_dev2 --config=$(PYTHIA_HOME)/config/spp_dev2.ini
    MLOP = --l2c_prefetcher_types=mlop --config=$(PYTHIA_HOME)/config/mlop.ini
    BINGO = --l2c_prefetcher_types=bingo --config=$(PYTHIA_HOME)/config/bingo.ini
    DSPATCH = --l2c_prefetcher_types=dspatch --config=$(PYTHIA_HOME)/config/dspatch.ini
    SPP_PPF_DEV = --l2c_prefetcher_types=spp_ppf_dev --config=$(PYTHIA_HOME)/config/spp_ppf_dev.ini
    PYTHIA = --l2c_prefetcher_types=scooby --config=$(PYTHIA_HOME)/config/pythia.ini
    
    nopref						$(BASE) $(NOPREF)
    spp						$(BASE) $(SPP_DEV2)
    bingo						$(BASE) $(BINGO)
    mlop						$(BASE) $(MLOP)
    pythia						$(BASE) $(PYTHIA)
    ```
    重新执行模拟
    ```Bash
    mkdir -p experiments_1C
    cd experiments_1C
    source ../jobfile.sh
    ```

    实验运行通过自动化脚本管理，生成的原始输出`.out`文件包含各预取器的性能数据。

## 5、数据提取

1. 关键指标：

    - 指令数（IPC）

    - 各级缓存缺失次数（L1/L2/LLC）

    - 预取器发出的预取请求数

    - 有用预取数等

2. 使用`rollup.pl`脚本汇总结果，生成结构化CSV文件：

    ```bash
    cd experiements_1C/
    perl ../../scripts/rollup.pl --tlist ../MICRO_1C.tlist --exp ../MICRO_1C.exp --mfile ../rollup_1C_base_config.mfile > rollup.csv
    ```

    可通过配置`mfile`文件指定需要统计的数据维度，CSV文件将作为后续分析的基础。

## 6、数据分析

得到汇总数据CSV文件后，通过以下步骤分析结果：

1. 将生成的 rollup.csv导入 Python Pandas、Excel 或其他数据分析工具。此次复现使用Python Pandas进行数据分析，相关python文件在experiment_1C文件夹中。
2. 可绘制柱状图、折线图等，对比 Pythia 与 SPP、Bingo、MLOP 等基线预取器的 IPC 提升、预取准确率等指标。
3. 与论文中关键图表进行定性、定量对比，验证复现一致性。
