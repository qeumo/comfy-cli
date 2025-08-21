#!/usr/bin/env python3
"""
Пример реализации алгоритма "Queue Selected Output Nodes" на Python
Основано на анализе кода rgthree-comfy

Этот модуль демонстрирует, как работает алгоритм обрезки workflow
для выполнения только выбранных выходных нод и их зависимостей.
"""

from typing import Dict, List, Any, Set, Optional
import json
import copy


class ComfyWorkflowProcessor:
    """
    Класс для обработки и обрезки ComfyUI workflow
    """
    
    def __init__(self):
        self.visited_nodes: Set[str] = set()
    
    def is_output_node(self, node_data: Dict[str, Any]) -> bool:
        """
        Определяет, является ли нода выходной
        
        Args:
            node_data: Данные ноды
            
        Returns:
            True если нода является выходной
        """
        # В реальном ComfyUI эта информация берется из node_data
        # Здесь используем простую эвристику
        class_type = node_data.get('class_type', '')
        
        # Типичные выходные ноды в ComfyUI
        output_node_types = [
            'SaveImage',
            'PreviewImage', 
            'SaveVideo',
            'SaveGIF',
            'VHS_VideoCombine',
            # Можно добавить другие типы выходных нод
        ]
        
        return class_type in output_node_types or node_data.get('_meta', {}).get('output_node', False)
    
    def get_output_nodes(self, workflow: Dict[str, Any], selected_node_ids: List[str] = None) -> List[str]:
        """
        Получает список ID выходных нод из workflow
        
        Args:
            workflow: Полный workflow ComfyUI
            selected_node_ids: Список выбранных нод (опционально)
            
        Returns:
            Список ID выходных нод
        """
        output_nodes = []
        
        nodes_to_check = selected_node_ids if selected_node_ids else workflow.keys()
        
        for node_id in nodes_to_check:
            if node_id in workflow:
                node_data = workflow[node_id]
                if self.is_output_node(node_data):
                    output_nodes.append(node_id)
                    
        return output_nodes
    
    def recursive_add_nodes(self, node_id: str, old_workflow: Dict[str, Any], 
                          new_workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рекурсивно добавляет ноду и все ее зависимости в новый workflow
        
        Args:
            node_id: ID текущей ноды
            old_workflow: Исходный полный workflow
            new_workflow: Новый обрезанный workflow
            
        Returns:
            Обновленный новый workflow
        """
        # Если нода уже обработана, пропускаем
        if node_id in new_workflow or node_id in self.visited_nodes:
            return new_workflow
            
        # Проверяем существование ноды
        if node_id not in old_workflow:
            print(f"Предупреждение: Нода {node_id} не найдена в workflow")
            return new_workflow
            
        # Добавляем ноду в посещенные
        self.visited_nodes.add(node_id)
        current_node = old_workflow[node_id]
        
        # Копируем ноду в новый workflow
        new_workflow[node_id] = copy.deepcopy(current_node)
        
        # Обрабатываем все входы ноды
        inputs = current_node.get('inputs', {})
        
        for input_name, input_value in inputs.items():
            # Проверяем, является ли вход подключением к другой ноде
            if isinstance(input_value, list) and len(input_value) >= 2:
                # input_value имеет формат [node_id, output_slot]
                connected_node_id = str(input_value[0])
                
                # Рекурсивно добавляем зависимую ноду
                self.recursive_add_nodes(connected_node_id, old_workflow, new_workflow)
        
        return new_workflow
    
    def create_minimal_workflow(self, full_workflow: Dict[str, Any], 
                              output_node_ids: List[str]) -> Dict[str, Any]:
        """
        Создает минимальный workflow содержащий только выбранные выходные ноды и их зависимости
        
        Args:
            full_workflow: Полный исходный workflow
            output_node_ids: Список ID выходных нод для выполнения
            
        Returns:
            Обрезанный workflow
        """
        # Сбрасываем состояние
        self.visited_nodes.clear()
        
        # Создаем новый пустой workflow
        minimal_workflow = {}
        
        # Для каждой выбранной выходной ноды добавляем ее и все зависимости
        for output_node_id in output_node_ids:
            self.recursive_add_nodes(output_node_id, full_workflow, minimal_workflow)
            
        return minimal_workflow
    
    def queue_selected_output_nodes(self, full_workflow: Dict[str, Any], 
                                  selected_node_ids: List[str]) -> Dict[str, Any]:
        """
        Главная функция, имитирующая работу rgthree "Queue Selected Output Nodes"
        
        Args:
            full_workflow: Полный workflow ComfyUI
            selected_node_ids: Список ID выбранных нод
            
        Returns:
            Обрезанный workflow для выполнения
        """
        # Шаг 1: Найти выходные ноды среди выбранных
        output_nodes = self.get_output_nodes(full_workflow, selected_node_ids)
        
        if not output_nodes:
            print("Внимание: Среди выбранных нод нет выходных нод")
            return {}
        
        print(f"Найденные выходные ноды: {output_nodes}")
        
        # Шаг 2: Создать минимальный workflow
        minimal_workflow = self.create_minimal_workflow(full_workflow, output_nodes)
        
        print(f"Исходный workflow: {len(full_workflow)} нод")
        print(f"Обрезанный workflow: {len(minimal_workflow)} нод")
        print(f"Экономия: {len(full_workflow) - len(minimal_workflow)} нод "
              f"({100 * (1 - len(minimal_workflow) / len(full_workflow)):.1f}%)")
        
        return minimal_workflow


def create_example_workflow() -> Dict[str, Any]:
    """
    Создает пример workflow для демонстрации алгоритма
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "model.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "beautiful landscape",
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": "blurry, bad quality",
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": 42,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": "output1"
            }
        },
        "8": {
            "class_type": "UpscaleModelLoader",
            "inputs": {
                "model_name": "RealESRGAN_x4plus.pth"
            }
        },
        "9": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {
                "upscale_model": ["8", 0],
                "image": ["6", 0]
            }
        },
        "10": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["9", 0],
                "filename_prefix": "upscaled_output"
            }
        }
    }


def main():
    """
    Демонстрация работы алгоритма
    """
    print("=== Демонстрация алгоритма Queue Selected Output Nodes ===\n")
    
    # Создаем процессор workflow
    processor = ComfyWorkflowProcessor()
    
    # Создаем пример workflow
    full_workflow = create_example_workflow()
    
    print("Исходный workflow:")
    for node_id, node_data in full_workflow.items():
        print(f"  {node_id}: {node_data['class_type']}")
    
    print(f"\nВсего нод: {len(full_workflow)}")
    
    # Сценарий 1: Выполнить только базовую генерацию (без апскейла)
    print("\n--- Сценарий 1: Только базовая генерация ---")
    selected_nodes = ["7"]  # Выбираем только SaveImage для базовой генерации
    
    minimal_workflow1 = processor.queue_selected_output_nodes(full_workflow, selected_nodes)
    
    print("Ноды в обрезанном workflow:")
    for node_id in sorted(minimal_workflow1.keys()):
        print(f"  {node_id}: {minimal_workflow1[node_id]['class_type']}")
    
    # Сценарий 2: Выполнить только апскейлинг
    print("\n--- Сценарий 2: Только апскейлинг ---") 
    selected_nodes = ["10"]  # Выбираем SaveImage для апскейла
    
    minimal_workflow2 = processor.queue_selected_output_nodes(full_workflow, selected_nodes)
    
    print("Ноды в обрезанном workflow:")
    for node_id in sorted(minimal_workflow2.keys()):
        print(f"  {node_id}: {minimal_workflow2[node_id]['class_type']}")
    
    # Сценарий 3: Выполнить оба выхода
    print("\n--- Сценарий 3: Оба выхода ---")
    selected_nodes = ["7", "10"]  # Оба SaveImage
    
    minimal_workflow3 = processor.queue_selected_output_nodes(full_workflow, selected_nodes)
    
    print("Ноды в обрезанном workflow:")
    for node_id in sorted(minimal_workflow3.keys()):
        print(f"  {node_id}: {minimal_workflow3[node_id]['class_type']}")
    
    # Демонстрация работы с JSON
    print("\n--- Сохранение обрезанного workflow в JSON ---")
    with open('/tmp/minimal_workflow_example.json', 'w', encoding='utf-8') as f:
        json.dump(minimal_workflow1, f, indent=2, ensure_ascii=False)
    print("Обрезанный workflow сохранен в /tmp/minimal_workflow_example.json")


if __name__ == "__main__":
    main()