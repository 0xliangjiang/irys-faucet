# Irys Faucet Tool

一个用于自动领取 Irys 测试网代币的批量工具，支持多钱包、多代理轮询，内置完整的浏览器指纹模拟。

本地先部署松鼠大佬的过验证码代码：[https://github.com/0xsongsu/cf-clearance-scraper/tree/main](https://github.com/0xsongsu/cf-clearance-scraper/tree/main)

## 🌟 功能特点

- **批量处理**：支持多个钱包地址同时处理
- **代理轮询**：自动轮询使用不同代理，避免IP限制
- **指纹模拟**：完整模拟Chrome 132浏览器指纹
- **多线程**：并发处理提高效率
- **结果统计**：实时显示成功率和详细结果
- **错误处理**：完善的异常处理和重试机制
- **结果保存**：自动保存领取结果到文件

## 📋 系统要求

- Python 3.7+
- 网络连接
- 本地Turnstile token服务（端口3000）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install tls-client requests
```

### 2. 配置文件

#### 钱包地址配置 (`wallets.txt`)
```
0x6879a03ea1fae3648a4a93bc55eac11aed199019
0xe5af4b721f0e328013e5b090c1af519ca7e8d1cc
# 添加更多钱包地址，每行一个
# 格式: 0x开头的以太坊地址
```

#### 代理配置 (`proxies.txt`)
```
user:pass@ip:port
# 添加更多代理配置，每行一个
# 格式: 用户名:密码@IP:端口
```

### 3. 运行脚本

```bash
python batch_faucet.py
```

## 📁 文件结构

```
irys-faucet/
├── batch_faucet.py      # 主脚本
├── wallets.txt          # 钱包地址配置
├── proxies.txt          # 代理配置
├── faucet_results.txt   # 结果输出文件
└── README.md           # 说明文档
```

## ⚙️ 配置说明

### 代理配置格式
```
用户名:密码@IP:端口
```

### 钱包地址格式
```
0x开头的以太坊地址
```


## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。

## ⚠️ 免责声明

本工具仅供技术研究使用，使用者需自行承担使用风险。开发者不对因使用本工具造成的任何损失负责。

---

**注意**: 使用前请确保了解相关风险，并遵守平台使用条款。 
