"""
测试复杂的订机票流程 - 带循环回退功能

改进点：
1. 信息不完整时，循环回到输入节点让用户重新输入
2. 输入错误时，使用 LLM 智能询问缺失信息
"""
from src.core.workflow import Workflow

# 创建工作流
workflow = Workflow("flight_booking_complete", "完整的机票预订流程", lang="zh")

# 添加 start 节点
workflow.add_start_node()

# ============ 步骤 1: 询问并获取机票需求 ============
welcome_block = workflow.add_text_reply(
    "欢迎使用机票预订系统！请告诉我您的出发地、目的地、出发日期和返程日期（如果是往返）。",
    title="欢迎询问"
)
capture_requirements_block = workflow.add_capture_user_reply(
    "flight_requirements", "机票需求", title="获取需求"
)

# 步骤 2: LLM 提取并验证机票信息
workflow.add_llm_variable_assignment(
    prompt_template="用户输入: {{flight_requirements}}\n\n请从用户输入中提取：出发地、目的地、出发日期、返程日期（如有）。如果信息不完整，返回'incomplete'，否则返回提取的结构化信息。",
    variable_assign="extracted_flight_info",
    title="提取机票信息"
)

# 步骤 3: 验证信息是否完整
condition_block_id, condition_ids = workflow.add_condition(
    if_else_conditions=[
        {
            "condition_name": "信息完整",
            "logical_operator": "and",
            "conditions": [
                {
                    "condition_type": "variable",
                    "comparison_operator": "!=",
                    "condition_value": "incomplete",
                    "condition_variable": "extracted_flight_info"
                }
            ],
            "condition_action": [],
            "condition_id": None
        },
        {
            "condition_name": "信息不完整",
            "logical_operator": "other",
            "conditions": [],
            "condition_action": [],
            "condition_id": None
        }
    ],
    title="验证信息完整性",
    auto_connect=True
)

# 分支 1: 信息完整 - 展示航班选项
show_flights_block = workflow.add_text_reply(
    "正在为您查询航班...\n\n已找到以下航班选项：\n1. 航班 CA1234 - 08:00-10:30 - ¥1200\n2. 航班 MU5678 - 14:00-16:30 - ¥980\n3. 航班 CZ9012 - 18:00-20:30 - ¥850\n\n请输入您想选择的航班编号（1/2/3）",
    title="展示航班",
    auto_connect=False
)
workflow.connect_condition_branch(condition_block_id, condition_ids[0], show_flights_block)

capture_flight_choice_block = workflow.add_capture_user_reply(
    "selected_flight_number", "选择的航班", title="获取航班选择"
)

# 验证航班选择
flight_choice_block_id, flight_choice_ids = workflow.add_condition(
    if_else_conditions=[
        {
            "condition_name": "有效选择",
            "logical_operator": "or",
            "conditions": [
                {"condition_type": "variable", "comparison_operator": "=", "condition_value": "1", "condition_variable": "selected_flight_number"},
                {"condition_type": "variable", "comparison_operator": "=", "condition_value": "2", "condition_variable": "selected_flight_number"},
                {"condition_type": "variable", "comparison_operator": "=", "condition_value": "3", "condition_variable": "selected_flight_number"}
            ],
            "condition_action": [],
            "condition_id": None
        },
        {
            "condition_name": "无效选择",
            "logical_operator": "other",
            "conditions": [],
            "condition_action": [],
            "condition_id": None
        }
    ],
    title="验证航班选择"
)

# 有效选择 - 加入购物车
cart_added = workflow.add_text_reply(
    "✓ 航班已加入购物车！\n\n请问需要几位乘机人的机票？",
    title="加入购物车",
    auto_connect=False
)
workflow.connect_condition_branch(flight_choice_block_id, flight_choice_ids[0], cart_added)

workflow.add_capture_user_reply("passenger_count", "乘机人数量", title="获取乘机人数")

# ============ 步骤 4: 收集乘机人信息 ============
ask_passenger_info_block = workflow.add_text_reply(
    "请提供第1位乘机人的信息：\n- 姓名（中文/拼音）\n- 身份证号\n- 手机号码",
    title="询问乘机人信息"
)
capture_passenger_block = workflow.add_capture_user_reply(
    "passenger_1_info", "第1位乘机人信息", title="获取乘机人1"
)

# LLM 验证乘机人信息
workflow.add_llm_variable_assignment(
    prompt_template="乘机人信息: {{passenger_1_info}}\n\n请验证信息是否包含：姓名、身份证号、手机号。如果完整返回'valid'，否则返回缺失的字段。",
    variable_assign="passenger_1_validation",
    title="验证乘机人1信息"
)

# 验证结果
passenger_valid_block_id, passenger_valid_ids = workflow.add_condition(
    if_else_conditions=[
        {
            "condition_name": "信息有效",
            "logical_operator": "and",
            "conditions": [
                {"condition_type": "variable", "comparison_operator": "=", "condition_value": "valid", "condition_variable": "passenger_1_validation"}
            ],
            "condition_action": [],
            "condition_id": None
        },
        {
            "condition_name": "信息无效",
            "logical_operator": "other",
            "conditions": [],
            "condition_action": [],
            "condition_id": None
        }
    ],
    title="检查乘机人信息"
)

# 信息有效 - 继续收集联系方式
contact_request = workflow.add_text_reply(
    "✓ 乘机人信息已确认！\n\n请提供订单联系方式：\n- 联系人姓名\n- 联系电话\n- 电子邮箱",
    title="询问联系方式",
    auto_connect=False
)
workflow.connect_condition_branch(passenger_valid_block_id, passenger_valid_ids[0], contact_request)

workflow.add_capture_user_reply("contact_info", "联系方式", title="获取联系方式")

# ============ 步骤 5: 生成订单 ============
workflow.add_llm_variable_assignment(
    prompt_template="航班: {{selected_flight_number}}, 乘机人: {{passenger_1_info}}, 联系方式: {{contact_info}}\n\n生成订单号（格式：FT + 12位数字）并计算总金额。",
    variable_assign="order_info",
    title="生成订单"
)

workflow.add_text_reply(
    "订单已生成！\n\n订单信息：{{order_info}}\n\n请选择支付方式：\n1. 信用卡支付\n2. 支付宝\n3. 微信支付\n\n请输入选项编号：",
    title="展示订单"
)

workflow.add_capture_user_reply("payment_method", "支付方式", title="获取支付方式")

# ============ 步骤 6: 信用卡支付流程 ============
payment_method_block_id, payment_method_ids = workflow.add_condition(
    if_else_conditions=[
        {
            "condition_name": "信用卡",
            "logical_operator": "and",
            "conditions": [
                {"condition_type": "variable", "comparison_operator": "=", "condition_value": "1", "condition_variable": "payment_method"}
            ],
            "condition_action": [],
            "condition_id": None
        },
        {
            "condition_name": "其他支付",
            "logical_operator": "other",
            "conditions": [],
            "condition_action": [],
            "condition_id": None
        }
    ],
    title="判断支付方式"
)

# 信用卡支付分支
ask_card_info_block = workflow.add_text_reply(
    "请输入信用卡信息：\n- 卡号（16位）\n- 有效期（MM/YY）\n- CVV（3位）\n- 持卡人姓名",
    title="请求信用卡信息",
    auto_connect=False
)
workflow.connect_condition_branch(payment_method_block_id, payment_method_ids[0], ask_card_info_block)

capture_card_block = workflow.add_capture_user_reply(
    "credit_card_info", "信用卡信息", title="获取卡信息"
)

# LLM 验证信用卡格式
workflow.add_llm_variable_assignment(
    prompt_template="信用卡信息: {{credit_card_info}}\n\n验证卡号是否为16位数字，有效期格式是否正确（MM/YY），CVV是否为3位数字。返回'valid'或具体错误。",
    variable_assign="card_validation",
    title="验证卡信息"
)

# 验证信用卡
card_valid_block_id, card_valid_ids = workflow.add_condition(
    if_else_conditions=[
        {
            "condition_name": "卡信息有效",
            "logical_operator": "and",
            "conditions": [
                {"condition_type": "variable", "comparison_operator": "=", "condition_value": "valid", "condition_variable": "card_validation"}
            ],
            "condition_action": [],
            "condition_id": None
        },
        {
            "condition_name": "卡信息无效",
            "logical_operator": "other",
            "conditions": [],
            "condition_action": [],
            "condition_id": None
        }
    ],
    title="检查卡信息"
)

# 卡信息有效 - 处理支付
payment_success = workflow.add_text_reply(
    "正在处理支付...\n\n✓ 支付成功！\n\n您的机票预订已完成！\n订单号：{{order_info}}\n\n电子票将发送至：{{contact_info}}\n\n感谢您的使用，祝您旅途愉快！",
    title="支付成功",
    auto_connect=False
)
workflow.connect_condition_branch(card_valid_block_id, card_valid_ids[0], payment_success)

# 其他支付方式分支
other_payment = workflow.add_text_reply(
    "正在跳转至支付页面...\n\n请在打开的页面中完成支付。",
    title="其他支付方式",
    auto_connect=False
)
workflow.connect_condition_branch(payment_method_block_id, payment_method_ids[1], other_payment)

# ============ 错误处理 - 带循环回退 ============

# 1. 机票信息不完整 -> 使用 LLM 智能提示缺失信息，然后回到输入节点
info_incomplete_llm = workflow.add_llm_reply(
    prompt_template="用户输入: {{flight_requirements}}\n提取结果: {{extracted_flight_info}}\n\n请友好地告诉用户哪些信息缺失，并引导他们补充。例如：'您好，我注意到您还没有提供目的地，请问您想去哪里呢？'",
    title="智能提示缺失信息",
    auto_connect=False
)
workflow.connect_condition_branch(condition_block_id, condition_ids[1], info_incomplete_llm)
# 循环回到获取需求节点
workflow.connect_nodes(info_incomplete_llm, capture_requirements_block)

# 2. 航班选择无效 -> 提示错误后回到选择节点
invalid_flight = workflow.add_text_reply(
    "❌ 无效的航班选择！请输入 1、2 或 3 来选择对应的航班。",
    title="航班选择错误",
    auto_connect=False
)
workflow.connect_condition_branch(flight_choice_block_id, flight_choice_ids[1], invalid_flight)
# 循环回到获取航班选择节点
workflow.connect_nodes(invalid_flight, capture_flight_choice_block)

# 3. 乘机人信息无效 -> 使用 LLM 智能提示缺失字段，然后回到输入节点
passenger_invalid_llm = workflow.add_llm_reply(
    prompt_template="用户输入的乘机人信息: {{passenger_1_info}}\n验证结果: {{passenger_1_validation}}\n\n请友好地告诉用户哪些信息缺失或格式错误，并引导他们重新提供完整的乘机人信息（姓名、身份证号、手机号）。",
    title="智能提示乘机人信息错误",
    auto_connect=False
)
workflow.connect_condition_branch(passenger_valid_block_id, passenger_valid_ids[1], passenger_invalid_llm)
# 循环回到获取乘机人信息节点
workflow.connect_nodes(passenger_invalid_llm, capture_passenger_block)

# 4. 信用卡信息无效 -> 使用 LLM 智能提示错误，然后回到输入节点
card_error_llm = workflow.add_llm_reply(
    prompt_template="用户输入的信用卡信息: {{credit_card_info}}\n验证结果: {{card_validation}}\n\n请友好地告诉用户信用卡信息有什么问题，并引导他们重新输入正确的信用卡信息（卡号、有效期、CVV、持卡人姓名）。",
    title="智能提示卡信息错误",
    auto_connect=False
)
workflow.connect_condition_branch(card_valid_block_id, card_valid_ids[1], card_error_llm)
# 循环回到获取卡信息节点
workflow.connect_nodes(card_error_llm, capture_card_block)

# ============ 保存 ============
filepath = workflow.save("output/flight_booking_complete.json")
print(f"\n✅ 完整的机票预订流程已生成（带循环回退）！")
print(f"📄 文件: {filepath}")

# 打印统计
stats = workflow.get_stats()
print(f"\n📊 统计信息:")
for key, value in stats.items():
    print(f"   - {key}: {value}")

print(f"\n🔄 循环回退功能:")
print(f"   - 机票信息不完整 -> LLM智能提示 -> 重新输入")
print(f"   - 航班选择无效 -> 错误提示 -> 重新选择")
print(f"   - 乘机人信息错误 -> LLM智能提示 -> 重新输入")
print(f"   - 信用卡信息错误 -> LLM智能提示 -> 重新输入")
