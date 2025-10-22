#!/bin/bash

# 意图识别测试脚本
# 测试各种输入是否能正确识别意图

echo "=========================================="
echo "意图识别测试"
echo "=========================================="
echo ""

cd "$(dirname "$0")/.." || exit

echo "📋 测试待办功能"
echo "-------------------------------------------"

echo ""
echo "✅ 测试 1: 查询今天的待办"
./ai-agent "今天有什么要做的" | grep -q "规则匹配: query_todo" && echo "✅ 通过" || echo "❌ 失败"

echo ""
echo "✅ 测试 2: 查询明天的安排"
./ai-agent "明天有什么安排" | grep -q "规则匹配: query_todo" && echo "✅ 通过" || echo "❌ 失败"

echo ""
echo "✅ 测试 3: 查询本周任务"
./ai-agent "本周有什么任务" | grep -q "规则匹配: query_todo" && echo "✅ 通过" || echo "❌ 失败"

echo ""
echo "✅ 测试 4: 添加今天的待办"
./ai-agent "今天下午5点写报告" | grep -q "规则匹配: add_todo" && echo "✅ 通过" || echo "❌ 失败"

echo ""
echo "✅ 测试 5: 添加明天的待办"
./ai-agent "明天早上8点晨跑" | grep -q "规则匹配: add_todo" && echo "✅ 通过" || echo "❌ 失败"

echo ""
echo "📋 测试现有功能不受影响"
echo "-------------------------------------------"

echo ""
echo "✅ 测试 6: 问答功能"
./ai-agent "什么是Python" | grep -q "意图: question" && echo "✅ 通过" || echo "❌ 失败"

echo ""
echo "✅ 测试 7: 终端命令"
./ai-agent "显示当前目录" | grep -q "意图: terminal_command" && echo "✅ 通过" || echo "❌ 失败"

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
