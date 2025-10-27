# detect_project_type

- 类型: function
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/src/tools/project_manager/detector.py

## 摘要
检测项目类型

Args:
    work_dir: 工作目录,默认使用配置的工作目录

Returns:
    {
        "type": "nodejs" | "python" | "unknown",
        "package_manager": "pnpm" | "npm" | "yarn" | "pip",
        "config_file": "package.json" | "requirements.txt" | ...,
        "scripts": {...},  # 仅 nodejs
        "main_files": [...],  # 仅 python
        "detected_files": [...]  # 检测到的关键文件
    }
