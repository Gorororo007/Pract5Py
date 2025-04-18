import random
import multiprocessing
import time
import os
import math
from collections import Counter
from threading import Thread
import psutil

def log_message(message, process_id=None):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_entry = f"[{timestamp}]"
    if process_id is not None:
        log_entry += f"[Процесс {process_id}]"
    log_entry += f" {message}\n"
    
    with open("analysis_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)

def save_result(task_name, result, process_id):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    filename = f"results_process_{process_id}.txt"
    
    with open(filename, "a", encoding="utf-8") as result_file:
        result_file.write(f"{timestamp} - {task_name}: {result}\n")
    
    log_message(f"Сохранен результат для задачи '{task_name}': {result}", process_id)

def background_saver(task_name, result, process_id):
    saver = Thread(target=save_result, args=(task_name, result, process_id))
    saver.start()

def find_most_common(numbers, process_id):
    counter = Counter(numbers)
    most_common = counter.most_common(1)[0]
    result = f"Наиболее частый элемент: {most_common[0]}, встречается {most_common[1]} раз"
    background_saver("Наиболее частый элемент", result, process_id)
    return result

def find_least_common(numbers, process_id):
    counter = Counter(numbers)
    least_common = counter.most_common()[-1]
    result = f"Наименее частый элемент: {least_common[0]}, встречается {least_common[1]} раз"
    background_saver("Наименее частый элемент", result, process_id)
    return result

def count_most_common(numbers, process_id):
    counter = Counter(numbers)
    count = counter.most_common(1)[0][1]
    result = f"Количество повторений наиболее частого числа: {count}"
    background_saver("Количество повторений наиболее частого числа", result, process_id)
    return result

def count_least_common(numbers, process_id):
    counter = Counter(numbers)
    count = counter.most_common()[-1][1]
    result = f"Количество повторений наименее частого числа: {count}"
    background_saver("Количество повторений наименее частого числа", result, process_id)
    return result

def calculate_sum(numbers, process_id):
    total = sum(numbers)
    result = f"Сумма всех чисел: {total}"
    background_saver("Сумма всех чисел", result, process_id)
    return total

def calculate_average(numbers, process_id):
    avg = sum(numbers) / len(numbers)
    result = f"Среднее арифметическое: {avg:.2f}"
    background_saver("Среднее арифметическое", result, process_id)
    return avg

def calculate_median(numbers, process_id):
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    mid = n // 2
    
    if n % 2 == 0:
        median = (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
    else:
        median = sorted_numbers[mid]
    
    result = f"Медиана: {median}"
    background_saver("Медиана", result, process_id)
    return median

def worker(task, numbers, process_id, results_queue):
    log_message(f"Начато выполнение задачи: {task.__name__}", process_id)
    
    try:
        result = task(numbers, process_id)
        results_queue.put((task.__name__, result))
        log_message(f"Завершено выполнение задачи: {task.__name__}", process_id)
    except Exception as e:
        log_message(f"Ошибка при выполнении задачи {task.__name__}: {str(e)}", process_id)
        results_queue.put((task.__name__, f"Ошибка: {str(e)}"))

def get_max_processes():
    cpu_usage = psutil.cpu_percent(interval=1)
    available_percent = (100 - cpu_usage) / 100
    logical_cores = psutil.cpu_count(logical=True)
    max_processes = min(
        math.floor(logical_cores * available_percent),
        logical_cores
    )
    return max(1, max_processes)  # Всегда хотя бы 1 процесс

def main():
    print("Анализатор списка чисел с использованием мультипроцессинга")
    
    # Получаем максимальное количество процессов
    max_processes = get_max_processes()
    print(f"Текущая загрузка процессора позволяет использовать до {max_processes} процессов")
    
    try:
        n = int(input("Введите количество элементов в списке: "))
        num_processes = int(input(f"Введите количество процессов для использования (1-{max_processes}): "))
        
        if num_processes < 1 or num_processes > max_processes:
            print(f"Ошибка: количество процессов должно быть от 1 до {max_processes}")
            return
    except ValueError:
        print("Ошибка: введите целое число")
        return
    
    # Генерация случайного списка
    numbers = [random.randint(1, 100) for _ in range(n)]
    print(f"\nСгенерирован список из {n} элементов: {numbers[:10]}... (первые 10 элементов)")
    
    # Очередь для результатов
    manager = multiprocessing.Manager()
    results_queue = manager.Queue()
    
    # Список задач
    tasks = [
        find_most_common,
        find_least_common,
        count_most_common,
        count_least_common,
        calculate_sum,
        calculate_average,
        calculate_median
    ]
    
    # Распределение задач по процессам
    processes = []
    for i in range(num_processes):
        # Распределяем задачи по процессам
        task_index = i % len(tasks)
        task = tasks[task_index]
        
        process = multiprocessing.Process(
            target=worker,
            args=(task, numbers.copy(), i + 1, results_queue)
        )
        
        processes.append(process)
        process.start()
        log_message(f"Запущен процесс {i+1} для задачи {task.__name__}")
    
    # Ожидаем завершения всех процессов
    for process in processes:
        process.join()
    
    # Собираем результаты
    print("\nРезультаты анализа:")
    while not results_queue.empty():
        task_name, result = results_queue.get()
        print(f"{task_name}: {result}")
    
    print("\nАнализ завершен. Результаты сохранены в файлы results_process_*.txt")
    print("Логи выполнения сохранены в analysis_log.txt")

if __name__ == "__main__":
    # Очистка лог-файла при каждом запуске
    if os.path.exists("analysis_log.txt"):
        os.remove("analysis_log.txt")
    
    # Очистка старых результатов
    for filename in os.listdir():
        if filename.startswith("results_process_") and filename.endswith(".txt"):
            os.remove(filename)
    
    main()