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