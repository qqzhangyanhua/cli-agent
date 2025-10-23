"""
数据转换工具模块
支持多种数据格式之间的转换、验证和格式化
"""

import json
import csv
import yaml
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path


class DataConverter:
    """数据格式转换器"""
    
    @staticmethod
    def detect_format(content: str, file_path: str = "") -> str:
        """
        检测数据格式
        
        Args:
            content: 文件内容
            file_path: 文件路径（可选，用于根据扩展名判断）
        
        Returns:
            格式类型: json/yaml/csv/xml/unknown
        """
        # 先根据文件扩展名判断
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext in ['.json']:
                return 'json'
            elif ext in ['.yaml', '.yml']:
                return 'yaml'
            elif ext in ['.csv']:
                return 'csv'
            elif ext in ['.xml']:
                return 'xml'
        
        # 尝试内容判断
        content = content.strip()
        
        # JSON
        if content.startswith('{') or content.startswith('['):
            try:
                json.loads(content)
                return 'json'
            except:
                pass
        
        # YAML
        if ':' in content and not content.startswith('<'):
            try:
                yaml.safe_load(content)
                return 'yaml'
            except:
                pass
        
        # XML
        if content.startswith('<'):
            try:
                ET.fromstring(content)
                return 'xml'
            except:
                pass
        
        # CSV (简单检测：包含逗号且多行)
        if ',' in content and '\n' in content:
            return 'csv'
        
        return 'unknown'
    
    # ============================================
    # JSON 相关转换
    # ============================================
    
    @staticmethod
    def validate_json(content: str) -> Tuple[bool, str]:
        """
        验证JSON格式
        
        Returns:
            (是否有效, 错误信息或成功提示)
        """
        try:
            json.loads(content)
            return True, "✅ JSON格式正确"
        except json.JSONDecodeError as e:
            return False, f"❌ JSON格式错误: 第{e.lineno}行，第{e.colno}列 - {e.msg}"
    
    @staticmethod
    def beautify_json(content: str, indent: int = 2) -> str:
        """美化JSON格式"""
        try:
            data = json.loads(content)
            return json.dumps(data, ensure_ascii=False, indent=indent)
        except Exception as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    @staticmethod
    def minify_json(content: str) -> str:
        """压缩JSON（去除空格和换行）"""
        try:
            data = json.loads(content)
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            raise ValueError(f"JSON解析失败: {str(e)}")
    
    @staticmethod
    def json_to_csv(content: str) -> str:
        """
        JSON转CSV
        支持: JSON数组 -> CSV表格
        """
        try:
            data = json.loads(content)
            
            # 必须是列表
            if not isinstance(data, list):
                raise ValueError("JSON必须是数组格式才能转换为CSV")
            
            if not data:
                return ""
            
            # 获取所有可能的字段
            all_keys = set()
            for item in data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            fieldnames = sorted(all_keys)
            
            # 生成CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                if isinstance(item, dict):
                    writer.writerow(item)
            
            return output.getvalue()
        
        except Exception as e:
            raise ValueError(f"JSON转CSV失败: {str(e)}")
    
    @staticmethod
    def json_to_yaml(content: str) -> str:
        """JSON转YAML"""
        try:
            data = json.loads(content)
            return yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise ValueError(f"JSON转YAML失败: {str(e)}")
    
    # ============================================
    # CSV 相关转换
    # ============================================
    
    @staticmethod
    def csv_to_json(content: str, as_array: bool = True) -> str:
        """
        CSV转JSON
        
        Args:
            content: CSV内容
            as_array: True返回数组，False返回对象
        """
        try:
            reader = csv.DictReader(StringIO(content))
            data = list(reader)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ValueError(f"CSV转JSON失败: {str(e)}")
    
    @staticmethod
    def format_csv(content: str, delimiter: str = ',') -> str:
        """格式化CSV（统一分隔符和引号）"""
        try:
            reader = csv.reader(StringIO(content))
            output = StringIO()
            writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
            
            for row in reader:
                writer.writerow(row)
            
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"CSV格式化失败: {str(e)}")
    
    # ============================================
    # YAML 相关转换
    # ============================================
    
    @staticmethod
    def yaml_to_json(content: str) -> str:
        """YAML转JSON"""
        try:
            data = yaml.safe_load(content)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ValueError(f"YAML转JSON失败: {str(e)}")
    
    @staticmethod
    def validate_yaml(content: str) -> Tuple[bool, str]:
        """验证YAML格式"""
        try:
            yaml.safe_load(content)
            return True, "✅ YAML格式正确"
        except yaml.YAMLError as e:
            return False, f"❌ YAML格式错误: {str(e)}"
    
    # ============================================
    # XML 相关转换
    # ============================================
    
    @staticmethod
    def xml_to_json(content: str) -> str:
        """XML转JSON（简化版）"""
        try:
            root = ET.fromstring(content)
            
            def element_to_dict(element):
                """递归转换XML元素为字典"""
                result = {}
                
                # 属性
                if element.attrib:
                    result['@attributes'] = element.attrib
                
                # 文本内容
                if element.text and element.text.strip():
                    result['#text'] = element.text.strip()
                
                # 子元素
                for child in element:
                    child_data = element_to_dict(child)
                    
                    if child.tag in result:
                        # 如果已存在，转为数组
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data
                
                return result
            
            data = {root.tag: element_to_dict(root)}
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        except Exception as e:
            raise ValueError(f"XML转JSON失败: {str(e)}")
    
    # ============================================
    # 数据操作
    # ============================================
    
    @staticmethod
    def extract_fields(content: str, fields: List[str], format_type: str = 'json') -> str:
        """
        提取指定字段
        
        Args:
            content: 数据内容
            fields: 要提取的字段列表
            format_type: 数据格式
        """
        try:
            # 解析数据
            if format_type == 'json':
                data = json.loads(content)
            elif format_type == 'yaml':
                data = yaml.safe_load(content)
            else:
                raise ValueError(f"不支持的格式: {format_type}")
            
            # 提取字段
            def extract_from_dict(obj, fields):
                if isinstance(obj, dict):
                    return {k: v for k, v in obj.items() if k in fields}
                elif isinstance(obj, list):
                    return [extract_from_dict(item, fields) for item in obj]
                else:
                    return obj
            
            result = extract_from_dict(data, fields)
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            raise ValueError(f"字段提取失败: {str(e)}")
    
    @staticmethod
    def filter_data(content: str, field: str, value: Any, format_type: str = 'json') -> str:
        """
        过滤数据
        
        Args:
            content: 数据内容
            field: 过滤字段
            value: 过滤值
            format_type: 数据格式
        """
        try:
            # 解析数据
            if format_type == 'json':
                data = json.loads(content)
            elif format_type == 'yaml':
                data = yaml.safe_load(content)
            else:
                raise ValueError(f"不支持的格式: {format_type}")
            
            # 过滤（仅支持数组）
            if isinstance(data, list):
                filtered = [item for item in data if isinstance(item, dict) and item.get(field) == value]
                return json.dumps(filtered, ensure_ascii=False, indent=2)
            else:
                raise ValueError("只能过滤数组类型的数据")
        
        except Exception as e:
            raise ValueError(f"数据过滤失败: {str(e)}")
    
    @staticmethod
    def sort_data(content: str, field: str, reverse: bool = False, format_type: str = 'json') -> str:
        """
        排序数据
        
        Args:
            content: 数据内容
            field: 排序字段
            reverse: 是否倒序
            format_type: 数据格式
        """
        try:
            # 解析数据
            if format_type == 'json':
                data = json.loads(content)
            elif format_type == 'yaml':
                data = yaml.safe_load(content)
            else:
                raise ValueError(f"不支持的格式: {format_type}")
            
            # 排序（仅支持数组）
            if isinstance(data, list):
                sorted_data = sorted(data, key=lambda x: x.get(field, ''), reverse=reverse)
                return json.dumps(sorted_data, ensure_ascii=False, indent=2)
            else:
                raise ValueError("只能排序数组类型的数据")
        
        except Exception as e:
            raise ValueError(f"数据排序失败: {str(e)}")


class DataConverterTools:
    """数据转换工具集成类"""
    
    def __init__(self):
        self.converter = DataConverter()
    
    def convert(self, content: str, source_format: str, target_format: str, 
                file_path: str = "") -> Dict[str, Any]:
        """
        通用转换接口
        
        Args:
            content: 数据内容
            source_format: 源格式 (json/yaml/csv/xml/auto)
            target_format: 目标格式 (json/yaml/csv)
            file_path: 文件路径（用于格式检测）
        
        Returns:
            结果字典: {"success": bool, "result": str, "error": str}
        """
        try:
            # 自动检测格式
            if source_format == 'auto':
                source_format = self.converter.detect_format(content, file_path)
                print(f"[数据转换] 检测到格式: {source_format}")
            
            # 执行转换
            if source_format == target_format:
                result = content  # 相同格式，直接返回
            elif source_format == 'json' and target_format == 'csv':
                result = self.converter.json_to_csv(content)
            elif source_format == 'json' and target_format == 'yaml':
                result = self.converter.json_to_yaml(content)
            elif source_format == 'csv' and target_format == 'json':
                result = self.converter.csv_to_json(content)
            elif source_format == 'yaml' and target_format == 'json':
                result = self.converter.yaml_to_json(content)
            elif source_format == 'xml' and target_format == 'json':
                result = self.converter.xml_to_json(content)
            else:
                return {
                    "success": False,
                    "result": "",
                    "error": f"不支持的转换: {source_format} -> {target_format}"
                }
            
            return {
                "success": True,
                "result": result,
                "source_format": source_format,
                "target_format": target_format,
                "size": len(result)
            }
        
        except Exception as e:
            return {
                "success": False,
                "result": "",
                "error": str(e)
            }
    
    def validate(self, content: str, format_type: str) -> Dict[str, Any]:
        """
        验证数据格式
        
        Returns:
            {"success": bool, "message": str, "valid": bool}
        """
        try:
            if format_type == 'json':
                valid, message = self.converter.validate_json(content)
            elif format_type == 'yaml':
                valid, message = self.converter.validate_yaml(content)
            else:
                return {
                    "success": False,
                    "valid": False,
                    "message": f"不支持验证格式: {format_type}"
                }
            
            return {
                "success": True,
                "valid": valid,
                "message": message
            }
        
        except Exception as e:
            return {
                "success": False,
                "valid": False,
                "message": str(e)
            }
    
    def beautify(self, content: str, format_type: str) -> Dict[str, Any]:
        """
        美化格式
        
        Returns:
            {"success": bool, "result": str, "error": str}
        """
        try:
            if format_type == 'json':
                result = self.converter.beautify_json(content)
            elif format_type == 'csv':
                result = self.converter.format_csv(content)
            else:
                return {
                    "success": False,
                    "result": "",
                    "error": f"不支持美化格式: {format_type}"
                }
            
            return {
                "success": True,
                "result": result,
                "original_size": len(content),
                "formatted_size": len(result)
            }
        
        except Exception as e:
            return {
                "success": False,
                "result": "",
                "error": str(e)
            }


# 全局实例
data_converter_tools = DataConverterTools()
