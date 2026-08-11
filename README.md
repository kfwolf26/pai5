# 体彩排列5过滤工具（狼奖多多）

一款基于 Python + Tkinter 开发的体彩排列5分析与预测桌面工具，集成号码过滤、历史查询、走势图、预测模型、定位定胆和回测中心等多种功能，帮助用户更好地分析排列5历史数据并辅助选号。

## 功能特性

本工具采用多标签页（Tab）布局，主要包含以下六大功能模块：

### 🎯 过滤工具
排列5号码过滤功能，支持多种形态过滤条件：
- **大小形态**：5 位大小组合（共 32 种）
- **奇偶形态**：5 位奇偶组合（共 32 种）
- **质合形态**：5 位质合组合（共 32 种）
- **012 路形态**：5 位 012 路组合（共 243 种）
- **小中大形态**：5 位小中大组合（共 243 种）
- 各位置（万/千/百/十/个）独立号码筛选

### 📊 历史查询
管理排列5历史开奖记录：
- 添加 / 编辑 / 删除开奖记录
- 按期号、日期查询历史数据
- 数据持久化保存至本地 JSON 文件

### 📈 走势图
一键跳转官方走势图页面：
- 3D 走势图
- 排列3 走势图
- 排列5 走势图

### 🔮 预测模型
基于历史数据的号码预测：
- 多种预测算法
- 预测结果保存与管理
- 增量更新预测数据

### 🎯 定位定胆
针对 5 个位置（万/千/百/十/个）分别定三胆：
- 多个虚拟"预测师"生成定胆方案
- 历史命中率统计
- 百分比布局展示

### 📊 回测中心
验证预测策略在历史数据上的真实表现：
- 多种内置策略：随机、频率、衰减加权、平滑、冷热等
- 滚动前推（Walk-Forward）回测
- 多维度指标汇总评估

## 项目结构

```
pai5/
├── main.py                     # 程序入口
├── modules/                    # 功能模块
│   ├── filter_tool.py          # 过滤工具
│   ├── history_query.py        # 历史查询
│   ├── trend_chart.py          # 走势图
│   ├── prediction_model.py     # 预测模型
│   ├── location_dingdan.py     # 定位定胆
│   └── backtest.py             # 回测中心
├── utils/                      # 工具层
│   ├── history_manager.py      # 历史数据管理（单例）
│   └── statistics.py           # 统计分析工具函数
├── history.json                # 历史开奖数据
├── prediction_data.json        # 预测数据
├── saved_predictions.json      # 保存的预测记录
└── _smoke_test_*.py            # 冒烟测试脚本
```

## 环境依赖

- Python 3.10+
- 仅依赖 Python 标准库（Tkinter、json、os、random、threading、itertools、collections 等），无需额外安装第三方包

## 快速开始

1. **克隆仓库**

   ```bash
   git clone https://github.com/你的用户名/pai5.git
   cd pai5
   ```

2. **运行程序**

   ```bash
   python main.py
   ```

3. **首次使用建议**
   - 进入「历史查询」标签页，录入或导入历史开奖数据
   - 数据保存后即可在其他模块使用

## 数据说明

所有数据均以 JSON 格式存储在项目根目录下：

| 文件名                  | 说明               |
| ----------------------- | ------------------ |
| `history.json`          | 历史开奖记录       |
| `prediction_data.json`  | 预测模型生成数据   |
| `saved_predictions.json`| 用户保存的预测结果 |

## 测试

项目附带多个冒烟测试脚本，可用于验证各模块基本功能：

```bash
python _smoke_test_backtest.py
python _smoke_test_history_query.py
python _smoke_test_pred_model.py
python _smoke_test_pl5.py
python _smoke_test_ldd_backtest.py
```

## 免责声明

本项目仅用于学习与技术研究，不构成任何购彩建议。彩票具有随机性，请理性消费，量力而行。

## License

本项目采用 MIT License。
