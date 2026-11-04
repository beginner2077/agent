# CS146S 9/22 课堂示例：DeepSeek Flash 适配及详细中文注释版。
# 原始来源为课程官网链接的 coding_agent_from_scratch.py。
# 未注释原版保存在同目录 lecture-9-22-official.original.py，原版共 193 行。
# 此前课堂讲解中的原始行号请对照原版；本文件加入注释后，行号会后移。
#
# 阅读主线：真实 Python 工具 → 工具说明 → 模型回复 → 解析请求 → 本机执行 → 结果回填。
# 这是一个采用自定义文本工具协议的最小 Agent，不是 Claude Code 的实现源码。
# 英文提示字符串及工具 docstring 保留；模型接入和初始指令角色已适配 DeepSeek。
# 适配前的 303 行中文注释版另存为 lecture-9-22-official.before-deepseek.py。
# 特别注意：函数 docstring 会通过 __doc__ 被加入提示，修改它会改变模型输入。

# inspect 用于从工具函数提取参数签名，让模型知道各工具需要哪些参数。
import inspect
# json 同时负责解析模型给出的工具参数，以及序列化发回模型的工具结果。
import json
# os 用于读取可选的配置文件路径覆盖，不从 OPENAI_API_KEY 获取密钥。
import os
# DeepSeek 官方支持 OpenAI SDK 的 Responses 接口；SDK 名称不代表请求发往 OpenAI。
from openai import OpenAI
# 这些类型注解用于说明接口，也会出现在工具签名中；它们不会自动校验运行时参数。
from typing import List, Dict, Any, Tuple
# Path 封装路径处理、目录遍历和文件读写。
from pathlib import Path

# 复用你平时 claude --settings 指定的命名配置，只读取服务地址和密钥。
# 这里不会启动 Claude Code，也不会加载它的 Skills、Hooks 或权限规则。
# 可通过项目专用环境变量选择其他配置文件；默认仍是 settings-deepseek.json。
DEEPSEEK_SETTINGS_PATH = Path(os.environ.get(
    "CS146S_DEEPSEEK_SETTINGS",
    str(Path.home() / ".claude" / "settings-deepseek.json"),
)).expanduser()
# 按本次学习要求明确使用 Flash，不继承该配置中可能仍为 Pro 的主模型设置。
DEEPSEEK_MODEL = "deepseek-flash"


def load_deepseek_settings(settings_path: Path) -> Dict[str, str]:
    # 配置可能含密钥。读取失败时只提示路径和检查方向，不输出原文件或解析内容。
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise RuntimeError(
            f"无法读取 DeepSeek 配置：{settings_path}。请检查文件路径和 JSON 格式。"
        ) from None
    if not isinstance(settings, dict) or not isinstance(settings.get("env"), dict):
        raise RuntimeError("DeepSeek 配置需要包含 env 对象。")
    env = settings["env"]
    # 当前命名配置使用 ANTHROPIC_AUTH_TOKEN；也接受兼容接口的 API_KEY 字段。
    api_key = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        raise RuntimeError("DeepSeek 配置缺少 ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY。")
    # 同一服务的两个协议入口不同：Claude 配置用 /anthropic，Responses 用根地址。
    # 明确核对域名，避免把该密钥发给旧代理、其他服务或 SDK 默认的 OpenAI 地址。
    base_url = env.get("ANTHROPIC_BASE_URL", "")
    if not isinstance(base_url, str) or base_url.rstrip("/") not in (
        "https://api.deepseek.com/anthropic", "https://api.deepseek.com"
    ):
        raise RuntimeError("该课堂样例要求配置中的服务地址为官方 DeepSeek HTTPS 入口。")
    return {"api_key": api_key.strip(), "base_url": "https://api.deepseek.com"}


# 创建客户端本身不发模型请求；首次请求仍发生在 execute_llm_call()。
# 这里显式设置密钥与 base_url，不会回落到 OPENAI_API_KEY 或 OpenAI 默认服务。
DEEPSEEK_SETTINGS = load_deepseek_settings(DEEPSEEK_SETTINGS_PATH)
deepseek_client = OpenAI(
    api_key=DEEPSEEK_SETTINGS["api_key"],
    base_url=DEEPSEEK_SETTINGS["base_url"],
)

# 提示模板由后面的 create_full_system_prompt() 填入工具清单。
# {tool_list_str} 是待替换位置；模板里的 {{JSON_ARGS}} 使用双花括号，
# 避免 str.format() 将其当作另一个占位符，格式化后会保留单层花括号。
# 这里约定模型用 tool: 工具名(JSON参数) 表达调用，不使用原生工具调用内容块。
# 英文提示的意图：协助完成编程任务；需要工具时只输出约定的单行调用，参数用双引号 JSON；
# 收到 tool_result(...) 后继续处理任务；不需要工具时，正常输出面向用户的回复。
# 原课堂代码使用 developer；DeepSeek 适配版使用 system，见主循环初始化。
SYSTEM_PROMPT = """
You are a helpful coding assistant whose goal is to help complete coding tasks. 
You have access to a series of tools you can execute. Here are the tools you have access to:

{tool_list_str}

When you want to use a tool reply with exactly one line in the format: 'tool: TOOL_NAME({{JSON_ARGS}})' and nothing else.
Use compact single-line JSON with double quotes. After receiving a tool_result(...) message, continue the task.
If no tool is needed, respond normally.
"""

# ANSI 颜色转义序列只影响终端显示，不属于发送给模型的对话内容。
YOU_COLOR = "\u001b[94m"
ASSISTANT_COLOR = "\u001b[93m"
RESET_COLOR = "\u001b[0m"

def resolve_abs_path(path_str: str) -> Path:
    # 展开路径开头的 ~，例如 ~/demo.py 指向当前用户主目录下的文件。
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        # 相对路径基于进程当前工作目录，不是本脚本所在目录。
        # 此分支再调用 resolve()，将相对路径解析成绝对路径。
        path = (Path.cwd() / path).resolve()
    # 绝对路径直接返回；这个函数没有实现“必须位于项目目录内”的访问限制。
    return path

# 工具一：读取文件。英文 docstring 保留原文，后续会作为工具描述提供给模型。
def read_file_tool(filename: str) -> Dict[str, Any]:
    """
    Gets the full content of a file provided by the user.
    :param filename: The name of the file to read.
    :return: The full content of the file.
    """
    # 把模型传来的文件名转换为本机可用的路径。
    full_path = resolve_abs_path(filename)
    # 仅向终端打印路径，便于观察；真正的文件内容通过下方返回值交给调用者。
    print(full_path)
    # 这里没有显式指定编码，使用 Python 当前环境的默认文本编码。
    # 文件不存在、目标是目录或读取失败时会抛异常，本函数没有自行捕获。
    with open(str(full_path), "r") as f:
        content = f.read()
    # 返回普通 Python 字典。主循环稍后将其转为 JSON，再放入对话。
    return {
        "file_path": str(full_path),
        "content": content
    }

# 工具二：列出目录的直接子项，用于让模型先了解文件分布。
def list_files_tool(path: str) -> Dict[str, Any]:
    """
    Lists the files in a directory provided by the user.
    :param path: The path to the directory to list files from.
    :return: A list of files in the directory.
    """
    full_path = resolve_abs_path(path)
    all_files = []
    # iterdir() 仅遍历当前一层，不递归进入子目录，也没有在这里排序。
    for item in full_path.iterdir():
        all_files.append({
            "filename": item.name,
            # 原实现将非普通文件项统一标为 dir，没有再调用 is_dir() 验证。
            "type": "file" if item.is_file() else "dir"
        })
    # 结果同时给出被列举的目录路径与子项列表，模型可据此决定下一步读取什么。
    return {
        "path": str(full_path),
        "files": all_files
    }

# 工具三：按旧文本替换文件中的第一处匹配，也允许创建或覆盖整个文件。
# 这个教学接口与生产 Claude Code 的 Edit 约定不同，应按这里的实际代码理解。
def edit_file_tool(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
    """
    Replaces first occurrence of old_str with new_str in file. If old_str is empty, creates/overwrites file with new_str.
    :param path: The path to the file to edit.
    :param old_str: The string to replace.
    :param new_str: The string to replace with.
    :return: A dictionary with the path to the file and the action taken.
    """
    full_path = resolve_abs_path(path)
    p = Path(full_path)
    if old_str == "":
        # 空旧串被约定为“写入整份新内容”，不是普通的字符串替换。
        # 文件不存在时创建；已经存在时覆盖。它不会自动创建缺失的父目录。
        p.write_text(new_str, encoding="utf-8")
        return {
            "path": str(full_path),
            # 此标签只是原作者选用的返回值；即使覆盖旧文件，也仍返回 created_file。
            "action": "created_file"
        }
    # 非空旧串：先读取当前磁盘内容，再检查是否包含待替换文本。
    original = p.read_text(encoding="utf-8")
    if original.find(old_str) == -1:
        # 找不到旧串时不写文件，返回一条普通结果供模型判断。
        # 这里没有抛异常，也没有原生 tool_result 的 is_error 标志。
        return {
            "path": str(full_path),
            "action": "old_str not found"
        }
    # 第三个参数 1 表示只替换第一处。多处匹配时不会因“不唯一”而拒绝。
    edited = original.replace(old_str, new_str, 1)
    # 这一行才真正把修改写入本机文件；模型生成文字本身不会完成写盘。
    # 原实现没有差异预览、权限确认、备份或写入后的测试等额外步骤。
    p.write_text(edited, encoding="utf-8")
    return {
        "path": str(full_path),
        "action": "edited"
    }

# 工具注册表：把模型使用的名称映射到真实 Python 函数。
# 左侧字符串是协议中的工具名，右侧是函数对象，这里尚未执行函数。
# 模型提出名称和参数后，由主循环查表并调用，模型不会直接访问文件系统。
TOOL_REGISTRY = {
    "read_file": read_file_tool,
    "list_files": list_files_tool,
    "edit_file": edit_file_tool
}

def get_tool_str_representation(tool_name: str) -> str:
    # 从注册表取出工具，避免在另一处重复手写完整函数接口。
    tool = TOOL_REGISTRY[tool_name]
    # __doc__ 提供函数文档，inspect.signature() 提供参数与类型注解。
    # 拼出来的是普通说明文本，不是 JSON Schema 或原生 tools 数组。
    # 本文件新增的 # 中文注释不在 __doc__ 中，因此不会随工具说明发给模型。
    return f"""
    Name: {tool_name}
    Description: {tool.__doc__}
    Signature: {inspect.signature(tool)}
    """

def create_full_system_prompt() -> str:
    tool_str_repr = ""
    # 逐个收集已注册工具的名称、文档和签名，拼成模型可阅读的清单。
    for tool_name in TOOL_REGISTRY:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        # 分隔线仅用于让说明更易读，不具有权限或执行语义。
        tool_str_repr += f"\n{"="*15}\n"
    # 将工具清单填入顶部的提示模板，返回完整指令字符串。
    return SYSTEM_PROMPT.format(tool_list_str=tool_str_repr)

# 把模型回复中的约定格式解析为“工具名、参数”列表。
# 它只是文本解析器：不会执行工具，也不会验证调用是否得到用户授权。
def extract_tool_invocations(text: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Return list of (tool_name, args) requested in 'tool: name({...})' lines.

    The parser expects single-line, compact JSON in parentheses.
    """
    invocations: List[Tuple[str, Dict[str, Any]]] = []
    # 虽然提示要求只返回一行，解析器实际上能收集多行工具调用。
    for raw_line in text.splitlines():
        # 去掉行首行尾空白，再检查是否具有约定的 tool: 前缀。
        line = raw_line.strip()
        if not line.startswith("tool:"):
            # 普通解释文字不会被当作工具请求；“我要读取文件”本身无法触发执行。
            continue
        # Expected format: tool: NAME(JSON)
        try:
            # 去掉前缀，再用第一个左括号分开工具名称和参数文本。
            after = line[len("tool:") :].strip()
            name, rest = after.split("(", 1)
            name = name.strip()
            # raw_decode() 从参数开头解析一个 JSON 值，另返回 JSON 结束位置。
            # 结束位置被 _ 丢弃，所以这里未严格检查右括号或多余的尾部文字。
            # JSON 合法也不保证根值是字典，或参数符合某个工具的真实签名。
            args, _ = json.JSONDecoder().raw_decode(rest)
            invocations.append((name, args))
        except Exception:
            # Ignore malformed tool requests
            # 解析失败直接忽略该行，没有把格式错误反馈给模型要求重试。
            # 如果所有行都被忽略，列表为空，主循环会按“没有工具调用”处理。
            continue
    return invocations

# 将当前对话交给模型，并将取得的文本交回主循环中的自定义解析器。
def execute_llm_call(conversation: List[Dict[str, str]]) -> str:
    # input 接收当前累积的对话。工具说明已经包含在初始指令里，
    # 此调用没有另外传入原生工具定义，也没有在此处处理 SSE 事件。
    # DeepSeek 官方已支持 Responses API，因此保留原课堂的请求形状和输出解析。
    response = deepseek_client.responses.create(
        model=DEEPSEEK_MODEL,
        input=conversation,
        # 这是单次请求的输出上限，不是内层循环的总轮数或总任务预算。
        max_output_tokens=5000,
    )
    # 取文本供 extract_tool_invocations() 解析，而不是直接处理原生工具调用项。
    return response.output_text

# Agent 主循环：外层等待用户任务，内层反复进行“模型请求 → 工具执行 → 结果回填”。
def run_coding_agent_loop():
    # 启动时显示实际来源、服务与模型，方便调试核对；不打印密钥。
    print(f"配置：{DEEPSEEK_SETTINGS_PATH}")
    print(f"服务：{DEEPSEEK_SETTINGS['base_url']} | 模型：{DEEPSEEK_MODEL}")
    # 整段会话共用一个列表；追加消息后，下一次请求就能看到已有历史。
    # DeepSeek 的 Responses 兼容层把 developer 当作 user；改用 system 承载初始指令。
    conversation = [{
        "role": "system",
        "content": create_full_system_prompt()
    }] 
    # 外层循环：一次内层任务结束后，继续接收下一条用户输入。
    while True:
        try:
            # input() 等待终端输入；颜色只改变提示符显示。
            user_msg = input(f"{YOU_COLOR}You{RESET_COLOR}: ")
        except (EOFError, KeyboardInterrupt):
            # 这里只捕获等待输入时的结束/中断，退出整个外层循环。
            # 模型请求和工具执行发生在 try 之外，其异常没有在这里统一恢复。
            break
        # 将用户原始意图写入会话。strip() 去除首尾空白，空输入也仍会被加入。
        conversation.append({
            "role": "user",
            "content": user_msg.strip()
        })
        # 内层循环：同一个用户任务可以触发多次模型请求，无需用户逐步下达工具指令。
        # 原例没有最大轮数、历史压缩或统一的任务完成校验。
        while True:
            # 决策层：由模型根据当前历史生成回复和可能的工具请求。
            assistant_resp = execute_llm_call(conversation)
            # 协议层：从回复文本中提取零个或多个 tool: NAME(JSON) 调用。
            tool_invocations = extract_tool_invocations(assistant_resp)
            if not tool_invocations:
                # 没有可解析调用时，将文本展示给用户，并保留在会话历史中。
                print(f"{ASSISTANT_COLOR}Assistant{RESET_COLOR}: {assistant_resp}")
                conversation.append({
                    "role": "assistant",
                    "content": assistant_resp
                })
                # 只结束内层循环，回到外层等待用户继续输入。
                # “没有工具请求”是本例停止本轮的条件，不是任务正确完成的证明。
                break
            # 有工具请求时，先显示并保存模型原始回复，记录模型要求执行了什么。
            print(f"{ASSISTANT_COLOR}Assistant{RESET_COLOR}: {assistant_resp}")
            conversation.append({
                "role": "assistant",
                "content": assistant_resp
            })
            # 执行层：按回复中的顺序逐个运行工具；这里没有并行调度。
            for name, args in tool_invocations:
                # 未注册的名字会在这里抛 KeyError；解析器本身没有校验名称是否存在。
                # 这份最小实现直接查表执行，没有生产系统中的完整权限门禁流程。
                tool = TOOL_REGISTRY[name]
                # 临时结果变量，正常分支会将它替换为相应工具返回的字典。
                resp = []
                if name == "read_file":
                    # 参数缺失时默认为当前目录；读取目录本身可能导致文件读取异常。
                    resp = tool(args.get("filename", "."))
                elif name == "list_files":
                    # 列目录工具的缺省路径为当前工作目录。
                    resp = tool(args.get("path", "."))
                elif name == "edit_file":
                    # 这里只用 get() 取参数，没有执行必填字段或类型校验。
                    # 尤其 old_str 缺失会默认空串，触发工具的整文件写入分支。
                    resp = tool(args.get("path", "."), args.get("old_str", ""), args.get("new_str", ""))
                # 反馈层：把工具返回值序列化，作为新的 user 文本消息加入历史。
                # 这里的 tool_result(...) 是约定文本，不是带 type/tool_use_id 的原生内容块。
                # 模型可据结果判断继续调用工具还是给出最终回复。
                conversation.append({
                    "role": "user",
                    "content": f"tool_result({json.dumps(resp)})"
                })
            # for 循环结束后，自然回到内层 while 顶部，带着新结果再次请求模型。
            


# 脚本直接运行时进入交互循环。作为模块导入时不调用此函数，
# 但前面读取 DeepSeek 配置与创建客户端等顶层初始化仍会执行。
if __name__ == "__main__":
    run_coding_agent_loop()
