import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
import numpy as np

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time=0.001, verbose=False):
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time
        
        self.bits_gpio = [26, 20, 19, 16, 13, 12, 25, 11]
        self.comp_gpio = 21

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial=0)
        GPIO.setup(self.comp_gpio, GPIO.IN)
    
    def __del__(self):
        """Деструктор - выставляет 0 на выход ЦАП и очищает настройки GPIO"""
        GPIO.output(self.bits_gpio, 0)
        GPIO.cleanup()
    
    def number_to_dac(self, number):
        """Подает число number на вход ЦАП"""
        binary = format(number, '08b')
        for i, pin in enumerate(self.bits_gpio):
            GPIO.output(pin, int(binary[i]))
    
    def fast_sequential_adc(self):
        """Быстрый последовательный АЦП"""
        for number in range(256):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            if GPIO.input(self.comp_gpio) == 1:
                return number
        return 255
    
    def get_sc_voltage(self):
        """Возвращает измеренное напряжение в Вольтах"""
        digital_value = self.fast_sequential_adc()
        voltage = (digital_value / 255) * self.dynamic_range
        return voltage


def plot_voltage_vs_time(time_data, voltage_data, max_voltage):
    """Строит график зависимости напряжения от времени"""
    plt.figure(figsize=(10, 6))
    plt.plot(time_data, voltage_data, 'b-', linewidth=2, label='Измеренное напряжение')
    plt.title('Зависимость напряжения от времени')
    plt.xlabel('Время, с')
    plt.ylabel('Напряжение, В')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, max_voltage * 1.1)
    plt.xlim(0, max(time_data) if time_data else 0)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_sampling_period_hist(time_data):
    """Строит распределение количества измерений по их продолжительности"""
    if len(time_data) < 2:
        print("Недостаточно данных для построения гистограммы (нужно хотя бы 2 измерения)")
        return
    
    # Создаем список для хранения промежутков времени между измерениями
    sampling_periods = []
    
    # Заполняем список разницами между соседними моментами времени
    for i in range(1, len(time_data)):
        period = time_data[i] - time_data[i-1]
        sampling_periods.append(period)
    
    print(f"\nРассчитанные периоды: {sampling_periods[:10]}...")  # Покажем первые 10
    
    # Создаем окно для отображения графика
    plt.figure(figsize=(10, 6))
    
    # Автоматически определяем границы для гистограммы
    max_period = max(sampling_periods) if sampling_periods else 0.06
    x_upper_limit = min(0.06, max_period * 1.1)  # Берем минимум из 0.06 и 110% от максимального периода
    
    # Создаем бины для гистограммы
    bins = np.linspace(0, x_upper_limit, 21)  # 20 бинов между 0 и верхним пределом
    
    # Размещаем гистограмму периодов измерений
    n, bins, patches = plt.hist(sampling_periods, bins=bins, color='skyblue', 
                               edgecolor='black', alpha=0.7, rwidth=0.8)
    
    # Задаем название графика и осей
    plt.title('Распределение периодов измерений')
    plt.xlabel('Период измерения, с')
    plt.ylabel('Количество измерений')
    
    # Задаем границы по оси X
    plt.xlim(0, x_upper_limit)
    
    # Включаем отображение сетки
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Добавляем статистическую информацию
    if sampling_periods:
        mean_period = np.mean(sampling_periods)
        std_period = np.std(sampling_periods)
        min_period = min(sampling_periods)
        max_period = max(sampling_periods)
        
        plt.axvline(mean_period, color='red', linestyle='--', linewidth=2, 
                   label=f'Среднее: {mean_period:.4f} с')
        
        # Добавляем аннотации
        plt.text(0.02, 0.95, f'Всего периодов: {len(sampling_periods)}', 
                transform=plt.gca().transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        plt.text(0.02, 0.85, f'Среднее: {mean_period:.4f} с', 
                transform=plt.gca().transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        plt.text(0.02, 0.75, f'Стандартное отклонение: {std_period:.4f} с', 
                transform=plt.gca().transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.legend()
        
        print(f"\n=== СТАТИСТИКА ПЕРИОДОВ ИЗМЕРЕНИЙ ===")
        print(f"Количество периодов: {len(sampling_periods)}")
        print(f"Средний период: {mean_period:.4f} с")
        print(f"Стандартное отклонение: {std_period:.4f} с")
        print(f"Минимальный период: {min_period:.4f} с")
        print(f"Максимальный период: {max_period:.4f} с")
        print(f"Частота измерений: {1/mean_period:.1f} Гц")
        print(f"Диапазон периодов: от {min_period:.4f} до {max_period:.4f} с")
    
    plt.tight_layout()
    plt.show()


# Основной скрипт
if __name__ == "__main__":
    voltage_values = []
    time_values = []
    duration = 15.0  # Увеличиваем продолжительность измерений
    
    adc = None
    try:
        # Создаем объект ADC
        adc = R2R_ADC(dynamic_range=3.3, compare_time=0.001, verbose=False)
        
        start_time = time.time()
        measurement_count = 0
        
        print(f"Начало измерений на {duration} секунд...")
        print("Изменяйте напряжение при помощи реостата для наблюдения изменений на графике")
        
        # Основной цикл измерений
        while (time.time() - start_time) < duration:
            current_time = time.time() - start_time
            voltage = adc.get_sc_voltage()
            
            voltage_values.append(voltage)
            time_values.append(current_time)
            measurement_count += 1
            
            # Выводим информацию о каждом измерении
            print(f"Измерение {measurement_count}: Время {current_time:.2f} с, Напряжение: {voltage:.2f} В")
            
            # Небольшая пауза между измерениями для разнообразия периодов
            time.sleep(0.01 + 0.005 * (measurement_count % 3))  # Небольшие вариации
        
        print(f"\nИзмерения завершены! Всего измерений: {measurement_count}")
        
        # Отображаем график напряжения от времени
        print("\nПостроение графика зависимости напряжения от времени...")
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
        # Отображаем гистограмму периодов измерений
        print("\nПостроение гистограммы периодов измерений...")
        plot_sampling_period_hist(time_values)
        
    except KeyboardInterrupt:
        print(f"\nИзмерения прерваны пользователем. Всего измерений: {len(voltage_values)}")
        if len(voltage_values) >= 2:
            print("Построение графиков по собранным данным...")
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else 3.3)
            plot_sampling_period_hist(time_values)
        else:
            print("Недостаточно данных для построения графиков")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем деструктор
        if adc is not None:
            adc.__del__()
        print("Программа завершена, ресурсы освобождены")