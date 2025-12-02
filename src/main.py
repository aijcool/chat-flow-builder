"""
主入口程序 - Chatflow Tailor

提供命令行界面供用户与 Agent 交互生成 chatflow
"""
import sys
import os
from .utils.config import get_config
from .agent.chatflow_agent import ChatflowAgent


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          🤖  Chatflow Tailor  🤖                         ║
║                                                          ║
║      Claude Agent for Workflow Generation                ║
║      将自然语言转换为 Agent Studio Chatflow              ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = """
💡 使用提示:

对话模式:
- 描述您想要的对话流程,Agent 会帮您生成
- 例如: "我想要一个收集客户信息的流程,先问姓名,再问邮箱,最后确认"
- Agent 会主动询问细节(如工作流名称等)

快速模式 (命令行参数):
- python -m src.main --quick "询问姓名,获取姓名,发送感谢" --name customer_info

命令:
- exit/quit: 退出程序
- reset: 重置对话历史
- help: 显示此帮助信息

示例对话流程:
  User: 我想创建一个简单的问答流程
  Agent: 好的!请描述具体的问答内容。
  User: 先问用户姓名,获取姓名,然后说"你好,{姓名}!"
  Agent: 明白了。请问这个工作流叫什么名字?
  User: greeting_flow
  Agent: [生成并保存] 已成功生成并保存到 output/greeting_flow.json
"""
    print(help_text)


def interactive_mode():
    """交互式对话模式"""
    # 加载配置
    try:
        config = get_config()
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("\n请确保 .env 文件包含以下内容:")
        print("BASE_URL=https://api.moonshot.cn/anthropic")
        print("API_KEY=your-api-key-here")
        sys.exit(1)

    # 初始化 Agent
    print("\n🔧 初始化 Agent...")
    agent = ChatflowAgent(
        api_key=config.api_key,
        base_url=config.base_url
    )
    print("✅ Agent 已就绪!\n")

    print_help()

    # 发送初始问候
    initial_greeting = agent.chat("你好!请介绍一下你自己。")
    print(f"\n🤖 Agent: {initial_greeting}\n")

    # 对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("👤 You: ").strip()

            if not user_input:
                continue

            # 处理命令
            if user_input.lower() in ["exit", "quit"]:
                print("\n👋 再见!")
                break

            elif user_input.lower() == "reset":
                agent.reset_conversation()
                print("\n🔄 对话历史已重置\n")
                continue

            elif user_input.lower() == "help":
                print_help()
                continue

            # 发送给 Agent
            response = agent.chat(user_input)
            print(f"\n🤖 Agent: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break

        except Exception as e:
            print(f"\n❌ 错误: {e}\n")


def quick_mode(description: str, workflow_name: str, lang: str = "auto"):
    """快速生成模式 (非对话)"""
    # 加载配置
    try:
        config = get_config()
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        sys.exit(1)

    # 初始化 Agent
    print("\n🔧 初始化 Agent...")
    agent = ChatflowAgent(
        api_key=config.api_key,
        base_url=config.base_url
    )

    # 快速生成
    print(f"\n🚀 开始生成 workflow: {workflow_name}")
    print(f"📝 描述: {description}\n")

    result = agent.quick_generate(description, workflow_name, lang)

    if result["success"]:
        print(f"\n✅ 成功!")
        print(f"📄 文件: {result['filepath']}")
        print(f"📊 统计:")
        for key, value in result["stats"].items():
            print(f"   - {key}: {value}")
    else:
        print(f"\n❌ 失败: {result.get('message', 'Unknown error')}")


def main():
    """主函数"""
    # 确保 output 目录存在
    os.makedirs("output", exist_ok=True)

    # 打印横幅
    print_banner()

    # 解析命令行参数
    if len(sys.argv) > 1:
        # 快速模式
        if "--quick" in sys.argv:
            try:
                quick_index = sys.argv.index("--quick")
                description = sys.argv[quick_index + 1]

                name_index = sys.argv.index("--name")
                workflow_name = sys.argv[name_index + 1]

                lang = "auto"
                if "--lang" in sys.argv:
                    lang_index = sys.argv.index("--lang")
                    lang = sys.argv[lang_index + 1]

                quick_mode(description, workflow_name, lang)

            except (IndexError, ValueError):
                print("❌ 参数错误!")
                print("\n使用方法:")
                print('  python -m src.main --quick "描述" --name workflow_name [--lang zh/en/auto]')
                sys.exit(1)

        elif "--help" in sys.argv or "-h" in sys.argv:
            print_help()

        else:
            print("❌ 未知参数!")
            print("使用 --help 查看帮助")
            sys.exit(1)

    else:
        # 交互模式
        interactive_mode()


if __name__ == "__main__":
    main()
