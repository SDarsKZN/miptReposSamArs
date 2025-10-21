import matplotlib.pyplot as plt
import time
from r2r_adc import R2R_ADC  # Предполагается, что предыдущий код сохранен в файле r2r_adc.py

def plot_voltage_vs_time(time_data, voltage_data, max_voltage):
    """Строит график зависимости напряжения от времени"""
    plt.figure(figsize=(10, 6))
    plt.plot(time_data, voltage_data, 'b-', linewidth=2, label='Измеренное напряжение')
    plt.title('Зависимость напряжения от времени')
    plt.xlabel('Время, с')
    plt.ylabel('Напряжение, В')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(0, max_voltage * 1.1)  # +10% от максимального напряжения для лучшего отображения
    plt.xlim(0, max(time_data) if time_data else 0)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Основной скрипт
if __name__ == "__main__":
    voltage_values = []
    time_values = []
    duration = 3.0  # Продолжительность измерений в секундах
    
    adc = None
    try:
        # Создаем объект ADC с измеренным динамическим диапазоном
        # ЗАМЕНИТЕ 3.3 на реально измеренное значение напряжения вашего ЦАП!
        adc = R2R_ADC(dynamic_range=3.3, verbose=False)
        
        start_time = time.time()
        print(f"Начало измерений на {duration} секунд...")
        
        while (time.time() - start_time) < duration:
            current_time = time.time() - start_time
            voltage = adc.get_sc_voltage()
            
            voltage_values.append(voltage)
            time_values.append(current_time)
            
            print(f"Время: {current_time:.2f} с, Напряжение: {voltage:.2f} В")
            time.sleep(0.1)  # Небольшая пауза между измерениями
        
        print("Измерения завершены, построение графика...")
        
        # Отображаем график
        plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
        
    except KeyboardInterrupt:
        print("\nИзмерения прерваны пользователем")
        if voltage_values:  # Если есть данные, строим график
            print("Построение графика по собранным данным...")
            plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range if adc else 3.3)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        # Вызываем деструктор
        if adc is not None:
            adc.__del__()
        print("Программа завершена, ресурсы освобождены")