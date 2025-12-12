#!/usr/bin/env python3
"""
Парсит SARIF файл и генерирует summary для GitHub Actions
Использование: python scripts/parse_sarif_summary.py <sarif-file>
"""

import json
import sys
import os
from pathlib import Path


def generate_summary(sarif_file: str, summary_file: str = None):
    """Генерирует summary из SARIF файла"""
    
    if not summary_file:
        summary_file = os.environ.get('GITHUB_STEP_SUMMARY', '/dev/stdout')
    
    try:
        # Проверяем существование файла (абсолютный и относительный путь)
        if not os.path.exists(sarif_file):
            # Пробуем найти файл в текущей директории
            current_dir = os.getcwd()
            possible_paths = [
                sarif_file,
                os.path.join(current_dir, sarif_file),
                os.path.join(current_dir, os.path.basename(sarif_file)),
            ]
            
            found = False
            for path in possible_paths:
                if os.path.exists(path):
                    sarif_file = path
                    found = True
                    break
            
            if not found:
                with open(summary_file, 'a') as out:
                    out.write(f"⚠️  SARIF файл не найден: {sarif_file}\n\n")
                    out.write(f"Проверенные пути: {', '.join(possible_paths)}\n\n")
                    out.write("💡 CodeQL может потребоваться несколько запусков для создания базы данных.\n")
                return
        
        with open(sarif_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        runs = data.get('runs', [])
        if not runs:
            with open(summary_file, 'a') as out:
                out.write("⚠️  SARIF файл пуст или не содержит результатов\n\n")
            return
        
        total_results = 0
        results_by_level = {}
        results_by_rule = {}
        results_by_file = {}
        
        for run in runs:
            tool = run.get('tool', {}).get('driver', {})
            tool_name = tool.get('name', 'Unknown')
            tool_version = tool.get('version', '')
            
            results = run.get('results', [])
            
            for result in results:
                total_results += 1
                level = result.get('level', 'unknown')
                rule_id = result.get('ruleId', 'unknown')
                
                results_by_level[level] = results_by_level.get(level, 0) + 1
                results_by_rule[rule_id] = results_by_rule.get(rule_id, 0) + 1
                
                # Собираем информацию о файлах
                locations = result.get('locations', [])
                if locations:
                    file_uri = locations[0].get('physicalLocation', {}).get('artifactLocation', {}).get('uri', 'unknown')
                    results_by_file[file_uri] = results_by_file.get(file_uri, 0) + 1
        
        # Выводим в summary
        with open(summary_file, 'a') as f:
            if total_results == 0:
                f.write("✅ **Нет проблем найдено!**\n\n")
            else:
                f.write(f"**Всего найдено проблем**: {total_results}\n\n")
                
                if results_by_level:
                    f.write("### По уровню серьезности:\n\n")
                    level_emoji = {'error': '🔴', 'warning': '🟡', 'note': '🔵', 'none': '⚪'}
                    for level in ['error', 'warning', 'note', 'none']:
                        if level in results_by_level:
                            emoji = level_emoji.get(level, '⚪')
                            f.write(f"- {emoji} **{level.upper()}**: {results_by_level[level]}\n")
                    f.write("\n")
                
                if results_by_rule:
                    f.write("### Топ-10 типов проблем:\n\n")
                    sorted_rules = sorted(results_by_rule.items(), key=lambda x: x[1], reverse=True)[:10]
                    for rule_id, count in sorted_rules:
                        f.write(f"- `{rule_id}`: {count}\n")
                    f.write("\n")
                
                if results_by_file:
                    f.write("### Файлы с проблемами:\n\n")
                    sorted_files = sorted(results_by_file.items(), key=lambda x: x[1], reverse=True)[:5]
                    for file_uri, count in sorted_files:
                        f.write(f"- `{file_uri}`: {count} проблем\n")
                    f.write("\n")
            
            f.write("### 📁 Артефакты:\n\n")
            f.write("- SARIF файл доступен в артефактах workflow\n")
            f.write("- Результаты также в GitHub Security Tab\n\n")
            
            f.write("### 🔍 Как посмотреть детали:\n\n")
            f.write("1. **GitHub Security Tab** - автоматически обрабатывается GitHub\n")
            f.write("2. **Скачайте артефакт** и используйте:\n")
            f.write("   - VS Code: установите расширение 'SARIF Viewer'\n")
            f.write("   - Онлайн: https://microsoft.github.io/sarif-web-component/\n")
            f.write("   - Скрипт: `python scripts/view_sarif.py codeql-results.sarif`\n")
    
    except FileNotFoundError:
        with open(summary_file, 'a') as out:
            out.write(f"⚠️  SARIF файл не найден: {sarif_file}\n\n")
    except json.JSONDecodeError as e:
        with open(summary_file, 'a') as out:
            out.write(f"⚠️  Ошибка парсинга SARIF: {e}\n\n")
    except Exception as e:
        with open(summary_file, 'a') as out:
            out.write(f"⚠️  Ошибка: {type(e).__name__}: {e}\n\n")


if __name__ == '__main__':
    sarif_file = sys.argv[1] if len(sys.argv) > 1 else 'codeql-results.sarif'
    generate_summary(sarif_file)

