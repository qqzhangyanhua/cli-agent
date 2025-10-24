# 🔧 配置文件设置指南

## 📋 概述

为了保护敏感信息（如 API 密钥），项目使用外部配置文件来管理所有配置项。

## 🚀 快速设置

### 1. 复制配置模板

```bash
cp config.template.json config.json
```

### 2. 编辑配置文件

打开 `config.json` 文件，填入你的真实 API 密钥：

```json
{
  "llm_configs": {
    "primary": {
      "model": "kimi-k2-0905-preview",
      "base_url": "https://api.moonshot.cn/v1",
      "api_key": "你的_KIMI_API_密钥",
      "temperature": 0
    },
    "secondary": {
      "model": "claude-3-5-sonnet", 
      "base_url": "https://sdwfger.edu.kg/v1",
      "api_key": "你的_CLAUDE_API_密钥",
      "temperature": 0
    }
  }
}
```

### 3. 验证配置

运行 AI Agent 来验证配置是否正确：

```bash
./ai-agent "测试配置"
```

## 📁 文件说明

| 文件 | 说明 | 版本控制 |
|------|------|----------|
| `config.template.json` | 配置模板文件 | ✅ 提交到 Git |
| `config.json` | 实际配置文件（包含敏感信息） | ❌ 被 .gitignore 忽略 |

## 🔒 安全性

- ✅ `config.json` 已被添加到 `.gitignore`，不会被提交到 Git
- ✅ 所有敏感信息都存储在本地配置文件中
- ✅ 配置模板提供了完整的配置结构示例

## ⚙️ 配置项说明

### LLM 配置

- **primary**: 主要 LLM（用于意图分析、问答等）
- **secondary**: 代码专用 LLM（用于生成命令和代码）

### 其他配置

- **working_directory**: 工作目录路径
- **security**: 安全相关配置（危险命令、超时时间）
- **memory**: 记忆配置（历史记录数量）
- **daily_report**: 日报配置
- **headers**: HTTP 请求头

## 🚨 错误处理

如果遇到配置相关错误：

### 配置文件不存在
```
❌ 配置文件不存在: /path/to/config.json
💡 请复制 config.template.json 为 config.json 并填入你的 API 密钥
```

**解决方案**: 按照上述步骤 1-2 创建并配置文件

### 配置文件格式错误
```
❌ 配置文件格式错误: Expecting ',' delimiter: line 5 column 10
```

**解决方案**: 检查 JSON 格式是否正确，可以使用在线 JSON 验证器

### API 密钥无效
```
❌ API 调用失败: Invalid API key
```

**解决方案**: 检查 API 密钥是否正确填写

## 🔄 迁移现有配置

如果你已经在使用旧版本的硬编码配置：

1. 备份当前的 API 密钥
2. 按照上述步骤创建 `config.json`
3. 将备份的 API 密钥填入新配置文件
4. 重启 AI Agent

## 📞 支持

如果遇到配置问题，请检查：

1. 配置文件路径是否正确
2. JSON 格式是否有效
3. API 密钥是否有效
4. 网络连接是否正常

更多帮助请查看项目文档或提交 Issue。
