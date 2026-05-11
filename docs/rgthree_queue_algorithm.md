# Алгоритм "Queue Selected Output Nodes (rgthree)" в ComfyUI

## Описание

Функция "Queue Selected Output Nodes (rgthree)" позволяет запускать выполнение только определенных выходных нод в рабочем процессе ComfyUI, а не весь workflow целиком. Это мощный инструмент для оптимизации и отладки сложных workflow.

## Основные принципы работы

### 1. **Обнаружение выходных нод**
```javascript
function getOutputNodes(nodes) {
    return nodes?.filter((n) => {
        return n.mode != LiteGraph.NEVER && n.constructor.nodeData?.output_node;
    }) || [];
}
```
- Функция фильтрует ноды, которые:
  - Не отключены (`mode != LiteGraph.NEVER`)
  - Помечены как выходные ноды (`output_node: true`)

### 2. **Добавление пункта в контекстное меню**
Когда вы выбираете ноды и щелкаете правой кнопкой мыши, rgthree добавляет пункт меню "Queue Selected Output Nodes (rgthree)", который активен только если среди выбранных нод есть выходные ноды.

### 3. **Основной алгоритм обрезки workflow**
При нажатии на этот пункт меню запускается метод `queueOutputNodes()`:

```javascript
async queueOutputNodes(nodeIds) {
    try {
        this.queueNodeIds = nodeIds;  // Сохраняем ID нод для обработки
        await app.queuePrompt(0);     // Запускаем стандартную очередь
    } finally {
        this.queueNodeIds = null;     // Очищаем после выполнения
    }
}
```

### 4. **Перехват и модификация workflow**
Основная магия происходит в перехваченном методе `api.queuePrompt()`:

```javascript
api.queuePrompt = async function(index, prompt) {
    if (rgthree.queueNodeIds?.length && prompt.output) {
        const oldOutput = prompt.output;
        let newOutput = {};
        
        // Для каждой выбранной выходной ноды
        for (const queueNodeId of rgthree.queueNodeIds) {
            rgthree.recursiveAddNodes(String(queueNodeId), oldOutput, newOutput);
        }
        
        prompt.output = newOutput;  // Заменяем полный workflow обрезанным
    }
    // Продолжаем стандартное выполнение
}
```

### 5. **Рекурсивный алгоритм обхода зависимостей**
Ключевая функция `recursiveAddNodes()` работает по принципу обратного обхода:

```javascript
recursiveAddNodes(nodeId, oldOutput, newOutput) {
    let currentNode = oldOutput[nodeId];
    
    if (newOutput[nodeId] == null) {  // Если нода еще не добавлена
        newOutput[nodeId] = currentNode;  // Добавляем ноду
        
        // Рекурсивно добавляем все входные зависимости
        for (const inputValue of Object.values(currentNode.inputs || [])) {
            if (Array.isArray(inputValue)) {
                this.recursiveAddNodes(inputValue[0], oldOutput, newOutput);
            }
        }
    }
    return newOutput;
}
```

## Пошаговый алгоритм работы

1. **Пользователь выбирает выходные ноды** и выбирает "Queue Selected Output Nodes"
2. **Система определяет выходные ноды** среди выбранных
3. **Сохраняются ID выбранных выходных нод** в `queueNodeIds`
4. **Запускается стандартный процесс очереди** ComfyUI
5. **Перехватывается вызов API** и модифицируется workflow:
   - Создается новый пустой объект `newOutput`
   - Для каждой выбранной выходной ноды запускается рекурсивный обход
   - **Рекурсивно добавляются все зависимости** (input connections) от выходной ноды до самых корней
   - Полный workflow заменяется на обрезанный
6. **Выполняется только необходимая часть** workflow

## Структуры данных

### Формат нод в ComfyUI API
```javascript
// Пример структуры ноды в prompt.output
{
  "node_id": {
    "inputs": {
      "input_name": ["connected_node_id", output_slot],
      "another_input": "literal_value"
    },
    "class_type": "NodeClassName",
    "_meta": { ... }
  }
}
```

### Типы входов
- **Подключенные входы**: `["node_id", slot_index]` - массив из ID ноды и индекса слота
- **Литеральные значения**: строки, числа, булевы значения и т.д.

## Преимущества алгоритма

- ⚡ **Экономия ресурсов** - выполняются только нужные ноды
- 🎯 **Точность** - можно тестировать отдельные ветки workflow
- 🚀 **Скорость** - быстрее, чем выполнение всего workflow
- 🔍 **Отладка** - удобно для тестирования частей workflow
- 🔧 **Гибкость** - работает с любыми типами нод ComfyUI

## Применение

Этот алгоритм особенно полезен в:
- Сложных workflow с множественными выходами
- Отладке и тестировании отдельных веток обработки
- Экономии вычислительных ресурсов при разработке
- Быстром прототипировании и итерации

## Ограничения

- Работает только с нодами, помеченными как `output_node: true`
- Не может обрабатывать циклические зависимости
- Зависит от корректной структуры connections в workflow
- Требует активной выходной ноды для работы

---

## Реализация в comfy-cli

Этот алгоритм реализован в `comfy-cli` через параметр `--output-nodes` команды `comfy run`.

### Использование через CLI

#### Базовое использование
```bash
# Запустить только конкретные output ноды по их ID
comfy run --workflow my_workflow.json --output-nodes "123,456"

# С подробным выводом статистики оптимизации
comfy run --workflow my_workflow.json --output-nodes "10" --verbose
```

#### Пример с подробным выводом
```bash
$ comfy run --workflow workflow.json --output-nodes "15,20" --verbose

Workflow optimization:
  Original nodes: 50
  Optimized nodes: 12
  Saved: 38 nodes (76.0%)

Executing workflow: /path/to/workflow.json
[============================] 100% 00:00:05
```

### Параметры команды

- `--workflow` - путь к API workflow JSON файлу (обязательный)
- `--output-nodes` - список ID нод через запятую (опциональный)
- `--verbose` - показать статистику оптимизации (опциональный)
- `--host` - хост ComfyUI сервера (по умолчанию: 127.0.0.1)
- `--port` - порт ComfyUI сервера (по умолчанию: 8188)
- `--wait` - ждать завершения выполнения (по умолчанию: true)
- `--timeout` - таймаут в секундах (по умолчанию: 30)

### Архитектура реализации

#### 1. Точка входа: `comfy_cli/cmdline.py`
```python
@app.command()
def run(
    workflow: str,
    output_nodes: Optional[str] = None,
    verbose: bool = False,
    ...
):
    # Парсинг списка нод
    output_node_ids = None
    if output_nodes:
        output_node_ids = [node_id.strip() for node_id in output_nodes.split(',')]

    run_inner.execute(workflow, ..., output_node_ids)
```

#### 2. Обработка workflow: `comfy_cli/command/run.py`
```python
def execute(workflow: str, ..., output_node_ids=None):
    workflow = load_api_workflow(workflow)

    # Оптимизация workflow если указаны output ноды
    if output_node_ids:
        processor = WorkflowProcessor()
        workflow = processor.process_workflow_for_output_nodes(
            workflow,
            output_node_ids
        )

        # Показать статистику
        if verbose:
            stats = processor.get_workflow_statistics(
                original_workflow,
                workflow
            )
            print_statistics(stats)
```

#### 3. Процессор workflow: `comfy_cli/workflow_processor.py`
```python
class WorkflowProcessor:
    def process_workflow_for_output_nodes(
        self,
        full_workflow: Dict,
        selected_node_ids: List[str]
    ) -> Dict:
        # 1. Найти output ноды среди выбранных
        output_nodes = self.get_output_nodes(
            full_workflow,
            selected_node_ids
        )

        # 2. Создать минимальный workflow
        minimal_workflow = self.create_minimal_workflow(
            full_workflow,
            output_nodes
        )

        return minimal_workflow

    def create_minimal_workflow(
        self,
        full_workflow: Dict,
        output_node_ids: List[str]
    ) -> Dict:
        minimal_workflow = {}

        # Рекурсивно добавить каждую output ноду и её зависимости
        for output_node_id in output_node_ids:
            self.recursive_add_nodes(
                output_node_id,
                full_workflow,
                minimal_workflow
            )

        return minimal_workflow

    def recursive_add_nodes(
        self,
        node_id: str,
        old_workflow: Dict,
        new_workflow: Dict
    ) -> Dict:
        # Пропустить если уже обработана
        if node_id in new_workflow:
            return new_workflow

        current_node = old_workflow[node_id]

        # Добавить ноду
        new_workflow[node_id] = copy.deepcopy(current_node)

        # Рекурсивно обработать все входы
        inputs = current_node.get('inputs', {})
        for input_value in inputs.values():
            # Проверить является ли вход подключением к другой ноде
            if isinstance(input_value, list) and len(input_value) >= 2:
                connected_node_id = str(input_value[0])
                self.recursive_add_nodes(
                    connected_node_id,
                    old_workflow,
                    new_workflow
                )

        return new_workflow
```

### Определение output нод

Процессор автоматически определяет output ноды по следующим критериям:

```python
def is_output_node(self, node_data: Dict) -> bool:
    class_type = node_data.get('class_type', '')

    # Известные типы output нод
    output_node_types = [
        'SaveImage',
        'PreviewImage',
        'SaveVideo',
        'SaveGIF',
        'VHS_VideoCombine',
        'SaveAnimatedWEBP',
        'SaveAnimatedPNG',
        'DisplayText',
        'ShowText',
        'PrintText',
    ]

    # Проверка явной метки или известного типа
    is_explicit_output = node_data.get('_meta', {}).get('output_node', False)
    is_known_output_type = class_type in output_node_types

    return is_explicit_output or is_known_output_type
```

### Статистика оптимизации

При использовании `--verbose` CLI показывает:

```python
def get_workflow_statistics(
    self,
    original_workflow: Dict,
    minimal_workflow: Dict
) -> Dict:
    original_count = len(original_workflow)
    minimal_count = len(minimal_workflow)
    saved_count = original_count - minimal_count
    saved_percentage = (saved_count / original_count * 100)

    return {
        "original_nodes": original_count,
        "minimal_nodes": minimal_count,
        "saved_nodes": saved_count,
        "saved_percentage": saved_percentage
    }
```

### Примеры использования

#### 1. Тестирование конкретной части workflow
```bash
# У вас есть большой workflow с несколькими выходами
# Вы хотите протестировать только одну конкретную output ноду

comfy run --workflow complex_workflow.json --output-nodes "save_image_1" --verbose
```

#### 2. Быстрая итерация при разработке
```bash
# Запустить только нужные output ноды для быстрой проверки
comfy run --workflow dev_workflow.json --output-nodes "10,15,20"
```

#### 3. Экономия ресурсов в production
```bash
# Запустить только необходимые части workflow
comfy run --workflow production.json \
  --output-nodes "final_output" \
  --host production-server \
  --port 8188 \
  --wait
```

### Преимущества CLI реализации

- ✅ **Автоматизация** - можно интегрировать в скрипты и CI/CD
- ✅ **Программный доступ** - использование из Python кода
- ✅ **Удаленное выполнение** - поддержка `--host` и `--port`
- ✅ **Статистика** - видимость оптимизации с `--verbose`
- ✅ **Гибкость** - работает с любыми API workflow файлами

### Требования

- ComfyUI должен быть запущен (например, через `comfy launch --background`)
- Workflow файл должен быть в API формате (JSON)
- Указанные ID нод должны существовать в workflow
- Среди указанных нод должна быть хотя бы одна output нода