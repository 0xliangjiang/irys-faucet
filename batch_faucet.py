import tls_client
import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
            proxy_url = f"http://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['ip']}:{proxy_config['port']}"
            session.proxies = {"http": proxy_url, "https": proxy_url}
            print(f"使用代理: {proxy_config['ip']}:{proxy_config['port']}")
        
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
    
    # 加载钱包和代理
    wallets = load_wallets()
    proxies = load_proxies()
    
    if not wallets:
        print("错误: 没有找到有效的钱包地址")
        return
    
    print(f"加载了 {len(wallets)} 个钱包地址")
    print(f"加载了 {len(proxies)} 个代理配置")
    
    # 如果没有代理，使用None
    if not proxies:
        print("警告: 没有代理配置，将直接连接")
        proxies = [None]
    
    # 创建结果列表
    results = []
    
    # 使用线程池处理
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        
        for i, wallet in enumerate(wallets):
            # 轮询使用代理
            proxy = proxies[i % len(proxies)] if proxies else None
            future = executor.submit(process_wallet, wallet, proxy)
            futures.append(future)
            
            # 添加随机延迟，避免请求过于频繁
            time.sleep(random.uniform(2, 5))
        
        # 收集结果
        for future in as_completed(futures):
            wallet, success, message = future.result()
            results.append((wallet, success, message))
    
    # 打印统计结果
    print("\n=== 领取结果统计 ===")
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
        
        for wallet, success, message in results:
            status = "✅ 成功" if success else "❌ 失败"
            f.write(f"{status}: {wallet} - {message}\n")

if __name__ == "__main__":
    main() 