import tls_client
import requests
import json
import time
import random

# 配置开关
USE_API_PROXIES = True  # 设置为True从API获取代理，False从文件读取
API_PROXY_URL = ""

# 配置说明:
# USE_API_PROXIES = True:  从API动态获取代理，每次处理一个钱包获取一个新代理，失败时重试3次
# USE_API_PROXIES = False: 从proxies.txt文件读取代理，每个钱包使用对应位置的代理
# API_PROXY_URL: 代理API地址，支持多种返回格式:
#   格式1: [{"username":"...","password":"...","ip":"...","port":"..."}]
#   格式2: {"code":0,"success":"true","msg":"","data":[{"IP":"...","Port":...}]}
#   格式3: {"code":0,"data":[{"ip":"...","port":"...","username":"...","password":"..."}]}

def load_wallets(filename="wallets.txt"):
    """加载钱包地址列表"""
    wallets = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and line.startswith('0x'):
                    wallets.append(line)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {filename}")
        return []
    return wallets

def get_api_proxies(count=1):
    """从API获取代理列表"""
    proxies = []
    try:
        print(f"正在从API获取 {count} 个代理...")
        response = requests.get(API_PROXY_URL, timeout=30)
        
        if response.status_code == 200:
            proxy_data = response.json()
            print(f"API返回数据: {proxy_data}")
            
            # 检查不同的返回格式
            if isinstance(proxy_data, list):
                # 格式1: [{"username": "...", "password": "...", "ip": "...", "port": "..."}]
                for proxy in proxy_data:
                    proxy_config = {
                        "ip": proxy.get("ip"),
                        "port": proxy.get("port"),
                        "username": proxy.get("username"),
                        "password": proxy.get("password")
                    }
                    if all(proxy_config.values()):  # 确保所有字段都有值
                        proxies.append(proxy_config)
                        print(f"获取代理: {proxy_config['username']}@{proxy_config['ip']}:{proxy_config['port']}")
            
            elif isinstance(proxy_data, dict):
                # 格式2: {"code":0,"success":"true","msg":"","data":[{"IP":"...","Port":...}]}
                if proxy_data.get("success") == "true" and "data" in proxy_data:
                    for proxy in proxy_data["data"]:
                        proxy_config = {
                            "ip": proxy.get("IP"),
                            "port": str(proxy.get("Port")),
                            "username": "",  # 这种格式通常没有用户名密码
                            "password": ""
                        }
                        if proxy_config["ip"] and proxy_config["port"]:
                            proxies.append(proxy_config)
                            print(f"获取代理: {proxy_config['ip']}:{proxy_config['port']} (无认证)")
                
                # 格式3: {"code":0,"data":[{"ip":"...","port":"...","username":"...","password":"..."}]}
                elif proxy_data.get("code") == 0 and "data" in proxy_data:
                    for proxy in proxy_data["data"]:
                        proxy_config = {
                            "ip": proxy.get("ip"),
                            "port": proxy.get("port"),
                            "username": proxy.get("username", ""),
                            "password": proxy.get("password", "")
                        }
                        if proxy_config["ip"] and proxy_config["port"]:
                            proxies.append(proxy_config)
                            if proxy_config["username"]:
                                print(f"获取代理: {proxy_config['username']}@{proxy_config['ip']}:{proxy_config['port']}")
                            else:
                                print(f"获取代理: {proxy_config['ip']}:{proxy_config['port']} (无认证)")
            
            if not proxies:
                print("警告: 无法解析API返回的代理数据")
        else:
            print(f"API请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"获取API代理失败: {e}")
    
    return proxies

def load_proxies(filename="proxies.txt"):
    """加载代理配置列表"""
    proxies = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        # 解析格式: 用户名:密码@IP:端口
                        if '@' in line:
                            auth_part, server_part = line.split('@')
                            username, password = auth_part.split(':')
                            ip, port = server_part.split(':')
                            proxy_config = {
                                "ip": ip,
                                "port": port,
                                "username": username,
                                "password": password
                            }
                            proxies.append(proxy_config)
                        else:
                            print(f"警告: 跳过无效的代理配置格式: {line}")
                    except Exception as e:
                        print(f"警告: 跳过无效的代理配置: {line} - {e}")
    except FileNotFoundError:
        print(f"错误: 找不到文件 {filename}")
        return []
    return proxies

def get_turnstile_token(proxy_config=None):
    """获取 Turnstile token"""
    try:
        # 本地请求不使用代理
        response = requests.post('http://127.0.0.1:3000/', 
            headers={'Content-Type': 'application/json'},
            json={
                "type": "cftoken",
                "websiteUrl": "https://irys.xyz/api/faucet",
                "websiteKey": "0x4AAAAAAA6vnrvBCtS4FAl-"
            },
            timeout=30
        )
        
        result = response.json()
        if result.get('code') == 200:
            return result['token']
        else:
            print(f"获取token失败: {result.get('message')}")
            return None
    except Exception as e:
        print(f"获取token异常: {e}")
        return None

def claim_faucet(wallet_address, proxy_config=None):
    """领取水龙头"""
    try:
        # 获取 token
        token = get_turnstile_token(proxy_config)
        if not token:
            return False, "获取token失败"
        
        # 构造 headers
        headers = {
            'accept': '*/*',
            'accept-language': 'ja',
            'content-type': 'application/json',
            'cookie': '_ga_N7ZGKKSTW8=GS2.1.s1751726728$o1$g0$t1751726728$j60$l0$h0; _ga=GA1.1.1969698972.1751726728',
            'origin': 'https://irys.xyz',
            'priority': 'u=1, i',
            'referer': 'https://irys.xyz/faucet',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        }
        
        # 构造请求数据
        data = {
            "captchaToken": token,
            "walletAddress": wallet_address
        }
        
        # 创建 tls_client session
        session = tls_client.Session(
            client_identifier="chrome_132",
            random_tls_extension_order=True
        )
        
        # 如果提供了代理配置，则使用代理
        if proxy_config:
            if proxy_config['username'] and proxy_config['password']:
                # 有认证信息的代理
                proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            else:
                # 无认证信息的代理
                proxy_url = f"http://{proxy_config['ip']}:{proxy_config['port']}"
            session.proxies = {"http": proxy_url, "https": proxy_url}
        
        # 发送请求
        response = session.post(
            "https://irys.xyz/api/faucet",
            headers=headers,
            json=data
        )
        
        result = response.json()
        if result.get('success'):
            return True, result.get('message', '领取成功')
        else:
            return False, result.get('message', '领取失败')
            
    except Exception as e:
        return False, f"请求异常: {e}"

def process_wallet(wallet_address, proxy_config=None):
    """处理单个钱包"""
    print(f"\n开始处理钱包: {wallet_address}")
    
    success, message = claim_faucet(wallet_address, proxy_config)
    
    if success:
        print(f"✅ 成功: {wallet_address} - {message}")
    else:
        print(f"❌ 失败: {wallet_address} - {message}")
    
    return wallet_address, success, message

def main():
    """主函数"""
    print("=== Irys 批量水龙头领取工具 ===")
    
    # 加载钱包
    wallets = load_wallets()
    
    if not wallets:
        print("错误: 没有找到有效的钱包地址")
        return
    
    print(f"加载了 {len(wallets)} 个钱包地址")
    
    # 创建结果列表
    results = []
    
    # 逐个处理钱包，每次获取一个代理
    for i, wallet in enumerate(wallets):
        print(f"\n{'='*50}")
        print(f"处理第 {i+1}/{len(wallets)} 个钱包")
        
        # 获取代理
        if USE_API_PROXIES:
            print("获取新的代理...")
            proxies = get_api_proxies(1)
            if proxies:
                proxy = proxies[0]
                print(f"使用代理: {proxy['username']}@{proxy['ip']}:{proxy['port']}")
            else:
                print("警告: 无法获取代理，将直接连接")
                proxy = None
        else:
            # 从文件读取代理
            proxies = load_proxies()
            proxy = proxies[i] if i < len(proxies) else None
            if proxy:
                print(f"使用代理: {proxy['username']}@{proxy['ip']}:{proxy['port']}")
            else:
                print("警告: 没有对应的代理，将直接连接")
        
        # 处理钱包，如果失败且使用API代理，则重试
        max_retries = 3 if USE_API_PROXIES else 1
        success = False
        
        for retry in range(max_retries):
            if retry > 0:
                print(f"重试第 {retry} 次...")
                if USE_API_PROXIES:
                    print("重新获取代理...")
                    proxies = get_api_proxies(1)
                    if proxies:
                        proxy = proxies[0]
                        print(f"使用新代理: {proxy['username']}@{proxy['ip']}:{proxy['port']}")
            
            wallet_result, success, message = process_wallet(wallet, proxy)
            
            if success:
                print(f"✅ 成功: {message}")
                break
            else:
                print(f"❌ 失败: {message}")
                if retry < max_retries - 1:
                    print("等待后重试...")
                    time.sleep(random.uniform(2, 5))
        
        results.append((wallet, success, message))
        
        # 添加延迟，避免请求过于频繁
        if i < len(wallets) - 1:  # 最后一个钱包不需要延迟
            delay = random.uniform(1, 5)
            print(f"等待 {delay:.1f} 秒后处理下一个钱包...")
            time.sleep(delay)
    
    # 打印统计结果
    print(f"\n{'='*50}")
    print("=== 领取结果统计 ===")
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    print(f"总计: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    # 保存结果到文件
    with open('faucet_results.txt', 'w', encoding='utf-8') as f:
        f.write("=== Irys 水龙头领取结果 ===\n")
        f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总计: {total_count}, 成功: {success_count}, 失败: {total_count - success_count}\n\n")
        
        for i, (wallet, success, message) in enumerate(results):
            status = "✅ 成功" if success else "❌ 失败"
            proxy_info = "API动态代理" if USE_API_PROXIES else "文件代理"
            f.write(f"{status}: {wallet} ({proxy_info}) - {message}\n")
    
    print(f"\n详细结果已保存到: faucet_results.txt")

if __name__ == "__main__":
    main() 
