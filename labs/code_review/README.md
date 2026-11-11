# Agent代码审查：发票列表优化

这是配合Fall 2026 10/27代码审查课堂的教师自拟练习，不是官方作业，也不连接真实发票系统。先审查，不修改待审代码；模型报告出来后再核对发现、漏报和误报。

## 变更与上下文

本次PR只把`base.py`中的InvoiceService替换为`candidate.py`版本：将排序移到初始化，并缓存重复查询，要求保持原有业务行为。`models.py`与`api.py`代表未改动的依赖和调用方。审查范围为这次变更引入的问题，不要求重构整个服务。

业务约束：

- Actor由已完成认证的上游构造，tenant_id是可信的服务端身份信息；本练习不实现登录或HTTP参数解析。调用方只允许查询自己的租户。
- 按租户与state筛选后的集合，按`(issued_on, number)`降序排列，再按page/page_size分页；page从1开始。state只接受all/open/paid。
- 进程内服务实例供不同租户复用。数据是初始化时取得的固定快照；同一实例存活期间不新增或修改发票，日期统一为ISO日期字符串。
- 返回不可变Invoice对象组成的tuple；调用方转换为items列表。不要求总条数、游标分页、缓存淘汰、数据库或并发访问实现。

材料：`base.py`是改前；`candidate.py`是改后；`api.py`显示实际使用方式；`models.py`提供类型和示例数据；`test_existing.py`是已有冒烟测试。示例数据不代替上述业务约束。

从学习仓库根目录查看实际差异（git diff --no-index发现差异时退出码1属正常）：

```powershell
git diff --no-index -- labs/code_review/base.py labs/code_review/candidate.py
```

运行已有测试：

```powershell
./.venv/Scripts/python.exe -m unittest -v labs.code_review.test_existing
```

这些用例通过仅说明已有检查通过，不能据此结束审查。教师另有独立反例核对，暂不放入待审材料，防止直接泄露答案；不将其作为独立盲测成绩。

准备核验（2026-11-11）：上述命令实际运行5项，全部通过；教师独立反例在基线与候选上取得不同结果，并核对实际调用方可达。尚无学习者的模型审查输出，不记审查成绩，也没有自动修复代码。

## 给Claude的任务

在本学习仓库启动现有DeepSeek配置；使用新会话，避免教师讲解或旧报告进入审查上下文。无需新装审查产品或启用新的Skill。

```powershell
claude --settings "C:\Users\admin\.claude\settings-deepseek.json" --model haiku
```

复制以下任务：

> 请审查 labs/code_review 中InvoiceService从base.py到candidate.py的改动。先读该目录README的需求、models.py、未改动的api.py调用方和已有测试，再查看两个版本的实际差异。只读取本练习材料，不搜索其他目录、评分资料或Git历史，不加载额外Skill，不发网络请求。不修改文件、不提交或推送。可以从仓库根目录用现有 ./.venv/Scripts/python.exe 运行已有测试，或用内存构造输入验证发现，不写新文件、不装依赖。仅报告由本次变更引入、有明确触发条件和实际影响的问题；不要把风格偏好当bug，不预设缺陷数量。每条给出candidate.py的实际行号、触发输入或调用顺序、预期与实际结果、影响及验证方式；未验证的推断明确标注。最后说明检查范围和未确认项，已有测试通过不能代替业务正确性。api.py中的Actor来自已认证上游，固定快照与非并发是题设。

反馈时贴最终报告及相关工具结果，尤其是模型为发现构造的输入和输出。不需要复制内部思考内容。暂不让模型自动修复，避免把发现能力和修复能力混成一次评分。

## 核对方式

按不同根因计数，重复表述不算多个发现。核对发现是否成立、位置是否准确、反例能否复现，并记录教师已知问题中的漏报；模型额外发现需另行验证，不能仅因不在教师清单就算误报。首轮结果只代表这次样本，不能推断总体审查准确率或模型排名。

来源：[10/27官方课堂文字/备注](https://docs.google.com/presentation/d/1u8WYtFj0O9yc4H4JX9D4URYKhDzvrAGKLzn38DXSrak/htmlpresent)、[Greptile原作者阅读](https://www.greptile.com/blog/how-to-build-a-code-review-agent)。课堂与阅读支持上下文、验证和评估方法；业务代码、题设与提示均为教学适配。课件视觉、视频与官方第六周作业未据此标记完成。
