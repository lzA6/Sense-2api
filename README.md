
<div align="center">

# 🌉 Sense-2api：您的私人商量(SenseChat) to OpenAI 协议转换桥梁 🚀

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Docker Support](https://img.shields.io/badge/Docker-Ready-blue.svg?logo=docker)](https://www.docker.com/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-lzA6/Sense--2api-blue?logo=github)](https://github.com/lzA6/Sense-2api)

**一个将商量(SenseChat)的非官方 Web 接口巧妙伪装成 OpenAI 标准格式的开源项目，让您心爱的应用无缝接入强大的商量模型！**

</div>

---

> “我们不是在编写代码，我们是在构建桥梁。每一行指令，都是通往更广阔世界的一块基石。Sense-2api 不仅仅是一个工具，它是一种信念——相信技术的力量可以打破壁垒，连接思想，让每一个人都能轻松驾驭未来。”

## ✨ 项目缘起：一个美丽的“谎言”

想象一下，您有一个非常棒的应用程序，它说着一口流利的 "OpenAI 语"，但您内心深处却渴望着商量(SenseChat)那独特而强大的对话能力。怎么办？难道要让您的应用从头开始学习一门新的、复杂的、甚至没有公开文档的语言吗？

不！我们选择了一种更优雅、更具智慧的方式——**创造一个完美的翻译官**。

Sense-2api 就是这个翻译官。它站在您的应用和商量服务器之间，将每一个 OpenAI 格式的请求，都实时、无损地翻译成商量能听懂的语言；反之，它又将商量的回应，精心包装成您的应用所熟悉的 OpenAI 格式。

这，就是一个美丽的“谎言”。您的应用自始至终都以为自己在和 OpenAI 对话，而实际上，它正在享受商量模型带来的澎湃动力！

## 核心特性：您的瑞士军刀 🛠️

*   **🤖 高度兼容 OpenAI**：就像一位语言天才，完美模拟了 `/v1/chat/completions` 和 `/v1/models` 接口，支持流式（Streaming）与非流式输出。
*   **🔑 智能账户池管理**：这不仅仅是一个密钥管理器，更是一位智慧的“钥匙管理员”。它能自动轮换账户凭证（Token & Cookie），确保服务 24/7 稳定在线。
*   **🚀 现代化技术栈**：基于 `FastAPI` + `Uvicorn` 构建，拥有闪电般的性能和强大的异步处理能力。
*   **🛡️ 浏览器行为模拟**：通过预热请求（Pre-heating）和精心构造的请求头，最大限度地模拟真实浏览器行为，提高稳定性。
*   **📦 一键部署**：无论您是 Docker 的信徒，还是喜欢在本地运行，我们都为您准备了“懒人一键部署”方案。
*   **📝 配置简单**：所有配置项都集中在 `.env` 文件中，清晰明了，易于修改。

## 🏛️ 宏伟蓝图：它是如何工作的？

这个项目的核心思想是“**拦截、转换与适配**”。让我们深入这座桥梁的内部，看看它的精密构造。

<div align="center">
<img src="https://user-images.githubusercontent.com/87383333/293931948-2a68872c-8121-4141-813a-111181111111.png" alt="架构图" width="800"/>
<p><em>上图：Sense-2api 工作流程示意图</em></p>
</div>

1.  **入口与守卫 (`main.py`)**
    *   **大白话解释**：这是项目的“前门”和“接待员”。它使用 `FastAPI` 框架搭建了一个网络服务，负责监听所有进来的请求。当有访客（API 请求）到来时，它会检查访客是否持有正确的“门票”（`API_MASTER_KEY`）。
    *   **技术点**：
        *   `FastAPI`：一个现代、高性能的 Python Web 框架，提供异步支持和自动 API 文档。
        *   `Depends(verify_api_key)`：FastAPI 的依赖注入系统。在处理请求前，会先调用 `verify_api_key` 函数进行身份验证，确保了接口的安全性。

2.  **总指挥与翻译官 (`sense_provider.py`)**
    *   **大白话解释**：这是整个项目的灵魂！它接收到 OpenAI 格式的“设计图”（请求），然后 meticulously 地将其转换为商量能看懂的“施工图”。
    *   **核心流程**：
        1.  **轮换账户**：从配置好的账户池中，按顺序取出一个 `auth_token` 和 `cookie`。
        2.  **模拟预热**：调用 `_preheat_session` 方法，发送几个“热身”请求，模仿真实浏览器加载页面时的行为，让会话看起来更像一个真实用户。
        3.  **加密载荷**：调用 `_encrypt_data` 方法，对请求体进行一种特殊的 Base64 变体加密，这是商量 Web 端的一个安全措施。
        4.  **发送请求**：将转换并加密后的请求发送给商量的聊天接口。
        5.  **解析与转换响应**：无论是流式还是非流式，它都会将商量返回的数据块（chunk）实时翻译成 OpenAI 的格式再发回给客户端。
    *   **技术点**：
        *   `httpx.AsyncClient`: 一个功能强大的异步 HTTP 客户端，是处理高并发网络请求的利器。
        *   `_stream_generator`: 一个异步生成器，这是实现流式响应（打字机效果）的关键。它逐行读取上游响应，并实时转换为 OpenAI 的 `chat.completion.chunk` 格式。
        *   `_encrypt_data`: 这个函数揭示了前端与后端通信时的一个小“花招”。它先进行 Base64 编码，然后将编码后的字符串一分为二，再交错合并。这是一种简单的混淆，而非真正的强加密。

3.  **配置中心 (`config.py`)**
    *   **大白话解释**：这是项目的“控制面板”。它负责从 `.env` 文件中读取所有的配置信息，比如 API 密钥、商量账户信息等，并提供给项目其他部分使用。
    *   **技术点**：
        *   `pydantic-settings`: 一个强大的配置管理库。它能自动从环境变量或 `.env` 文件中读取、验证和转换配置。
        *   `@property`: Python 的装饰器，将方法变成了只读属性。这里巧妙地用它来将 `.env` 中以逗号分隔的字符串（如 `SENSE_API_KEYS_STR`）实时解析成 Python 列表，代码既干净又高效。

## 📂 项目文件结构

```
.
├── app
│   ├── core
│   │   ├── __init__.py
│   │   └── config.py         # ⚙️ 配置中心，管理所有环境变量
│   ├── providers
│   │   ├── __init__.py
│   │   ├── base.py           # 🦴 提供者基类 (为未来扩展准备)
│   │   └── sense_provider.py # 🧠 核心逻辑，负责API转换与请求
│   └── __init__.py
├── docker-compose.yml        # 🐳 Docker编排文件，定义服务
├── Dockerfile                # 🏗️ Docker镜像构建文件
├── main.py                   # 🚀 FastAPI应用主入口
├── nginx.conf                # 🛡️ Nginx配置文件 (可选，用于负载均衡)
├── requirements.txt          # 📦 Python依赖列表
├── .env                      # 🔑 你的私人配置文件 (需要自己创建)
└── .env.example              # 📝 .env文件的模板
```

---

## 🚀 快速开始：三分钟，开启您的 AI 之旅！

选择您最喜欢的冒险方式，让我们即刻出发！

### 方式一：Docker - 懒人福音 🐳 (强烈推荐)

这是最简单、最省心的方式。您不需要关心环境配置，只需几条命令。

**1. 准备工作**

*   安装 [Docker](https://www.docker.com/get-started) 和 [Docker Compose](https://docs.docker.com/compose/install/)。
*   克隆本项目：
    ```bash
    git clone https://github.com/lzA6/Sense-2api.git
    cd Sense-2api
    ```

**2. 创建您的“秘密指令” (`.env` 文件)**

*   项目根目录下有一个 `.env.example` 文件。复制它并重命名为 `.env`：
    ```bash
    cp .env.example .env
    ```
*   **这是最关键的一步！** 打开 `.env` 文件，填入你自己的商量账户信息。

    **如何获取 `SENSE_API_KEYS_STR` 和 `SENSE_COOKIES_STR`？**
    1.  在浏览器中登录 [商量 SenseChat 官网](https://chat.sensetime.com/)。
    2.  按 `F12` 打开开发者工具，切换到 “网络 (Network)” 选项卡。
    3.  随便发送一条消息，然后在网络请求列表中找到名为 `chat` 的请求。
    4.  点击 `chat` 请求，在右侧的 “标头 (Headers)” 中找到 “请求标头 (Request Headers)”。
    5.  `Authorization`: `Bearer ` 后面的那一长串字符就是你的 `SENSE_API_KEYS_STR`。
    6.  `cookie`: 整行 `cookie` 的值就是你的 `SENSE_COOKIES_STR`。

*   将获取到的值填入 `.env` 文件，并设置你自己的 `API_MASTER_KEY` 作为访问密码。

**3. 启动帝国！**

*   在项目根目录，运行：
    ```bash
    docker-compose up -d
    ```
    这条命令会启动一个 Nginx 负载均衡器和一个 API 服务实例。

**4. 验证**

*   您的服务现在运行在 `http://localhost:8080`。您可以像使用 OpenAI API 一样调用它了！

### 方式二：本地部署 - 传统手艺人的选择 👨‍💻

如果您想完全掌控一切，可以手动在本地运行。

1.  **环境准备**：确保您已安装 Python 3.10+。
2.  **克隆项目**：
    ```bash
    git clone https://github.com/lzA6/Sense-2api.git
    cd Sense-2api
    ```
3.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```
4.  **配置**：同样，复制 `.env.example` 为 `.env` 并按照上面的教程填入你的信息。
5.  **启动服务**：
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
6.  服务将运行在 `http://localhost:8000`。

---

## ⚙️ 配置详解：您的专属控制面板

通过 `.env` 文件，您可以精细地调整服务的行为。这是 `.env.example` 的内容，您可以直接复制创建 `.env` 文件。

```env
# --------------------------------------------------------------------------
# Sense-2api Configuration
# --------------------------------------------------------------------------

# 【必填】主控访问密钥，用于客户端访问此代理服务，请务必修改为一个复杂的密码！
# 对应请求头中的 Authorization: Bearer <API_MASTER_KEY>
API_MASTER_KEY="sk-your-secret-key"

# 【必填】商量(SenseChat)的认证Token
# 获取方法：登录官网 -> F12开发者工具 -> 网络 -> 找到'chat'请求 -> 请求头 -> 复制'Authorization'中'Bearer '后面的部分
# 如果有多个账户，用英文逗号(,)隔开，程序会自动轮换
SENSE_API_KEYS_STR="eyJhbGciOiJIU...YourTokenHere...,another-token-if-you-have"

# 【必填】商量(SenseChat)的Cookie
# 获取方法：同上，在'chat'请求的请求头中，复制'cookie'的完整值
# 如果有多个账户，同样用英文逗号(,)隔开，请与上面的Token顺序对应
SENSE_COOKIES_STR="acw_tc=...YourCookieHere...,another-cookie-if-you-have"

# 【可选】模型映射关系
# 如果商量更新了模型ID，可以在这里修改，左边是OpenAI格式的模型名，右边是商量实际的模型ID
MODEL_MAPPING_STR='{"sense-chat-pro": "nova-ptc-xl-v1"}'
```

---

## 🎯 使用示例：见证奇迹的时刻

现在，让我们用一个简单的 Python 脚本来调用我们的 API。

```python
import requests
import json

# 你的 API 服务地址和密钥
# 如果使用 Docker Compose, 端口是 8080; 如果是本地部署, 默认是 8000
API_BASE_URL = "http://localhost:8080"
# 替换为你在 .env 中设置的 API_MASTER_KEY
API_KEY = "sk-your-secret-key"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# 用户的请求
messages = [
    {"role": "user", "content": "你好，请介绍一下你自己"}
]

# 构建请求体
data = {
    "model": "sense-chat-pro",  # 这是在 config.py 中定义的模型名
    "messages": messages,
    "stream": False  # 设置为 True 可以体验流式输出
}

# 发送请求
try:
    print("正在向 Sense-2api 发送请求...")
    response = requests.post(
        f"{API_BASE_URL}/v1/chat/completions",
        headers=headers,
        json=data
    )
    response.raise_for_status()  # 如果请求失败，则抛出异常

    # 解析响应
    result = response.json()
    print("🤖 模型回答：")
    print(result["choices"]["message"]["content"])

except requests.exceptions.RequestException as e:
    print(f"请求出错了: {e}")
    print(f"响应内容: {e.response.text if e.response else 'N/A'}")

```

---

## 🧐 项目深度解析

### 👍 优点 (Pros)

1.  **无缝集成 (★★★★★)**：最大的优点！它让大量现有的、基于 OpenAI API 开发的生态工具、应用、客户端（如 NextChat, LobeChat）都能立刻使用商量模型，学习成本几乎为零。
2.  **稳定可靠 (★★★★☆)**：内置的账户轮换机制和完整的浏览器行为模拟，大大增强了服务的健壮性，能有效应对单个账户失效或网络不稳定的情况。
3.  **高性能 (★★★★☆)**：采用现代化的 FastAPI 和 Uvicorn，保证了 API 的高吞吐和低延迟。
4.  **易于部署 (★★★★★)**：提供了开箱即用的 Docker-Compose 配置，对新手极其友好，真正实现了一键启动。

### 👎 缺点与风险 (Cons)

1.  **依赖于非公开接口 (高风险)**：本项目强依赖于商量的 Web 端非公开 API。如果官方对 API 进行修改（例如更改加密方式、请求路径、增加验证码等）、限制或关闭，本项目可能会立刻失效。这是一种“寄生”关系，存在极高的不确定性。
2.  **潜在的合规风险 (用户自负)**：模拟和转换第三方 API 可能涉及服务条款（ToS）问题。**本项目仅供学习和技术研究，严禁用于任何商业或非法用途，使用者需自行承担一切风险。**
3.  **维护成本 (中等)**：由于依赖于随时可能变化的非官方接口，需要持续关注上游变化并及时更新代码以保持可用性。

### 适用场景

*   **个人开发者**：希望在自己的小项目或原型中使用商量模型，但又不想研究和适配其非官方接口。
*   **学习与研究**：深入理解 API 转换、SSE 流处理、反向工程、HTTP 客户端使用等技术的绝佳案例。
*   **AI 应用爱好者**：希望在各种支持 OpenAI 协议的第三方客户端中体验商量模型。

---

## 🧭 项目状态与未来展望

### ✅ 已完成的功能

*   **核心转换**：实现了 `v1/chat/completions` 接口的请求和响应转换。
*   **流式输出**：完美支持流式响应，提供优秀的打字机体验。
*   **模型列表**：实现了 `v1/models` 接口，可以返回支持的模型列表。
*   **账户轮询**：支持配置多个账户，并按顺序轮流使用。
*   **Docker化**：提供了完整的 Docker 和 Docker-Compose 支持。

### 🚧 不足与待实现

1.  **错误处理**：目前的错误处理较为简单。当上游返回特定错误码（如需要验证）时，无法智能处理，只能简单地返回错误信息。
2.  **Function Calling / Tool Usage**：**暂未支持**。这是 OpenAI API 的一个高级功能，需要对商量的接口进行更深入的逆向工程，才能知道是否可以适配。
3.  **配置热重载**：修改 `.env` 文件后，需要重启服务才能生效。
4.  **加密方式的脆弱性**：`_encrypt_data` 中的加密逻辑是固定的。如果商量前端更新了加密算法，此项目会立即失效。

### 🌌 星辰大海的征途 (未来扩展方向)

*   **支持更多模型后端 (★★★★★)**：项目的 `providers` 结构已经为此做好了准备。未来可以编写更多的 `transformer`，来支持其他优秀的国产大模型，让 Sense-2api 成为一个真正的“万能转换器”。
*   **可视化管理面板 (★★★★☆)**：开发一个简单的 Web UI，可以实时查看账户池状态、请求日志、统计数据，甚至在线热更新配置。
*   **智能账户管理 (★★★★☆)**：当某个账户连续失败多次后，能自动将其“冷冻”一段时间，而不是简单轮询。
*   **插件化架构 (★★★☆☆)**：将核心逻辑与模型适配层分离，允许社区开发者轻松编写插件来支持新的模型或功能。

---

## ❤️ 贡献：众人拾柴火焰高

我们相信开源的力量，也相信每一个人的智慧。如果您对这个项目有任何想法、建议或发现了 Bug，都热烈欢迎您：

1.  **提交 Issue**：有任何问题或新功能建议，请不要犹豫，在 [GitHub Issues](https://github.com/lzA6/Sense-2api/issues) 中告诉我们。
2.  **发起 Pull Request**：如果您修复了 Bug 或实现了新功能，请大胆地提交 PR！我们非常乐意与您一起完善这个项目。

让我们一起，把这座桥建得更宽、更长、更坚固！

## 📜 开源协议

本项目采用 **Apache 2.0** 开源协议。

这意味着您可以自由地使用、修改和分发本软件，无论是商业还是非商业用途，但需要遵守协议中的相关条款。

```text
Copyright 2025 lzA6

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

**最后，感谢您的阅读。愿代码与您同在，愿探索精神永不熄灭！**
```
