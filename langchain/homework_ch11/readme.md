# 作业要求

1. 扩展本节课学习的 Reflection Agent，使其能够完成更通用的生成任务，包括但不限于代码、报告等。
2. （可选）使用扩展后的 Reflection Agent 生成代码，实现在 GitHubSentinel 上新增一个信息渠道。

# 作业提交

## 问题 1

1. 优化了 writer 的 prompt， 让其只关心当前轮的写作任务，和当前轮的用户的反馈。（太长的对话历史，不利于当前的写作任务的改进）
2. 优化了 reflect 的 prompt， 让其只对当前轮的写作内容，给出反馈。
3. 优化了 reflect 的 prompt， 让其作为内容审核者角色，给出反馈。

## demo 演示

贪吃蛇代码生成：

![image](./code.gif)

南游记慧能大师传法故事生成：

![image](./doc.gif)

[实现代码 <-- 点击这里](./writer_and_reflect_agent.py)

## 问题 2

TODO::