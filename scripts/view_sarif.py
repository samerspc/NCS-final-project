#!/usr/bin/env python3
"""
Простой просмотрщик SARIF файлов
Использование: python scripts/view_sarif.py <path-to-sarif-file>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def colorize(text: str, color: str) -> str:
    """Добавляет ANSI цвета для терминала"""
    colors = {
        'red': '\033[91m',
        'yellow': '\033[93m',
        'green': '\033[92m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'reset': '\033[0m',
        'bold': '\033[1m'
    }
    return f"{colors.get(color, '')}{text}{colors.get('reset', '')}"


def get_severity_emoji(level: str) -> str:
    """Возвращает emoji для уровня серьезности"""
    emoji_map = {
        'error': '🔴',
        'warning': '🟡',
        'note': '🔵',
        'none': '⚪'
    }
    return emoji_map.get(level.lower(), '❓')


def format_location(location: Dict[str, Any]) -> str:
    """Форматирует информацию о местоположении"""
    physical = location.get('physicalLocation', {})
    artifact = physical.get('artifactLocation', {})
    region = physical.get('region', {})
    
    uri = artifact.get('uri', 'unknown')
    start_line = region.get('startLine', '?')
    start_col = region.get('startColumn', '?')
    end_line = region.get('endLine', start_line)
    end_col = region.get('endColumn', '?')
    
    if start_line == end_line and start_col == end_col:
        return f"{uri}:{start_line}:{start_col}"
    elif start_line == end_line:
        return f"{uri}:{start_line}:{start_col}-{end_col}"
    else:
        return f"{uri}:{start_line}:{start_col}-{end_line}:{end_col}"


def view_sarif(file_path: str, filter_level: str = None, filter_rule: str = None):
    """Просматривает SARIF файл и выводит результаты"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(colorize(f"❌ Файл не найден: {file_path}", 'red'))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(colorize(f"❌ Ошибка парсинга JSON: {e}", 'red'))
        sys.exit(1)
    
    runs = data.get('runs', [])
    if not runs:
        print(colorize("⚠️  Файл не содержит результатов анализа", 'yellow'))
        return
    
    total_results = 0
    results_by_level = {}
    
    for run in runs:
        tool = run.get('tool', {}).get('driver', {})
        tool_name = tool.get('name', 'Unknown')
        tool_version = tool.get('version', '')
        
        print(colorize(f"\n{'='*70}", 'bold'))
        print(colorize(f"Tool: {tool_name} {tool_version}", 'bold'))
        print(colorize(f"{'='*70}\n", 'bold'))
        
        results = run.get('results', [])
        
        # Фильтрация
        if filter_level:
            results = [r for r in results if r.get('level', '').lower() == filter_level.lower()]
        if filter_rule:
            results = [r for r in results if filter_rule.lower() in r.get('ruleId', '').lower()]
        
        if not results:
            print(colorize("✅ Нет результатов, соответствующих фильтрам", 'green'))
            continue
        
        # Группировка по уровню
        for result in results:
            level = result.get('level', 'unknown')
            results_by_level[level] = results_by_level.get(level, 0) + 1
        
        # Вывод результатов
        for idx, result in enumerate(results, 1):
            rule_id = result.get('ruleId', 'unknown')
            message = result.get('message', {}).get('text', 'No message')
            level = result.get('level', 'unknown')
            
            # Информация о местоположении
            locations = result.get('locations', [])
            location_str = "unknown location"
            if locations:
                location_str = format_location(locations[0])
            
            # Дополнительная информация
            properties = result.get('properties', {})
            tags = properties.get('tags', [])
            precision = properties.get('precision', 'unknown')
            
            # Вывод
            emoji = get_severity_emoji(level)
            level_color = 'red' if level == 'error' else 'yellow' if level == 'warning' else 'blue'
            
            print(f"{emoji} {colorize(f'[{level.upper()}]', level_color)} {colorize(rule_id, 'cyan')}")
            print(f"   📍 {colorize(location_str, 'blue')}")
            print(f"   💬 {message}")
            
            if tags:
                tag_str = ', '.join([t for t in tags if not t.startswith('external/')])
                if tag_str:
                    print(f"   🏷️  Tags: {tag_str}")
            
            if precision != 'unknown':
                print(f"   🎯 Precision: {precision}")
            
            # Ссылки на правила
            rule_info = result.get('rule', {})
            if rule_info:
                help_uri = rule_info.get('helpUri', '')
                if help_uri:
                    print(f"   📚 Help: {help_uri}")
            
            print()
            total_results += 1
        
        # Статистика
        print(colorize(f"\n{'─'*70}", 'bold'))
        print(colorize(f"📊 Статистика:", 'bold'))
        print(f"   Всего найдено: {total_results}")
        for level, count in sorted(results_by_level.items()):
            emoji = get_severity_emoji(level)
            print(f"   {emoji} {level.upper()}: {count}")
        print()


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python scripts/view_sarif.py <sarif-file> [--level=error|warning|note] [--rule=<rule-id>]")
        print("\nПримеры:")
        print("  python scripts/view_sarif.py codeql-results.sarif")
        print("  python scripts/view_sarif.py codeql-results.sarif --level=error")
        print("  python scripts/view_sarif.py codeql-results.sarif --rule=sql-injection")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Парсинг аргументов
    filter_level = None
    filter_rule = None
    
    for arg in sys.argv[2:]:
        if arg.startswith('--level='):
            filter_level = arg.split('=', 1)[1]
        elif arg.startswith('--rule='):
            filter_rule = arg.split('=', 1)[1]
    
    view_sarif(file_path, filter_level, filter_rule)


if __name__ == '__main__':
    main()

