"""
简单测试脚本 - 演示 Workflow API 的使用
"""
from src.core.workflow import Workflow

def test_simple_workflow():
    """测试简单的线性工作流"""
    print("=" * 60)
    print("测试: 简单线性工作流 (问姓名 -> 捕获姓名 -> 感谢)")
    print("=" * 60)

    # 创建 workflow
    workflow = Workflow(
        flow_name="customer_info_collection",
        description="收集客户信息的简单示例"
    )

    # 添加节点
    workflow.add_start_node()
    workflow.add_text_reply("请问您的姓名?", title="Ask Name")
    workflow.add_capture_user_reply("name", "用户姓名", title="Capture Name")
    workflow.add_text_reply("感谢您,{{name}}!", title="Thank You")

    # 打印统计信息
    stats = workflow.get_stats()
    print(f"\n✅ Workflow 创建成功!")
    print(f"   - 工作流名称: {stats['flow_name']}")
    print(f"   - 节点数量: {stats['node_count']} (包括 {stats['node_count'] // 2} 个功能节点 + {stats['node_count'] // 2} 个 Block)")
    print(f"   - 边数量: {stats['edge_count']}")
    print(f"   - 变量数量: {stats['variable_count']}")
    print(f"   - 变量列表: {workflow.variable_tracker.get_variable_names()}")

    # 保存 JSON
    output_path = "output/test_simple_workflow.json"
    workflow.save(output_path)
    print(f"\n✅ JSON 已保存到: {output_path}")

    return workflow


def test_complex_workflow():
    """测试包含条件分支的复杂工作流"""
    print("\n" + "=" * 60)
    print("测试: 复杂工作流 (带条件分支)")
    print("=" * 60)

    # 创建 workflow
    workflow = Workflow(
        flow_name="age_verification",
        description="年龄验证流程"
    )

    # 添加节点
    workflow.add_start_node()
    workflow.add_text_reply("请问您的年龄?", title="Ask Age")
    workflow.add_capture_user_reply("age", "用户年龄", title="Capture Age")

    # 添加条件节点
    block_id, condition_ids = workflow.add_condition(
        if_else_conditions=[
            {
                "condition_name": "成年人",
                "logical_operator": "and",
                "conditions": [
                    {
                        "condition_type": "variable",
                        "comparison_operator": ">=",
                        "condition_value": "18",
                        "condition_variable": "age"
                    }
                ],
                "condition_action": []
            },
            {
                "condition_name": "未成年",
                "logical_operator": "and",
                "conditions": [
                    {
                        "condition_type": "variable",
                        "comparison_operator": "<",
                        "condition_value": "18",
                        "condition_variable": "age"
                    }
                ],
                "condition_action": []
            },
            {
                "condition_name": "Other",
                "logical_operator": "other",
                "conditions": [],
                "condition_action": []
            }
        ],
        title="Age Check"
    )

    # 为每个分支添加不同的回复 (禁用自动连接)
    adult_block = workflow.add_text_reply(
        "欢迎!您已通过年龄验证。",
        title="Adult Welcome",
        auto_connect=False
    )

    minor_block = workflow.add_text_reply(
        "抱歉,您未满18岁,无法继续。",
        title="Minor Rejection",
        auto_connect=False
    )

    other_block = workflow.add_text_reply(
        "年龄格式错误,请重新输入。",
        title="Error Message",
        auto_connect=False
    )

    # 手动连接条件分支
    workflow.connect_condition_branch(block_id, condition_ids[0], adult_block)
    workflow.connect_condition_branch(block_id, condition_ids[1], minor_block)
    workflow.connect_condition_branch(block_id, condition_ids[2], other_block)

    # 打印统计信息
    stats = workflow.get_stats()
    print(f"\n✅ Workflow 创建成功!")
    print(f"   - 工作流名称: {stats['flow_name']}")
    print(f"   - 节点数量: {stats['node_count']}")
    print(f"   - 边数量: {stats['edge_count']}")
    print(f"   - 变量数量: {stats['variable_count']}")
    print(f"   - 条件分支数量: {len(condition_ids)}")

    # 保存 JSON
    output_path = "output/test_complex_workflow.json"
    workflow.save(output_path)
    print(f"\n✅ JSON 已保存到: {output_path}")

    return workflow


def test_llm_workflow():
    """测试包含 LLM 节点的工作流"""
    print("\n" + "=" * 60)
    print("测试: LLM 工作流 (LLM 处理用户输入)")
    print("=" * 60)

    # 创建 workflow
    workflow = Workflow(
        flow_name="llm_greeting",
        description="使用 LLM 生成个性化问候"
    )

    # 添加节点
    workflow.add_start_node()
    workflow.add_text_reply("请告诉我您的姓名和喜好。", title="Ask Info")
    workflow.add_capture_user_reply("user_input", "用户输入", title="Capture Input")

    # 添加 LLM 节点 - 提取信息
    workflow.add_llm_variable_assignment(
        prompt_template="用户输入: {{user_input}}\n\n请从用户输入中提取姓名和喜好,并以 JSON 格式输出:\n{\"name\": \"...\", \"hobbies\": \"...\"}",
        variable_assign="extracted_info",
        title="Extract Info"
    )

    # 添加 LLM 节点 - 生成个性化回复
    workflow.add_llm_reply(
        prompt_template="用户信息: {{extracted_info}}\n\n请生成一段热情友好的问候语。",
        title="Generate Greeting"
    )

    # 打印统计信息
    stats = workflow.get_stats()
    print(f"\n✅ Workflow 创建成功!")
    print(f"   - 工作流名称: {stats['flow_name']}")
    print(f"   - 节点数量: {stats['node_count']}")
    print(f"   - 边数量: {stats['edge_count']}")
    print(f"   - 变量数量: {stats['variable_count']}")
    print(f"   - 变量列表: {workflow.variable_tracker.get_variable_names()}")

    # 保存 JSON
    output_path = "output/test_llm_workflow.json"
    workflow.save(output_path)
    print(f"\n✅ JSON 已保存到: {output_path}")

    return workflow


if __name__ == "__main__":
    print("\n🚀 开始测试 Workflow API\n")

    # 创建 output 目录
    import os
    os.makedirs("output", exist_ok=True)

    # 运行测试
    test_simple_workflow()
    test_complex_workflow()
    test_llm_workflow()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)
    print("\n📁 生成的 JSON 文件:")
    print("   - output/test_simple_workflow.json")
    print("   - output/test_complex_workflow.json")
    print("   - output/test_llm_workflow.json")
    print("\n💡 提示: 可以将生成的 JSON 文件导入 Agent Studio 查看效果")
